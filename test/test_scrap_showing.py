import time
from datetime import datetime

from google_scraper import GoogleScraper
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from bs4.element import Tag

# Type hinting
ExhibitionData = Dict[str, Union[str, datetime]]

OPTIONS = [
    "-headless",  # Remove if you debug
    "--log-level=0",
]

PROXY_COOKIE_KEYWORD = "cookie"
COOKIE_ANCHOR_KEYWORD = ["refuser", "accepter", "accept", "refuse"]
website_entrypoint_url = "https://www.offi.fr/expositions-musees/programme.html"


def find_element_by_inner_text(wd: webdriver.Firefox, inner_text: str):
    return wd.find_elements(
        By.XPATH,
        f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{inner_text}')]",
    )


def find_accept_cookie_popup(wd: webdriver.Firefox) -> List:
    for keyword in COOKIE_ANCHOR_KEYWORD:
        print("INFO: Looking for cookie anchor keyword: ", keyword)
        elements: List[WebElement] = find_element_by_inner_text(wd, keyword)
        if elements:
            break

    if elements:
        elements[0].click()


def scrape_html_exhibitions_offi(content: str) -> List[ExhibitionData]:
    soup: BeautifulSoup = BeautifulSoup(content, "html.parser")
    exhibitions: List[Tag] = soup.find_all(
        "div", class_="mini-fiche-details d-flex has-padding-20"
    )
    full_res = []
    for exhibition in exhibitions:
        exhibition_name: str = exhibition.find("span", itemprop="name").text.strip()
        exhibition_place: str = (
            exhibition.find("div", class_="event-place pt-1").find("a").text.strip()
        )
        exhibition_start_date: str = exhibition.find("meta", itemprop="startDate")[
            "content"
        ]
        exhibition_end_date: str = exhibition.find("meta", itemprop="endDate")[
            "content"
        ]
        full_res.append(
            {
                "name": exhibition_name,
                "place": exhibition_place,
                "exhibition_start_date": datetime.strptime(
                    exhibition_start_date, "%Y-%m-%d"
                ),
                "exhibition_end_date": datetime.strptime(
                    exhibition_end_date, "%Y-%m-%d"
                ),
            }
        )
    return full_res


def crawl_exhibitions_offi_next_page(
    wb: webdriver.Firefox, is_first_page: bool = False
) -> int:
    CURRENT_PAGE_CLASS = "page-item active"
    current_page_number_ref_tag = wb.find_element(
        By.XPATH, f"//li[@class='{CURRENT_PAGE_CLASS}']/a"
    )
    current_page_number = int(current_page_number_ref_tag.text)

    if (is_first_page == True) or (is_first_page == False and current_page_number > 1):
        next_page_ref_tag = wb.find_element(By.XPATH, f"//a[@id='page_suivante']")
        next_page_ref_tag.click()
    else:
        print("INFO: No next page")
        return 0  # No next page


with GoogleScraper(lang="fr", extra_options=OPTIONS) as scraper:
    scraper._search_on(url_link=website_entrypoint_url)
    wd: webdriver.Firefox = scraper.driver

    # Get HTML and scrape with bs4
    res = []
    content = wd.execute_script("return document.body.innerHTML")
    res.extend(scrape_html_exhibitions_offi(content=content))

    current_page = 1
    while True:
        current_page = crawl_exhibitions_offi_next_page(
            wb=wd, is_first_page=(current_page == 1)
        )
        if current_page == 0:
            break
        res.extend(scrape_html_exhibitions_offi(content=content))
    import pprint

    pprint.pprint(res)
