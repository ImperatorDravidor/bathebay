#!/usr/bin/env python
"""
Test script to verify admin functionality and redirects
"""
import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from django.contrib.auth.models import User
from products.models import Product

def test_admin_setup():
    """Test admin setup and functionality"""
    print("🔧 Testing Admin Setup...")
    print("=" * 50)
    
    # Check if admin user exists
    admin_users = User.objects.filter(is_superuser=True)
    print(f"📊 Admin users found: {admin_users.count()}")
    
    if admin_users.exists():
        admin_user = admin_users.first()
        print(f"✅ Admin user: {admin_user.username}")
    else:
        print("❌ No admin user found. Run: python scripts/create_admin.py")
        return False
    
    # Check product count
    product_count = Product.objects.count()
    print(f"📦 Products in database: {product_count}")
    
    # Check brands
    brands = Product.objects.values_list('brand', flat=True).distinct()
    print(f"🏢 Brands: {list(brands)[:5]}{'...' if len(brands) > 5 else ''}")
    
    print("\n🌐 Admin URLs to test:")
    print("   Main Admin: http://127.0.0.1:8000/admin/")
    print("   Product Catalog: http://127.0.0.1:8000/admin/products/product/")
    print("   Dashboard: http://127.0.0.1:8000/admin/products/product/dashboard/")
    print("   Scraping Control: http://127.0.0.1:8000/admin/products/product/scraping-control/")
    
    print("\n👤 Login credentials:")
    print("   Username: admin")
    print("   Password: magnesium")
    
    return True

def test_server_response():
    """Test if server is running and admin redirects work"""
    print("\n🔍 Testing server responses...")
    
    base_url = "http://127.0.0.1:8000"
    
    test_urls = [
        "/",
        "/admin/",
        "/admin/products/product/",
    ]
    
    for url in test_urls:
        try:
            response = requests.get(f"{base_url}{url}", timeout=5, allow_redirects=False)
            print(f"   {url}: Status {response.status_code}")
            
            if response.status_code in [301, 302]:
                redirect_url = response.headers.get('Location', 'Unknown')
                print(f"      → Redirects to: {redirect_url}")
                
        except requests.exceptions.ConnectionError:
            print(f"   {url}: ❌ Server not running")
            print("   💡 Start server with: python manage.py runserver")
            break
        except Exception as e:
            print(f"   {url}: ❌ Error: {e}")

if __name__ == "__main__":
    if test_admin_setup():
        test_server_response()
    
    print("\n🎉 Admin testing complete!")
    print("🚀 Start the server and visit: http://127.0.0.1:8000/admin/") 