# Bathing Brands Product Scraper

A Django-based web scraper for extracting product information from bathingbrands.com. This project scrapes product details including titles, descriptions, prices, images, SKUs, brands, and specifications, then stores them in a Django database with options to export to various formats.

## Features

- **Comprehensive Product Scraping**: Extracts all product details from bathingbrands.com
- **Image Download**: Downloads and stores product images locally
- **Database Storage**: Uses Django ORM with SQLite (easily configurable for other databases)
- **Export Capabilities**: Export to CSV, eBay, Amazon, and Shopify formats
- **Management Commands**: Easy-to-use Django management commands
- **Robust Error Handling**: Retry logic and comprehensive logging
- **Respectful Scraping**: Built-in delays to avoid overwhelming the target server

## Project Structure

```
bathscraper/
├── bathing_scraper/          # Django project configuration
├── products/                 # Main app containing models, scraper, and exporters
│   ├── models.py            # Product and ProductImage models
│   ├── scraper.py           # Main scraping logic
│   ├── exporters.py         # Export functionality for various platforms
│   ├── admin.py             # Django admin configuration
│   ├── views.py             # Web views for product display
│   └── management/
│       └── commands/
│           ├── scrape_products.py    # Scraping management command
│           └── export_products.py    # Export management command
├── media/                   # Directory for downloaded images
├── db.sqlite3              # SQLite database
├── manage.py               # Django management script
└── requirements.txt        # Python dependencies
```

## Installation

1. **Clone or download the project**
2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run migrations**:
   ```bash
   python manage.py migrate
   ```

5. **Create a superuser** (optional, for admin access):
   ```bash
   python manage.py createsuperuser
   ```

## Usage

### Scraping Products

#### Scrape All Products
```bash
python manage.py scrape_products
```

#### Scrape with Limit
```bash
python manage.py scrape_products --limit 50
```

#### Scrape Single Product
```bash
python manage.py scrape_products --url "https://www.bathingbrands.com/product-url"
```

#### Scrape Specific Category
```bash
python manage.py scrape_products --category "https://www.bathingbrands.com/category-url"
```

#### Verbose Logging
```bash
python manage.py scrape_products --verbose
```

### Exporting Products

#### Export to CSV
```bash
python manage.py export_products --format csv --output products.csv
```

#### Export to eBay Format
```bash
python manage.py export_products --format ebay --output ebay_products.csv
```

#### Export to Amazon Format
```bash
python manage.py export_products --format amazon --output amazon_products.csv
```

#### Export to Shopify Format
```bash
python manage.py export_products --format shopify --output shopify_products.csv
```

#### Export with Filters
```bash
# Export only products from specific brand
python manage.py export_products --format csv --brand "BrandName"

# Export products within price range
python manage.py export_products --format csv --min-price 100 --max-price 500
```

### Web Interface

Start the Django development server to access the web interface:

```bash
python manage.py runserver
```

Then visit:
- `http://127.0.0.1:8000/` - Product listing
- `http://127.0.0.1:8000/admin/` - Django admin interface (requires superuser)

## Models

### Product Model
- `title`: Product title
- `description`: Product description
- `price`: Product price (decimal)
- `sku`: Stock Keeping Unit (unique)
- `brand`: Product brand
- `category`: Product category
- `subcategory`: Product subcategory
- `specifications`: JSON-formatted specifications
- `source_url`: Original product URL
- `slug`: URL-friendly identifier
- `is_active`: Active status
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### ProductImage Model
- `product`: Foreign key to Product
- `image_url`: Original image URL
- `local_path`: Local file path
- `alt_text`: Alternative text
- `is_primary`: Primary image flag
- `created_at`: Creation timestamp

## Scraper Features

### Intelligent Product Discovery
- Automatically discovers category pages
- Handles pagination
- Extracts product links from various page structures

### Robust Data Extraction
- Multiple fallback selectors for each data field
- Price extraction with currency handling
- Specification parsing from tables and lists
- Brand detection from breadcrumbs and URLs

### Image Handling
- Downloads all product images
- Generates unique filenames
- Supports various image formats
- Handles broken or missing images gracefully

### Error Handling
- Retry logic for failed requests
- Comprehensive logging
- Graceful handling of missing data
- Duplicate detection and prevention

## Export Formats

### CSV Export
Standard CSV format with all product fields.

### eBay Export
eBay-compatible CSV format with required fields for bulk listing.

### Amazon Export
Amazon inventory file format for seller central.

### Shopify Export
Shopify product import format with variants and images.

## Configuration

### Settings
Key settings in `bathing_scraper/settings.py`:
- `MEDIA_ROOT`: Directory for storing downloaded images
- `MEDIA_URL`: URL prefix for serving images
- Database configuration (default: SQLite)

### Scraper Configuration
Modify `products/scraper.py` to adjust:
- Request headers and user agent
- Retry logic and delays
- Selector patterns for different page structures
- Image download limits

## Extending the Scraper

### Adding New Export Formats
1. Create a new exporter class in `products/exporters.py`
2. Inherit from `ProductExporter`
3. Implement the `export()` method
4. Add the format to the export management command

### Customizing Data Extraction
1. Modify selector patterns in `scraper.py`
2. Add new extraction methods for additional fields
3. Update the Product model if needed
4. Create and run migrations

### Adding New Scraped Fields
1. Add fields to the Product model
2. Update the scraper extraction logic
3. Modify export formats as needed
4. Run migrations

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed
2. **Permission Errors**: Check media directory permissions
3. **Network Errors**: Verify internet connection and target site availability
4. **Database Errors**: Run migrations if model changes were made

### Logging
Enable verbose logging for debugging:
```bash
python manage.py scrape_products --verbose
```

### Performance
- Use `--limit` for testing
- Monitor memory usage for large scrapes
- Consider database optimization for large datasets

## Legal Considerations

- Respect robots.txt and terms of service
- Implement appropriate delays between requests
- Use scraped data responsibly
- Consider reaching out to the website owner for permission

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is for educational and personal use. Please respect the terms of service of the websites you scrape. 