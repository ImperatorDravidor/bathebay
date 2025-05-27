#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from products.scraper_enhanced import EnhancedBathingBrandsScraper
import requests
from bs4 import BeautifulSoup

def find_huum_products():
    """Find valid HUUM product URLs"""
    
    print("🔍 Finding HUUM products...")
    
    scraper = EnhancedBathingBrandsScraper()
    
    # Start from HUUM brand page
    huum_url = "https://bathingbrands.com/huum"
    
    try:
        response = requests.get(huum_url, headers=scraper.session.headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find product links
        product_links = []
        
        # Look for product links in various formats
        for link in soup.find_all('a', href=True):
            href = link['href']
            if 'huum' in href.lower() and any(keyword in href.lower() for keyword in ['cliff', 'drop', 'steel', 'hive']):
                full_url = scraper._resolve_url(href, huum_url)
                product_links.append(full_url)
        
        # Remove duplicates
        product_links = list(set(product_links))
        
        print(f"✅ Found {len(product_links)} potential HUUM product URLs:")
        for i, url in enumerate(product_links[:10], 1):  # Show first 10
            print(f"  {i}. {url}")
            
        # Test the first URL
        if product_links:
            test_url = product_links[0]
            print(f"\n🧪 Testing first URL: {test_url}")
            
            product_data = scraper.extract_product_data(test_url)
            if product_data:
                print(f"✅ Successfully extracted: {product_data.get('title', 'Unknown')}")
                return test_url
            else:
                print("❌ Failed to extract data")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        
    return None

if __name__ == "__main__":
    find_huum_products() 