from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from products.scraper_improved import ImprovedBathingBrandsScraper, DataValidator
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape products from bathingbrands.com using improved scraper'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit the number of products to scrape',
        )
        parser.add_argument(
            '--url',
            type=str,
            help='Scrape a single product by URL',
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Scrape products from a specific category URL',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose logging',
        )

    def handle(self, *args, **options):
        if options['verbose']:
            logging.basicConfig(level=logging.DEBUG)
        
        scraper = ImprovedBathingBrandsScraper()
        validator = DataValidator()
        start_time = timezone.now()
        
        try:
            if options['url']:
                # Scrape single product with validation
                self.stdout.write(f"Scraping single product: {options['url']}")
                product_data = scraper.scrape_product(options['url'])
                if product_data:
                    validation = validator.validate_product_data(product_data)
                    if validation['is_valid']:
                        product = scraper.save_product(product_data)
                        if product:
                            self.stdout.write(
                                self.style.SUCCESS(f'✅ Successfully scraped: {product.title}')
                            )
                            self.stdout.write(f"   Brand: {product.brand}")
                            self.stdout.write(f"   Price: ${product.price or 'N/A'}")
                            self.stdout.write(f"   SKU: {product.sku}")
                        else:
                            self.stdout.write(
                                self.style.ERROR('❌ Failed to save product')
                            )
                    else:
                        self.stdout.write(
                            self.style.ERROR(f'❌ Data validation failed: {validation["errors"]}')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR('❌ Failed to scrape product data')
                    )
            
            elif options['category']:
                # Scrape specific category with validation
                self.stdout.write(f"Scraping category: {options['category']}")
                product_links = scraper.get_product_links_from_category(options['category'])
                self.stdout.write(f"Found {len(product_links)} product links")
                
                total_products = 0
                successful_products = 0
                failed_products = 0
                limit = options.get('limit')
                
                for product_url in product_links:
                    if limit and total_products >= limit:
                        break
                    
                    total_products += 1
                    product_data = scraper.scrape_product(product_url)
                    if product_data:
                        validation = validator.validate_product_data(product_data)
                        if validation['is_valid']:
                            product = scraper.save_product(product_data)
                            if product:
                                successful_products += 1
                                self.stdout.write(f"✅ {successful_products}/{total_products}: {product.brand} - {product.title}")
                            else:
                                failed_products += 1
                                self.stdout.write(f"❌ {total_products}: Failed to save")
                        else:
                            failed_products += 1
                            self.stdout.write(f"❌ {total_products}: Validation failed")
                    else:
                        failed_products += 1
                        self.stdout.write(f"❌ {total_products}: Failed to extract data")
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Category completed: {successful_products} successful, {failed_products} failed')
                )
            
            else:
                # Scrape all products with progress tracking
                self.stdout.write("Starting comprehensive product scrape...")
                limit = options.get('limit')
                if limit:
                    self.stdout.write(f"Limited to {limit} products")
                
                from products.models import Product
                initial_count = Product.objects.count()
                
                total_products = scraper.scrape_all_products(limit=limit)
                
                final_count = Product.objects.count()
                new_products = final_count - initial_count
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Scraping completed: {total_products} processed, {new_products} new products added')
                )
                
                # Show sample of recent products
                if new_products > 0:
                    self.stdout.write("\nRecent products added:")
                    recent_products = Product.objects.all().order_by('-created_at')[:5]
                    for i, product in enumerate(recent_products, 1):
                        self.stdout.write(f"  {i}. {product.brand} - {product.title} (${product.price or 'N/A'})")
        
        except Exception as e:
            logger.exception("Error during scraping")
            raise CommandError(f'Scraping failed: {str(e)}')
        
        finally:
            end_time = timezone.now()
            duration = end_time - start_time
            self.stdout.write(f"Scraping completed in {duration}") 