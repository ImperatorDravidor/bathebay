# 🏢 Bathing Brands Scraper - Complete Usage Guide

## 📋 Table of Contents
1. [Overview](#overview)
2. [Getting Started](#getting-started)
3. [Admin Panel Navigation](#admin-panel-navigation)
4. [Scraping Methods](#scraping-methods)
5. [Data Structure](#data-structure)
6. [Command Line Usage](#command-line-usage)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

## 🎯 Overview

The Bathing Brands Scraper is a comprehensive Django-based system designed to extract product information from bathingbrands.com following their exact hierarchy structure:

**Brand → Category → Collection → Product**

### Key Features
- ✅ **Hierarchical Navigation**: Browse products by brand, category, and collection
- ✅ **Intelligent Scraping**: Automatically discovers and follows website structure
- ✅ **Complete Data Extraction**: Images, specifications, documents, related products
- ✅ **Admin Interface**: User-friendly web interface for management
- ✅ **Command Line Tools**: Powerful CLI for batch operations

## 🚀 Getting Started

### 1. Initial Setup
```bash
# Navigate to project directory
cd bathscraper

# Activate virtual environment
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create admin user (if not exists)
python manage.py createsuperuser
```

### 2. Start the Server
```bash
python manage.py runserver
```

### 3. Access Admin Panel
Open your browser and go to: `http://127.0.0.1:8000/admin/`
- Username: `admin`
- Password: `magnesium` (or your custom password)

## 🏢 Admin Panel Navigation

### Main Dashboard
The admin panel provides a hierarchical view of your scraped data:

1. **Brand Hierarchy Manager** (`/admin/products/product/hierarchy/`)
   - Overview of all brands
   - Statistics for each brand
   - Quick navigation to categories

2. **Scraping Control Center** (`/admin/products/product/scraping/`)
   - Forms for different scraping operations
   - Real-time status updates
   - Quick action buttons

### Navigation Flow
```
🏢 All Brands
    ↓ Click on brand
📂 Brand Categories (e.g., HUUM)
    ↓ Click on category
📦 Category Collections (e.g., HUUM → Electric Heaters)
    ↓ Click on collection
🛍️ Products List (e.g., HUUM → Electric Heaters → DROP Series)
    ↓ Click on product
📋 Product Details (Edit/View individual product)
```

## 🚀 Scraping Methods

### Method 1: Web Interface (Recommended for Beginners)

#### A. Scrape by Brand
1. Go to **Scraping Control Center**
2. Select **"Scrape by Brand"** section
3. Choose a brand from dropdown (e.g., "HUUM")
4. Set product limit (start with 5-10)
5. Click **"🚀 Scrape Brand"**

#### B. Scrape by Category
1. Select **"Scrape by Category"** section
2. Choose brand and enter category name
3. Example: Brand="HUUM", Category="Electric Heaters"
4. Click **"📂 Scrape Category"**

#### C. Scrape Single Product
1. Select **"Scrape Single Product"** section
2. Paste full product URL
3. Example: `https://www.bathingbrands.com/54661/huum/drop-45/electric-heaters`
4. Click **"🛍️ Scrape Product"**

### Method 2: Command Line Interface

#### Basic Commands
```bash
# Scrape specific brand (limit 10 products)
python manage.py intelligent_scrape --brand "HUUM" --limit 10

# Scrape specific category
python manage.py intelligent_scrape --brand "HUUM" --category "Electric Heaters" --limit 5

# Scrape single product
python manage.py intelligent_scrape --test-url "https://www.bathingbrands.com/54661/huum/drop-45/electric-heaters"

# Delete all products (careful!)
python manage.py delete_all_products
```

#### Advanced Examples
```bash
# Scrape multiple brands sequentially
python manage.py intelligent_scrape --brand "HUUM" --limit 5
python manage.py intelligent_scrape --brand "Harvia" --limit 5
python manage.py intelligent_scrape --brand "Mr.Steam" --limit 5

# Scrape all products from a brand (no limit)
python manage.py intelligent_scrape --brand "HUUM"

# Scrape with specific category focus
python manage.py intelligent_scrape --brand "HUUM" --category "Controls" --limit 3
```

## 📊 Data Structure

### What Gets Scraped
For each product, the scraper extracts:

#### Basic Information
- **Title**: Product name
- **Brand**: Manufacturer (HUUM, Harvia, etc.)
- **Category**: Main category (Electric Heaters, Controls, etc.)
- **Collection**: Subcategory/series (DROP Series, UKU Series, etc.)
- **SKU**: Product code
- **Model**: Model number
- **Price**: Current price

#### Detailed Content
- **Descriptions**: Short and full descriptions
- **Features**: Product features list
- **Includes**: What's included in the box
- **Technical Info**: Technical specifications and requirements
- **Inspiration**: Design and usage inspiration content

#### Media & Documents
- **Images**: All product images (main, gallery, technical)
- **Specifications**: Detailed technical specifications
- **Documents**: PDFs, manuals, certificates

#### Related Products
- **Required for Operation**: Essential accessories
- **Sauna Heater Controls**: Compatible controls
- **Related Items**: Complementary products
- **Accessories**: Optional add-ons

### Database Structure
```
Product (Main table)
├── ProductImage (Multiple images per product)
├── ProductSpecification (Key-value specifications)
├── ProductDocument (PDFs and manuals)
├── ProductVariant (Color/size options)
└── RelatedProduct (Product relationships)
```

## 🛠️ Command Line Usage

### Available Commands

#### 1. Intelligent Scraper
```bash
python manage.py intelligent_scrape [options]
```

**Options:**
- `--brand BRAND`: Target specific brand
- `--category CATEGORY`: Target specific category
- `--limit NUMBER`: Maximum products to scrape
- `--test-url URL`: Test single product URL

**Examples:**
```bash
# Quick test with single product
python manage.py intelligent_scrape --test-url "https://www.bathingbrands.com/54661/huum/drop-45/electric-heaters"

# Scrape HUUM brand, limit 10 products
python manage.py intelligent_scrape --brand "HUUM" --limit 10

# Scrape specific category
python manage.py intelligent_scrape --brand "HUUM" --category "Electric Heaters" --limit 5
```

#### 2. Data Management
```bash
# Delete all products
python manage.py delete_all_products

# Create admin user
python manage.py createsuperuser

# Run database migrations
python manage.py migrate
```

### Scraping Process Flow
1. **Brand Discovery**: Finds all available brands
2. **Category Discovery**: Discovers categories for each brand
3. **Collection Discovery**: Finds collections within categories
4. **Product Discovery**: Locates all products in collections
5. **Data Extraction**: Extracts complete product information
6. **Related Products**: Links related/required products

## 🔧 Troubleshooting

### Common Issues

#### 1. "No products found" Error
**Cause**: Website structure changed or network issues
**Solution**:
```bash
# Test with single product first
python manage.py intelligent_scrape --test-url "https://www.bathingbrands.com/54661/huum/drop-45/electric-heaters"

# Check if website is accessible
curl -I https://www.bathingbrands.com
```

#### 2. "UNIQUE constraint failed" Error
**Cause**: Trying to scrape duplicate products
**Solution**:
```bash
# Clear existing data
python manage.py delete_all_products

# Or check existing products
python manage.py shell
>>> from products.models import Product
>>> Product.objects.filter(sku="H1001012").exists()
```

#### 3. Template Errors
**Cause**: Missing template tags or filters
**Solution**:
- Ensure `{% load custom_filters %}` is in templates
- Check that `products/templatetags/custom_filters.py` exists

#### 4. Slow Scraping
**Cause**: Network delays or large datasets
**Solution**:
- Use smaller limits: `--limit 5`
- Scrape specific categories instead of entire brands
- Check internet connection

### Debug Mode
Enable detailed logging:
```python
# In settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'products.scraper_enhanced': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## ✅ Best Practices

### 1. Start Small
```bash
# Begin with single products
python manage.py intelligent_scrape --test-url "URL"

# Then try small batches
python manage.py intelligent_scrape --brand "HUUM" --limit 3
```

### 2. Respect the Website
- Use reasonable delays between requests (built-in)
- Don't scrape excessively large batches
- Monitor for any blocking or rate limiting

### 3. Data Management
```bash
# Regular backups
python manage.py dumpdata products > backup.json

# Clean data periodically
python manage.py delete_all_products  # When needed
```

### 4. Monitoring Progress
- Use the admin panel to monitor scraping progress
- Check logs for any errors or warnings
- Verify data quality in the hierarchy view

### 5. Incremental Scraping
```bash
# Scrape different brands separately
python manage.py intelligent_scrape --brand "HUUM" --limit 10
python manage.py intelligent_scrape --brand "Harvia" --limit 10
python manage.py intelligent_scrape --brand "Mr.Steam" --limit 10
```

## 📈 Advanced Usage

### Batch Operations
```bash
# Create a batch script (Windows)
@echo off
echo Starting batch scraping...
python manage.py intelligent_scrape --brand "HUUM" --limit 5
python manage.py intelligent_scrape --brand "Harvia" --limit 5
python manage.py intelligent_scrape --brand "Mr.Steam" --limit 5
echo Batch scraping complete!
```

### Custom Filtering
```python
# In Django shell
python manage.py shell

# Filter products by criteria
from products.models import Product

# Find products without images
products_no_images = Product.objects.filter(images__isnull=True)

# Find expensive products
expensive_products = Product.objects.filter(price__gt=1000)

# Find products by brand and category
huum_heaters = Product.objects.filter(brand="HUUM", category="Electric Heaters")
```

### Export Data
```python
# Export to CSV (in Django shell)
import csv
from products.models import Product

with open('products_export.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(['Brand', 'Title', 'SKU', 'Price', 'Category'])
    
    for product in Product.objects.all():
        writer.writerow([
            product.brand,
            product.title,
            product.sku,
            product.price,
            product.category
        ])
```

## 🎯 Quick Start Checklist

- [ ] Server running (`python manage.py runserver`)
- [ ] Admin panel accessible (`http://127.0.0.1:8000/admin/`)
- [ ] Test single product scraping
- [ ] Try brand scraping with small limit
- [ ] Explore hierarchy navigation
- [ ] Check scraped data quality
- [ ] Set up regular scraping routine

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Review error messages carefully
3. Test with single products before batch operations
4. Use the admin panel for visual debugging
5. Check Django logs for detailed error information

---

**Happy Scraping! 🚀**

*Remember: Always respect the website's terms of service and use reasonable scraping practices.* 