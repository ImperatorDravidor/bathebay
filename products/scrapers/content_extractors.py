"""
Content extraction utilities for product scraping
"""

import re
import json
import logging
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class ContentExtractor:
    """Handles extraction of various content types from product pages"""
    
    def __init__(self, base_scraper):
        self.scraper = base_scraper
        self.validator = base_scraper.validator
    
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
                    img_url = self.scraper._resolve_url(img_url, product_url)
                    
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
            
            # Method 4: Look for specific product data using regex patterns
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
                    href = self.scraper._resolve_url(href, self.scraper.base_url)
                    
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
    
    def extract_tab_content(self, soup, tab_name):
        """Extract content from specific tabs like Description, Features, Includes, etc."""
        content = ""
        
        try:
            # Look for tab content by various methods
            tab_patterns = [tab_name.lower(), tab_name.replace(' ', '').lower()]
            
            # Method 1: Look for tab panels with ID or class containing tab name
            for pattern in tab_patterns:
                tab_panel = soup.find(['div', 'section'], {'id': re.compile(pattern, re.I)})
                if not tab_panel:
                    tab_panel = soup.find(['div', 'section'], {'class': re.compile(pattern, re.I)})
                
                if tab_panel:
                    content = self.scraper.extract_text_from_element(tab_panel)
                    break
            
            # Method 2: Look for headings followed by content
            if not content:
                headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                                       string=re.compile(tab_name, re.I))
                for heading in headings:
                    # Get content after the heading
                    content_parts = []
                    for sibling in heading.find_next_siblings():
                        if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                            break
                        content_parts.append(self.scraper.extract_text_from_element(sibling))
                    
                    if content_parts:
                        content = " ".join(content_parts)
                        break
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error extracting tab content for {tab_name}: {e}")
            return ""
    
    def extract_content_by_heading(self, soup, heading_text):
        """Extract content that appears after a specific heading"""
        content = ""
        
        try:
            # Find heading containing the text
            headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'], 
                                   string=re.compile(heading_text, re.I))
            
            for heading in headings:
                content_parts = []
                
                # Get all siblings until next heading
                for sibling in heading.find_next_siblings():
                    if sibling.name in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                        break
                    
                    text = self.scraper.extract_text_from_element(sibling)
                    if text:
                        content_parts.append(text)
                
                if content_parts:
                    content = " ".join(content_parts)
                    break
            
            return content.strip()
            
        except Exception as e:
            logger.error(f"❌ Error extracting content by heading {heading_text}: {e}")
            return "" 