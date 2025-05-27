from django.core.management.base import BaseCommand
from products.scraper_enhanced import EnhancedBathingBrandsScraper


class Command(BaseCommand):
    help = 'Enhanced scraper that captures ALL product information including multiple images, specifications, and documents'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit the number of products to scrape'
        )
        parser.add_argument(
            '--test-url',
            type=str,
            default=None,
            help='Test scraper with a single product URL'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting Enhanced Bathing Brands Scraper...')
        )
        
        scraper = EnhancedBathingBrandsScraper()
        
        try:
            products = scraper.run_scraper(
                limit=options['limit'],
                test_url=options['test_url']
            )
            
            if products:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully scraped {len(products)} products!'
                    )
                )
                
                # Show summary of scraped products
                for product in products:
                    images_count = product.images.count()
                    specs_count = product.product_specifications.count()
                    docs_count = product.documents.count()
                    
                    self.stdout.write(
                        f"📦 {product.brand} - {product.title}"
                    )
                    self.stdout.write(
                        f"   💰 Price: ${product.price or 'N/A'}"
                    )
                    self.stdout.write(
                        f"   🖼️ Images: {images_count}"
                    )
                    self.stdout.write(
                        f"   📋 Specifications: {specs_count}"
                    )
                    self.stdout.write(
                        f"   📄 Documents: {docs_count}"
                    )
                    self.stdout.write("")
                    
            else:
                self.stdout.write(
                    self.style.WARNING('⚠️ No products were scraped.')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during scraping: {e}')
            )
            raise 