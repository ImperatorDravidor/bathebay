"""
Base scraper class with common functionality
"""

import requests
import time
import logging
from urllib.parse import urljoin
from bs4 import BeautifulSoup

from .data_validator import DataValidator

logger = logging.getLogger(__name__)


class BaseScraper:
    """Base scraper class with common functionality"""
    
    def __init__(self, base_url="https://bathingbrands.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.validator = DataValidator()
        self.scraped_urls = set()
        
    def get_page(self, url, timeout=30):
        """Get a web page with error handling and retries"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, timeout=timeout)
                response.raise_for_status()
                return BeautifulSoup(response.content, 'html.parser')
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    raise
        return None
    
    def _resolve_url(self, href, base_url):
        """Resolve relative URLs to absolute URLs"""
        if href.startswith('//'):
            return 'https:' + href
        elif href.startswith('/'):
            return urljoin(self.base_url, href)
        elif href.startswith('http'):
            return href
        else:
            return urljoin(base_url, href)
    
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        return " ".join(text.strip().split())
    
    def extract_text_from_element(self, element):
        """Extract clean text from a BeautifulSoup element"""
        if not element:
            return ""
        return self.clean_text(element.get_text())
    
    def find_elements_by_text(self, soup, text_patterns, tag_types=None):
        """Find elements containing specific text patterns"""
        if tag_types is None:
            tag_types = ['div', 'span', 'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
        elements = []
        for tag_type in tag_types:
            for pattern in text_patterns:
                found = soup.find_all(tag_type, string=lambda text: text and pattern.lower() in text.lower())
                elements.extend(found)
        
        return elements 