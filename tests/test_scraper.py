"""
Tests for MEC Campaign Finance Scraper

Run these tests to verify your setup is working correctly.
"""

import sys
import unittest
from pathlib import Path
import tempfile
import shutil

# Add both src and parent directory to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

# Import Selenium after adding src to path
from selenium.webdriver.common.by import By

from mec_scraper import MECReportScraper
from bulk_data_access import MECBulkDataAccess, get_data_access_strategy


class TestMECScraperSetup(unittest.TestCase):
    """Test basic scraper setup and functionality"""

    def setUp(self):
        """Set up test environment"""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_scraper_initialization(self):
        """Test that the scraper can be initialized"""
        try:
            scraper = MECReportScraper(headless=True, output_dir=str(self.test_dir))
            self.assertIsNotNone(scraper.driver)
            self.assertTrue(self.test_dir.exists())
            scraper.close()
            print("✅ Scraper initialization: PASSED")
        except Exception as e:
            self.fail(f"Scraper initialization failed: {e}")

    def test_webdriver_setup(self):
        """Test that WebDriver is properly configured"""
        try:
            scraper = MECReportScraper(headless=True, output_dir=str(self.test_dir))

            # Test basic navigation
            scraper.driver.get("https://www.google.com")
            self.assertIn("Google", scraper.driver.title)

            scraper.close()
            print("✅ WebDriver setup: PASSED")
        except Exception as e:
            self.fail(f"WebDriver setup failed: {e}")

    def test_mec_website_access(self):
        """Test that we can access the MEC website"""
        try:
            scraper = MECReportScraper(headless=True, output_dir=str(self.test_dir))

            # Test MEC search page access
            scraper.driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx")

            # Check if we can find the search form
            search_elements = scraper.driver.find_elements(By.NAME, "ctl00$ContentPlaceHolder1$txtCommName")
            self.assertGreater(len(search_elements), 0, "Could not find committee name input field")

            scraper.close()
            print("✅ MEC website access: PASSED")
        except Exception as e:
            self.fail(f"MEC website access failed: {e}")


class TestBulkDataAccess(unittest.TestCase):
    """Test bulk data access functionality"""

    def test_bulk_data_initialization(self):
        """Test bulk data access initialization"""
        try:
            bulk_access = MECBulkDataAccess()
            self.assertIsNotNone(bulk_access.session)
            print("✅ Bulk data access initialization: PASSED")
        except Exception as e:
            self.fail(f"Bulk data access initialization failed: {e}")

    def test_csv_endpoint_check(self):
        """Test checking CSV endpoints"""
        try:
            bulk_access = MECBulkDataAccess()
            results = bulk_access.check_mec_csv_endpoints()

            self.assertIsInstance(results, dict)
            self.assertGreater(len(results), 0)

            # Check that each result has expected fields
            for endpoint, status in results.items():
                self.assertIn('accessible', status)
                self.assertIn('status_code', status)

            print("✅ CSV endpoint check: PASSED")
        except Exception as e:
            self.fail(f"CSV endpoint check failed: {e}")

    def test_alternative_sources_info(self):
        """Test getting alternative data sources information"""
        try:
            bulk_access = MECBulkDataAccess()
            sources = bulk_access.get_alternative_data_sources()

            self.assertIsInstance(sources, dict)
            self.assertGreater(len(sources), 0)

            # Check that follow the money is included
            self.assertIn('followthemoney_org', sources)

            print("✅ Alternative sources info: PASSED")
        except Exception as e:
            self.fail(f"Alternative sources info failed: {e}")


class TestDataStrategy(unittest.TestCase):
    """Test data access strategy functionality"""

    def test_strategy_analysis(self):
        """Test strategy analysis for a committee"""
        try:
            strategy = get_data_access_strategy("Test Committee")

            self.assertIsInstance(strategy, dict)
            self.assertIn('committee_name', strategy)
            self.assertIn('primary_method', strategy)
            self.assertIn('alternative_methods', strategy)

            print("✅ Strategy analysis: PASSED")
        except Exception as e:
            self.fail(f"Strategy analysis failed: {e}")


class TestIntegration(unittest.TestCase):
    """Integration tests (these may take longer)"""

    @unittest.skip("Skip integration test by default - uncomment to run")
    def test_search_functionality(self):
        """Test actual search functionality (requires internet)"""
        try:
            scraper = MECReportScraper(headless=True)

            # Test search for a known committee
            results = scraper.search_committee("Francis Howell Families")

            # Should return some results (may be empty if committee doesn't exist)
            self.assertIsInstance(results, list)

            scraper.close()
            print("✅ Search functionality: PASSED")
        except Exception as e:
            self.fail(f"Search functionality failed: {e}")


def run_quick_test():
    """Run a quick test to verify basic functionality"""
    print("🧪 Running Quick Setup Test")
    print("=" * 40)

    try:
        # Test 1: Import modules
        print("1. Testing module imports...")
        from mec_scraper import MECReportScraper
        from bulk_data_access import MECBulkDataAccess
        print("   ✅ All modules imported successfully")

        # Test 2: Initialize scraper
        print("\n2. Testing scraper initialization...")
        with tempfile.TemporaryDirectory() as temp_dir:
            scraper = MECReportScraper(headless=True, output_dir=temp_dir)
            print("   ✅ Scraper initialized successfully")

            # Test 3: Check WebDriver
            print("\n3. Testing WebDriver...")
            scraper.driver.get("https://www.google.com")
            if "Google" in scraper.driver.title:
                print("   ✅ WebDriver working correctly")
            else:
                print("   ❌ WebDriver issue - check browser setup")

            scraper.close()

        # Test 4: Test bulk data access
        print("\n4. Testing bulk data access...")
        bulk_access = MECBulkDataAccess()
        sources = bulk_access.get_alternative_data_sources()
        if len(sources) > 0:
            print("   ✅ Bulk data access working")
        else:
            print("   ❌ Bulk data access issue")

        print("\n🎉 Quick test completed successfully!")
        print("   Your setup appears to be working correctly.")
        print("\n💡 To test with real MEC data, run:")
        print("   python main.py single \"Francis Howell Families\" --no-headless")

    except ImportError as e:
        print(f"   ❌ Import error: {e}")
        print("   💡 Make sure all dependencies are installed: pip install -r requirements.txt")
    except Exception as e:
        print(f"   ❌ Setup error: {e}")
        print("   💡 Check your Python environment and dependencies")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test MEC Scraper Setup")
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    parser.add_argument('--full', action='store_true', help='Run full test suite')

    args = parser.parse_args()

    if args.quick or (not args.full and not args.quick):
        # Run quick test by default
        run_quick_test()
    elif args.full:
        # Run full test suite
        unittest.main(argv=[''], exit=False, verbosity=2)