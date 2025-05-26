# Bathing Brands Product Scraper - Usage Guide

## Quick Start

### 1. Setup
```bash
# Run the setup script
python setup.py

# Or manually:
pip install -r requirements.txt
python manage.py migrate
```

### 2. Start Scraping
```bash
# Scrape a few products for testing
python manage.py scrape_products --limit 10

# Scrape all products (this will take a while!)
python manage.py scrape_products

# Scrape with verbose logging
python manage.py scrape_products --limit 5 --verbose
```

### 3. View Results
```bash
# Start the web server
python manage.py runserver

# Visit http://127.0.0.1:8000/ to see scraped products
```

## Detailed Usage

### Scraping Commands

#### Scrape All Products
```bash
python manage.py scrape_products
```
This will scrape all products from bathingbrands.com. It automatically discovers categories and products.

#### Scrape with Limit
```bash
python manage.py scrape_products --limit 50
```
Limits the scraping to 50 products. Useful for testing.

#### Scrape Single Product
```bash
python manage.py scrape_products --url "https://www.bathingbrands.com/products/huum/sauna/accessories"
```
Scrapes a single product from the specified URL.

#### Scrape Specific Category
```bash
python manage.py scrape_products --category "https://www.bathingbrands.com/products/huum/sauna/accessories"
```
Scrapes all products from a specific category page.

#### Verbose Logging
```bash
python manage.py scrape_products --verbose
```
Enables detailed logging to help debug issues.

### Export Commands

#### Export to CSV
```bash
python manage.py export_products csv
python manage.py export_products csv --filename my_products.csv
```

#### Export to eBay Format
```bash
python manage.py export_products ebay --filename ebay_upload.csv
```

#### Export to Amazon Format
```bash
python manage.py export_products amazon --filename amazon_inventory.csv
```

#### Export to Shopify Format
```bash
python manage.py export_products shopify --filename shopify_import.csv
```

#### Export with Filters
```bash
# Export only HUUM products
python manage.py export_products csv --brand "HUUM"

# Export only sauna products
python manage.py export_products csv --category "sauna"
```

### Web Interface

#### Start the Server
```bash
python manage.py runserver
```

#### Access Points
- **Product List**: http://127.0.0.1:8000/
- **Admin Interface**: http://127.0.0.1:8000/admin/ (requires superuser)

#### Create Admin User
```bash
python manage.py createsuperuser
```

## Data Structure

### Product Fields
- **title**: Product name
- **description**: Product description
- **price**: Product price (decimal)
- **sku**: Stock Keeping Unit (unique identifier)
- **brand**: Product brand (e.g., HUUM, Harvia, Mr.Steam)
- **category**: Main category (e.g., Sauna, Steam)
- **subcategory**: Subcategory (e.g., Electric Heaters, Accessories)
- **specifications**: JSON-formatted technical specifications
- **source_url**: Original product URL
- **slug**: URL-friendly identifier
- **is_active**: Whether the product is active
- **created_at**: When the product was first scraped
- **updated_at**: When the product was last updated

### Product Images
- **image_url**: Original image URL
- **local_path**: Local file path (downloaded image)
- **alt_text**: Alternative text for accessibility
- **is_primary**: Whether this is the main product image

## Troubleshooting

### Common Issues

#### No Products Found
```bash
# Check if the website is accessible
python test_scraper.py

# Try with verbose logging
python manage.py scrape_products --limit 1 --verbose
```

#### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Check Django installation
python -c "import django; print(django.get_version())"
```

#### Database Issues
```bash
# Reset database
rm db.sqlite3
python manage.py migrate
```

#### Permission Errors
```bash
# Check media directory permissions
ls -la media/
chmod 755 media/
chmod 755 media/products/
```

### Performance Tips

#### For Large Scrapes
- Use `--limit` for testing first
- Monitor memory usage
- Consider running overnight for full scrapes
- The scraper includes delays to be respectful to the target server

#### Database Optimization
```bash
# For large datasets, consider PostgreSQL
# Update DATABASES in settings.py
```

### Customization

#### Adding New Brands
Edit `products/scraper.py` and add new brand names to the `brands` list in `get_all_category_urls()`.

#### Adding New Categories
Edit `products/scraper.py` and add new category names to the `categories` list in `get_all_category_urls()`.

#### Modifying Selectors
If the website structure changes, update the CSS selectors in:
- `get_product_links_from_category()` for finding product links
- `scrape_product()` for extracting product data
- `extract_price()` for finding prices

#### Adding New Export Formats
1. Create a new exporter class in `products/exporters.py`
2. Inherit from `ProductExporter`
3. Implement the `export()` method
4. Add the format to `products/management/commands/export_products.py`

## Legal and Ethical Considerations

### Respectful Scraping
- The scraper includes delays between requests
- It respects robots.txt (check manually)
- Use scraped data responsibly
- Consider reaching out to the website owner for permission

### Rate Limiting
The scraper includes built-in delays:
- 1 second between product requests
- Exponential backoff for failed requests
- Retry logic for network issues

### Data Usage
- This tool is for educational and personal use
- Respect the website's terms of service
- Don't overwhelm the target server
- Consider the legal implications of web scraping in your jurisdiction

## Support

### Getting Help
1. Check this documentation
2. Review the error logs with `--verbose`
3. Test with a small limit first
4. Check the GitHub issues (if applicable)

### Reporting Issues
When reporting issues, include:
- The exact command you ran
- The full error message
- Your operating system
- Python version (`python --version`)
- Django version (`python -c "import django; print(django.get_version())"`)

## Advanced Usage

### Custom Scraping Scripts
```python
from products.scraper import BathingBrandsScraper

scraper = BathingBrandsScraper()
product_data = scraper.scrape_product("https://example.com/product")
if product_data:
    product = scraper.save_product(product_data)
```

### Batch Processing
```python
from products.models import Product
from products.exporters import export_to_csv

# Get products from last week
from django.utils import timezone
from datetime import timedelta

week_ago = timezone.now() - timedelta(days=7)
recent_products = Product.objects.filter(created_at__gte=week_ago)

# Export them
response = export_to_csv(recent_products, "recent_products.csv")
```

### Database Queries
```python
from products.models import Product

# Get all HUUM products
huum_products = Product.objects.filter(brand__icontains="huum")

# Get products by price range
expensive_products = Product.objects.filter(price__gte=1000)

# Get products with images
products_with_images = Product.objects.filter(images__isnull=False).distinct()
``` 