"""
Utility functions for scrapers
"""
import time
import logging
from datetime import datetime
from dateutil import parser

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_datetime(date_string):
    """
    Parse datetime string from API to Python datetime
    Handles ISO 8601 format: 2024-01-15T10:30:00+0500
    """
    try:
        return parser.isoparse(date_string)
    except (ValueError, TypeError):
        logger.warning(f"Could not parse date: {date_string}")
        return None


def safe_get(data, *keys, default=None):
    """
    Safely get nested dictionary values
    
    Example:
        safe_get(data, 'employer', 'name', default='Unknown')
    """
    for key in keys:
        if isinstance(data, dict):
            data = data.get(key)
            if data is None:
                return default
        else:
            return default
    return data


def normalize_salary(salary_data):
    """
    Extract salary information from API response
    
    Returns: dict with salary_min, salary_max, currency, gross
    """
    if not salary_data:
        return {
            'salary_min': None,
            'salary_max': None,
            'currency': 'UZS',
            'gross': False
        }
    
    return {
        'salary_min': salary_data.get('from'),
        'salary_max': salary_data.get('to'),
        'currency': salary_data.get('currency', 'UZS'),
        'gross': salary_data.get('gross', False)
    }


def rate_limit(delay=1):
    """
    Simple rate limiting - wait between requests
    """
    time.sleep(delay)


def clean_text(text):
    """
    Clean text from HTML tags and extra whitespace
    """
    if not text:
        return ""
    
    # Remove HTML tags (basic cleaning)
    import re
    text = re.sub(r'<[^>]+>', '', text)
    
    # Remove extra whitespace
    text = ' '.join(text.split())
    
    return text.strip()


def extract_area_name(area_data):
    """
    Extract area (location) name from API response
    """
    if not area_data:
        return "Unknown"
    
    # Sometimes it's nested: {"area": {"name": "Tashkent"}}
    if isinstance(area_data, dict):
        return area_data.get('name', 'Unknown')
    
    return str(area_data)


def log_scraping_stats(stats):
    """
    Log scraping statistics
    """
    logger.info("=" * 50)
    logger.info("SCRAPING STATISTICS")
    logger.info("=" * 50)
    for key, value in stats.items():
        logger.info(f"{key}: {value}")
    logger.info("=" * 50)