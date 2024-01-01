from selenium.common.exceptions import NoSuchElementException
import backoff
from selenium import webdriver
from selenium.webdriver.common.by import By
import urllib
import requests
import http.cookiejar as cookielib
import time
from typing import Any, Tuple, Dict, List
import json
import random
import base64
from .utils.utils import put_cookies_in_jar
from google_scraper.driver_config import USER_AGENTS

GOOGLE_HOME = "https://www.google.fr/"
SEARCH_PATH = "search"
MAPS_PATH = "maps/search/"
COOKIE_ANCHOR = "Tout refuser"  # WARNING: Dependant on browser language here French


class CoordinatesScrapper(object):
    """
    Class to scrap google maps coordinates given an input string
    """

    IMPLICIT_WAIT_BEFORE_NO_SUCH_ELEMENT_SEC = 4

    # subject to Changes, double check
    ANCHOR_MAPS_FOR_MULTIPLE_RESULTS = "m6QErb DxyBCb kA9KIf dS8AEf ecceSd"
    ANCHOR_MAPS_ITEM_IN_RESULT_LIST = "hfpxzc"

    ANCHOR_SEARCH_FOR_IMG_RESULT_DIV = "isv-r PNCib ViTmJb BUooTd"

    ANCHOR_SIDE_BAR_IMG_WITH_SOURCE_CLASS = "sFlh5c pT0Scc iPVvYb"
    ANCHOR_SIDE_BAR_IMG_IMG_TAG_CLASS = "sFlh5c pT0Scc"

    SLEEP_BETWEEN_REQUESTS_SEC = 3

    def __init__(
        self,
        lang: str = "fr",
        extra_options: List[str | Any] = None,
        cookies: List[Dict[str, str]] = None,
    ) -> None:
        # Setup Driver
        options = webdriver.FirefoxOptions()
        options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")

        for option in extra_options:
            options.add_argument(option)
        self.driver: webdriver.Firefox = webdriver.Firefox(
            service=None,
            options=options,
        )
        self.driver.implicitly_wait(
            time_to_wait=self.IMPLICIT_WAIT_BEFORE_NO_SUCH_ELEMENT_SEC
        )
        if cookies:
            for cookie in cookies:
                self.driver.add_cookie(cookie)
        self.lang = lang

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.close()

    @property
    def current_page_source(self) -> str:
        """
        returns: a string of the current page html
        """
        return self.driver.page_source

    @property
    def driver_cookies(self):
        self.driver.get_cookies()

    def validate_google_cookies(self) -> None:
        """
        validate google cookies by clicking accept
        """
        self.driver.get(GOOGLE_HOME)
        skip_cookie_el = self.driver.find_element(
            By.XPATH, f"//*[text()='{COOKIE_ANCHOR}']"
        )
        parent_el = skip_cookie_el.find_element(By.XPATH, "..")
        if parent_el.aria_role == "button":
            parent_el.click()
        # Selenium cookies
        self.cookies = self.driver.get_cookies()

        # cookieJar
        self.cookijar = cookielib.CookieJar(policy=None)
        put_cookies_in_jar(selenium_cookies=self.cookies, cookie_jar=self.cookijar)

    def reject_google_cookies(self) -> None:
        """ """
        raise NotImplementedError("TBD")

    @staticmethod
    def encode_search_str(search_str: str) -> str:
        """
        encode a search string into an url
        """
        return urllib.parse.quote_plus(search_str)

    def _create_url_link(self, search_str: str, type: str = "maps") -> str:
        """
        create a search url for google maps given a search string
        """
        params = {"authuser": "0", "entry": "ttu", "api": 1, "hl": self.lang}
        if type == "maps":
            params["query"] = search_str
            return GOOGLE_HOME + MAPS_PATH + f"?{urllib.parse.urlencode(params)}"
        elif type == "images":
            params.update(
                {
                    "tbm": "isch",
                    "q": CoordinatesScrapper.encode_search_str(search_str=search_str),
                }
            )
            params["q"] = search_str
            return GOOGLE_HOME + SEARCH_PATH + f"?{urllib.parse.urlencode(params)}"

    def _maps_get_current_page_state(self) -> List[Any]:
        """
        get the script values that describe the state of the page, includes coordinates data
        """
        # This part contains the information with the initial states (everything used in displaying information in the browser for that request)
        script_content = self.current_page_source.split(
            ";window.APP_INITIALIZATION_STATE="
        )[1].split(";window.APP_FLAGS")[0]
        result = json.loads(script_content)
        return result

    def _search_on(self, url_link: str) -> None:
        """
        makes the driver go to the given url
        """
        self.driver.get(url=url_link)

    def _maps_go_to_first_result_from_multiple(self) -> None:
        """
        if google maps is uncertains, it returns a list of result
        this functions selects the first one (the best candidate ?) and makes the driver go to the result
        """
        top_result = self.driver.find_element(
            By.CLASS_NAME, self.ANCHOR_MAPS_ITEM_IN_RESULT_LIST
        )
        link = top_result.get_attribute("href")
        self._search_on(link)

    def get_maps_coordinates(
        self, search_str: str, take_first_on_multiple_res: bool = True
    ) -> Tuple[float, float]:
        """
        Retrieves coordinates given an search string,
        if Google Maps returns a list of result (i.e: it is uncertains about the result) the fcn
        will go to the first result from the list, considered to be the best candidate
        """
        url_to_request = self._create_url_link(search_str=search_str, type="maps")
        self._search_on(url_link=url_to_request)
        # Check if the query returned a single result or if Google returned a list of candidates
        if (self.ANCHOR_MAPS_FOR_MULTIPLE_RESULTS in self.current_page_source) and (
            take_first_on_multiple_res is True
        ):
            print(
                f"WARNING: Google returned multiples results on {search_str}, taking the first candidate"
            )
            self._maps_go_to_first_result_from_multiple()

        page_state = self._maps_get_current_page_state()
        long, lat = (safe_get(page_state, 0, 0, 1), safe_get(page_state, 0, 0, 2))
        return (lat, long)

    def _slow_down(self) -> None:
        self.SLEEP_BETWEEN_REQUESTS_SEC += 1
        time.sleep(self.SLEEP_BETWEEN_REQUESTS_SEC)

    def handle_failure(self) -> None:
        pass

    @backoff.on_exception(
        backoff.expo,
        NoSuchElementException,
        max_time=60,
        max_tries=10,
        on_backoff=lambda x: print(
            f"Retrying to get image on backoff see error: \n {x}"
        ),
    )
    def _get_img_url_for_first_result(self, search_str: str) -> str:
        url_to_request = self._create_url_link(search_str=search_str, type="images")
        self._search_on(url_link=url_to_request)

        first_result = self.driver.find_element(
            by=By.XPATH,
            value=f"//div[contains(@class, '{self.ANCHOR_SEARCH_FOR_IMG_RESULT_DIV}')]",
        )
        first_result.click()

        try:
            img_container_img_tag = self.driver.find_element(
                by=By.XPATH,
                value=f"//img[contains(@class, '{self.ANCHOR_SIDE_BAR_IMG_WITH_SOURCE_CLASS}')]",
            )
        except NoSuchElementException:
            img_container_img_tag = self.driver.find_element(
                by=By.XPATH,
                value=f"//img[contains(@class, '{self.ANCHOR_SIDE_BAR_IMG_IMG_TAG_CLASS}')]",
            )

        url = img_container_img_tag.get_attribute("src")
        return url

    def get_img_for_search_string(self, search_str: str) -> bytes:
        """
        Retrieves the image bytes content for the given search string
        The first result from google images is taken
        """
        try:
            url_img = self._get_img_url_for_first_result(search_str=search_str)
        except NoSuchElementException as e:
            print(f"Fail: see error {e}, retrying once after waiting 1min")
            time.sleep(60)
            url_img = self._get_img_url_for_first_result(search_str=search_str)

        if "data:image" in url_img:
            print(
                f"WARNING: image is base64 encoded for search string {search_str} returning raw value"
            )
            result = base64.b64decode(url_img.split("base64,")[1].encode("utf-8"))
        else:
            try:
                content = requests.get(
                    url=url_img, headers={"User-Agent": random.choice(USER_AGENTS)}
                )
                result = content.content
            except requests.exceptions.SSLError as e:
                print(f"FAIL: SSLError, See: \n {e}")
                return None

            if content.status_code != 200:
                print({content.text})
                print(f"FAIL: see response with status code {content.status_code}")
                return None

        return result


def safe_get(data: List[List[float | int]], *keys: int):
    for key in keys:
        try:
            data = data[key]
        except (IndexError, TypeError, KeyError):
            return None
    return data
