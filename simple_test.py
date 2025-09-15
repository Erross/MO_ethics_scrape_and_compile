"""
Simple diagnostic test for MEC scraper setup
Run this to verify your environment is working
"""

import sys
import os
from pathlib import Path

def test_environment():
    print("🔍 MEC Scraper Environment Test")
    print("=" * 50)

    # Test 1: Basic Python setup
    print(f"1. Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")

    # Check if using virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("   ✅ Using virtual environment")
    else:
        print("   ⚠️  Using global Python (consider using virtual environment)")
        print("   💡 In PyCharm: File → Settings → Project → Python Interpreter → Add → Virtualenv Environment")

    # Check pip location
    try:
        import subprocess
        pip_location = subprocess.check_output([sys.executable, "-m", "pip", "--version"], text=True).strip()
        print(f"   pip info: {pip_location}")
    except Exception as e:
        print(f"   ⚠️  Could not check pip location: {e}")

    # Test 2: Check project structure
    print("\n2. Project structure:")
    project_root = Path(__file__).parent
    print(f"   Project root: {project_root}")

    required_files = [
        "config.py",
        "main.py",
        "src/mec_scraper.py",
        "src/bulk_data_access.py",
        "tests/test_scraper.py"
    ]

    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if full_path.exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - MISSING")
            missing_files.append(file_path)

    if missing_files:
        print(f"\n❌ Missing files: {missing_files}")
        print("   Please create these files as described in the setup guide")
        return False

    # Test 3: Required packages
    print("\n3. Required packages:")
    # Package name -> import name mapping
    required_packages = {
        "selenium": "selenium",
        "requests": "requests",
        "beautifulsoup4": "bs4",  # beautifulsoup4 imports as bs4
        "webdriver_manager": "webdriver_manager",
        "pandas": "pandas"
    }

    missing_packages = []
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
            print(f"   ✅ {package_name}")
        except ImportError:
            print(f"   ❌ {package_name} - NOT INSTALLED")
            missing_packages.append(package_name)

    if missing_packages:
        print(f"\n❌ Missing packages: {missing_packages}")
        print("   Install with: pip install " + " ".join(missing_packages))
        # Special note for beautifulsoup4
        if "beautifulsoup4" in missing_packages:
            print("   💡 Note: beautifulsoup4 installs as 'bs4' - this might be a path issue")
            try:
                import bs4
                print("     Actually, bs4 is available! This might be an environment issue.")
            except ImportError:
                print("     bs4 is truly not available")
        return False

    # Test 4: Config import
    print("\n4. Testing config import:")
    try:
        sys.path.append(str(project_root))
        import config
        print("   ✅ config.py imported successfully")
        print(f"   ✅ Downloads dir: {config.DOWNLOADS_DIR}")
    except Exception as e:
        print(f"   ❌ Config import failed: {e}")
        return False

    # Test 5: Module imports
    print("\n5. Testing module imports:")
    try:
        sys.path.append(str(project_root / "src"))
        from mec_scraper import MECReportScraper
        print("   ✅ mec_scraper imported successfully")
    except Exception as e:
        print(f"   ❌ mec_scraper import failed: {e}")
        return False

    try:
        from bulk_data_access import MECBulkDataAccess
        print("   ✅ bulk_data_access imported successfully")
    except Exception as e:
        print(f"   ❌ bulk_data_access import failed: {e}")
        return False

    # Test 6: WebDriver test
    print("\n6. Testing WebDriver setup:")
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from webdriver_manager.chrome import ChromeDriverManager

        print("   ✅ Selenium imports successful")

        # Test ChromeDriverManager
        driver_path = ChromeDriverManager().install()
        print(f"   ✅ ChromeDriver available at: {driver_path}")

    except Exception as e:
        print(f"   ❌ WebDriver setup failed: {e}")
        print("   💡 Make sure Chrome browser is installed")
        return False

    print("\n🎉 All tests passed! Your setup is ready.")
    print("\n🚀 Try running: python main.py single \"Francis Howell Families\" --no-headless")

    # Quick verification of actual imports our scraper needs
    print("\n💡 Quick verification of scraper imports:")
    try:
        from bs4 import BeautifulSoup
        print("   ✅ BeautifulSoup import works")
    except ImportError as e:
        print(f"   ❌ BeautifulSoup import failed: {e}")

    return True

def test_simple_scraper():
    """Test basic scraper functionality"""
    print("\n" + "=" * 50)
    print("🧪 Testing Basic Scraper Functionality")

    try:
        # Import required modules
        sys.path.append(str(Path(__file__).parent))
        sys.path.append(str(Path(__file__).parent / "src"))

        from mec_scraper import MECReportScraper
        import tempfile

        # Create scraper with headless mode
        with tempfile.TemporaryDirectory() as temp_dir:
            print("   Creating scraper instance...")
            scraper = MECReportScraper(headless=True, output_dir=temp_dir)

            print("   ✅ Scraper created successfully")

            # Test basic navigation
            print("   Testing basic navigation...")
            scraper.driver.get("https://www.google.com")

            if "Google" in scraper.driver.title:
                print("   ✅ Basic navigation working")
            else:
                print("   ❌ Navigation issue")
                return False

            # Clean up
            scraper.close()
            print("   ✅ Scraper closed successfully")

        print("\n🎉 Basic scraper test passed!")
        return True

    except Exception as e:
        print(f"   ❌ Scraper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_environment()

    if success:
        print("\nWould you like to test the scraper functionality? (y/n): ", end="")
        try:
            response = input().lower().strip()
            if response == 'y':
                test_simple_scraper()
        except KeyboardInterrupt:
            print("\n\nTest cancelled by user")
    else:
        print("\n❌ Please fix the issues above before proceeding")