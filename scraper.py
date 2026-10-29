"""Selenium + headless Chrome scraper for MIT Technology Review."""
import os
import re
import urllib.parse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

BASE_URL = "https://www.technologyreview.com"
# Article URLs look like https://www.technologyreview.com/2025/03/11/1112345/some-slug/
ARTICLE_RE = re.compile(r"^https://www\.technologyreview\.com/\d{4}/\d{2}/\d{2}/\d+/[^/?#]+/?$")

LINKS_JS = """
const scope = document.querySelector('main') || document.body;
return Array.from(scope.querySelectorAll('a[href]')).map(a => a.href);
"""

PARAGRAPHS_JS = """
let ps = document.querySelectorAll('article p, main p');
if (ps.length === 0) ps = document.querySelectorAll('p');
return Array.from(ps).map(p => p.innerText.trim()).filter(t => t.length > 40);
"""


def make_driver():
    opts = Options()
    opts.binary_location = os.environ.get("CHROME_BIN", "/usr/bin/google-chrome")
    for arg in (
        "--headless=new",
        "--no-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
        "--window-size=1920,1080",
        "--disable-blink-features=AutomationControlled",
        "--blink-settings=imagesEnabled=false",
    ):
        opts.add_argument(arg)
    opts.page_load_strategy = "eager"

    service = Service(os.environ.get("CHROMEDRIVER_PATH", "/usr/local/bin/chromedriver"))
    driver = webdriver.Chrome(service=service, options=opts)
    driver.set_page_load_timeout(45)

    # Look like regular Chrome rather than "HeadlessChrome"
    ua = driver.execute_script("return navigator.userAgent").replace("HeadlessChrome", "Chrome")
    driver.execute_cdp_cmd("Network.setUserAgentOverride", {"userAgent": ua})
    return driver


def _article_links(driver):
    links = []
    for href in driver.execute_script(LINKS_JS) or []:
        href = href.split("#")[0].split("?")[0]
        if ARTICLE_RE.match(href) and href not in links:
            links.append(href)
    return links


def _wait_for_links(driver, timeout=20):
    try:
        return WebDriverWait(driver, timeout).until(lambda d: _article_links(d) or False)
    except TimeoutException:
        return []


def search_site(driver, keyword):
    """Use the site's own search page and return the first article result."""
    q = urllib.parse.quote_plus(keyword)
    for url in (f"{BASE_URL}/search/?s={q}", f"{BASE_URL}/?s={q}"):
        try:
            driver.get(url)
        except TimeoutException:
            pass  # eager load may still have rendered results
        links = _wait_for_links(driver)
        if links:
            return links[0]
    return None


def search_fallback(driver, keyword):
    """Fallback: DuckDuckGo restricted to technologyreview.com, still driven by Selenium."""
    q = urllib.parse.quote_plus(f"site:technologyreview.com {keyword}")
    driver.get(f"https://html.duckduckgo.com/html/?q={q}")
    hrefs = driver.execute_script(
        "return Array.from(document.querySelectorAll('a.result__a')).map(a => a.href);"
    ) or []
    for href in hrefs:
        parsed = urllib.parse.urlparse(href)
        target = urllib.parse.parse_qs(parsed.query).get("uddg", [href])[0]
        target = target.split("#")[0].split("?")[0]
        if ARTICLE_RE.match(target):
            return target
    return None


def extract_article(driver, url):
    try:
        driver.get(url)
    except TimeoutException:
        pass
    try:
        WebDriverWait(driver, 20).until(lambda d: len(d.execute_script(PARAGRAPHS_JS) or []) > 0)
    except TimeoutException:
        pass

    title = driver.execute_script("const h = document.querySelector('h1'); return h ? h.innerText.trim() : '';")
    paragraphs = driver.execute_script(PARAGRAPHS_JS) or []
    body = " ".join(paragraphs)
    if not body:  # paywall / layout change: fall back to meta description
        body = driver.execute_script(
            "const m = document.querySelector('meta[name=\"description\"], meta[property=\"og:description\"]');"
            "return m ? m.content : '';"
        ) or ""
    return title, body


def fetch_first_article(keyword):
    """Returns (url, title, body_text). Raises RuntimeError if nothing is found."""
    driver = make_driver()
    try:
        url = search_site(driver, keyword)
        if not url:
            url = search_fallback(driver, keyword)
        if not url:
            raise RuntimeError(f"No MIT Technology Review article found for '{keyword}'")
        title, body = extract_article(driver, url)
        return url, title, body
    except WebDriverException as e:
        raise RuntimeError(f"Browser error: {e.msg}") from e
    finally:
        driver.quit()
