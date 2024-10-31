from abc import ABC, abstractmethod
from typing import List, Dict, Any, Union, Optional

import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common import TimeoutException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from structlog import BoundLogger, get_logger

from app.core.enums import ChromeOptionFlag, ChromePreferences

# Logger
logger: BoundLogger = get_logger()


class ChromeOptionsBuilder:
    """
    Chrome options builder for the ChromeOptions class.
    """

    def __init__(self):
        self._options: List[str] = []
        self._preferences: Dict[str, Any] = {}

    def add_option(self, option: Union[ChromeOptionFlag, str]) -> 'ChromeOptionsBuilder':
        """
        Add Chrome option to the ChromeOptions class.
        """

        if isinstance(option, ChromeOptionFlag):
            self._options.append(option.value)
        else:
            self._options.append(option)
        return self

    def add_preference(self, preference: ChromePreferences) -> 'ChromeOptionsBuilder':
        """
        Add Chrome preference to the ChromeOptions class
        """

        self._preferences[preference.key] = preference.value
        return self

    def add_default_options(self) -> 'ChromeOptionsBuilder':
        """
        Add default Chrome options.
        """

        self._options.extend(ChromeOptionFlag.get_default_options())
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build Chrome options and preferences.
        """

        return {
            'arguments': self._options,
            'preferences': self._preferences
        }


class ScraperConfig:
    """
    This class is used to store the configuration of the scraper.
    """

    def __init__(self,
                 headers: Optional[Dict[str, str]] = None,
                 timeout: int = 30,
                 retry_times: int = 3,
                 chrome_options: Optional[Dict[str, Any]] = None):
        self.headers = headers or {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        self.timeout = timeout
        self.retry_times = retry_times
        self.chrome_options = chrome_options or ChromeOptionsBuilder().add_default_options().build()


class AbstractWebScrapper(ABC):
    """
    Define the interface for the web scraper.
    """

    @abstractmethod
    def fetch_data(self, url: str) -> Any:
        """
        Fetch data from the given URL.
        """
        pass

    @abstractmethod
    def parse_data(self, content: Any) -> Any:
        """
        Parse the data from the content.
        """
        pass

    @abstractmethod
    def process_data(self, data: Any) -> Any:
        """
        Process the data.
        """
        pass


class BaseWebScraper(AbstractWebScrapper):
    """
    The base class for the web scraper, which provides the basic implementation of the web scraper.
    """

    def __init__(self, config: ScraperConfig):
        self.config = config
        self._driver: Optional[WebDriver] = None
        self._session: Optional[requests.Session] = None

    def _init_selenium(self) -> WebDriver:
        """
        Initialize the Selenium WebDriver.
        """

        options = webdriver.ChromeOptions()

        for key, value in self.config.chrome_options.items():
            options.add_argument(value)

        return webdriver.Chrome(options=options)

    def _init_session(self) -> requests.Session:
        """
        Initialize the requests session
        """

        session = requests.Session()
        session.headers.update(self.config.headers)
        return session

    def _get_with_retry(self, url: str) -> Any:
        """
        Get the content of the URL with retry.
        """

        for attempt in range(self.config.retry_times):
            try:
                if not self._session:
                    self._session = self._init_session()

                response = self._session.get(url, timeout=self.config.timeout)
                response.raise_for_status()
                return response

            except Exception as e:
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt == self.config.retry_times - 1:
                    raise

    def fetch_data(self, url: str) -> Any:
        """
        Fetch data from the given URL.
        """

        return self._get_with_retry(url)

    def parse_data(self, content: Any) -> Any:
        """
        Parse the data from the content.
        """

        return BeautifulSoup(content, 'html.parser')

    def process_data(self, data: Any) -> Any:
        """
        Process the data.
        """

        return data

    def close(self):
        """
        Close the web scraper.
        """

        if self._driver:
            self._driver.quit()
        if self._session:
            self._session.close()


class SeleniumWebScraper(BaseWebScraper):
    """
    The Selenium web scraper, which provides the implementation of the web scraper using Selenium.
    """

    def fetch_data(self, url: str) -> Any:
        if not self._driver:
            self._driver = self._init_selenium()

        self._driver.get(url)

        return self._driver.page_source

    def wait_for_element(self, locator, timeout: Optional[int] = None):
        timeout = timeout or self.config.timeout
        return WebDriverWait(self._driver, timeout).until(
            ec.presence_of_element_located(locator)
        )


class NationalStatWebScraper(SeleniumWebScraper):
    """
    The web scraper for the national statistics website.
    """

    def _get_with_retry(self, url: str) -> Any:
        if not self._driver:
            self._driver = self._init_selenium()
            self._driver.set_page_load_timeout(self.config.timeout)

        for attempt in range(self.config.retry_times):
            try:
                self._driver.get(url)

                return self._driver.page_source

            except TimeoutException as e:
                self._driver.execute_script("window.stop();")
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")

                if attempt == self.config.retry_times - 1:
                    raise

    def fetch_data(self, url: str) -> Any:
        """
        Fetch data from the given URL.
        """

        return self._get_with_retry(url)

    def parse_data(self, content: Any) -> Any:
        """
        Parse the data from the content.
        """

        soup = BeautifulSoup(content, 'html.parser')
        table = soup.find('table', {'id': 'ctl05_gv'})
        return table

    def process_data(self, data: Any) -> Any:
        """
        Process the data.
        """

        rows = data.find_all('tr')
        results = []

        for row in rows[1:]:
            columns = row.find_all('td')
            result = {
                'date': columns[0].text.strip(),
                'title': columns[1].text.strip(),
                'link': columns[1].find('a')['href']
            }
            results.append(result)

        return results
