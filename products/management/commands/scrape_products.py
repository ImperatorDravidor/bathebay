from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from products.scraper import BathingBrandsScraper
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Scrape products from bathingbrands.com'

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
        
        scraper = BathingBrandsScraper()
        start_time = timezone.now()
        
        try:
            if options['url']:
                # Scrape single product
                self.stdout.write(f"Scraping single product: {options['url']}")
                product_data = scraper.scrape_product(options['url'])
                if product_data:
                    product = scraper.save_product(product_data)
                    if product:
                        self.stdout.write(
                            self.style.SUCCESS(f'Successfully scraped product: {product.title}')
                        )
                    else:
                        self.stdout.write(
                            self.style.ERROR('Failed to save product')
                        )
                else:
                    self.stdout.write(
                        self.style.ERROR('Failed to scrape product data')
                    )
            
            elif options['category']:
                # Scrape specific category
                self.stdout.write(f"Scraping category: {options['category']}")
                product_links = scraper.get_product_links_from_category(options['category'])
                
                total_products = 0
                limit = options.get('limit')
                
                for product_url in product_links:
                    if limit and total_products >= limit:
                        break
                    
                    product_data = scraper.scrape_product(product_url)
                    if product_data:
                        product = scraper.save_product(product_data)
                        if product:
                            total_products += 1
                            self.stdout.write(f"Processed {total_products}: {product.title}")
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully scraped {total_products} products from category')
                )
            
            else:
                # Scrape all products
                self.stdout.write("Starting full product scrape...")
                limit = options.get('limit')
                total_products = scraper.scrape_all_products(limit=limit)
                
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully scraped {total_products} products')
                )
        
        except Exception as e:
            logger.exception("Error during scraping")
            raise CommandError(f'Scraping failed: {str(e)}')
        
        finally:
            end_time = timezone.now()
            duration = end_time - start_time
            self.stdout.write(f"Scraping completed in {duration}") 