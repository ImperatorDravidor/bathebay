#!/usr/bin/env python
"""
Create admin user with specific credentials for team access
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'bathing_scraper.settings')
django.setup()

from django.contrib.auth.models import User

def create_admin_user():
    """Create admin user with specified credentials"""
    username = 'admin'
    email = 'admin@bathingbrands.com'
    password = 'magnesium'
    
    # Delete existing admin user if exists
    if User.objects.filter(username=username).exists():
        User.objects.filter(username=username).delete()
        print(f"Deleted existing user: {username}")
    
    # Create new admin user
    admin_user = User.objects.create_superuser(
        username=username,
        email=email,
        password=password
    )
    
    print(f"✅ Admin user created successfully!")
    print(f"   Username: {username}")
    print(f"   Password: {password}")
    print(f"   Access URL: http://127.0.0.1:8000/admin/")
    print(f"   Main Site: http://127.0.0.1:8000/ (requires login)")

if __name__ == '__main__':
    create_admin_user() 