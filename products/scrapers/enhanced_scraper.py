"""
Enhanced Bathing Brands Scraper - Refactored modular version
"""

import os
import re
import json
import logging
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from .base_scraper import BaseScraper
from .content_extractors import ContentExtractor

# Only setup Django if running as script, not when imported
if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
    django.setup()

logger = logging.getLogger(__name__)


class EnhancedBathingBrandsScraper(BaseScraper):
    """Enhanced scraper following exact Brand → Category → Collection → Product hierarchy"""
    
    def __init__(self):
        super().__init__()
        self.content_extractor = ContentExtractor(self)
        self.hierarchy_map = {}  # Track brand → category → collection structure
        self.known_brands = [
            'Amerec', 'Aromamist', 'Auroom', 'Cozy Heat', 'Delta', 'EmotionWood',
            'Finlandia', 'Finnmark', 'Haljas Houses', 'Harvia', 'HUUM', 'Hukka',
            'Kohler', 'Kolo', 'Mr.Steam', 'Narvi', 'PROSAUNAS', 'Rento',
            'SaunaLife', 'Saunum', 'Steamist', 'ThermaSol'
        ]
    
    def discover_brands(self):
        """Step 1: Discover all brands from the main products page"""
        logger.info("🏢 Step 1: Discovering brands from bathingbrands.com/products...")
        
        try:
            soup = self.get_page(f"{self.base_url}/products/")
            brands = {}
            
            # Find all navigation links
            nav_items = soup.find_all('a', href=True)
            
            for link in nav_items:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Check if this link text matches a known brand
                for brand_name in self.known_brands:
                    if (brand_name.lower() == text.lower() or 
                        brand_name.lower().replace('.', '') == text.lower().replace('.', '')):
                        
                        # Extract brand slug from URL or create from name
                        if '/products/' in href:
                            url_parts = href.split('/')
                            if len(url_parts) >= 3:
                                brand_slug = url_parts[2]
                            else:
                                brand_slug = brand_name.lower().replace(' ', '-').replace('.', '')
                        else:
                            brand_slug = brand_name.lower().replace(' ', '-').replace('.', '')
                        
                        brand_url = f"{self.base_url}/products/{brand_slug}/"
                        
                        brands[brand_name] = {
                            'name': brand_name,
                            'slug': brand_slug,
                            'url': brand_url,
                            'categories': {},
                            'scraped': False
                        }
                        break
            
            # If we didn't find brands in navigation, create them manually
            if not brands:
                logger.info("🔍 Creating brand URLs manually...")
                for brand_name in self.known_brands:
                    brand_slug = brand_name.lower().replace(' ', '-').replace('.', '')
                    brand_url = f"{self.base_url}/products/{brand_slug}/"
                    
                    brands[brand_name] = {
                        'name': brand_name,
                        'slug': brand_slug,
                        'url': brand_url,
                        'categories': {},
                        'scraped': False
                    }
            
            logger.info(f"🏢 Found {len(brands)} brands: {list(brands.keys())}")
            return brands
            
        except Exception as e:
            logger.error(f"❌ Error discovering brands: {e}")
            return {}
    
    def extract_product_data(self, product_url):
        """Extract comprehensive product data from a product page"""
        logger.info(f"🛍️ Extracting product data from: {product_url}")
        
        try:
            soup = self.get_page(product_url)
            if not soup:
                return None
            
            # Extract basic product information
            product_data = {
                'title': self._extract_title(soup),
                'brand': self._extract_brand(soup, product_url),
                'sku': self._extract_sku(soup, product_url),
                'price': self._extract_price(soup),
                'retail_price': self._extract_price(soup, price_type='retail'),
                'short_description': self._extract_short_description(soup),
                'full_description': self._extract_full_description(soup),
                'category': self._extract_category(soup),
                'subcategory': self._extract_subcategory(soup),
                'source_url': product_url,
            }
            
            # Extract detailed content using content extractor
            product_data.update({
                'features': self.content_extractor.extract_tab_content(soup, 'Features'),
                'technical_info': self.content_extractor.extract_tab_content(soup, 'Technical'),
                'includes': self.content_extractor.extract_tab_content(soup, 'Includes'),
                'shipping_info': self.content_extractor.extract_tab_content(soup, 'Shipping'),
                'images': self.content_extractor.extract_all_images(soup, product_url),
                'specifications_dict': self.content_extractor.extract_specifications(soup),
                'documents': self.content_extractor.extract_documents(soup),
            })
            
            # Extract model name and other details
            product_data['model_name'] = self._extract_model_name(soup)
            
            # Validate required fields
            if not self.validator.validate_title(product_data['title']):
                logger.error(f"❌ Invalid title: {product_data['title']}")
                return None
            
            if not self.validator.validate_brand(product_data['brand']):
                logger.error(f"❌ Invalid brand: {product_data['brand']}")
                return None
            
            if not self.validator.validate_sku(product_data['sku']):
                logger.error(f"❌ Invalid SKU: {product_data['sku']}")
                return None
            
            logger.info(f"✅ Successfully extracted: {product_data['title']}")
            return product_data
            
        except Exception as e:
            logger.error(f"❌ Error extracting product data from {product_url}: {e}")
            return None
    
    def _extract_title(self, soup):
        """Extract product title"""
        # Try multiple selectors for title
        title_selectors = [
            'h1.product-title',
            'h1[class*="title"]',
            'h1[class*="product"]',
            '.product-name h1',
            '.product-title',
            'h1'
        ]
        
        for selector in title_selectors:
            element = soup.select_one(selector)
            if element:
                title = self.clean_text(element.get_text())
                if title and len(title) > 3:
                    return title
        
        return "Unknown Product"
    
    def _extract_brand(self, soup, product_url):
        """Extract brand name from page or URL"""
        # Try to extract from breadcrumbs or navigation
        breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], {'class': re.compile(r'breadcrumb', re.I)})
        for breadcrumb in breadcrumbs:
            links = breadcrumb.find_all('a')
            for link in links:
                text = link.get_text(strip=True)
                if text in self.known_brands:
                    return text
        
        # Extract from URL
        for brand in self.known_brands:
            brand_slug = brand.lower().replace(' ', '-').replace('.', '')
            if f'/{brand_slug}/' in product_url.lower():
                return brand
        
        return "Unknown Brand"
    
    def _extract_sku(self, soup, product_url):
        """Extract SKU from page"""
        # Try multiple methods to find SKU
        sku_patterns = [
            r'SKU[:\s]*([A-Z0-9\-_]+)',
            r'Model[:\s]*([A-Z0-9\-_]+)',
            r'Item[:\s]*#?([A-Z0-9\-_]+)',
        ]
        
        text_content = soup.get_text()
        for pattern in sku_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Extract from URL as fallback
        url_parts = product_url.split('/')
        for part in url_parts:
            if part.isdigit() and len(part) >= 4:
                return part
        
        return f"SKU-{hash(product_url) % 100000}"
    
    def _extract_price(self, soup, price_type='regular'):
        """Extract price from page"""
        price_selectors = [
            '.price',
            '.product-price',
            '[class*="price"]',
            '.cost',
            '.amount'
        ]
        
        for selector in price_selectors:
            elements = soup.select(selector)
            for element in elements:
                price_text = element.get_text(strip=True)
                price = self._parse_price(price_text)
                if price:
                    return price
        
        return None
    
    def _parse_price(self, price_text):
        """Parse price from text"""
        if not price_text:
            return None
        
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
        if price_match:
            try:
                return Decimal(price_match.group())
            except (InvalidOperation, ValueError):
                pass
        
        return None
    
    def _extract_short_description(self, soup):
        """Extract short product description"""
        desc_selectors = [
            '.product-summary',
            '.short-description',
            '.product-intro',
            '.description-short'
        ]
        
        for selector in desc_selectors:
            element = soup.select_one(selector)
            if element:
                return self.clean_text(element.get_text())
        
        return ""
    
    def _extract_full_description(self, soup):
        """Extract full product description"""
        return self.content_extractor.extract_tab_content(soup, 'Description')
    
    def _extract_category(self, soup):
        """Extract product category"""
        # Try to extract from breadcrumbs
        breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], {'class': re.compile(r'breadcrumb', re.I)})
        for breadcrumb in breadcrumbs:
            links = breadcrumb.find_all('a')
            if len(links) >= 3:  # Home > Brand > Category
                return self.clean_text(links[2].get_text())
        
        return ""
    
    def _extract_subcategory(self, soup):
        """Extract product subcategory"""
        # Try to extract from breadcrumbs
        breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], {'class': re.compile(r'breadcrumb', re.I)})
        for breadcrumb in breadcrumbs:
            links = breadcrumb.find_all('a')
            if len(links) >= 4:  # Home > Brand > Category > Subcategory
                return self.clean_text(links[3].get_text())
        
        return ""
    
    def _extract_model_name(self, soup):
        """Extract model name from product page"""
        model_patterns = [
            r'Model[:\s]*([A-Z0-9\-\s]+)',
            r'Series[:\s]*([A-Z0-9\-\s]+)',
        ]
        
        text_content = soup.get_text()
        for pattern in model_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ""
    
    def save_product(self, product_data):
        """Save product data to database"""
        try:
            from products.models import Product, ProductImage, ProductSpecification, ProductDocument
            
            # Create or update product
            product, created = Product.objects.update_or_create(
                sku=product_data['sku'],
                defaults={
                    'title': product_data['title'],
                    'brand': product_data['brand'],
                    'short_description': product_data.get('short_description', ''),
                    'full_description': product_data.get('full_description', ''),
                    'price': product_data.get('price'),
                    'retail_price': product_data.get('retail_price'),
                    'category': product_data.get('category', ''),
                    'subcategory': product_data.get('subcategory', ''),
                    'model': product_data.get('model_name', ''),
                    'features': product_data.get('features', ''),
                    'technical_info': product_data.get('technical_info', ''),
                    'includes': product_data.get('includes', ''),
                    'shipping_info': product_data.get('shipping_info', ''),
                    'source_url': product_data['source_url'],
                    'specifications': json.dumps(product_data.get('specifications_dict', {})),
                }
            )
            
            # Save images
            if product_data.get('images'):
                # Clear existing images
                product.images.all().delete()
                
                for i, img_data in enumerate(product_data['images']):
                    ProductImage.objects.create(
                        product=product,
                        image_url=img_data['url'],
                        alt_text=img_data.get('alt_text', ''),
                        image_type=img_data.get('type', 'main'),
                        is_primary=(i == 0)
                    )
            
            # Save specifications
            if product_data.get('specifications_dict'):
                # Clear existing specifications
                product.product_specifications.all().delete()
                
                for name, value in product_data['specifications_dict'].items():
                    ProductSpecification.objects.create(
                        product=product,
                        name=name,
                        value=str(value)
                    )
            
            # Save documents
            if product_data.get('documents'):
                # Clear existing documents
                product.documents.all().delete()
                
                for doc_data in product_data['documents']:
                    ProductDocument.objects.create(
                        product=product,
                        title=doc_data['title'],
                        document_url=doc_data['url'],
                        document_type=doc_data.get('type', 'manual')
                    )
            
            action = "Created" if created else "Updated"
            logger.info(f"✅ {action} product: {product.title}")
            return product
            
        except Exception as e:
            logger.error(f"❌ Error saving product: {e}")
            return None 