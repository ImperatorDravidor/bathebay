from django.core.management.base import BaseCommand
from django.db import transaction
from products.models import Product
import re


class Command(BaseCommand):
    help = 'Clean up product data - fix invalid brands, unify duplicates, and improve data quality'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be cleaned without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Get all products
        products = Product.objects.all()
        self.stdout.write(f"Found {products.count()} products to analyze")
        
        # Brand mapping for common issues
        brand_mapping = {
            'https:': 'Unknown Brand',
            'http:': 'Unknown Brand',
            'manufacturers': 'Unknown Brand',
            'prosaunas': 'ProSaunas',
            'saunalife': 'SaunaLife',
            'huum': 'HUUM',
        }
        
        # Category mapping for consistency
        category_mapping = {
            'steam': 'Steam Systems',
            'sauna': 'Sauna Equipment',
            'accessories': 'Accessories',
            'lighting': 'Lighting',
            'controls': 'Controls & Packages',
        }
        
        # Track changes
        brand_fixes = 0
        category_fixes = 0
        price_fixes = 0
        title_fixes = 0
        duplicates_found = []
        
        # Analyze and fix data
        for product in products:
            changes_made = False
            original_brand = product.brand
            original_category = product.category
            original_price = product.price
            original_title = product.title
            
            # Fix brand names
            brand_lower = product.brand.lower().strip()
            if brand_lower in brand_mapping:
                product.brand = brand_mapping[brand_lower]
                brand_fixes += 1
                changes_made = True
                self.stdout.write(f"Brand fix: '{original_brand}' -> '{product.brand}' for {product.title[:50]}")
            elif not product.brand or len(product.brand.strip()) < 2:
                product.brand = 'Unknown Brand'
                brand_fixes += 1
                changes_made = True
                self.stdout.write(f"Brand fix: '{original_brand}' -> '{product.brand}' for {product.title[:50]}")
            
            # Fix category names
            if product.category:
                category_lower = product.category.lower().strip()
                for key, value in category_mapping.items():
                    if key in category_lower:
                        product.category = value
                        category_fixes += 1
                        changes_made = True
                        self.stdout.write(f"Category fix: '{original_category}' -> '{product.category}' for {product.title[:50]}")
                        break
            
            # Fix price issues
            if product.price is not None:
                try:
                    # Handle string prices
                    if isinstance(product.price, str):
                        price_str = product.price.replace('$', '').replace(',', '').strip()
                        product.price = float(price_str)
                        price_fixes += 1
                        changes_made = True
                        self.stdout.write(f"Price fix: '{original_price}' -> '{product.price}' for {product.title[:50]}")
                except (ValueError, TypeError):
                    self.stdout.write(self.style.ERROR(f"Could not fix price '{original_price}' for {product.title[:50]}"))
            
            # Fix title issues
            if product.title:
                # Remove common navigation elements
                if product.title.lower() in ['home', 'products', 'category', 'brand']:
                    product.title = f"{product.brand} Product"
                    title_fixes += 1
                    changes_made = True
                    self.stdout.write(f"Title fix: '{original_title}' -> '{product.title}' for SKU {product.sku}")
                
                # Clean up title
                cleaned_title = re.sub(r'\s+', ' ', product.title.strip())
                if cleaned_title != product.title:
                    product.title = cleaned_title
                    title_fixes += 1
                    changes_made = True
            
            # Save changes
            if changes_made and not dry_run:
                try:
                    product.save()
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error saving {product.title[:50]}: {e}"))
        
        # Find potential duplicates
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CHECKING FOR DUPLICATES")
        self.stdout.write("="*50)
        
        # Group by SKU patterns
        sku_groups = {}
        for product in Product.objects.all():
            # Create a normalized SKU for comparison
            normalized_sku = re.sub(r'[^a-zA-Z0-9]', '', product.sku.lower())
            if normalized_sku in sku_groups:
                sku_groups[normalized_sku].append(product)
            else:
                sku_groups[normalized_sku] = [product]
        
        # Find duplicates
        for normalized_sku, products_list in sku_groups.items():
            if len(products_list) > 1:
                duplicates_found.append(products_list)
                self.stdout.write(f"Potential duplicates found:")
                for p in products_list:
                    self.stdout.write(f"  - {p.title[:40]} (SKU: {p.sku}, Brand: {p.brand})")
        
        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CLEANUP SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Brand fixes: {brand_fixes}")
        self.stdout.write(f"Category fixes: {category_fixes}")
        self.stdout.write(f"Price fixes: {price_fixes}")
        self.stdout.write(f"Title fixes: {title_fixes}")
        self.stdout.write(f"Potential duplicate groups: {len(duplicates_found)}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\nDry run complete - use without --dry-run to apply changes'))
        else:
            self.stdout.write(self.style.SUCCESS('\nData cleanup complete!'))
            
        # Show current brand distribution
        self.stdout.write("\n" + "="*50)
        self.stdout.write("CURRENT BRAND DISTRIBUTION")
        self.stdout.write("="*50)
        
        from django.db.models import Count
        brand_counts = Product.objects.values('brand').annotate(count=Count('id')).order_by('-count')
        for brand_data in brand_counts:
            self.stdout.write(f"{brand_data['brand']}: {brand_data['count']} products") 