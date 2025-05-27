#!/usr/bin/env python
"""
Enhanced Bathing Brands Scraper - Captures ALL product information
Designed to extract comprehensive product data from bathingbrands.com
"""

import os
import sys
import requests
import time
import json
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, NavigableString, Tag
from decimal import Decimal, InvalidOperation
import logging
import hashlib

# Only setup Django if running as script, not when imported
if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
    django.setup()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class DataValidator:
    """Enhanced data validation for scraped product information"""
    
    @staticmethod
    def validate_title(title):
        """Validate product title"""
        if not title or len(title.strip()) < 3:
            return False
        if title.lower().startswith(('http', 'www', 'error')):
            return False
        return True
    
    @staticmethod
    def validate_brand(brand):
        """Validate brand name"""
        if not brand or len(brand.strip()) < 2:
            return False
        invalid_brands = ['http', 'https', 'www', 'error', 'n/a', 'none', 'unknown']
        return brand.lower().strip() not in invalid_brands
    
    @staticmethod
    def validate_price(price):
        """Validate price value"""
        if price is None: # Allow None for price
            return True
        try:
            price_val = float(str(price).replace('$', '').replace(',', ''))
            return 0 <= price_val < 100000  # Allow 0, reasonable price range
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_sku(sku):
        """Validate SKU format"""
        if not sku or len(sku.strip()) < 1: # Allow shorter SKUs
            return False
        return not sku.lower().startswith(('http', 'error', 'n/a'))
    
    @staticmethod
    def validate_image_url(url):
        """Validate image URL"""
        if not url:
            return False
        return url.startswith(('http://', 'https://')) and any(ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])


