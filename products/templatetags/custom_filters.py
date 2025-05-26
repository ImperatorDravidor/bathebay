import json
from django import template
from django.db.models import Q

register = template.Library()

@register.filter
def parse_json(value):
    """Parse JSON string into Python dict"""
    try:
        return json.loads(value)
    except (json.JSONDecodeError, TypeError):
        return {}

@register.filter
def related_products(product, count=4):
    """Get related products based on brand and category"""
    from products.models import Product
    
    related = Product.objects.filter(
        Q(brand=product.brand) | Q(category=product.category),
        is_active=True
    ).exclude(id=product.id)[:count]
    
    return related 