# 🛠️ Bathing Brands Scraper

A Django-based web scraper that automatically extracts product data from bathingbrands.com and exports it to eBay, Amazon, and Shopify.

## 🚀 Quick Start

1. **Setup**: Double-click `documentation/SETUP_FOR_TEAM.bat`
2. **Start**: Run `python manage.py runserver`
3. **Access**: Go to `http://127.0.0.1:8000/admin/`
4. **Scrape**: Run `python manage.py scrape_products_improved`

## 📚 Complete Documentation

**👉 All guides are in the `documentation/` folder:**
- `documentation/README.md` - Complete system guide
- `documentation/SETUP_FOR_TEAM.bat` - Automated setup

## 🎯 What This Does

- **Scrapes** bathingbrands.com for product data
- **Stores** products in database with quality indicators
- **Exports** to eBay, Amazon, Shopify formats
- **Manages** products through web admin panel

## 🔧 Core Files

- `products/scraper_improved.py` - Main scraper (recommended)
- `products/exporters.py` - Export tools
- `products/admin.py` - Admin panel
- `products/management/commands/` - Command-line tools

## 🏗️ Tech Stack Overview - ### For TJ 

### Backend Framework
- **Django 5.2.1+** - Main web framework
  - Django Admin - Custom admin interface with dashboard
  - Django ORM - Database models and relationships
  - Django Management Commands - CLI tools for scraping
  - Django Templates - HTML rendering system
  - Django Static Files - CSS/JS asset management

### Database
- **SQLite3** - Default database (development)
  - Database file: `db.sqlite3`
  - Supports migrations and indexing
  - Easy to backup and transfer

### Web Scraping & HTTP
- **Requests 2.32.3+** - HTTP client for web scraping
  - Session management with headers
  - Cookie handling and authentication
  - Error handling and retries

- **BeautifulSoup4 4.13.4+** - HTML/XML parsing
  - CSS selector support
  - Tree traversal and manipulation
  - Robust HTML parsing

- **lxml 4.9.0+** - XML/HTML parser backend
  - Fast C-based parsing
  - XPath support
  - Used by BeautifulSoup for performance

### Image Processing
- **Pillow 10.0.0+** - Image processing library
  - Image validation and manipulation
  - Format conversion support
  - Used for product image handling

### Python Environment
- **Python 3.x** - Core language
- **Virtual Environment** - Isolated dependencies in `venv/`

### Development Tools
- **Django Debug Mode** - Development debugging
- **Logging** - Comprehensive logging system
- **CSV Export** - Data export functionality

### Project Structure
```
bathscraper/
├── bathing_scraper/          # Django project settings
│   ├── settings.py           # Configuration
│   ├── urls.py              # URL routing
│   └── wsgi.py              # WSGI application
├── products/                 # Main Django app
│   ├── models.py            # Database models
│   ├── admin.py             # Admin interface
│   ├── scraper_enhanced.py  # Web scraping logic
│   ├── views.py             # Web views
│   ├── management/commands/ # CLI commands
│   └── templates/           # HTML templates
├── media/                   # Uploaded files
├── venv/                    # Virtual environment
├── requirements.txt         # Python dependencies
└── manage.py               # Django management script
```

### Key Features Implemented
- **Custom Django Admin Dashboard** - Centralized control panel
- **Advanced Web Scraping** - Multi-stage hierarchical scraping
- **Data Validation** - Quality checks and data integrity
- **Export Systems** - CSV and marketplace format exports
- **Management Commands** - CLI tools for automation
- **Image Management** - Product image handling and storage
- **Relationship Modeling** - Complex product relationships
- **Search & Filtering** - Advanced admin search capabilities

### For TJ 
1. **Dependencies**: All listed in `requirements.txt`
2. **Database**: SQLite file included, maybe push to supabase? 
3. **Admin Access**: Create superuser with `python create_admin.py`
4. **Main Code**: Focus on `products/` directory
5. **Scraping Logic**: See `products/scraper_enhanced.py`
6. **Admin Interface**: Fully customized in `products/admin.py`

---

**Need help?** Check `documentation/README.md` for complete instructions. 