class EnhancedBathingBrandsScraper:
    """Enhanced scraper following exact Brand → Category → Collection → Product hierarchy"""
    
    def __init__(self):
        self.base_url = "https://bathingbrands.com"
        self.session = requests.Session()
        self.BeautifulSoup = BeautifulSoup # Assign to self for access from management command
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self.validator = DataValidator()
        self.scraped_urls = set()
        self.known_brands = [
            'Amerec', 'Aromamist', 'Auroom', 'Cozy Heat', 'Delta', 'EmotionWood',
            'Finlandia', 'Finnmark', 'Haljas Houses', 'Harvia', 'HUUM', 'Hukka',
            'Kohler', 'Kolo', 'Mr.Steam', 'Narvi', 'PROSAUNAS', 'Rento',
            'SaunaLife', 'Saunum', 'Steamist', 'ThermaSol'
        ]
        self.hierarchy_map = {}  # Track brand → category → collection structure
        
    def discover_brands(self):
        """Step 1: Discover all brands from the main products page"""
        logger.info("🏢 Step 1: Discovering brands from bathingbrands.com/products...")
        
        try:
            response = self.session.get(f"{self.base_url}/products/")
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            brands = {}
            
            # Based on the website structure, brands are in the main navigation
            # Look for the specific brand names we know exist
            known_brands = [
                'Amerec', 'Aromamist', 'Auroom', 'Cozy Heat', 'Delta', 'EmotionWood',
                'Finlandia', 'Finnmark', 'Haljas Houses', 'Harvia', 'HUUM', 'Hukka',
                'Kohler', 'Kolo', 'Mr.Steam', 'Narvi', 'PROSAUNAS', 'Rento',
                'SaunaLife', 'Saunum', 'Steamist', 'ThermaSol'
            ]
            
            # Find all navigation links
            nav_items = soup.find_all('a', href=True)
            
            for link in nav_items:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Check if this link text matches a known brand
                for brand_name in known_brands:
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
                for brand_name in known_brands:
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
    
    def discover_brand_categories(self, brand_data):
        """Step 2: Discover categories for a specific brand"""
        logger.info(f"📂 Step 2: Discovering categories for {brand_data['name']}...")
        
        try:
            response = self.session.get(brand_data['url'])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            categories = {}
            
            # Look for category links within the brand page
            nav_items = soup.find_all('a', href=True)
            
            for link in nav_items:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Category URLs follow pattern: /products/brand/category/
                if (f"/products/{brand_data['slug']}/" in href and 
                    href.count('/') == 4 and text):
                    
                    category_slug = href.split('/')[3]
                    if category_slug and len(category_slug) > 1:
                        category_url = urljoin(self.base_url, href)
                        categories[text] = {
                            'name': text,
                            'slug': category_slug,
                            'url': category_url,
                            'collections': {},
                            'scraped': False
                        }
            
            logger.info(f"📂 Found {len(categories)} categories for {brand_data['name']}: {list(categories.keys())}")
            return categories
            
        except Exception as e:
            logger.error(f"❌ Error discovering categories for {brand_data['name']}: {e}")
            return {}
    
    def discover_category_collections(self, brand_data, category_data):
        """Step 3: Discover collections within a category"""
        logger.info(f"📦 Step 3: Discovering collections for {brand_data['name']} → {category_data['name']}...")
        
        try:
            response = self.session.get(category_data['url'])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            collections = {}
            
            # Look for collection/subcategory links
            nav_items = soup.find_all('a', href=True)
            
            for link in nav_items:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Collection URLs follow pattern: /products/brand/category/collection/
                if (f"/products/{brand_data['slug']}/{category_data['slug']}/" in href and 
                    href.count('/') == 5 and text):
                    
                    collection_slug = href.split('/')[4]
                    if collection_slug and len(collection_slug) > 1:
                        collection_url = urljoin(self.base_url, href)
                        collections[text] = {
                            'name': text,
                            'slug': collection_slug,
                            'url': collection_url,
                            'products': [],
                            'scraped': False
                        }
            
            # If no collections found, treat the category itself as a collection
            if not collections:
                collections[category_data['name']] = {
                    'name': category_data['name'],
                    'slug': category_data['slug'],
                    'url': category_data['url'],
                    'products': [],
                    'scraped': False
                }
            
            logger.info(f"📦 Found {len(collections)} collections for {brand_data['name']} → {category_data['name']}: {list(collections.keys())}")
            return collections
            
        except Exception as e:
            logger.error(f"❌ Error discovering collections for {brand_data['name']} → {category_data['name']}: {e}")
            return {}
    
    def discover_collection_products(self, brand_data, category_data, collection_data):
        """Step 4: Discover all products in a collection"""
        logger.info(f"🛍️ Step 4: Discovering products in {brand_data['name']} → {category_data['name']} → {collection_data['name']}...")
        
        try:
            response = self.session.get(collection_data['url'])
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product_urls = []
            brand_slug = brand_data['slug'].lower()
            
            # Look for product links - these typically have numeric IDs
            product_links = soup.find_all('a', href=True)
            
            for link in product_links:
                href = link.get('href', '')
                
                # Product URLs typically contain numeric IDs: /12345/brand/product-name/
                if re.match(r'/\d+/', href):
                    # CRITICAL FIX: Ensure the URL contains the correct brand
                    if f'/{brand_slug}/' in href.lower():
                        product_url = urljoin(self.base_url, href)
                        if product_url not in self.scraped_urls:
                            product_urls.append(product_url)
                            logger.info(f"      ✓ Found {brand_data['name']} product: {href}")
                    else:
                        logger.warning(f"      ❌ Skipping non-{brand_data['name']} product: {href}")
                
                # Also look for direct product links with brand validation
                elif '/products/' in href and href.count('/') >= 5:
                    if f'/{brand_slug}/' in href.lower():
                        product_url = urljoin(self.base_url, href)
                        if product_url not in self.scraped_urls:
                            product_urls.append(product_url)
                            logger.info(f"      ✓ Found {brand_data['name']} product: {href}")
            
            # Remove duplicates while preserving order
            unique_products = []
            seen = set()
            for url in product_urls:
                if url not in seen:
                    seen.add(url)
                    unique_products.append(url)
            
            logger.info(f"🛍️ Found {len(unique_products)} {brand_data['name']} products in {brand_data['name']} → {category_data['name']} → {collection_data['name']}")
            return unique_products
            
        except Exception as e:
            logger.error(f"❌ Error discovering products in collection: {e}")
            return []
    
    def extract_all_images(self, soup, product_url):
        """Extract ALL product images from the page"""
        images = []
        
        try:
            # Method 1: Look for image gallery/carousel
            gallery_images = soup.find_all('img', {'class': re.compile(r'product|gallery|carousel|zoom', re.I)})
            
            # Method 2: Look for data attributes commonly used for product images
            data_images = soup.find_all('img', attrs={'data-src': True})
            data_images.extend(soup.find_all('img', attrs={'data-zoom': True}))
            data_images.extend(soup.find_all('img', attrs={'data-large': True}))
            
            # Method 3: Look for images in specific containers
            image_containers = soup.find_all(['div', 'section'], {'class': re.compile(r'image|photo|gallery|product.*image', re.I)})
            container_images = []
            for container in image_containers:
                container_images.extend(container.find_all('img'))
            
            # Method 4: Look for images with product-related alt text
            alt_images = soup.find_all('img', {'alt': re.compile(r'product|heater|sauna|bathing', re.I)})
            
            # Combine all found images
            all_images = gallery_images + data_images + container_images + alt_images
            
            for img in all_images:
                # Try different src attributes
                img_url = (img.get('data-src') or 
                          img.get('data-zoom') or 
                          img.get('data-large') or 
                          img.get('src'))
                
                if img_url:
                    # Convert relative URLs to absolute
                    if img_url.startswith('//'):
                        img_url = 'https:' + img_url
                    elif img_url.startswith('/'):
                        img_url = urljoin(self.base_url, img_url)
                    
                    # Validate image URL
                    if self.validator.validate_image_url(img_url):
                        alt_text = img.get('alt', '').strip()
                        
                        # Determine image type
                        image_type = 'main'
                        if 'gallery' in img.get('class', []):
                            image_type = 'gallery'
                        elif 'technical' in alt_text.lower():
                            image_type = 'technical'
                        elif 'lifestyle' in alt_text.lower():
                            image_type = 'lifestyle'
                        
                        images.append({
                            'url': img_url,
                            'alt_text': alt_text,
                            'type': image_type
                        })
            
            # Remove duplicates while preserving order
            seen_urls = set()
            unique_images = []
            for img in images:
                if img['url'] not in seen_urls:
                    seen_urls.add(img['url'])
                    unique_images.append(img)
            
            logger.info(f"🖼️ Found {len(unique_images)} unique images")
            return unique_images
            
        except Exception as e:
            logger.error(f"❌ Error extracting images: {e}")
            return []
    
    def extract_specifications(self, soup):
        """Extract detailed product specifications"""
        specifications = {}
        
        try:
            # Method 1: Look for specification tables
            spec_tables = soup.find_all('table')
            for table in spec_tables:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        key = cells[0].get_text(strip=True)
                        value = cells[1].get_text(strip=True)
                        if key and value:
                            specifications[key] = value
            
            # Method 2: Look for specification lists
            spec_lists = soup.find_all(['ul', 'ol'], {'class': re.compile(r'spec|feature|detail', re.I)})
            for spec_list in spec_lists:
                items = spec_list.find_all('li')
                for item in items:
                    text = item.get_text(strip=True)
                    if ':' in text:
                        key, value = text.split(':', 1)
                        specifications[key.strip()] = value.strip()
            
            # Method 3: Look for definition lists
            dl_elements = soup.find_all('dl')
            for dl in dl_elements:
                terms = dl.find_all('dt')
                definitions = dl.find_all('dd')
                for term, definition in zip(terms, definitions):
                    key = term.get_text(strip=True)
                    value = definition.get_text(strip=True)
                    if key and value:
                        specifications[key] = value
            
            # Method 4: Look for specific product data
            # Extract dimensions, power, capacity, etc.
            text_content = soup.get_text()
            
            # Common specification patterns
            patterns = {
                'Power': r'(\d+(?:\.\d+)?)\s*kW',
                'Voltage': r'(\d+)V',
                'Amperage': r'(\d+(?:\.\d+)?)\s*Amps?',
                'Weight': r'(\d+(?:\.\d+)?)\s*lbs?',
                'Capacity': r'(\d+(?:\.\d+)?)\s*(?:cubic feet|CF|cu\.?\s*ft)',
                'Width': r'Width:?\s*(\d+(?:\.\d+)?)"?',
                'Height': r'Height:?\s*(\d+(?:\.\d+)?)"?',
                'Depth': r'Depth:?\s*(\d+(?:\.\d+)?)"?',
            }
            
            for spec_name, pattern in patterns.items():
                match = re.search(pattern, text_content, re.IGNORECASE)
                if match:
                    specifications[spec_name] = match.group(1)
            
            logger.info(f"📋 Extracted {len(specifications)} specifications")
            return specifications
            
        except Exception as e:
            logger.error(f"❌ Error extracting specifications: {e}")
            return {}
    
    def extract_documents(self, soup):
        """Extract technical documents and manuals"""
        documents = []
        
        try:
            # Look for PDF links
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$', re.I))
            
            for link in pdf_links:
                href = link.get('href')
                if href:
                    # Convert relative URLs to absolute
                    if href.startswith('/'):
                        href = urljoin(self.base_url, href)
                    
                    title = link.get_text(strip=True) or link.get('title', '')
                    
                    # Determine document type
                    doc_type = 'manual'
                    if 'installation' in title.lower():
                        doc_type = 'installation'
                    elif 'warranty' in title.lower():
                        doc_type = 'warranty'
                    elif 'specification' in title.lower():
                        doc_type = 'specification'
                    elif 'certificate' in title.lower():
                        doc_type = 'certificate'
                    
                    documents.append({
                        'url': href,
                        'title': title,
                        'type': doc_type
                    })
            
            logger.info(f"📄 Found {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"❌ Error extracting documents: {e}")
            return []
    
    def _extract_tab_content(self, soup, tab_name):
        """Extract content from specific tabs like Description, Features, Includes, etc."""
        content = ""
        
        # Method 1: Look for tab content by ID or class
        tab_content = soup.find('div', {'id': re.compile(f'{tab_name.lower()}', re.I)})
        if not tab_content:
            tab_content = soup.find('div', {'class': re.compile(f'{tab_name.lower()}', re.I)})
        
        # Method 2: Look for tab panels
        if not tab_content:
            # Look for tab navigation first
            tab_link = soup.find('a', text=re.compile(f'^{tab_name}$', re.I))
            if tab_link:
                # Get the href or data attribute that points to content
                href = tab_link.get('href', '')
                if href.startswith('#'):
                    tab_content = soup.find('div', {'id': href[1:]})
        
        # Method 3: Look for content after tab headings
        if not tab_content:
            heading = soup.find(['h2', 'h3', 'h4', 'strong'], text=re.compile(f'^{tab_name}$', re.I))
            if heading:
                content_parts = []
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h2', 'h3', 'h4'] and sibling.get_text(strip=True).lower() != tab_name.lower():
                        break
                    if isinstance(sibling, Tag):
                        # Clean up scripts and styles
                        for s in sibling.find_all(['script', 'style']):
                            s.decompose()
                        
                        text = sibling.get_text(separator=' ', strip=True)
                        if text:
                            content_parts.append(text)
                
                content = "\n".join(content_parts).strip()
        
        # Method 4: Extract from tab content div
        if tab_content:
            # Remove scripts and styles
            for s in tab_content.find_all(['script', 'style']):
                s.decompose()
            
            # Handle different content types
            content_parts = []
            
            # Look for paragraphs
            paragraphs = tab_content.find_all('p')
            for p in paragraphs:
                text = p.get_text(separator=' ', strip=True)
                if text:
                    content_parts.append(text)
            
            # Look for lists
            lists = tab_content.find_all(['ul', 'ol'])
            for ul in lists:
                list_items = []
                for li in ul.find_all('li'):
                    item_text = li.get_text(separator=' ', strip=True)
                    if item_text:
                        list_items.append(f"• {item_text}")
                if list_items:
                    content_parts.append("\n".join(list_items))
            
            # Look for tables
            tables = tab_content.find_all('table')
            for table in tables:
                table_text = []
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                    if any(cells):  # Only add non-empty rows
                        table_text.append(" | ".join(cells))
                if table_text:
                    content_parts.append("\n".join(table_text))
            
            # If no structured content found, get all text
            if not content_parts:
                content = tab_content.get_text(separator=' ', strip=True)
            else:
                content = "\n\n".join(content_parts)
        
        # Clean up and limit length
        if content:
            content = re.sub(r'\s+', ' ', content).strip()
            return content[:3000] if len(content) > 3000 else content
        
        return ""

    def _extract_content_by_heading(self, soup, heading_text):
        """Extracts content under a specific heading (h2, h3, h4)."""
        # First try the tab extraction method
        tab_content = self._extract_tab_content(soup, heading_text)
        if tab_content:
            return tab_content
        
        # Fallback to original method
        heading = soup.find(['h2', 'h3', 'h4', 'strong'], text=re.compile(r'\b' + re.escape(heading_text) + r'\b', re.I))
        if not heading:
            return ""

        content_parts = []
        for sibling in heading.find_next_siblings():
            if sibling.name in ['h2', 'h3', 'h4'] and sibling.get_text(strip=True).lower() != heading_text.lower():
                break
            if isinstance(sibling, Tag):
                for s in sibling.find_all(['script', 'style']):
                    s.decompose()
                
                if sibling.name == 'ul':
                    list_items = []
                    for li in sibling.find_all('li'):
                        item_text = li.get_text(separator=' ', strip=True)
                        if item_text:
                            list_items.append(f"• {item_text}")
                    if list_items:
                         content_parts.append("\n".join(list_items))
                elif sibling.name == 'table':
                    table_str = ""
                    for row in sibling.find_all('tr'):
                        cells = [cell.get_text(strip=True) for cell in row.find_all(['td', 'th'])]
                        table_str += " | ".join(cells) + "\n"
                    if table_str:
                        content_parts.append(table_str)
                else:
                    text = sibling.get_text(separator=' ', strip=True)
                    if text:
                        content_parts.append(text)
        
        full_content = "\n".join(content_parts).strip()
        return full_content[:3000] if len(full_content) > 3000 else full_content

    def _extract_model_name(self, soup):
        """Extracts the product's model name."""
        # Try finding a 'Model' label and its value
        model_label = soup.find(['strong', 'dt', 'span', 'div'], text=re.compile(r'^Model[:\s]*$', re.I))
        if model_label:
            # Next sibling or parent's next significant text
            next_elem = model_label.find_next_sibling()
            if next_elem and next_elem.get_text(strip=True):
                model_name = next_elem.get_text(strip=True)
                if self.validator.validate_sku(model_name): # SKU validation is somewhat similar to model name
                    return model_name
            # Check parent's text content if model_label is part of a larger element
            parent_text = model_label.parent.get_text(separator=' ', strip=True)
            match = re.search(r'Model[:\s]*([A-Za-z0-9\-_\s]+)', parent_text, re.I)
            if match and match.group(1).strip():
                 model_val = match.group(1).strip()
                 # Avoid capturing the word 'Model' itself or very long descriptions
                 if model_val.lower() != 'model' and len(model_val) < 100 :
                    return model_val

        # Try common product detail containers
        product_details_container = soup.find('div', class_=re.compile(r'product-details|product-info|sku-model', re.I))
        if product_details_container:
            model_text = product_details_container.find(text=re.compile(r'Model:\s*([\w-]+)', re.I))
            if model_text:
                match = re.search(r'Model:\s*([\w-]+)', model_text, re.I)
                if match:
                    return match.group(1)
        return ""
        
    def extract_related_products(self, soup, main_product_instance):
        """Extracts related products and saves them."""
        # Import models here to avoid import issues
        from products.models import Product, RelatedProduct
        
        logger.info(f"🤝 Extracting related products for: {main_product_instance.title}")
        relationship_types_map = {
            'Required for Operation': 'required_operation',
            'Sauna Heater Controls': 'heater_control',
            'Related Items': 'related_item',
            'Accessories': 'accessory',
            'Sauna Accessories & Packages': 'accessory',
            'Sauna Room Safety': 'accessory',
            # Add more mappings if other section titles appear
        }

        extracted_relations = []
        processed_products = set()  # Track processed products to avoid duplicates

        # First, let's log all potential section headings we can find
        all_headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'div'], text=True)
        logger.info(f"  Found {len(all_headings)} potential headings on page")
        
        # Log headings that might be related to our sections
        for heading in all_headings:
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text.lower() for keyword in ['required', 'control', 'related', 'accessor', 'safety', 'heater']):
                logger.info(f"    Potential section heading: '{heading_text}'")

        for section_title_text, type_key in relationship_types_map.items():
            # Find section heading with multiple approaches
            heading = None
            
            # Approach 1: Exact match
            for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'div', 'span']:
                heading = soup.find(tag, text=re.compile(r'\b' + re.escape(section_title_text) + r'\b', re.I))
                if heading:
                    logger.info(f"  Found exact match for '{section_title_text}' in {tag} tag")
                    break
            
            # Approach 2: Partial match if exact match fails
            if not heading:
                key_words = section_title_text.split()
                for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'strong', 'div', 'span']:
                    # Look for headings containing most of the key words
                    potential_headings = soup.find_all(tag, text=True)
                    for pot_heading in potential_headings:
                        heading_text = pot_heading.get_text(strip=True).lower()
                        matches = sum(1 for word in key_words if word.lower() in heading_text)
                        if matches >= len(key_words) - 1:  # Allow missing one word
                            heading = pot_heading
                            logger.info(f"  Found partial match for '{section_title_text}': '{pot_heading.get_text(strip=True)}'")
                            break
                    if heading:
                        break
            
            # Approach 3: Look for text containing the section name anywhere
            if not heading:
                text_elements = soup.find_all(text=re.compile(re.escape(section_title_text), re.I))
                for text_elem in text_elements:
                    if hasattr(text_elem, 'parent') and text_elem.parent:
                        heading = text_elem.parent
                        logger.info(f"  Found text match for '{section_title_text}' in {heading.name if hasattr(heading, 'name') else 'text'}")
                        break
                        
            if heading:
                logger.info(f"  ✓ Processing section: {section_title_text}")
                
                # Find products in this section
                products_found = []
                
                # Strategy 1: Look in the same container as the heading
                container = heading.parent if hasattr(heading, 'parent') else heading
                if container:
                    # Look for elements that contain both price and product info
                    potential_products = container.find_all(['div', 'article', 'li', 'tr', 'form', 'section'], recursive=True)
                    for elem in potential_products:
                        # Must have price and some product identifier
                        has_price = bool(elem.find(text=re.compile(r'\$\d+', re.I)) or elem.find(class_=re.compile(r'price', re.I)))
                        has_sku = bool(elem.find(text=re.compile(r'SKU[:\s]*[A-Z0-9\-_]+', re.I)))
                        has_model = bool(elem.find(text=re.compile(r'Model[:\s]*[A-Za-z0-9\-_\s]+', re.I)))
                        has_title = bool(elem.find(['h3', 'h4', 'h5', 'strong', 'a'], text=lambda t: t and len(t.strip()) > 3))
                        
                        # Also check for text patterns that indicate a product
                        elem_text = elem.get_text()
                        has_product_pattern = bool(re.search(r'(UKU|HUUM|KOLO|Model|SKU)', elem_text, re.I))
                        
                        if has_price and (has_sku or has_model or has_product_pattern) and (has_title or len(elem_text.strip()) > 50):
                            # Create a unique identifier for this product to avoid duplicates
                            sku_match = re.search(r'SKU[:\s]*([A-Z0-9\-_]+)', elem_text, re.I)
                            model_match = re.search(r'Model[:\s]*([A-Za-z0-9\-_\s]+)', elem_text, re.I)
                            
                            product_id = None
                            if sku_match:
                                product_id = f"sku_{sku_match.group(1)}"
                            elif model_match:
                                product_id = f"model_{model_match.group(1).strip()}"
                            else:
                                # Use a hash of the text as fallback
                                product_id = f"text_{hashlib.md5(elem_text.encode()).hexdigest()[:8]}"
                            
                            if product_id and product_id not in processed_products:
                                products_found.append(elem)
                                processed_products.add(product_id)
                                logger.info(f"      Found potential product: {product_id}")
                
                # Strategy 2: Look in following siblings
                current_element = heading.find_next_sibling() if hasattr(heading, 'find_next_sibling') else None
                sibling_count = 0
                while current_element and sibling_count < 20:  # Increased limit
                    sibling_count += 1
                    if hasattr(current_element, 'name') and current_element.name:
                        # Stop if we hit another major section
                        if current_element.name in ['h1', 'h2', 'h3'] and current_element.get_text(strip=True) != section_title_text:
                            # Check if this is another known section
                            is_another_section = any(
                                re.search(r'\b' + re.escape(title) + r'\b', current_element.get_text(strip=True), re.I)
                                for title in relationship_types_map.keys()
                            )
                            if is_another_section:
                                break
                        
                        # Check if current element contains products
                        has_price = bool(current_element.find(text=re.compile(r'\$\d+', re.I)) or current_element.find(class_=re.compile(r'price', re.I)))
                        has_sku = bool(current_element.find(text=re.compile(r'SKU[:\s]*[A-Z0-9\-_]+', re.I)))
                        has_model = bool(current_element.find(text=re.compile(r'Model[:\s]*[A-Za-z0-9\-_\s]+', re.I)))
                        
                        elem_text = current_element.get_text()
                        has_product_pattern = bool(re.search(r'(UKU|HUUM|KOLO|Model|SKU)', elem_text, re.I))
                        
                        if has_price and (has_sku or has_model or has_product_pattern):
                            sku_match = re.search(r'SKU[:\s]*([A-Z0-9\-_]+)', elem_text, re.I)
                            model_match = re.search(r'Model[:\s]*([A-Za-z0-9\-_\s]+)', elem_text, re.I)
                            
                            product_id = None
                            if sku_match:
                                product_id = f"sku_{sku_match.group(1)}"
                            elif model_match:
                                product_id = f"model_{model_match.group(1).strip()}"
                            else:
                                import hashlib
                                product_id = f"text_{hashlib.md5(elem_text.encode()).hexdigest()[:8]}"
                            
                            if product_id and product_id not in processed_products:
                                products_found.append(current_element)
                                processed_products.add(product_id)
                                logger.info(f"      Found potential product in sibling: {product_id}")
                    
                    current_element = current_element.find_next_sibling() if hasattr(current_element, 'find_next_sibling') else None
                
                # Strategy 3: Look for specific patterns in the entire section
                if len(products_found) == 0:
                    logger.info(f"    No products found with standard methods, trying text-based extraction...")
                    
                    # Get all text from the section
                    section_container = heading.parent if hasattr(heading, 'parent') else soup
                    section_text = section_container.get_text()
                    
                    # Look for product patterns in the text
                    product_patterns = [
                        r'(HUUM UKU[^$]*?\$[\d,]+\.?\d*)',
                        r'(KOLO[^$]*?\$[\d,]+\.?\d*)',
                        r'(Model[^$]*?\$[\d,]+\.?\d*)',
                        r'(SKU[^$]*?\$[\d,]+\.?\d*)',
                    ]
                    
                    for pattern in product_patterns:
                        matches = re.finditer(pattern, section_text, re.I | re.DOTALL)
                        for match in matches:
                            product_text = match.group(1)
                            # Create a pseudo-element for text-based products
                            pseudo_elem = type('TextProduct', (), {
                                'get_text': lambda: product_text,
                                'find': lambda *args, **kwargs: None,
                                'find_all': lambda *args, **kwargs: [],
                            })()
                            
                            # Check if we've already processed this
                            if product_id not in processed_products:
                                products_found.append(pseudo_elem)
                                processed_products.add(product_id)
                                logger.info(f"      Found text-based product: {product_text[:50]}...")
                
                logger.info(f"    Found {len(products_found)} unique product blocks in {section_title_text}")
                
                # Extract data from each product block
                for block in products_found:
                    try:
                        # Get the text content of the block
                        block_text = block.get_text() if hasattr(block, 'get_text') else str(block)
                        
                        # Extract title - look for the most prominent text element
                        title_elem = None
                        related_title = None
                        
                        if hasattr(block, 'find'):
                            for tag in ['h3', 'h4', 'h5', 'strong']:
                                title_elem = block.find(tag)
                                if title_elem and title_elem.get_text(strip=True):
                                    related_title = title_elem.get_text(strip=True)
                                    break
                            
                            if not title_elem:
                                # Fallback: look for first link with substantial text
                                title_elem = block.find('a', text=lambda t: t and len(t.strip()) > 5)
                                if title_elem:
                                    related_title = title_elem.get_text(strip=True)
                        
                        if not related_title:
                            # Extract title from text patterns
                            title_patterns = [
                                r'(HUUM UKU [^$\n]*?)(?:\n|Model|SKU|Digital)',
                                r'(HUUM [^$\n]*?)(?:\n|Model|SKU)',
                                r'(KOLO [^$\n]*?)(?:\n|Model|SKU)',
                                r'^([^$\n]{10,50})(?:\n|Model|SKU)',
                            ]
                            
                            for pattern in title_patterns:
                                match = re.search(pattern, block_text, re.I | re.MULTILINE)
                                if match:
                                    related_title = match.group(1).strip()
                                    break
                        
                        if not related_title:
                            # Last resort: use first meaningful line
                            lines = block_text.split('\n')
                            for line in lines:
                                line = line.strip()
                                if len(line) > 5 and not line.startswith('$') and not line.lower().startswith('sku'):
                                    related_title = line
                                    break
                        
                        if not related_title:
                            continue
                            
                        # Extract subtitle/short description (often right after title)
                        subtitle = ""
                        if hasattr(title_elem, 'find_next_sibling'):
                            next_elem = title_elem.find_next_sibling()
                            if next_elem and hasattr(next_elem, 'name') and next_elem.name in ['p', 'div', 'span']:
                                subtitle = next_elem.get_text(strip=True)
                        
                        # Extract full description (usually in a paragraph)
                        description = ""
                        if hasattr(block, 'find'):
                            desc_elem = block.find('p', text=lambda t: t and len(t.strip()) > 20)
                            if desc_elem:
                                description = desc_elem.get_text(strip=True)
                        
                        # Extract Model
                        related_model = None
                        model_patterns = [
                            r'Model\s*[:\s]*([A-Za-z0-9\-_\s]+?)(?:\n|$|SKU)',
                            r'Model\s+([A-Za-z0-9\-_\s]+?)(?:\n|$|SKU)',
                        ]
                        for pattern in model_patterns:
                            match = re.search(pattern, block_text, re.I | re.MULTILINE)
                            if match:
                                model_val = match.group(1).strip()
                                if model_val and model_val.lower() != 'model' and len(model_val) < 50:
                                    related_model = model_val
                                    break
                        
                        # Extract SKU
                        related_sku = None
                        sku_patterns = [
                            r'SKU\s*[:\s]*([A-Z0-9\-_]+)',
                            r'SKU([A-Z0-9\-_]+)',
                        ]
                        for pattern in sku_patterns:
                            match = re.search(pattern, block_text, re.I)
                            if match:
                                related_sku = match.group(1).strip()
                                break
                        
                        # Extract price
                        related_price = None
                        price_patterns = [
                            r'Your Price\s*\$?([\d,]+\.?\d*)',
                            r'Price\s*[:\s]*\$?([\d,]+\.?\d*)',
                            r'\$\s*([\d,]+\.?\d*)',
                        ]
                        for pattern in price_patterns:
                            match = re.search(pattern, block_text, re.I)
                            if match:
                                related_price = self._parse_price(match.group(1))
                                if related_price:
                                    break
                        
                        # Extract URL
                        related_url = None
                        if hasattr(title_elem, 'name') and title_elem.name == 'a':
                            related_url = urljoin(self.base_url, title_elem.get('href', ''))
                        elif hasattr(block, 'find'):
                            # Look for a link within the block
                            link = block.find('a', href=True)
                            if link:
                                related_url = urljoin(self.base_url, link.get('href'))
                        
                        # Log what we found
                        logger.info(f"    Extracted related product:")
                        logger.info(f"      Title: {related_title}")
                        logger.info(f"      Model: {related_model}")
                        logger.info(f"      SKU: {related_sku}")
                        logger.info(f"      Price: ${related_price if related_price else 'N/A'}")
                        logger.info(f"      Section: {section_title_text}")
                        
                        if related_title and (related_sku or related_model):
                            # Try to find this product in DB
                            related_product_instance = None
                            
                            # First try by SKU
                            if related_sku:
                                try:
                                    related_product_instance = Product.objects.get(sku=related_sku)
                                    logger.info(f"      ✓ Found in DB by SKU: {related_sku}")
                                except Product.DoesNotExist:
                                    pass
                            
                            # Then try by model
                            if not related_product_instance and related_model:
                                try:
                                    # Try exact model match first
                                    related_product_instance = Product.objects.get(model=related_model)
                                    logger.info(f"      ✓ Found in DB by exact model: {related_model}")
                                except Product.DoesNotExist:
                                    # Try partial title match with model
                                    try:
                                        related_product_instance = Product.objects.filter(
                                            model=related_model,
                                            title__icontains=related_title.split()[0]  # First word of title
                                        ).first()
                                        if related_product_instance:
                                            logger.info(f"      ✓ Found in DB by model + title match")
                                    except:
                                        pass
                            
                            if related_product_instance:
                                # Create the relationship
                                relation, created = RelatedProduct.objects.get_or_create(
                                    main_product=main_product_instance,
                                    related_product=related_product_instance,
                                    relationship_type=type_key,
                                    defaults={
                                        'description': subtitle or description or f"Found as '{section_title_text}'",
                                        'is_mandatory': type_key == 'required_operation'
                                    }
                                )
                                if created:
                                    logger.info(f"      🔗 Created relation: {main_product_instance.title} -> {related_product_instance.title}")
                                else:
                                    logger.info(f"      🔗 Relation already exists")
                                extracted_relations.append(relation)
                            else:
                                # Product not in DB yet - log the details for potential scraping
                                logger.warning(f"      ⚠️ Related product not found in DB:")
                                logger.warning(f"         Title: {related_title}")
                                logger.warning(f"         SKU: {related_sku}")
                                logger.warning(f"         Model: {related_model}")
                                logger.warning(f"         Price: ${related_price}")
                                logger.warning(f"         URL: {related_url}")
                                logger.warning(f"         Consider scraping this product separately.")
                        
                    except Exception as e:
                        logger.error(f"    ❌ Error extracting related product from block: {e}")
                        continue
            else:
                logger.warning(f"  ❌ Section '{section_title_text}' not found on page")
                        
        logger.info(f"  🤝 Created {len(extracted_relations)} related product relationships")
        return extracted_relations

    def extract_product_data(self, product_url):
        """Extract comprehensive product data from a single product page"""
        try:
            logger.info(f"🔍 Extracting data from: {product_url}")
            
            response = self.session.get(product_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            title = self._extract_title(soup)
            brand = self._extract_brand(soup, product_url)
            
            # CRITICAL FIX: Validate brand matches URL
            url_brand = None
            for known_brand in self.known_brands:
                if f'/{known_brand.lower().replace(" ", "-").replace(".", "")}/' in product_url.lower():
                    url_brand = known_brand
                    break
            
            if url_brand:
                brand = url_brand
                logger.info(f"    ✓ Confirmed brand from URL: {brand}")
            else:
                logger.warning(f"    ⚠️ Could not confirm brand from URL: {product_url}")
                # Try to extract from title as fallback
                for known_brand in self.known_brands:
                    if known_brand.lower() in title.lower():
                        brand = known_brand
                        logger.info(f"    ✓ Found brand in title: {brand}")
                        break


            price = self._extract_price(soup)
            sku = self._extract_sku(soup, product_url)
            model_name = self._extract_model_name(soup)
            
            # Extract content from tabs and sections
            short_description = self._extract_short_description(soup)
            
            # Extract from specific tabs
            full_description = (
                self._extract_tab_content(soup, "Description") or 
                self._extract_content_by_heading(soup, "Description") or 
                self._extract_full_description(soup)
            )
            
            features = (
                self._extract_tab_content(soup, "Features") or
                self._extract_content_by_heading(soup, "Features")
            )
            
            includes = (
                self._extract_tab_content(soup, "Includes") or
                self._extract_content_by_heading(soup, "Includes")
            )
            
            technical_info = (
                self._extract_tab_content(soup, "Technical") or
                self._extract_tab_content(soup, "Specifications") or
                self._extract_content_by_heading(soup, "Technical") or
                self._extract_content_by_heading(soup, "Specifications")
            )
            
            # Additional content extraction
            shipping_info = (
                self._extract_tab_content(soup, "Shipping") or
                self._extract_content_by_heading(soup, "Shipping")
            )
            
            inspiration_content = (
                self._extract_tab_content(soup, "Inspiration") or
                self._extract_content_by_heading(soup, "Inspiration")
            )
            
            # If full_description is still empty, use short_description or a generic part of the page
            if not full_description and short_description:
                full_description = short_description
            elif not full_description and not short_description:
                # Fallback: Try to get main content area if no description found
                main_content = soup.find('div', id='main-content') or soup.find('main') or soup.find('div', class_=re.compile(r'product-(content|description|body)'))
                if main_content:
                    full_description = main_content.get_text(separator=' ', strip=True)[:2000]


            category = self._extract_category(soup)
            subcategory = self._extract_subcategory(soup)
            
            images = self.extract_all_images(soup, product_url)
            specifications_dict = self.extract_specifications(soup) # This returns a dict
            documents = self.extract_documents(soup)
            
            # Validate core data
            if not self.validator.validate_title(title):
                logger.warning(f"⚠️ Invalid title: '{title}' from {product_url}. Skipping.")
                return None
            if not self.validator.validate_brand(brand):
                logger.warning(f"⚠️ Invalid brand: '{brand}' for '{title}'. Skipping.")
                return None
            if not self.validator.validate_sku(sku):
                logger.warning(f"⚠️ Invalid SKU: '{sku}' for '{title}'. Skipping.")
                # If SKU is invalid, but we have a model, try to generate SKU from model
                if model_name and self.validator.validate_sku(model_name):
                    sku = model_name
                    logger.info(f"    Using model name as SKU: {sku}")
                else: # If model is also not valid as SKU, generate one
                    sku = f"GEN_{brand.upper()}_{int(time.time())%10000}"
                    logger.warning(f"    Generated fallback SKU: {sku}")


            if not self.validator.validate_price(price):
                logger.warning(f"⚠️ Invalid price: '{price}' for '{title}'. Setting to None.")
                price = None # Set invalid price to None

            product_data = {
                'title': title,
                'model_name': model_name,
                'short_description': short_description,
                'full_description': full_description,
                'price': price,
                'sku': sku,
                'brand': brand,
                'category': category,
                'subcategory': subcategory,
                'source_url': product_url,
                'images': images,
                'specifications_dict': specifications_dict,
                'documents': documents,
                'features': features,
                'includes': includes,
                'technical_info': technical_info,
                'shipping_info': shipping_info,
                'inspiration_content': inspiration_content,
                # Related products will be handled after product is saved
            }
            
            logger.info(f"✅ Successfully extracted data for: {title} (SKU: {sku}, Model: {model_name})")
            return product_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ HTTP Error extracting product data from {product_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Unexpected Error extracting product data from {product_url}: {e}", exc_info=True)
            return None

    def _extract_title(self, soup):
        """Extract product title with multiple fallback methods"""
        # Method 1: Page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Clean up title
            title = re.sub(r'\s*\|\s*.*$', '', title)  # Remove site name
            if self.validator.validate_title(title):
                return title
        
        # Method 2: H1 tag
        h1_tag = soup.find('h1')
        if h1_tag:
            title = h1_tag.get_text(strip=True)
            if self.validator.validate_title(title):
                return title
        
        # Method 3: Product name class
        product_name = soup.find(['h1', 'h2', 'div'], {'class': re.compile(r'product.*name|title', re.I)})
        if product_name:
            title = product_name.get_text(strip=True)
            if self.validator.validate_title(title):
                return title
        
        # Method 4: Meta property
        meta_title = soup.find('meta', {'property': 'og:title'})
        if meta_title:
            title = meta_title.get('content', '').strip()
            if self.validator.validate_title(title):
                return title
        
        return "Unknown Product"
    
    def _extract_brand(self, soup, product_url):
        """Extract brand name with multiple methods"""
        # Method 1: From URL structure
        url_parts = product_url.split('/')
        if len(url_parts) >= 5 and 'products' in url_parts:
            brand_index = url_parts.index('products') + 1
            if brand_index < len(url_parts):
                brand = url_parts[brand_index].replace('-', ' ').title()
                if self.validator.validate_brand(brand):
                    return brand
        
        # Method 2: From breadcrumbs
        breadcrumbs = soup.find_all(['a', 'span'], {'class': re.compile(r'breadcrumb', re.I)})
        for crumb in breadcrumbs:
            text = crumb.get_text(strip=True)
            if text and len(text) > 2 and text.lower() not in ['home', 'products']:
                if self.validator.validate_brand(text):
                    return text
        
        # Method 3: From product title
        title = self._extract_title(soup)
        if title:
            # Common brand names in bathing industry
            brands = ['HUUM', 'Harvia', 'Amerec', 'Mr.Steam', 'ThermaSol', 'Steamist', 'Kohler', 'Delta']
            for brand in brands:
                if brand.lower() in title.lower():
                    return brand
        
        # Method 4: From meta tags
        meta_brand = soup.find('meta', {'name': 'brand'})
        if meta_brand:
            brand = meta_brand.get('content', '').strip()
            if self.validator.validate_brand(brand):
                return brand
        
        return "Unknown Brand"
    
    def _extract_price(self, soup):
        """Extract price with multiple methods"""
        # Method 1: Price class selectors
        price_selectors = [
            '.price', '.product-price', '.your-price', '.sale-price',
            '[class*="price"]', '[id*="price"]'
        ]
        
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price = self._parse_price(price_text)
                if price:
                    return price
        
        # Method 2: Text pattern matching
        text_content = soup.get_text()
        price_patterns = [
            r'Your Price[:\s]*\$?([\d,]+\.?\d*)',
            r'Price[:\s]*\$?([\d,]+\.?\d*)',
            r'\$\s*([\d,]+\.?\d*)',
        ]
        
        for pattern in price_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                price = self._parse_price(match.group(1))
                if price:
                    return price
        
        return None
    
    def _parse_price(self, price_text):
        """Parse price from text"""
        try:
            # Remove currency symbols and commas
            price_clean = re.sub(r'[^\d.]', '', price_text)
            if price_clean:
                price = Decimal(price_clean)
                if self.validator.validate_price(price):
                    return price
        except (InvalidOperation, ValueError):
            pass
        return None
    
    def _extract_sku(self, soup, product_url):
        """Extract SKU with multiple methods. Prioritize explicit SKU/Model fields."""
        
        # Method 1: Look for "SKU" label and its value
        sku_label = soup.find(['strong', 'dt', 'span', 'div', 'p'], text=re.compile(r'^SKU[:\s]*$', re.I))
        if sku_label:
            next_elem = sku_label.find_next_sibling(text=True)
            if next_elem and next_elem.strip():
                sku_val = next_elem.strip()
                if self.validator.validate_sku(sku_val): 
                    logger.info(f"    Found SKU via label: {sku_val}")
                    return sku_val
            # Check parent's text if label is inside something
            parent_text = sku_label.parent.get_text(separator=' ', strip=True)
            match = re.search(r'SKU[:\s]*([A-Za-z0-9\-_]+)', parent_text, re.I)
            if match and self.validator.validate_sku(match.group(1).strip()):
                logger.info(f"    Found SKU via parent text: {match.group(1).strip()}")
                return match.group(1).strip()

        # Method 2: Look for "Model" label as a fallback for SKU
        model_label = soup.find(['strong', 'dt', 'span', 'div', 'p'], text=re.compile(r'^Model[:\s]*$', re.I))
        if model_label:
            next_elem = model_label.find_next_sibling(text=True)
            if next_elem and next_elem.strip():
                model_val = next_elem.strip()
                if self.validator.validate_sku(model_val) and model_val.lower() != 'model': 
                    logger.info(f"    Found SKU via model label: {model_val}")
                    return model_val
            parent_text = model_label.parent.get_text(separator=' ', strip=True)
            match = re.search(r'Model[:\s]*([A-Za-z0-9\-_\s]+)', parent_text, re.I)
            if match:
                model_as_sku = match.group(1).strip()
                if self.validator.validate_sku(model_as_sku) and model_as_sku.lower() != 'model' and len(model_as_sku) < 50:
                    logger.info(f"    Found SKU via model parent: {model_as_sku}")
                    return model_as_sku

        # Method 3: Common class/id attributes
        sku_elem = soup.find(['span', 'div'], {'class': re.compile(r'sku|product-sku|model-number|product-id', re.I), 'id': re.compile(r'sku|model', re.I)})
        if sku_elem:
            sku = sku_elem.get_text(strip=True)
            # Sometimes this contains "SKU: value", so extract value
            if ":" in sku: sku = sku.split(":")[-1].strip()
            if self.validator.validate_sku(sku):
                logger.info(f"    Found SKU via class/id: {sku}")
                return sku
        
        # Method 4: Enhanced text pattern matching with better patterns
        text_content = soup.get_text()
        sku_patterns = [
            r'SKU[:\s]*([H][A-Z0-9\-_]+)',  # HUUM SKUs start with H
            r'Model[:\s]*([H][A-Z0-9\-_]+)', # HUUM Models start with H
            r'SKU[:\s]*([A-Z0-9\-_]{6,})',   # General SKUs 6+ chars
            r'Model No[:.\s]*([A-Z0-9\-_]+)',
            r'Item No[:.\s]*([A-Z0-9\-_]+)',
        ]
        for pattern in sku_patterns:
            match = re.search(pattern, text_content, re.IGNORECASE)
            if match:
                sku = match.group(1).strip()
                if self.validator.validate_sku(sku):
                    logger.info(f"    Found SKU via text pattern: {sku}")
                    return sku
        
        # Method 5: Extract from URL path for HUUM products
        if '/huum/' in product_url.lower():
            # For HUUM, try to extract from URL structure
            url_parts = product_url.split('/')
            if len(url_parts) >= 2:
                # Look for numeric ID in URL
                for part in url_parts:
                    if part.isdigit() and len(part) >= 5:
                        # Generate HUUM-style SKU from URL ID
                        potential_sku = f"H{part}"
                        if self.validator.validate_sku(potential_sku):
                            logger.info(f"    Generated SKU from URL: {potential_sku}")
                            return potential_sku
        
        logger.warning(f"Could not find valid SKU for {product_url}")
        return None
    
    def _extract_short_description(self, soup):
        """Extract short product description - the content that appears under the price"""
        # Method 1: Look for the specific product description section under price
        # This is typically in a div with product details or description class
        product_desc_selectors = [
            'div.product-description',
            'div.product-details', 
            'div.product-summary',
            'div.product-info',
            '.product-description',
            '.product-details',
            '.product-summary'
        ]
        
        for selector in product_desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                # Clean up the text
                for script in desc_elem.find_all(['script', 'style']):
                    script.decompose()
                
                text = desc_elem.get_text(separator=' ', strip=True)
                if text and len(text) > 20:
                    return text[:1000]  # Increased limit for better content
        
        # Method 2: Look for content immediately after price section
        price_elem = soup.find(text=re.compile(r'\$\d+', re.I))
        if price_elem and hasattr(price_elem, 'parent'):
            price_container = price_elem.parent
            # Look for next significant content after price
            for sibling in price_container.find_next_siblings():
                if sibling.name in ['p', 'div'] and len(sibling.get_text(strip=True)) > 50:
                    text = sibling.get_text(strip=True)
                    if not any(skip_word in text.lower() for skip_word in ['add to cart', 'quantity', 'sku:', 'model:']):
                        return text[:1000]
        
        # Method 3: Look for the main product content area
        main_content_selectors = [
            'div.col-sm-12',
            'div.product-content',
            'div.main-content',
            'section.product-info'
        ]
        
        for selector in main_content_selectors:
            content_elem = soup.select_one(selector)
            if content_elem:
                # Look for the first substantial paragraph
                paragraphs = content_elem.find_all('p')
                for p in paragraphs:
                    text = p.get_text(strip=True)
                    if len(text) > 50 and not any(skip_word in text.lower() for skip_word in ['sku:', 'model:', 'price:']):
                        return text[:1000]
        
        # Method 4: Look for short description elements
        short_desc_elem = soup.find(['p', 'div'], {'class': re.compile(r'short.*desc|summary', re.I)})
        if short_desc_elem:
            return short_desc_elem.get_text(strip=True)[:1000]
        
        # Method 5: Fallback - First meaningful paragraph
        paragraphs = soup.find_all('p')
        for p in paragraphs:
            text = p.get_text(strip=True)
            if len(text) > 50 and not any(skip_word in text.lower() for skip_word in ['sku:', 'model:', 'price:', 'add to cart']):
                return text[:1000]
        
        return ""
    
    def _extract_full_description(self, soup):
        """Extract full product description"""
        # Look for description tab content
        desc_tab = soup.find(['div', 'section'], {'class': re.compile(r'description|desc.*content', re.I)})
        if desc_tab:
            return desc_tab.get_text(strip=True)
        
        # Look for product details
        details = soup.find(['div', 'section'], {'class': re.compile(r'detail|feature', re.I)})
        if details:
            return details.get_text(strip=True)
        
        return ""
    
    def _extract_category(self, soup):
        """Extract product category"""
        # From breadcrumbs
        breadcrumbs = soup.find_all(['a', 'span'], {'class': re.compile(r'breadcrumb', re.I)})
        if len(breadcrumbs) >= 2:
            return breadcrumbs[-2].get_text(strip=True)
        
        # From URL
        url_parts = soup.find('link', {'rel': 'canonical'})
        if url_parts:
            url = url_parts.get('href', '')
            parts = url.split('/')
            if 'products' in parts and len(parts) > parts.index('products') + 2:
                return parts[parts.index('products') + 2].replace('-', ' ').title()
        
        return "General"
    
    def _extract_subcategory(self, soup):
        """Extract product subcategory"""
        # From breadcrumbs
        breadcrumbs = soup.find_all(['a', 'span'], {'class': re.compile(r'breadcrumb', re.I)})
        if len(breadcrumbs) >= 3:
            return breadcrumbs[-1].get_text(strip=True)
        
        return ""
    
    def save_product(self, product_data):
        """Save product with all related data to database"""
        try:
            # Import models here to avoid import issues
            from products.models import Product, ProductImage, ProductSpecification, ProductDocument, RelatedProduct
            
            if not product_data.get('sku'):
                logger.error(f"❌ SKU is missing for product '{product_data.get('title', 'N/A')}'. Cannot save.")
                return None

            # Create or update product
            product, created = Product.objects.update_or_create( # Use update_or_create
                sku=product_data['sku'],
                defaults={
                    'title': product_data['title'],
                    'model': product_data.get('model_name', ''), # Add model
                    'short_description': product_data.get('short_description', ''),
                    'full_description': product_data.get('full_description', ''),
                    'price': product_data.get('price'), # Already handles None
                    'brand': product_data['brand'],
                    'category': product_data.get('category', ''),
                    'subcategory': product_data.get('subcategory', ''),
                    'source_url': product_data['source_url'],
                    'features': product_data.get('features', ''),
                    'includes': product_data.get('includes', ''),
                    'technical_info': product_data.get('technical_info', ''),
                    'shipping_info': product_data.get('shipping_info', ''),
                    'inspiration_content': product_data.get('inspiration_content', ''),
                    # 'specifications' field (JSON text) is not directly populated here
                    # It could be if extract_specifications returned JSON string
                }
            )
            
            action = "Created" if created else "Updated"
            logger.info(f"💾 {action} product core: {product.title} (SKU: {product.sku})")
            
            # Save images
            if 'images' in product_data and product_data['images']:
                ProductImage.objects.filter(product=product).delete()
                for i, image_data in enumerate(product_data['images']):
                    ProductImage.objects.create(
                        product=product,
                        image_url=image_data['url'],
                        alt_text=image_data.get('alt_text', ''),
                        image_type=image_data.get('type', 'gallery'),
                        is_primary=(i == 0)
                    )
                logger.info(f"  🖼️ Saved {len(product_data['images'])} images for {product.title}")

            # Save specifications (from dict to ProductSpecification model)
            if 'specifications_dict' in product_data and product_data['specifications_dict']:
                ProductSpecification.objects.filter(product=product).delete()
                for key, value in product_data['specifications_dict'].items():
                    if key and value: # Ensure key and value are not empty
                        ProductSpecification.objects.create(
                            product=product,
                            name=str(key)[:100], # Ensure name is within max_length
                            value=str(value)
                        )
                logger.info(f"  📋 Saved {len(product_data['specifications_dict'])} specifications for {product.title}")
            
            # Save documents
            if 'documents' in product_data and product_data['documents']:
                ProductDocument.objects.filter(product=product).delete()
                for doc_data in product_data['documents']:
                    ProductDocument.objects.create(
                        product=product,
                        title=doc_data.get('title', 'Document')[:200],
                        document_url=doc_data['url'],
                        document_type=doc_data.get('type', 'unknown')[:50]
                    )
                logger.info(f"  📄 Saved {len(product_data['documents'])} documents for {product.title}")
            
            # After saving the main product, attempt to extract and link related products
            # This requires the product instance, so we pass it.
            # We need the BeautifulSoup object `soup` from `extract_product_data`
            # This means `extract_related_products` should ideally be called from within `extract_product_data`
            # or `extract_product_data` should return `soup` as well.
            # For now, this call is illustrative and needs proper `soup` passing.
            # It will be called from run_intelligent_scraper after product save.

            return product # Return the saved product instance
            
        except Exception as e:
            logger.error(f"❌ Error saving product '{product_data.get('title', 'N/A')}' (SKU: {product_data.get('sku', 'N/A')}): {e}", exc_info=True)
            return None

    def run_intelligent_scraper(self, target_brand=None, target_category=None, limit=None):
        """Run the intelligent hierarchy-based scraper"""
        # Import models here to avoid import issues
        from products.models import Product
        
        logger.info("🚀 Starting Intelligent Bathing Brands Hierarchy Scraper...")
        logger.info("📋 Following Brand → Category → Collection → Product structure")
        
        saved_products_instances = []
        
        # Step 1: Discover all brands
        brands_dict = self.discover_brands() # Renamed for clarity
        if not brands_dict:
            logger.error("❌ No brands found!")
            return []
        
        # Filter to specific brand if requested
        if target_brand:
            brands_dict = {k: v for k, v in brands_dict.items() if target_brand.lower() in k.lower()}
            if not brands_dict:
                logger.error(f"❌ Brand '{target_brand}' not found!")
                return []
        
        # Process each brand
        for brand_name, brand_data in brands_dict.items():
            logger.info(f"\n🏢 Processing Brand: {brand_name}")
            
            categories_dict = self.discover_brand_categories(brand_data)
            if not categories_dict:
                logger.warning(f"⚠️ No categories found for {brand_name}")
                continue
            
            if target_category:
                categories_dict = {k: v for k, v in categories_dict.items() if target_category.lower() in k.lower()}
                if not categories_dict:
                    logger.warning(f"⚠️ Category '{target_category}' not found in {brand_name}")
                    continue
            
            for category_name, category_data in categories_dict.items():
                logger.info(f"  📂 Processing Category: {brand_name} → {category_name}")
                
                collections_dict = self.discover_category_collections(brand_data, category_data)
                if not collections_dict:
                    logger.warning(f"⚠️ No collections found for {brand_name} → {category_name}")
                    continue
                
                for collection_name, collection_data in collections_dict.items():
                    logger.info(f"    📦 Processing Collection: {brand_name} → {category_name} → {collection_name}")
                    
                    product_urls = self.discover_collection_products(brand_data, category_data, collection_data)
                    if not product_urls:
                        logger.warning(f"⚠️ No products found in {brand_name} → {category_name} → {collection_name}")
                        continue
                    
                    for i, product_url in enumerate(product_urls):
                        if product_url in self.scraped_urls:
                            logger.info(f"      ⏭️ Skipping already processed URL: {product_url}")
                            continue

                        if limit and len(saved_products_instances) >= limit:
                            logger.info(f"🛑 Reached limit of {limit} products")
                            # Log hierarchy state before returning
                            self._log_hierarchy_state(brands_dict)
                            return saved_products_instances
                        
                        logger.info(f"      🛍️ Scraping Product {i+1}/{len(product_urls)}: {product_url}")
                        
                        # Extract ALL product data
                        # We need the soup object from extract_product_data to pass to extract_related_products
                        # Modifying extract_product_data to potentially return (product_data, soup)
                        # Or, fetch again in extract_related_products, less ideal.
                        # For now, let's assume extract_product_data fetches and extract_related_products also fetches.
                        
                        product_info_dict = self.extract_product_data(product_url) # This is a dict
                        
                        if product_info_dict:
                            # Ensure hierarchy information is consistently applied
                            product_info_dict['brand'] = brand_name
                            product_info_dict['category'] = category_name
                            product_info_dict['subcategory'] = collection_name # Collection name becomes subcategory
                            
                            product_instance = self.save_product(product_info_dict)
                            if product_instance:
                                saved_products_instances.append(product_instance)
                                self.scraped_urls.add(product_url)
                                logger.info(f"        ✅ Saved to DB: {product_instance.title}")

                                # Now extract related products for the saved instance
                                # Fetch the page content again for related products (or modify extract_product_data to return soup)
                                try:
                                    response = self.session.get(product_url)
                                    response.raise_for_status()
                                    soup_for_related = BeautifulSoup(response.content, 'html.parser')
                                    self.extract_related_products(soup_for_related, product_instance)
                                except requests.exceptions.RequestException as e_rel:
                                    logger.error(f"❌ HTTP Error fetching page again for related products for {product_url}: {e_rel}")
                                except Exception as e_rel_parse:
                                     logger.error(f"❌ Error parsing for related products for {product_url}: {e_rel_parse}", exc_info=True)

                            else:
                                logger.warning(f"        ⚠️ Failed to save product from {product_url} to DB.")
                        else:
                            logger.warning(f"        ⚠️ Failed to extract data from {product_url}. Not saved.")
                        
                        time.sleep(1) # Respectful delay
                    
                    collection_data['scraped'] = True
                    collection_data['product_count'] = len(product_urls)
                    logger.info(f"    ✅ Completed Collection: {collection_name} ({len(product_urls)} products attempted)")
                
                category_data['scraped'] = True
                logger.info(f"  ✅ Completed Category: {category_name}")
            
            brand_data['scraped'] = True
            logger.info(f"✅ Completed Brand: {brand_name}")
        
        logger.info(f"\n🎉 Intelligent scraping complete!")
        self._log_hierarchy_state(brands_dict)
        logger.info(f"📊 Total products saved to DB in this run: {len(saved_products_instances)}")
        
        return saved_products_instances

    def _log_hierarchy_state(self, brands_dict):
        logger.info("📊 Hierarchy Scraping Summary:")
        for brand_name, brand_data in brands_dict.items():
            if brand_data.get('scraped'):
                logger.info(f"  🏢 Brand: {brand_name} (Processed)")
                categories_dict = brand_data.get('categories', {}) # Might not be populated if using discover_brand_categories directly
                # This part needs adjustment if categories/collections are not stored back into brands_dict
                # For now, it just indicates the brand was processed.
            else:
                 logger.info(f"  🏢 Brand: {brand_name} (Not Processed or Filtered Out)")


if __name__ == "__main__":
    scraper = EnhancedBathingBrandsScraper()
    
    # Example usage:
    
    # 1. Test single product
    # test_url = "https://bathingbrands.com/54661/huum/drop-45/electric-heaters" # HUUM DROP 4.5
    # test_url = "https://bathingbrands.com/28331/mr-steam/maxwell-3/commercial-steam-generators" # Mr.Steam Commercial
    # scraper.run_scraper(test_url=test_url)
    
    # 2. Scrape specific brand
    # scraper.run_scraper(target_brand="HUUM", limit=3)
    
    # 3. Scrape specific brand and category
    # scraper.run_scraper(target_brand="Mr.Steam", target_category="Commercial Steam", limit=5)
    
    # 4. Scrape everything (be careful - this will take a long time!)
    scraper.run_scraper(limit=10) # Limit for testing 