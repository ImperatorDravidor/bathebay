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

---

**Need help?** Check `documentation/README.md` for complete instructions. 