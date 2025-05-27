#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from products.models import Product

# Check HUUM products
huum_products = Product.objects.filter(brand__icontains='HUUM')
print(f"🔥 Total HUUM products: {huum_products.count()}")

# Show breakdown by category
huum_by_category = {}
for product in huum_products:
    cat = product.category or 'Unknown'
    subcat = product.subcategory or 'Unknown'
    key = f"{cat} → {subcat}"
    huum_by_category[key] = huum_by_category.get(key, 0) + 1

print(f"\n📂 HUUM Products by Category:")
for category_path, count in sorted(huum_by_category.items()):
    print(f"  {category_path}: {count} products")

# Show all brands
all_brands = Product.objects.values_list('brand', flat=True).distinct()
print(f"\n🏢 All brands in database: {list(all_brands)}")
print(f"📊 Total products in database: {Product.objects.count()}") 