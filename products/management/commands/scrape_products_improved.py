from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from products.scraper_improved import ImprovedBathingBrandsScraper, DataValidator
from products.models import Product
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
        parser.add_argument(
            '--validate-only',
            action='store_true',
            help='Only validate existing data without scraping new products',
        )
        parser.add_argument(
            '--test-mode',
            action='store_true',
            help='Run in test mode with comprehensive validation',
        )

    def handle(self, *args, **options):
        if options['verbose']:
            logging.basicConfig(level=logging.DEBUG)
        
        start_time = timezone.now()
        
        # Handle validation-only mode
        if options['validate_only']:
            self.validate_existing_data()
            return
        
        # Handle test mode
        if options['test_mode']:
            self.run_test_mode()
            return
        
        scraper = ImprovedBathingBrandsScraper()
        
        try:
            if options['url']:
                # Scrape single product
                self.scrape_single_product(scraper, options['url'])
            
            elif options['category']:
                # Scrape specific category
                self.scrape_category(scraper, options['category'], options.get('limit'))
            
            else:
                # Scrape all products
                self.scrape_all_products(scraper, options.get('limit'))
        
        except Exception as e:
            logger.exception("Error during scraping")
            raise CommandError(f'Scraping failed: {str(e)}')
        
        finally:
            end_time = timezone.now()
            duration = end_time - start_time
            self.stdout.write(f"Operation completed in {duration}")
    
    def scrape_single_product(self, scraper, url):
        """Scrape a single product with validation"""
        self.stdout.write(f"Scraping single product: {url}")
        
        product_data = scraper.scrape_product(url)
        if product_data:
            # Validate data before saving
            validator = DataValidator()
            validation = validator.validate_product_data(product_data)
            
            if validation['is_valid']:
                product = scraper.save_product(product_data)
                if product:
                    self.stdout.write(
                        self.style.SUCCESS(f'✅ Successfully scraped: {product.title}')
                    )
                    self.display_product_info(product)
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
    
    def scrape_category(self, scraper, category_url, limit):
        """Scrape products from a specific category"""
        self.stdout.write(f"Scraping category: {category_url}")
        
        product_links = scraper.get_product_links_from_category(category_url)
        self.stdout.write(f"Found {len(product_links)} product links")
        
        if not product_links:
            self.stdout.write(
                self.style.WARNING('⚠️  No product links found in this category')
            )
            return
        
        total_products = 0
        successful_products = 0
        failed_products = 0
        
        for product_url in product_links:
            if limit and total_products >= limit:
                break
            
            total_products += 1
            self.stdout.write(f"Processing {total_products}/{len(product_links)}: {product_url}")
            
            product_data = scraper.scrape_product(product_url)
            if product_data:
                # Validate data
                validator = DataValidator()
                validation = validator.validate_product_data(product_data)
                
                if validation['is_valid']:
                    product = scraper.save_product(product_data)
                    if product:
                        successful_products += 1
                        self.stdout.write(f"  ✅ {product.brand} - {product.title}")
                    else:
                        failed_products += 1
                        self.stdout.write("  ❌ Failed to save")
                else:
                    failed_products += 1
                    self.stdout.write(f"  ❌ Validation failed: {validation['errors']}")
            else:
                failed_products += 1
                self.stdout.write("  ❌ Failed to extract data")
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Category scraping completed: {successful_products} successful, {failed_products} failed'
            )
        )
    
    def scrape_all_products(self, scraper, limit):
        """Scrape all products with progress tracking"""
        self.stdout.write("Starting comprehensive product scrape...")
        
        if limit:
            self.stdout.write(f"Limited to {limit} products")
        
        # Get initial count
        initial_count = Product.objects.count()
        
        # Run scraping
        total_products = scraper.scrape_all_products(limit=limit)
        
        # Get final count
        final_count = Product.objects.count()
        new_products = final_count - initial_count
        
        self.stdout.write(
            self.style.SUCCESS(
                f'✅ Scraping completed: {total_products} processed, {new_products} new products added'
            )
        )
        
        # Show sample of recent products
        if new_products > 0:
            self.stdout.write("\nRecent products added:")
            recent_products = Product.objects.all().order_by('-created_at')[:5]
            for i, product in enumerate(recent_products, 1):
                self.stdout.write(f"  {i}. {product.brand} - {product.title}")
    
    def validate_existing_data(self):
        """Validate existing products in database"""
        self.stdout.write("🔍 Validating existing product data...")
        
        products = Product.objects.all()
        total_count = products.count()
        
        if total_count == 0:
            self.stdout.write("No products found in database")
            return
        
        validator = DataValidator()
        valid_count = 0
        invalid_count = 0
        issues = []
        
        for product in products:
            product_data = {
                'title': product.title,
                'brand': product.brand,
                'price': product.price,
                'sku': product.sku,
                'source_url': product.source_url,
            }
            
            validation = validator.validate_product_data(product_data)
            if validation['is_valid']:
                valid_count += 1
            else:
                invalid_count += 1
                issues.extend(validation['errors'])
        
        # Display results
        self.stdout.write(f"\nValidation Results:")
        self.stdout.write(f"  Total products: {total_count}")
        self.stdout.write(f"  Valid products: {valid_count} ({(valid_count/total_count)*100:.1f}%)")
        self.stdout.write(f"  Invalid products: {invalid_count} ({(invalid_count/total_count)*100:.1f}%)")
        
        if issues:
            self.stdout.write(f"\nCommon issues found:")
            issue_counts = {}
            for issue in issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
                self.stdout.write(f"  - {issue}: {count} occurrences")
        
        # Provide recommendations
        quality_score = (valid_count / total_count) * 100
        if quality_score < 50:
            self.stdout.write(
                self.style.ERROR(f"\n🔴 Data quality is POOR ({quality_score:.1f}%). Immediate action needed!")
            )
            self.stdout.write("Recommendations:")
            self.stdout.write("  1. Use the improved scraper: python manage.py scrape_products_improved")
            self.stdout.write("  2. Clear bad data: python manage.py flush")
            self.stdout.write("  3. Re-scrape with validation")
        elif quality_score < 80:
            self.stdout.write(
                self.style.WARNING(f"\n🟡 Data quality is FAIR ({quality_score:.1f}%). Improvements needed.")
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(f"\n🟢 Data quality is GOOD ({quality_score:.1f}%).")
            )
    
    def run_test_mode(self):
        """Run comprehensive tests"""
        self.stdout.write("🧪 Running test mode...")
        
        scraper = ImprovedBathingBrandsScraper()
        
        # Test URL discovery
        self.stdout.write("\n1. Testing URL discovery...")
        categories = scraper.discover_category_urls()
        self.stdout.write(f"   Found {len(categories)} category URLs")
        
        if not categories:
            self.stdout.write(
                self.style.ERROR("   ❌ No categories found - check website accessibility")
            )
            return
        
        # Test product extraction
        self.stdout.write("\n2. Testing product extraction...")
        test_category = categories[0]
        product_links = scraper.get_product_links_from_category(test_category)
        self.stdout.write(f"   Found {len(product_links)} product links in test category")
        
        if product_links:
            test_product_url = product_links[0]
            product_data = scraper.scrape_product(test_product_url)
            
            if product_data:
                self.stdout.write("   ✅ Product extraction successful")
                
                # Validate data
                validator = DataValidator()
                validation = validator.validate_product_data(product_data)
                
                if validation['is_valid']:
                    self.stdout.write("   ✅ Data validation passed")
                    self.stdout.write(f"      Title: {product_data['title']}")
                    self.stdout.write(f"      Brand: {product_data['brand']}")
                    self.stdout.write(f"      Price: ${product_data['price']}")
                else:
                    self.stdout.write(
                        self.style.ERROR(f"   ❌ Data validation failed: {validation['errors']}")
                    )
            else:
                self.stdout.write(
                    self.style.ERROR("   ❌ Product extraction failed")
                )
        else:
            self.stdout.write(
                self.style.ERROR("   ❌ No product links found")
            )
        
        # Test database integration
        self.stdout.write("\n3. Testing database integration...")
        initial_count = Product.objects.count()
        
        try:
            scraped_count = scraper.scrape_all_products(limit=2)
            final_count = Product.objects.count()
            
            if final_count > initial_count:
                self.stdout.write("   ✅ Database integration successful")
                self.stdout.write(f"      Added {final_count - initial_count} products")
            else:
                self.stdout.write(
                    self.style.WARNING("   ⚠️  No new products added to database")
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"   ❌ Database integration failed: {e}")
            )
        
        self.stdout.write("\n🏁 Test mode completed!")
    
    def display_product_info(self, product):
        """Display detailed product information"""
        self.stdout.write(f"  Brand: {product.brand}")
        self.stdout.write(f"  Price: ${product.price or 'N/A'}")
        self.stdout.write(f"  SKU: {product.sku}")
        self.stdout.write(f"  Category: {product.category or 'N/A'}")
        self.stdout.write(f"  Images: {product.images.count()}")
        if product.description:
            desc_preview = product.description[:100] + "..." if len(product.description) > 100 else product.description
            self.stdout.write(f"  Description: {desc_preview}") 