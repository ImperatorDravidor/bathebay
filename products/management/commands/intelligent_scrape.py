from django.core.management.base import BaseCommand
from products.scrapers import EnhancedBathingBrandsScraper
from products.models import Product


class Command(BaseCommand):
    help = 'Run intelligent hierarchy-based scraper following Brand → Category → Collection → Product structure'

    def add_arguments(self, parser):
        parser.add_argument(
            '--brand',
            type=str,
            help='Target specific brand (e.g., "HUUM", "Harvia")',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Target specific category (e.g., "Sauna", "Steam")',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None, # Changed default to None for unlimited unless specified
            help='Maximum number of products to scrape (default: all)',
        )
        parser.add_argument(
            '--test-url',
            type=str,
            help='Test single product URL. Scrapes and saves one product.',
        )

    def handle(self, *args, **options):
        scraper = EnhancedBathingBrandsScraper()
        
        brand = options.get('brand')
        category = options.get('category')
        limit = options.get('limit')
        test_url = options.get('test_url')
        
        saved_products_count = 0

        if test_url:
            self.stdout.write(self.style.WARNING(f"🧪 Testing single product URL: {test_url}"))
            # For a single test URL, we directly call extract and save
            product_data_dict = scraper.extract_product_data(test_url)
            if product_data_dict:
                product_instance = scraper.save_product(product_data_dict)
                if product_instance:
                    self.stdout.write(self.style.SUCCESS(f"  ✅ Successfully scraped and saved: {product_instance.title} (SKU: {product_instance.sku})"))
                    # Attempt to scrape related products for this single instance
                    try:
                        response = scraper.session.get(test_url) # Fetch page content again
                        response.raise_for_status()
                        soup_for_related = scraper.BeautifulSoup(response.content, 'html.parser')
                        scraper.extract_related_products(soup_for_related, product_instance)
                        self.stdout.write(self.style.SUCCESS(f"  🤝 Successfully processed related products for: {product_instance.title}"))
                    except Exception as e_rel:
                        self.stdout.write(self.style.ERROR(f"  ❌ Error processing related products for {test_url}: {e_rel}"))
                    saved_products_count = 1
                else:
                    self.stdout.write(self.style.ERROR(f"  ❌ Failed to save product from {test_url}"))
            else:
                self.stdout.write(self.style.ERROR(f"  ❌ Failed to extract data from {test_url}"))
        else:
            if brand:
                self.stdout.write(self.style.SUCCESS(f"🏢 Targeting brand: {brand}"))
            if category:
                self.stdout.write(self.style.SUCCESS(f"📂 Targeting category: {category}"))
            if limit:
                self.stdout.write(self.style.SUCCESS(f"📊 Limit: {limit} products"))
            else:
                self.stdout.write(self.style.WARNING("📊 Limit: Not set (will attempt to scrape all found products)"))
            
            # Call the main hierarchical scraper
            products_saved_list = scraper.run_intelligent_scraper(
                target_brand=brand,
                target_category=category,
                limit=limit
            )
            saved_products_count = len(products_saved_list)
        
        self.stdout.write(
            self.style.SUCCESS(f'✅ Scraping run complete! Saved {saved_products_count} products in this run.')
        ) 