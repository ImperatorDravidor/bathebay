#!/usr/bin/env python
"""
Simple test script to verify the scraper functionality
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from products.scraper import BathingBrandsScraper

def test_scraper():
    """Test the scraper with a specific product URL"""
    scraper = BathingBrandsScraper()
    
    # Test with a known product URL
    test_url = "https://www.bathingbrands.com/products/huum/sauna/accessories"
    
    print(f"Testing scraper with URL: {test_url}")
    
    # Get product links from category
    product_links = scraper.get_product_links_from_category(test_url)
    print(f"Found {len(product_links)} product links")
    
    if product_links:
        # Test scraping the first product
        first_product_url = product_links[0]
        print(f"\nTesting product scraping with: {first_product_url}")
        
        product_data = scraper.scrape_product(first_product_url)
        if product_data:
            print("Successfully scraped product data:")
            for key, value in product_data.items():
                if key != 'image_urls':
                    print(f"  {key}: {value}")
                else:
                    print(f"  {key}: {len(value)} images found")
        else:
            print("Failed to scrape product data")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_scraper() 