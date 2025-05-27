from django.core.management.base import BaseCommand
from django.db import models
from products.scraper_enhanced import EnhancedBathingBrandsScraper
from products.models import Product
import time


class Command(BaseCommand):
    help = 'Scrape ALL brands from bathingbrands.com following the complete hierarchy'

    def add_arguments(self, parser):
        parser.add_argument(
            '--brands',
            type=str,
            nargs='*',
            help='Specific brands to scrape (space-separated). If not provided, scrapes all brands.',
        )
        parser.add_argument(
            '--limit-per-brand',
            type=int,
            default=None,
            help='Maximum number of products to scrape per brand (default: unlimited)',
        )
        parser.add_argument(
            '--total-limit',
            type=int,
            default=None,
            help='Maximum total products to scrape across all brands (default: unlimited)',
        )
        parser.add_argument(
            '--start-from-brand',
            type=str,
            help='Start scraping from a specific brand (useful for resuming)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be scraped without actually scraping',
        )
        parser.add_argument(
            '--delay',
            type=float,
            default=1.0,
            help='Delay between requests in seconds (default: 1.0)',
        )

    def handle(self, *args, **options):
        scraper = EnhancedBathingBrandsScraper()
        
        # Get all known brands
        all_brands = scraper.known_brands
        target_brands = options.get('brands') or all_brands
        limit_per_brand = options.get('limit_per_brand')
        total_limit = options.get('total_limit')
        start_from_brand = options.get('start_from_brand')
        dry_run = options.get('dry_run')
        delay = options.get('delay')
        
        self.stdout.write(self.style.SUCCESS('🌐 COMPREHENSIVE BATHINGBRANDS.COM SCRAPER'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        
        # Show current database status
        current_products = Product.objects.count()
        current_brands = Product.objects.values('brand').distinct().count()
        self.stdout.write(f"📊 Current database status:")
        self.stdout.write(f"   Products: {current_products}")
        self.stdout.write(f"   Brands: {current_brands}")
        
        # Show scraping plan
        self.stdout.write(f"\n🎯 Scraping Plan:")
        self.stdout.write(f"   Target brands: {len(target_brands)} ({', '.join(target_brands)})")
        self.stdout.write(f"   Limit per brand: {limit_per_brand or 'Unlimited'}")
        self.stdout.write(f"   Total limit: {total_limit or 'Unlimited'}")
        self.stdout.write(f"   Delay between requests: {delay}s")
        self.stdout.write(f"   Dry run: {'Yes' if dry_run else 'No'}")
        
        if dry_run:
            self.stdout.write(self.style.WARNING("\n🔍 DRY RUN MODE - No products will be saved"))
            # Discover brands and show what would be scraped
            brands_dict = scraper.discover_brands()
            for brand_name in target_brands:
                if brand_name in brands_dict:
                    self.stdout.write(f"\n🏢 Would scrape brand: {brand_name}")
                    categories = scraper.discover_brand_categories(brands_dict[brand_name])
                    for cat_name, cat_data in categories.items():
                        self.stdout.write(f"   📂 Category: {cat_name}")
                        collections = scraper.discover_category_collections(brands_dict[brand_name], cat_data)
                        for coll_name, coll_data in collections.items():
                            products = scraper.discover_collection_products(brands_dict[brand_name], cat_data, coll_data)
                            self.stdout.write(f"      📦 Collection: {coll_name} ({len(products)} products)")
            return
        
        # Start scraping
        self.stdout.write(self.style.SUCCESS(f"\n🚀 Starting comprehensive scraping..."))
        
        total_scraped = 0
        brands_processed = 0
        start_scraping = not start_from_brand  # If no start brand specified, start immediately
        
        for brand_name in target_brands:
            # Check if we should start scraping from this brand
            if start_from_brand and brand_name == start_from_brand:
                start_scraping = True
                self.stdout.write(self.style.WARNING(f"▶️ Resuming from brand: {brand_name}"))
            
            if not start_scraping:
                self.stdout.write(f"⏭️ Skipping brand: {brand_name} (before start point)")
                continue
            
            # Check total limit
            if total_limit and total_scraped >= total_limit:
                self.stdout.write(self.style.WARNING(f"🛑 Reached total limit of {total_limit} products"))
                break
            
            self.stdout.write(f"\n🏢 Processing brand: {brand_name}")
            self.stdout.write(f"   Progress: {brands_processed + 1}/{len(target_brands)} brands")
            
            # Calculate remaining limit for this brand
            remaining_total = None
            if total_limit:
                remaining_total = total_limit - total_scraped
            
            # Use the smaller of per-brand limit and remaining total limit
            brand_limit = limit_per_brand
            if remaining_total is not None:
                if brand_limit is None:
                    brand_limit = remaining_total
                else:
                    brand_limit = min(brand_limit, remaining_total)
            
            # Get current count for this brand before scraping
            brand_products_before = Product.objects.filter(brand=brand_name).count()
            
            try:
                # Scrape this brand
                products_saved = scraper.run_intelligent_scraper(
                    target_brand=brand_name,
                    limit=brand_limit
                )
                
                brand_scraped_count = len(products_saved)
                total_scraped += brand_scraped_count
                brands_processed += 1
                
                # Get current count for this brand after scraping
                brand_products_after = Product.objects.filter(brand=brand_name).count()
                brand_products_added = brand_products_after - brand_products_before
                
                self.stdout.write(self.style.SUCCESS(
                    f"   ✅ {brand_name}: {brand_scraped_count} products scraped, "
                    f"{brand_products_after} total in DB (+{brand_products_added})"
                ))
                
                # Add delay between brands
                if delay > 0 and brand_name != target_brands[-1]:  # Don't delay after last brand
                    self.stdout.write(f"   ⏱️ Waiting {delay}s before next brand...")
                    time.sleep(delay)
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"   ❌ Error scraping {brand_name}: {e}"))
                continue
        
        # Final summary
        final_products = Product.objects.count()
        final_brands = Product.objects.values('brand').distinct().count()
        products_added = final_products - current_products
        
        self.stdout.write(self.style.SUCCESS('\n🎉 SCRAPING COMPLETE!'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(f"📊 Final Results:")
        self.stdout.write(f"   Brands processed: {brands_processed}/{len(target_brands)}")
        self.stdout.write(f"   Products scraped in this run: {total_scraped}")
        self.stdout.write(f"   Products added to database: {products_added}")
        self.stdout.write(f"   Total products in database: {final_products}")
        self.stdout.write(f"   Total brands in database: {final_brands}")
        
        # Show brand breakdown
        self.stdout.write(f"\n📈 Brand Breakdown:")
        for brand in Product.objects.values('brand').annotate(count=models.Count('id')).order_by('-count'):
            self.stdout.write(f"   {brand['brand']}: {brand['count']} products")
        
        self.stdout.write(f"\n🌐 Admin URL: http://127.0.0.1:8000/admin/products/product/") 