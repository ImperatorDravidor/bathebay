#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from products.scrapers import EnhancedBathingBrandsScraper
from products.models import Product

def test_huum_product():
    """Test scraping a specific HUUM product"""
    
    # HUUM DROP 4.5 product URL - confirmed working
    test_url = "https://bathingbrands.com/54661/huum/drop-45/electric-heaters"
    
    print("🔥 Testing Enhanced HUUM Scraper...")
    print(f"🎯 Target URL: {test_url}")
    
    scraper = EnhancedBathingBrandsScraper()
    
    # Extract product data
    print("\n📊 Extracting product data...")
    product_data = scraper.extract_product_data(test_url)
    
    if product_data:
        print(f"✅ Successfully extracted: {product_data['title']}")
        print(f"   SKU: {product_data['sku']}")
        print(f"   Model: {product_data.get('model_name', 'N/A')}")
        print(f"   Price: ${product_data.get('price', 'N/A')}")
        print(f"   Brand: {product_data['brand']}")
        
        print(f"\n📝 Content Extraction:")
        print(f"   Description: {len(product_data.get('full_description', ''))} chars")
        print(f"   Features: {len(product_data.get('features', ''))} chars")
        print(f"   Includes: {len(product_data.get('includes', ''))} chars")
        print(f"   Technical: {len(product_data.get('technical_info', ''))} chars")
        print(f"   Shipping: {len(product_data.get('shipping_info', ''))} chars")
        
        print(f"\n🖼️ Media & Docs:")
        print(f"   Images: {len(product_data.get('images', []))}")
        print(f"   Specifications: {len(product_data.get('specifications_dict', {}))}")
        print(f"   Documents: {len(product_data.get('documents', []))}")
        
        # Save to database
        print(f"\n💾 Saving to database...")
        product = scraper.save_product(product_data)
        
        if product:
            print(f"✅ Saved product: {product.title}")
            print(f"   ID: {product.id}")
            print(f"   Admin URL: http://127.0.0.1:8000/admin/products/product/{product.id}/change/")
            
            # Show extracted content samples
            if product.full_description:
                print(f"\n📖 Description Sample:")
                print(f"   {product.full_description[:200]}...")
            
            if product.features:
                print(f"\n⭐ Features Sample:")
                print(f"   {product.features[:200]}...")
            
            if product.technical_info:
                print(f"\n🔧 Technical Sample:")
                print(f"   {product.technical_info[:200]}...")
            
            # Show specifications
            specs = product.product_specifications.all()
            if specs:
                print(f"\n📋 Specifications ({specs.count()}):")
                for spec in specs[:5]:
                    print(f"   • {spec.name}: {spec.value}")
                if specs.count() > 5:
                    print(f"   ... and {specs.count() - 5} more")
            
            # Show images
            images = product.images.all()
            if images:
                print(f"\n🖼️ Images ({images.count()}):")
                for img in images[:3]:
                    print(f"   • {img.image_type}: {img.image_url}")
                if images.count() > 3:
                    print(f"   ... and {images.count() - 3} more")
            
            return product
        else:
            print("❌ Failed to save product")
    else:
        print("❌ Failed to extract product data")
    
    return None

if __name__ == "__main__":
    test_huum_product() 