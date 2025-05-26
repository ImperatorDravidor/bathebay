#!/usr/bin/env python
"""
Setup script for Bathing Brands Product Scraper
"""
import os
import sys
import subprocess
import django
from django.core.management import execute_from_command_line

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        if isinstance(command, list):
            subprocess.run(command, check=True)
        else:
            os.system(command)
        print(f"✓ {description} completed successfully")
    except (subprocess.CalledProcessError, OSError) as e:
        print(f"✗ Error during {description}: {e}")
        return False
    return True

def setup_project():
    """Setup the Django project"""
    print("🚀 Setting up Bathing Brands Product Scraper...")
    
    # Check if we're in a virtual environment
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: You're not in a virtual environment. It's recommended to use one.")
        response = input("Continue anyway? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled. Please create and activate a virtual environment first.")
            return
    
    # Install dependencies
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      "Installing dependencies"):
        return
    
    # Setup Django environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
    django.setup()
    
    # Run migrations
    if not run_command([sys.executable, "manage.py", "migrate"], "Running database migrations"):
        return
    
    # Create media directories
    media_dirs = ['media', 'media/products']
    for dir_path in media_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"✓ Created directory: {dir_path}")
    
    # Collect static files (if needed)
    if not run_command([sys.executable, "manage.py", "collectstatic", "--noinput"], 
                      "Collecting static files"):
        print("⚠️  Static files collection failed, but this is not critical for basic functionality")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Start scraping products:")
    print("   python manage.py scrape_products --limit 10")
    print("\n2. Export products to CSV:")
    print("   python manage.py export_products csv")
    print("\n3. Start the web server to view products:")
    print("   python manage.py runserver")
    print("\n4. Create a superuser for admin access:")
    print("   python manage.py createsuperuser")

if __name__ == "__main__":
    setup_project() 