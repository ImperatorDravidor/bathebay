import csv
import json
from io import StringIO
from django.http import HttpResponse
from .models import Product


class ProductExporter:
    """Base class for product exporters"""
    
    def __init__(self, queryset=None):
        self.queryset = queryset or Product.objects.filter(is_active=True)
    
    def export(self):
        """Override in subclasses"""
        raise NotImplementedError


class CSVExporter(ProductExporter):
    """Export products to CSV format"""
    
    def export(self, filename="products.csv"):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Write header
        writer.writerow([
            'SKU', 'Title', 'Brand', 'Category', 'Subcategory', 
            'Description', 'Price', 'Specifications', 'Source URL',
            'Image URLs', 'Created At'
        ])
        
        # Write data
        for product in self.queryset:
            image_urls = ', '.join([img.image_url for img in product.images.all()])
            writer.writerow([
                product.sku,
                product.title,
                product.brand,
                product.category,
                product.subcategory,
                product.short_description or product.full_description,
                product.price or '',
                product.specifications,
                product.source_url,
                image_urls,
                product.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ])
        
        return response


class eBayExporter(ProductExporter):
    """Export products in eBay-compatible CSV format"""
    
    def export(self, filename="ebay_products.csv"):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # eBay CSV headers
        writer.writerow([
            'Action(SiteID=US|Country=US|Currency=USD|Version=1193)',
            'Category', 'StoreCategory', 'Title', 'Subtitle', 'PicURL',
            'Description', 'Format', 'Duration', 'Quantity', 'StartPrice',
            'BuyItNowPrice', 'CustomLabel', 'Location', 'PayPalAccepted',
            'PaymentSeeDescription', 'ShippingType', 'ShippingService-1:Option',
            'ShippingService-1:Cost', 'DispatchTimeMax', 'ReturnsAcceptedOption',
            'ReturnsWithinOption', 'ReturnsDescription', 'RefundOption'
        ])
        
        # Write data
        for product in self.queryset:
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image_url if primary_image else ''
            
            # Clean title for eBay (max 80 chars)
            title = product.title[:77] + "..." if len(product.title) > 80 else product.title
            
            # Create description with specifications
            description = f"<p>{product.short_description or product.full_description or 'No description available'}</p>"
            if product.specifications:
                try:
                    specs = json.loads(product.specifications)
                    description += "<ul>"
                    for key, value in specs.items():
                        description += f"<li><strong>{key}:</strong> {value}</li>"
                    description += "</ul>"
                except:
                    pass
            
            writer.writerow([
                'Add',  # Action
                'Business & Industrial',  # Category (adjust as needed)
                '',  # StoreCategory
                title,
                f"{product.brand} - {product.category}",  # Subtitle
                image_url,
                description,
                'FixedPriceItem',  # Format
                'GTC',  # Duration (Good Till Cancelled)
                '1',  # Quantity
                product.price or '0.01',  # StartPrice
                product.price or '0.01',  # BuyItNowPrice
                product.sku,  # CustomLabel
                'United States',  # Location
                '1',  # PayPalAccepted
                '0',  # PaymentSeeDescription
                'Flat',  # ShippingType
                'USPSPriority',  # ShippingService-1:Option
                '15.00',  # ShippingService-1:Cost
                '3',  # DispatchTimeMax
                'ReturnsAccepted',  # ReturnsAcceptedOption
                'Days_30',  # ReturnsWithinOption
                'Return shipping paid by buyer',  # ReturnsDescription
                'MoneyBack'  # RefundOption
            ])
        
        return response


class AmazonExporter(ProductExporter):
    """Export products in Amazon-compatible format"""
    
    def export(self, filename="amazon_products.csv"):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Amazon inventory file headers (simplified)
        writer.writerow([
            'sku', 'product-id', 'product-id-type', 'price', 'minimum-seller-allowed-price',
            'maximum-seller-allowed-price', 'item-condition', 'quantity', 'add-delete',
            'will-ship-internationally', 'expedited-shipping', 'standard-plus',
            'item-note', 'fulfillment-center-id', 'product-tax-code',
            'merchant-shipping-group-name'
        ])
        
        # Write data
        for product in self.queryset:
            writer.writerow([
                product.sku,
                product.sku,  # product-id (using SKU)
                '1',  # product-id-type (1 = ASIN, 2 = UPC, 3 = EAN, 4 = ISBN)
                product.price or '0.01',
                '',  # minimum-seller-allowed-price
                '',  # maximum-seller-allowed-price
                '11',  # item-condition (11 = New)
                '1',  # quantity
                'a',  # add-delete (a = add/update)
                'n',  # will-ship-internationally
                'n',  # expedited-shipping
                'n',  # standard-plus
                f"{product.brand} {product.title}",  # item-note
                '',  # fulfillment-center-id
                '',  # product-tax-code
                ''   # merchant-shipping-group-name
            ])
        
        return response


