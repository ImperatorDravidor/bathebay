# Bathing Brands Scraper

A Django-based web scraper for extracting product information from bathingbrands.com with a comprehensive admin interface and modular architecture.

## 🏗️ Project Structure

```
bathscraper/
├── docs/                           # Documentation files
│   ├── HOW_TO_USE_SCRAPER.md      # Detailed usage guide
│   ├── NAVBAR_IMPLEMENTATION_SUMMARY.md
│   ├── PRODUCT_HIERARCHY_TREE.md   # Product categorization structure
│   ├── SYSTEM_IMPROVEMENTS.md     # System enhancement notes
│   └── FRONTEND_IMPROVEMENTS.md   # UI/UX improvement notes
├── scripts/                        # Utility scripts
│   ├── check_server.py            # Server status checker
│   ├── check_products.py          # Product database checker
│   ├── create_admin.py            # Admin user creation
│   ├── find_huum_urls.py          # HUUM product URL finder
│   └── test_scraper.py            # Scraper testing utility
├── products/                       # Main Django app
│   ├── scrapers/                  # Modular scraper components
│   │   ├── __init__.py
│   │   ├── base_scraper.py        # Base scraper functionality
│   │   ├── data_validator.py      # Data validation utilities
│   │   ├── content_extractors.py  # Content extraction methods
│   │   └── enhanced_scraper.py    # Main scraper implementation
│   ├── management/commands/       # Django management commands
│   │   ├── intelligent_scrape.py  # Smart hierarchical scraping
│   │   ├── scrape_huum.py         # HUUM-specific scraper
│   │   ├── scrape_all_brands.py   # All brands scraper
│   │   ├── export_products.py     # Product export utility
│   │   ├── clean_product_data.py  # Data cleaning utility
│   │   ├── delete_all_products.py # Database cleanup
│   │   └── populate_hierarchy.py  # Hierarchy population
│   ├── templates/                 # Django templates
│   ├── migrations/                # Database migrations
│   ├── models.py                  # Database models
│   ├── views.py                   # Web views
│   ├── admin.py                   # Admin interface
│   └── urls.py                    # URL routing
├── bathing_scraper/               # Django project settings
├── media/                         # Media files storage
├── venv/                          # Virtual environment
├── manage.py                      # Django management script
├── requirements.txt               # Python dependencies
└── db.sqlite3                     # SQLite database
```

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create admin user
python scripts/create_admin.py
```

### 3. Start Development Server

```bash
# Start Django server
python manage.py runserver

# Check server status
python scripts/check_server.py
```

## 📊 Usage

### Web Interface

- **Home**: http://127.0.0.1:8000/
- **Products**: http://127.0.0.1:8000/products/
- **Admin**: http://127.0.0.1:8000/admin/
  - Username: `admin`
  - Password: `magnesium`

### Command Line Scraping

#### Scrape All Brands
```bash
python manage.py scrape_all_brands
python manage.py scrape_all_brands --brands HUUM Harvia --limit-per-brand 10
python manage.py scrape_all_brands --dry-run  # Preview without saving
```

#### Scrape Specific Brand
```bash
python manage.py scrape_huum
python manage.py scrape_huum --limit 5 --category "Sauna"
```

#### Intelligent Scraping
```bash
python manage.py intelligent_scrape --brand HUUM
python manage.py intelligent_scrape --test-url "https://bathingbrands.com/54661/huum/drop-45/electric-heaters"
```

### Utility Scripts

```bash
# Test scraper functionality
python scripts/test_scraper.py

# Check product database
python scripts/check_products.py

# Find HUUM product URLs
python scripts/find_huum_urls.py

# Check server status
python scripts/check_server.py
```

## 🏗️ Architecture

### Modular Scraper Design

The scraper is built with a modular architecture for maintainability and extensibility:

- **BaseScraper**: Core functionality (HTTP requests, URL handling, text processing)
- **DataValidator**: Input validation and data quality checks
- **ContentExtractor**: Specialized content extraction methods
- **EnhancedBathingBrandsScraper**: Main scraper implementation

### Database Models

- **Product**: Main product information
- **ProductImage**: Product images and media
- **ProductSpecification**: Technical specifications
- **ProductDocument**: Manuals and documentation
- **ProductVariant**: Product variations
- **RelatedProduct**: Product relationships

## 🔧 Features

### Scraping Capabilities

- **Hierarchical Discovery**: Brand → Category → Collection → Product
- **Comprehensive Data Extraction**: 
  - Product details (title, price, SKU, descriptions)
  - Technical specifications
  - Images and media
  - Documentation (PDFs, manuals)
  - Related products
- **Smart Validation**: Data quality checks and validation
- **Error Handling**: Robust error handling and retry mechanisms
- **Rate Limiting**: Configurable delays to respect server resources

### Admin Interface

- **Rich Product Management**: Full CRUD operations
- **Advanced Filtering**: Filter by brand, category, price, etc.
- **Bulk Operations**: Mass edit and export capabilities
- **Image Management**: Product image handling and display
- **Search Functionality**: Full-text search across products

### Web Interface

- **Responsive Design**: Mobile-friendly product browsing
- **Brand Navigation**: Organized brand and category browsing
- **Product Details**: Comprehensive product information display
- **Search and Filtering**: Advanced product search capabilities

## 📚 Documentation

Detailed documentation is available in the `docs/` directory:

- **[HOW_TO_USE_SCRAPER.md](docs/HOW_TO_USE_SCRAPER.md)**: Complete usage guide
- **[PRODUCT_HIERARCHY_TREE.md](docs/PRODUCT_HIERARCHY_TREE.md)**: Product categorization
- **[SYSTEM_IMPROVEMENTS.md](docs/SYSTEM_IMPROVEMENTS.md)**: Enhancement notes
- **[FRONTEND_IMPROVEMENTS.md](docs/FRONTEND_IMPROVEMENTS.md)**: UI/UX notes

## 🛠️ Development

### Adding New Scrapers

1. Create a new scraper class inheriting from `BaseScraper`
2. Implement required extraction methods
3. Add validation using `DataValidator`
4. Create management command for CLI access

### Extending Models

1. Add new fields to existing models or create new models
2. Create and run migrations: `python manage.py makemigrations && python manage.py migrate`
3. Update admin interface in `admin.py`
4. Update scraper to extract new data

### Testing

```bash
# Test specific product URL
python manage.py intelligent_scrape --test-url "PRODUCT_URL"

# Run scraper tests
python scripts/test_scraper.py

# Check data integrity
python scripts/check_products.py
```

## 📋 Requirements

- Python 3.8+
- Django 5.2+
- BeautifulSoup4
- Requests
- Pillow (for image handling)
- lxml (for XML parsing)

## 🤝 Contributing

1. Follow the modular architecture patterns
2. Add appropriate validation for new data fields
3. Update documentation for new features
4. Test thoroughly before committing changes

## 📄 License

This project is for educational and research purposes. Please respect the terms of service of the target website. 