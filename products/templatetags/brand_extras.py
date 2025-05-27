from django import template
from django.utils.safestring import mark_safe
import os
from django.conf import settings

register = template.Library()

# Brand logo mapping - maps brand names to their logo filenames
BRAND_LOGO_MAPPING = {
    'HUUM': 'huum logo.jpg',
    'Harvia': 'harvia-logo.jpg',
    'Mr.Steam': 'mr-steam-logo.jpg',
    'ThermaSol': 'BB-Thermasol-products.jpg',
    'Steamist': 'BB-Steamist-products.jpg',
    'Amerec': 'amerec logo.jpg',
    'Kohler': 'kohler-logo.jpg',
    'Bathology': 'bathology logo.jpg',
    'Auroom': 'BB-Auroom_products logo.jpg',
    'Prosaunas': 'BB-Prosaunas-Logo.jpg',
    'Aromamist': 'BB-Aromamist-products.jpg',
    'Saunalife': 'BB-saunalife_2.jpg',
    'Haljas': 'BB-Haljas-houses.jpg',
    'EmotionWood': 'BB-EmotionWood.jpg',
    'Finlandia': 'BB-Finlandia.jpg',
    'Kolo': 'BB-Kolo.jpg',
    'Saunum': 'BB-Saunum.jpg',
    'EOS': 'EOS-Logo-Image.jpg',
    'Delta': 'Delta-Logo-Image.jpg',
    'Hukka': 'Hukka-Log-Image.jpg',
    'Finnmark': 'Finnmark-Log-Image.jpg',
    'Narvi': 'Narvi.jpg',
    'Rento': 'Rento-Sauna-Products.jpg',
    'Cozy Heat': 'cozy-heat-sauna-products.jpg',
    'Wedi': 'Wedi-Shower-Substrates.jpg',
}

@register.filter
def brand_logo(brand_name):
    """
    Returns the logo URL for a given brand name.
    Falls back to a placeholder if no logo is found.
    """
    if not brand_name:
        return '/static/images/placeholder-logo.png'
    
    # Clean brand name and check mapping
    clean_brand = brand_name.strip()
    logo_filename = BRAND_LOGO_MAPPING.get(clean_brand)
    
    if logo_filename:
        logo_url = f'/media/{logo_filename}'
        # Check if file exists (optional - for production you might skip this check)
        return logo_url
    
    # Fallback to placeholder
    return f'https://via.placeholder.com/200x120/007cba/ffffff?text={clean_brand.replace(" ", "+")}'

@register.simple_tag
def brand_logo_img(brand_name, css_class="img-fluid", alt_text=None):
    """
    Returns a complete img tag for a brand logo.
    """
    if not brand_name:
        return ''
    
    logo_url = brand_logo(brand_name)
    alt = alt_text or f'{brand_name} logo'
    
    return mark_safe(f'<img src="{logo_url}" class="{css_class}" alt="{alt}" onerror="this.src=\'https://via.placeholder.com/200x120/007cba/ffffff?text={brand_name.replace(" ", "+")}\'">')

@register.filter
def get_brand_categories(brand_name):
    """
    Get categories for a specific brand (you can implement this based on your needs)
    """
    from products.models import Product
    return Product.objects.filter(brand=brand_name).values_list('category', flat=True).distinct()

@register.inclusion_tag('products/partials/brand_card.html')
def brand_card(brand_data, show_logo=True, show_stats=True):
    """
    Renders a brand card with logo and statistics
    """
    return {
        'brand': brand_data,
        'show_logo': show_logo,
        'show_stats': show_stats,
    } 