class ShopifyExporter(ProductExporter):
    """Export products in Shopify-compatible CSV format"""
    
    def export(self, filename="shopify_products.csv"):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        
        writer = csv.writer(response)
        
        # Shopify CSV headers
        writer.writerow([
            'Handle', 'Title', 'Body (HTML)', 'Vendor', 'Type', 'Tags',
            'Published', 'Option1 Name', 'Option1 Value', 'Option2 Name',
            'Option2 Value', 'Option3 Name', 'Option3 Value', 'Variant SKU',
            'Variant Grams', 'Variant Inventory Tracker', 'Variant Inventory Qty',
            'Variant Inventory Policy', 'Variant Fulfillment Service',
            'Variant Price', 'Variant Compare At Price', 'Variant Requires Shipping',
            'Variant Taxable', 'Variant Barcode', 'Image Src', 'Image Position',
            'Image Alt Text', 'Gift Card', 'SEO Title', 'SEO Description',
            'Google Shopping / Google Product Category', 'Google Shopping / Gender',
            'Google Shopping / Age Group', 'Google Shopping / MPN',
            'Google Shopping / AdWords Grouping', 'Google Shopping / AdWords Labels',
            'Google Shopping / Condition', 'Google Shopping / Custom Product',
            'Google Shopping / Custom Label 0', 'Google Shopping / Custom Label 1',
            'Google Shopping / Custom Label 2', 'Google Shopping / Custom Label 3',
            'Google Shopping / Custom Label 4', 'Variant Image', 'Variant Weight Unit',
            'Variant Tax Code', 'Cost per item'
        ])
        
        # Write data
        for product in self.queryset:
            handle = f"{product.brand}-{product.title}".lower().replace(' ', '-').replace('/', '-')
            handle = ''.join(c for c in handle if c.isalnum() or c == '-')
            
            # Create HTML description
            description = f"<p>{product.short_description or product.full_description or 'No description available'}</p>"
            if product.specifications:
                try:
                    specs = json.loads(product.specifications)
                    description += "<h3>Specifications:</h3><ul>"
                    for key, value in specs.items():
                        description += f"<li><strong>{key}:</strong> {value}</li>"
                    description += "</ul>"
                except:
                    pass
            
            # Get primary image
            primary_image = product.images.filter(is_primary=True).first()
            image_url = primary_image.image_url if primary_image else ''
            
            # Tags
            tags = f"{product.brand}, {product.category}"
            if product.subcategory:
                tags += f", {product.subcategory}"
            
            writer.writerow([
                handle,  # Handle
                product.title,  # Title
                description,  # Body (HTML)
                product.brand,  # Vendor
                product.category,  # Type
                tags,  # Tags
                'TRUE',  # Published
                '',  # Option1 Name
                '',  # Option1 Value
                '',  # Option2 Name
                '',  # Option2 Value
                '',  # Option3 Name
                '',  # Option3 Value
                product.sku,  # Variant SKU
                '1000',  # Variant Grams (default weight)
                'shopify',  # Variant Inventory Tracker
                '1',  # Variant Inventory Qty
                'deny',  # Variant Inventory Policy
                'manual',  # Variant Fulfillment Service
                product.price or '0.01',  # Variant Price
                '',  # Variant Compare At Price
                'TRUE',  # Variant Requires Shipping
                'TRUE',  # Variant Taxable
                '',  # Variant Barcode
                image_url,  # Image Src
                '1',  # Image Position
                product.title,  # Image Alt Text
                'FALSE',  # Gift Card
                product.title,  # SEO Title
                (product.short_description or product.full_description or '')[:160],  # SEO Description
                'Home & Garden',  # Google Shopping Category
                '',  # Google Shopping Gender
                '',  # Google Shopping Age Group
                product.sku,  # Google Shopping MPN
                product.category,  # Google Shopping AdWords Grouping
                product.brand,  # Google Shopping AdWords Labels
                'new',  # Google Shopping Condition
                'FALSE',  # Google Shopping Custom Product
                product.brand,  # Custom Label 0
                product.category,  # Custom Label 1
                product.subcategory,  # Custom Label 2
                '',  # Custom Label 3
                '',  # Custom Label 4
                '',  # Variant Image
                'g',  # Variant Weight Unit
                '',  # Variant Tax Code
                ''   # Cost per item
            ])
        
        return response


# Convenience functions
def export_to_csv(queryset=None, filename="products.csv"):
    """Export products to CSV"""
    exporter = CSVExporter(queryset)
    return exporter.export(filename)

def export_to_ebay(queryset=None, filename="ebay_products.csv"):
    """Export products to eBay format"""
    exporter = eBayExporter(queryset)
    return exporter.export(filename)

def export_to_amazon(queryset=None, filename="amazon_products.csv"):
    """Export products to Amazon format"""
    exporter = AmazonExporter(queryset)
    return exporter.export(filename)

def export_to_shopify(queryset=None, filename="shopify_products.csv"):
    """Export products to Shopify format"""
    exporter = ShopifyExporter(queryset)
    return exporter.export(filename) 