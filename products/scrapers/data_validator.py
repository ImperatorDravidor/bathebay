"""
Data validation utilities for scraped product information
"""


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
        if price is None:  # Allow None for price
            return True
        try:
            price_val = float(str(price).replace('$', '').replace(',', ''))
            return 0 <= price_val < 100000  # Allow 0, reasonable price range
        except (ValueError, TypeError):
            return False
    
    @staticmethod
    def validate_sku(sku):
        """Validate SKU format"""
        if not sku or len(sku.strip()) < 1:  # Allow shorter SKUs
            return False
        return not sku.lower().startswith(('http', 'error', 'n/a'))
    
    @staticmethod
    def validate_image_url(url):
        """Validate image URL"""
        if not url:
            return False
        return url.startswith(('http://', 'https://')) and any(
            ext in url.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp']
        ) 