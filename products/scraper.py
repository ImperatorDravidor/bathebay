import os
import re
import json
import time
import logging
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from django.conf import settings
from django.core.files.base import ContentFile
from django.utils.text import slugify
from .models import Product, ProductImage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_URL = "https://www.bathingbrands.com"
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

class BathingBrandsScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.scraped_urls = set()
        
    def get_page(self, url, retries=3):
        """Get page content with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response
            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
                if attempt < retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None
    
    def get_all_category_urls(self):
        """Scrape the main navigation and return all category/subcategory links"""
        logger.info("Fetching main category URLs...")
        response = self.get_page(BASE_URL)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        category_urls = []
        
        # Start with the main products page
        category_urls.append(f"{BASE_URL}/products")
        
        # Look for brand-specific URLs in the navigation
        # Based on the website structure, brands are organized under /products/[brand]/[category]
        brands = [
            'amerec', 'aromamist', 'auroom', 'cozy-heat', 'delta', 'emotionwood',
            'finlandia', 'finnmark', 'haljas-houses', 'harvia', 'huum', 'hukka',
            'kohler', 'kolo', 'mr-steam', 'narvi', 'prosaunas', 'rento',
            'saunalife', 'saunum', 'steamist', 'thermasol'
        ]
        
        categories = [
            'residential-steam', 'commercial-steam', 'sauna', 'room-kits',
            'accessories', 'steam-shower-generators', 'controls-packages',
            'lighting', 'aromatherapy-systems', 'audio-video', 'seats',
            'water-treatment', 'installation-materials', 'steam-heads',
            'aromas', 'club-generators', 'eucalyptus-pumps', 'electric-heaters',
            'wood-sauna-stoves', 'gauges', 'safety', 'generator-packages',
            'speakers', 'modular', 'outdoor', 'aroma', 'backyard-fire-pits',
            'decorative-sauna-walls', 'infrared-room-kits', 'infrared-sauna-essentials',
            'heater-packages', 'buckets-ladles', 'wall-cladding', 'bench-material',
            'trim', 'sauna-doors', 'lighting-chromotherapy', 'back-headrests',
            'sauna-buckets-ladles', 'sauna-accessories', 'sauna-aromatherapy',
            'barrel-saunas', 'indoor', 'cold-plunge-tubs', 'hot-tubs',
            'outdoor-showers', 'heat-equalizing-systems', 'chromotherapy',
            'shower-systems', 'spa-generators', 'maintenance', 'fixtures-drains',
            'fog-free-mirrors', 'rains-body-sprays'
        ]
        
        # Generate URLs for brand/category combinations
        for brand in brands:
            # Add main brand page
            brand_url = f"{BASE_URL}/products/{brand}"
            category_urls.append(brand_url)
            
            # Add brand category pages
            for category in categories:
                category_url = f"{BASE_URL}/products/{brand}/{category}"
                category_urls.append(category_url)
        
        # Also try to extract links from the actual navigation
        nav_links = soup.find_all('a', href=True)
        for link in nav_links:
            href = link.get('href')
            if href and '/products/' in href and not href.startswith('#'):
                full_url = urljoin(BASE_URL, href)
                if full_url not in category_urls:
                    category_urls.append(full_url)
        
        # Remove duplicates and sort
        category_urls = list(set(category_urls))
        logger.info(f"Found {len(category_urls)} category URLs")
        return category_urls
    
    def get_product_links_from_category(self, category_url):
        """Scrape each category page for individual product links"""
        logger.info(f"Scraping products from category: {category_url}")
        response = self.get_page(category_url)
        if not response:
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        product_links = []
        
        # Look for product links using various selectors specific to bathingbrands.com
        selectors = [
            'a[href*="/products/"]',  # General product links
            '.product-item a',
            '.product-link',
            '.product-title a',
            'a[href*="/view-product"]',  # Specific to bathingbrands.com
            'a:contains("View Product")',
            'a[href*="/product/"]',
            '.view-product a',
            '.product a'
        ]
        
        for selector in selectors:
            try:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        full_url = urljoin(BASE_URL, href)
                        # Filter out non-product URLs
                        if ('/products/' in full_url and 
                            'view-product' in full_url.lower() or 
                            '/product/' in full_url or
                            any(brand in full_url for brand in ['amerec', 'harvia', 'huum', 'mr-steam', 'steamist', 'thermasol'])):
                            product_links.append(full_url)
            except Exception as e:
                logger.warning(f"Error with selector {selector}: {e}")
        
        # Look for "View Product" buttons or links
        view_product_links = soup.find_all('a', string=re.compile(r'View Product', re.IGNORECASE))
        for link in view_product_links:
            href = link.get('href')
            if href:
                full_url = urljoin(BASE_URL, href)
                product_links.append(full_url)
        
        # Also check for pagination and get more pages
        pagination_selectors = [
            'a[href*="page="]',
            '.pagination a',
            '.pager a',
            'a:contains("Next")',
            'a:contains("›")'
        ]
        
        for selector in pagination_selectors:
            try:
                pagination_links = soup.select(selector)
                for page_link in pagination_links:
                    href = page_link.get('href')
                    if href and 'page=' in href:
                        page_url = urljoin(category_url, href)
                        if page_url not in self.scraped_urls:
                            self.scraped_urls.add(page_url)
                            time.sleep(1)  # Be respectful
                            product_links.extend(self.get_product_links_from_category(page_url))
            except Exception as e:
                logger.warning(f"Error with pagination selector {selector}: {e}")
        
        # Remove duplicates
        product_links = list(set(product_links))
        logger.info(f"Found {len(product_links)} product links in category")
        return product_links
    
    def extract_price(self, soup):
        """Extract price from various possible locations"""
        price_selectors = [
            '.price',
            '.product-price',
            '[class*="price"]',
            '.cost',
            '.amount',
            '.your-price',
            '.retail-price',
            '.sale-price',
            '.current-price',
            '[data-price]'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                # Extract numeric price - handle various formats
                price_match = re.search(r'\$?(\d+(?:,\d{3})*(?:\.\d{2})?)', price_text)
                if price_match:
                    return float(price_match.group(1).replace(',', ''))
        
        # Also check for data attributes
        price_elem = soup.find(attrs={'data-price': True})
        if price_elem:
            try:
                return float(price_elem['data-price'])
            except (ValueError, KeyError):
                pass
        
        # Look for price in meta tags
        price_meta = soup.find('meta', {'property': 'product:price:amount'})
        if price_meta:
            try:
                return float(price_meta.get('content', ''))
            except ValueError:
                pass
        
        return None
    
    def extract_specifications(self, soup):
        """Extract product specifications"""
        specs = {}
        
        # Look for specification tables or lists
        spec_containers = soup.find_all(['table', 'dl', 'div'], class_=re.compile(r'spec|feature|detail'))
        
        for container in spec_containers:
            if container.name == 'table':
                rows = container.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            specs[key] = value
            
            elif container.name == 'dl':
                terms = container.find_all('dt')
                descriptions = container.find_all('dd')
                for term, desc in zip(terms, descriptions):
                    key = term.get_text(strip=True)
                    value = desc.get_text(strip=True)
                    if key and value:
                        specs[key] = value
        
        return json.dumps(specs) if specs else ""
    
    def scrape_product(self, product_url):
        """Scrape individual product details"""
        if product_url in self.scraped_urls:
            return None
        
        self.scraped_urls.add(product_url)
        logger.info(f"Scraping product: {product_url}")
        
        response = self.get_page(product_url)
        if not response:
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract basic product information
        title_selectors = [
            'h1', 
            '.product-title', 
            '.product-name', 
            '.title',
            '[class*="title"]',
            '.product-info h1',
            '.product-details h1'
        ]
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                if title and len(title) > 3:  # Make sure we have a meaningful title
                    break
        
        # Fallback: try to extract from page title
        if not title:
            page_title = soup.find('title')
            if page_title:
                title = page_title.get_text(strip=True)
                # Clean up the title
                title = title.replace(' | Bathing Brands', '').replace('Bathing Brands - ', '').strip()
        
        if not title or len(title) < 3:
            logger.warning(f"Could not find meaningful title for {product_url}")
            return None
        
        # Extract description
        desc_selectors = [
            '.product-description',
            '.description',
            '.product-details',
            '.product-info p',
            '.content p'
        ]
        description = ""
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                break
        
        # Extract price
        price = self.extract_price(soup)
        
        # Extract SKU/Model number
        sku_selectors = [
            '[class*="sku"]',
            '[class*="model"]',
            '[class*="part"]',
            '.product-code'
        ]
        sku = None
        for selector in sku_selectors:
            sku_elem = soup.select_one(selector)
            if sku_elem:
                sku_text = sku_elem.get_text(strip=True)
                sku_match = re.search(r'(?:SKU|Model|Part)[\s:]*([A-Z0-9-]+)', sku_text, re.IGNORECASE)
                if sku_match:
                    sku = sku_match.group(1)
                    break
        
        # Generate SKU from URL if not found
        if not sku:
            sku = urlparse(product_url).path.split('/')[-1] or str(hash(product_url))[-8:]
        
        # Extract brand from URL or breadcrumbs
        brand = "Unknown"
        breadcrumbs = soup.find_all(['nav', 'ol', 'ul'], class_=re.compile(r'breadcrumb'))
        for breadcrumb in breadcrumbs:
            links = breadcrumb.find_all('a')
            if len(links) > 1:  # Skip "Home"
                brand = links[1].get_text(strip=True)
                break
        
        # Fallback: extract brand from URL
        if brand == "Unknown":
            url_parts = product_url.split('/')
            if '/products/' in product_url:
                # Find the brand part in the URL structure
                try:
                    products_index = url_parts.index('products')
                    if products_index + 1 < len(url_parts):
                        brand_part = url_parts[products_index + 1]
                        if brand_part and brand_part not in ['www.bathingbrands.com', 'products', 'product']:
                            brand = brand_part.replace('-', ' ').title()
                except (ValueError, IndexError):
                    pass
        
        # If still unknown, try to extract from page content
        if brand == "Unknown":
            brand_selectors = [
                '[class*="brand"]',
                '[class*="manufacturer"]',
                '.product-brand',
                '.brand-name'
            ]
            for selector in brand_selectors:
                brand_elem = soup.select_one(selector)
                if brand_elem:
                    brand = brand_elem.get_text(strip=True)
                    break
        
        # Extract category information
        category = ""
        subcategory = ""
        if breadcrumbs:
            breadcrumb_links = breadcrumbs[0].find_all('a') if breadcrumbs else []
            if len(breadcrumb_links) > 2:
                category = breadcrumb_links[2].get_text(strip=True)
            if len(breadcrumb_links) > 3:
                subcategory = breadcrumb_links[3].get_text(strip=True)
        
        # Extract specifications
        specifications = self.extract_specifications(soup)
        
        # Extract images
        image_urls = []
        img_selectors = [
            '.product-images img',
            '.product-gallery img',
            '.product-image img',
            '.gallery img',
            'img[src*="product"]'
        ]
        
        for selector in img_selectors:
            images = soup.select(selector)
            for img in images:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_img_url = urljoin(BASE_URL, src)
                    if full_img_url not in image_urls:
                        image_urls.append(full_img_url)
        
        return {
            'title': title,
            'description': description,
            'price': price,
            'sku': sku,
            'brand': brand,
            'category': category,
            'subcategory': subcategory,
            'specifications': specifications,
            'source_url': product_url,
            'image_urls': image_urls
        }
    
    def download_image(self, image_url, sku):
        """Download image and return local path"""
        try:
            response = self.get_page(image_url)
            if not response:
                return None
            
            # Get file extension
            parsed_url = urlparse(image_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            # Create filename
            filename = f"{slugify(sku)}_{hash(image_url) % 10000}{ext}"
            
            # Save image
            content = ContentFile(response.content)
            return filename, content
            
        except Exception as e:
            logger.error(f"Failed to download image {image_url}: {e}")
            return None
    
    def save_product(self, product_data):
        """Save product data to database"""
        try:
            # Check if product already exists
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults={
                    'title': product_data['title'],
                    'description': product_data['description'],
                    'price': product_data['price'],
                    'brand': product_data['brand'],
                    'category': product_data['category'],
                    'subcategory': product_data['subcategory'],
                    'specifications': product_data['specifications'],
                    'source_url': product_data['source_url'],
                }
            )
            
            if not created:
                # Update existing product
                for field, value in product_data.items():
                    if field != 'image_urls' and hasattr(product, field):
                        setattr(product, field, value)
                product.save()
                logger.info(f"Updated existing product: {product.title}")
            else:
                logger.info(f"Created new product: {product.title}")
            
            # Handle images
            for i, image_url in enumerate(product_data['image_urls'][:5]):  # Limit to 5 images
                # Check if image already exists
                if not ProductImage.objects.filter(product=product, image_url=image_url).exists():
                    image_data = self.download_image(image_url, product.sku)
                    if image_data:
                        filename, content = image_data
                        product_image = ProductImage(
                            product=product,
                            image_url=image_url,
                            is_primary=(i == 0)
                        )
                        product_image.local_path.save(filename, content, save=True)
                        logger.info(f"Downloaded image: {filename}")
            
            return product
            
        except Exception as e:
            logger.error(f"Failed to save product {product_data.get('sku', 'Unknown')}: {e}")
            return None
    
    def scrape_all_products(self, limit=None):
        """Main function to scrape all products"""
        logger.info("Starting full product scrape...")
        
        # Get all category URLs
        categories = self.get_all_category_urls()
        
        total_products = 0
        for category_url in categories:
            if limit and total_products >= limit:
                break
                
            logger.info(f"Processing category: {category_url}")
            
            # Get product links from this category
            product_links = self.get_product_links_from_category(category_url)
            
            for product_url in product_links:
                if limit and total_products >= limit:
                    break
                
                # Scrape individual product
                product_data = self.scrape_product(product_url)
                if product_data:
                    product = self.save_product(product_data)
                    if product:
                        total_products += 1
                        logger.info(f"Processed {total_products} products")
                
                # Be respectful - add delay
                time.sleep(1)
        
        logger.info(f"Scraping completed. Total products processed: {total_products}")
        return total_products


# Convenience functions for management commands
def scrape_all_products(limit=None):
    """Scrape all products from bathingbrands.com"""
    scraper = BathingBrandsScraper()
    return scraper.scrape_all_products(limit=limit)

def scrape_single_product(url):
    """Scrape a single product by URL"""
    scraper = BathingBrandsScraper()
    product_data = scraper.scrape_product(url)
    if product_data:
        return scraper.save_product(product_data)
    return None 