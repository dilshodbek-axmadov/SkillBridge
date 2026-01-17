"""
Base scraper class with common functionality
"""
import requests
import logging
from abc import ABC, abstractmethod
from .config import USER_AGENT, REQUEST_DELAY
from .utils import rate_limit

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Abstract base class for all scrapers
    """
    
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': USER_AGENT,
            'HH-User-Agent': USER_AGENT,
        })
    
    def get(self, endpoint, params=None):
        """
        Make GET request to API
        
        Returns: response JSON or None if error
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            rate_limit(REQUEST_DELAY)  # Be polite to API
            
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {e}")
            logger.error(f"URL: {url}")
            logger.error(f"Response: {response.text}")
            return None
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Error: {e}")
            return None
            
        except ValueError as e:
            logger.error(f"JSON Decode Error: {e}")
            return None
    
    @abstractmethod
    def scrape(self):
        """
        Main scraping method - must be implemented by subclasses
        """
        pass