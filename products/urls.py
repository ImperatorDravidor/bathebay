from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    # Homepage
    path('', views.home, name='home'),
    
    # Product listing and filtering
    path('products/', views.product_list, name='product_list'),
    path('brand/<str:brand_name>/', views.brand_products, name='brand_products'),
    path('category/<str:category_name>/', views.category_products, name='category_products'),
    
    # Product detail
    path('product/<str:slug>/', views.product_detail, name='product_detail'),
    path('product/<int:pk>/', views.product_detail_by_id, name='product_detail_by_id'),
    
    # Search
    path('search/', views.search_products, name='search_products'),
    
    # API endpoints for AJAX
    path('api/brands/', views.api_brands, name='api_brands'),
    path('api/categories/', views.api_categories, name='api_categories'),
] 