#!/usr/bin/env python
"""
Setup script for Bathing Brands Scraper
Automates the initial setup process
"""

import os
import sys
import subprocess
import platform

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Bathing Brands Scraper Setup")
    print("=" * 40)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version.split()[0]} detected")
    
    # Determine the correct activation command based on OS
    if platform.system() == "Windows":
        activate_cmd = "venv\\Scripts\\activate"
        pip_cmd = "venv\\Scripts\\pip"
        python_cmd = "venv\\Scripts\\python"
    else:
        activate_cmd = "source venv/bin/activate"
        pip_cmd = "venv/bin/pip"
        python_cmd = "venv/bin/python"
    
    # Create virtual environment
    if not os.path.exists("venv"):
        if not run_command("python -m venv venv", "Creating virtual environment"):
            sys.exit(1)
    else:
        print("✅ Virtual environment already exists")
    
    # Install dependencies
    if not run_command(f"{pip_cmd} install -r requirements.txt", "Installing dependencies"):
        sys.exit(1)
    
    # Run migrations
    if not run_command(f"{python_cmd} manage.py migrate", "Setting up database"):
        sys.exit(1)
    
    # Create admin user
    if not run_command(f"{python_cmd} scripts/create_admin.py", "Creating admin user"):
        print("⚠️ Admin user creation failed, you may need to create one manually")
    
    print("\n🎉 Setup completed successfully!")
    print("\n📋 Next steps:")
    print(f"1. Activate virtual environment:")
    if platform.system() == "Windows":
        print("   venv\\Scripts\\activate")
    else:
        print("   source venv/bin/activate")
    
    print("2. Start the development server:")
    print("   python manage.py runserver")
    
    print("3. Access the application:")
    print("   🌐 Web interface: http://127.0.0.1:8000/")
    print("   ⚙️ Admin panel: http://127.0.0.1:8000/admin/")
    print("   👤 Login: admin / magnesium")
    
    print("\n🔧 Available commands:")
    print("   python manage.py scrape_huum --limit 5")
    print("   python manage.py intelligent_scrape --brand HUUM")
    print("   python scripts/test_scraper.py")
    print("   python scripts/check_server.py")

if __name__ == "__main__":
    main() 