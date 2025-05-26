from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from .models import Product


def product_list(request):
    """Display paginated list of all products"""
    products = Product.objects.filter(is_active=True).select_related().prefetch_related('images')
    
    # Add filtering by brand if requested
    brand = request.GET.get('brand')
    if brand:
        products = products.filter(brand__icontains=brand)
    
    # Add search functionality
    search = request.GET.get('search')
    if search:
        products = products.filter(title__icontains=search)
    
    # Pagination
    paginator = Paginator(products, 20)  # Show 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique brands for filter dropdown
    brands = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
    
    context = {
        'page_obj': page_obj,
        'brands': brands,
        'current_brand': brand,
        'current_search': search,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, slug):
    """Display detailed view of a single product"""
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()
    
    context = {
        'product': product,
        'images': images,
    }
    return render(request, 'products/product_detail.html', context)
