#!/usr/bin/env python
"""
Management command to scrape all HUUM products from bathingbrands.com
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from products.scraper_enhanced import EnhancedBathingBrandsScraper
from products.models import Product
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape all HUUM products from bathingbrands.com'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of products to scrape (for testing)',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Specific category to scrape (e.g., "Sauna")',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without saving to database',
        )
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔥 Starting HUUM Product Scraper...'))
        
        # Initialize scraper
        scraper = EnhancedBathingBrandsScraper()
        
        # Get options
        limit = options.get('limit')
        category = options.get('category')
        dry_run = options.get('dry_run')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODE - No data will be saved'))
        
        # Show current HUUM products count
        current_huum_count = Product.objects.filter(brand__icontains='HUUM').count()
        self.stdout.write(f'📊 Current HUUM products in database: {current_huum_count}')
        
        try:
            # Run the intelligent scraper for HUUM brand
            self.stdout.write(f'🎯 Targeting HUUM brand...')
            if category:
                self.stdout.write(f'📂 Filtering by category: {category}')
            if limit:
                self.stdout.write(f'🔢 Limiting to {limit} products')
            
            # Use the intelligent scraper
            scraped_products = scraper.run_intelligent_scraper(
                target_brand='HUUM',
                target_category=category,
                limit=limit
            )
            
            if not dry_run:
                # Show results
                new_huum_count = Product.objects.filter(brand__icontains='HUUM').count()
                products_added = new_huum_count - current_huum_count
                
                self.stdout.write(self.style.SUCCESS(f'\n✅ HUUM Scraping Complete!'))
                self.stdout.write(f'📈 Products scraped in this run: {len(scraped_products)}')
                self.stdout.write(f'📊 Total HUUM products in database: {new_huum_count}')
                self.stdout.write(f'🆕 New products added: {products_added}')
                
                # Show breakdown by category
                huum_by_category = {}
                for product in Product.objects.filter(brand__icontains='HUUM'):
                    cat = product.category or 'Unknown'
                    subcat = product.subcategory or 'Unknown'
                    key = f"{cat} → {subcat}"
                    huum_by_category[key] = huum_by_category.get(key, 0) + 1
                
                self.stdout.write(f'\n📂 HUUM Products by Category:')
                for category_path, count in sorted(huum_by_category.items()):
                    self.stdout.write(f'  {category_path}: {count} products')
                
                # Show some sample products
                sample_products = Product.objects.filter(brand__icontains='HUUM')[:5]
                if sample_products:
                    self.stdout.write(f'\n🛍️ Sample HUUM Products:')
                    for product in sample_products:
                        self.stdout.write(f'  • {product.title} (SKU: {product.sku}) - ${product.price or "N/A"}')
            else:
                self.stdout.write(self.style.WARNING(f'\n🧪 DRY RUN COMPLETE - {len(scraped_products)} products would have been processed'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error during HUUM scraping: {e}'))
            logger.error(f"HUUM scraping error: {e}", exc_info=True)
            return
        
        self.stdout.write(self.style.SUCCESS('\n🎉 HUUM scraping job completed successfully!'))
        self.stdout.write('🔗 You can now view the products in the Django admin panel.')
        self.stdout.write('🌐 Admin URL: http://127.0.0.1:8000/admin/products/product/') 