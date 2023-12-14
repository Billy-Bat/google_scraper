from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
import urllib
import requests
import http.cookiejar as cookielib
from requests_html import HTMLSession
from typing import Any, Tuple, Dict, List
import json
from pprint import pprint
from utils.multithread import multithread_callable
from pathlib import Path

from utils.utils import put_cookies_in_jar

GOOGLE_HOME = "https://www.google.fr/"
MAPS_PATH = "maps/search/"
COOKIE_ANCHOR = "Tout refuser"  # WARNING: Dependant on browser language here French


class CoordinatesScrapper(object):
    """
    Class to scrap google maps coordinates given an input string
    """

    USER_AGENT = "education_illustration 0.1"
    BROWSER_PATH = f"{Path(__file__).parent}/geckodriver/geckodriver"
    IMPLICIT_WAIT_BEFORE_NO_SUCH_ELEMENT_SEC = 1

    # subject to Changes, double check
    ANCHOR_FOR_MULTIPLE_RESULTS = "m6QErb DxyBCb kA9KIf dS8AEf ecceSd"
    ANCHOR_ITEM_IN_RESULT_LIST = "hfpxzc"

    def __init__(self, lang: str = "fr") -> None:
        # Setup Driver
        options = webdriver.FirefoxOptions()
        options.add_argument(f"user-agent={self.USER_AGENT}")
        service = Service(executable_path=self.BROWSER_PATH)
        self.driver: webdriver.Firefox = webdriver.Firefox(
            service=service, options=options
        )
        self.driver.implicitly_wait(
            time_to_wait=self.IMPLICIT_WAIT_BEFORE_NO_SUCH_ELEMENT_SEC
        )
        self.cookies = None
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

    def get_requests_response_content(self, url: str) -> requests.Response:
        """
        get the raw html from the request module, not using a driver
        """
        resp = requests.get(
            url=url, params=None, data=None, headers=None, cookies=self.cookijar
        )
        if resp.status_code != 200:
            print({resp.text})
            print(f"FAIL: see response with status code {resp.status_code}")
            resp.raise_for_status()
        return resp

    def get_requests_response_render_html(self, url: str) -> requests.Response:
        """
        render html for the given session
        """
        session = HTMLSession(mock_browser=True)
        r = session.get(
            url=url, params=None, data=None, headers=None, cookies=self.cookijar
        )
        r.html.render()
        return r

    def create_url_link(self, search_str: str) -> str:
        """
        create a search url for google maps given a search string
        """
        params = {"authuser": "0", "entry": "ttu", "api": 1, "hl": self.lang}
        params["query"] = CoordinatesScrapper.encode_search_str(search_str=search_str)
        params["query"] = search_str
        return GOOGLE_HOME + MAPS_PATH + f"?{urllib.parse.urlencode(params)}"

    def get_current_page_state(self):
        """
        get the script values that describe the state of the page, includes coordinates data
        """
        # This part contains the information with the initial states (everything used in displaying information in the browser for that request)
        script_content = self.current_page_source.split(
            ";window.APP_INITIALIZATION_STATE="
        )[1].split(";window.APP_FLAGS")[0]
        result = json.loads(script_content)
        return result

    def search_on(self, url_link: str) -> None:
        """
        makes the driver go to the given url
        """
        self.driver.get(url=url_link)

    def go_to_first_result_from_multiple(self) -> None:
        """
        if google maps is uncertains, it returns a list of result
        this functions selects the first one (the best candidate ?) and makes the driver go to the result
        """
        top_result = self.driver.find_element(
            By.CLASS_NAME, self.ANCHOR_ITEM_IN_RESULT_LIST
        )
        link = top_result.get_attribute("href")
        self.search_on(link)

    def get_coordinates(self, search_str: str, take_first_on_multiple_res: bool = True):
        """
        Retrieves coordinates given an search string,
        if Google Maps returns a list of result (i.e: it is uncertains about the result) the fcn
        will go to the first result from the list, considered to be the best candidate
        """
        url_to_request = self.create_url_link(search_str=search_str)
        self.search_on(url_link=url_to_request)
        # Check if the query returned a single result or if Google returned a list of candidates
        if (self.ANCHOR_FOR_MULTIPLE_RESULTS in self.current_page_source) and (
            take_first_on_multiple_res == True
        ):
            print(
                f"WARNING: Google returned multiples results on {search_str}, taking the first candidate"
            )
            self.go_to_first_result_from_multiple()

        page_state = self.get_current_page_state()
        long, lat = (safe_get(page_state, 0, 0, 1), safe_get(page_state, 0, 0, 2))
        return (lat, long)


def safe_get(data: List[List[float | int]], *keys: int):
    for key in keys:
        try:
            data = data[key]
        except (IndexError, TypeError, KeyError):
            return None
    return data


def thread_result(thread_number: int):
    search_examples = [
        "Convent, Játiva",
        "Hospital de la Caridad, Seville",
        "Via Nicolò Lionello, 1, Udine",
        "Castle chapel, Riom (Puy-de-Dôme)",
        "Maryland Historical Society, Baltimore",
        "Church of Santo Domingo el Antiguo, Toledo",
        "Duomo, Sansepolcro",
        "Museo de San Petronio, Bologna",
        "Museo Nazionale di Villa Guinigi, Lucca",
        "Stanza della Fama, Palazzo Vitelli a Sant'Egidio, Città di Castello",
        "University of Liège, Liège",
        "Convent church of St. Cyriakus, Gernrode",
        "Silvacane Abbey, La Roque-d'Anthéron (Bouches-du-Rhône)",
    ]

    with CoordinatesScrapper() as scrapper:
        scrapper.validate_google_cookies()
        result = {}
        for s_ in search_examples:
            result[s_] = scrapper.get_coordinates(s_)


if __name__ == "__main__":
    thread_result(thread_number=1)
    # thread_list = [{
    #     "thread_number": i
    # } for i in range(0, 1)]
    # multithread_callable(func=thread_result, kwargs_list=thread_list)
