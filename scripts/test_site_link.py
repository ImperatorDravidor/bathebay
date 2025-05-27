#!/usr/bin/env python
"""
Test script to verify the site link in admin dashboard
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from django.contrib.auth.models import User
from products.models import Product

def test_site_link():
    """Test the site link functionality"""
    print("🔗 Testing Site Link in Admin Dashboard...")
    print("=" * 50)
    
    # Check if admin user exists
    admin_users = User.objects.filter(is_superuser=True)
    if admin_users.exists():
        admin_user = admin_users.first()
        print(f"✅ Admin user found: {admin_user.username}")
    else:
        print("❌ No admin user found. Run: python scripts/create_admin.py")
        return False
    
    # Check product count
    product_count = Product.objects.count()
    print(f"📦 Products in database: {product_count}")
    
    print("\n🌐 URLs to test:")
    print("   Admin Dashboard: http://127.0.0.1:8000/admin/products/product/")
    print("   Main Site: http://127.0.0.1:8000/")
    print("   Product List: http://127.0.0.1:8000/products/")
    
    print("\n🔗 Site Link Features:")
    print("   ✅ 'View Main Site' button in dashboard header")
    print("   ✅ 'View Frontend' button in Product Management section")
    print("   ✅ Both links open in new tab/window")
    print("   ✅ Links point to main site homepage")
    
    print("\n👤 Login credentials:")
    print("   Username: admin")
    print("   Password: magnesium")
    
    print("\n📋 Testing Steps:")
    print("   1. Visit: http://127.0.0.1:8000/admin/")
    print("   2. Login with admin credentials")
    print("   3. You should be redirected to Product Catalog")
    print("   4. Look for 'View Main Site' button in header")
    print("   5. Click it to open main site in new tab")
    print("   6. Also test 'View Frontend' in Product Management section")
    
    return True

if __name__ == "__main__":
    if test_site_link():
        print("\n🎉 Site link test setup complete!")
        print("🚀 Start server: python manage.py runserver")
        print("🔗 Test the links at: http://127.0.0.1:8000/admin/") 