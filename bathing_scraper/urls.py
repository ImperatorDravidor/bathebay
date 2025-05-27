"""
URL configuration for bathing_scraper project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect
from django.views.generic import RedirectView

def admin_redirect(request):
    """Redirect admin root to product catalog control center"""
    return redirect('/admin/products/product/')

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    
    # Redirect admin root to product catalog
    path('admin', RedirectView.as_view(url='/admin/products/product/', permanent=False)),
    
    # Additional admin redirects for convenience
    path('admin/dashboard/', admin_redirect, name='admin_dashboard_redirect'),
    path('catalog/', admin_redirect, name='catalog_redirect'),
    path('products-admin/', admin_redirect, name='products_admin_redirect'),
    
    # Main application URLs
    path('', include('products.urls')),  # Include product URLs
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
