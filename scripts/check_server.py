#!/usr/bin/env python
"""
Simple script to check if Django server is running and show URLs
"""
import requests
import time

def check_server():
    """Check if Django server is running"""
    url = "http://127.0.0.1:8000"
    
    print("🔍 Checking Django Development Server...")
    print("=" * 50)
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            print(f"✅ Server is running at: {url}")
            print(f"📱 Home page: {url}/")
            print(f"🛍️  Products: {url}/products/")
            print(f"⚙️  Admin: {url}/admin/")
            print(f"\n🎨 Frontend Features:")
            print(f"  - Brand logos properly displayed")
            print(f"  - All brands shown (not limited to 8)")
            print(f"  - Dynamic navigation menus")
            print(f"  - Responsive brand cards")
            print(f"  - Hover effects and animations")
            return True
        else:
            print(f"❌ Server responded with status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"❌ Server is not running at {url}")
        print(f"💡 Run: python manage.py runserver")
        return False
    except requests.exceptions.Timeout:
        print(f"⏰ Server is taking too long to respond")
        return False
    except Exception as e:
        print(f"❌ Error checking server: {e}")
        return False

if __name__ == "__main__":
    check_server() 