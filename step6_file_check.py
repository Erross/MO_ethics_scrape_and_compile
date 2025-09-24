"""
Step 6: File Existence Check
VERSION: 6.0 - Adds duplicate checking before downloads
⚠️  WARNING: THIS SCRIPT WILL ACTUALLY DOWNLOAD PDF FILES ⚠️

Based on step5_enhanced.py with file existence validation
- Uses browser automation to navigate MEC website
- Downloads PDFs using pyautogui (Ctrl+S method)
- Checks for existing files before downloading to avoid duplicates
- Limited to 3 downloads for testing (remove limit for production)
"""

import random
import time
import re
from pathlib import Path
import pyautogui

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager

class EnhancedStealthBrowser:
    """Helper class with human-like interactions"""

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def human_delay(self, min_seconds=0.5, max_seconds=2):
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)

    def human_click(self, element):
        self.actions.move_to_element(element).perform()
        self.human_delay(0.5, 1.2)
        element.click()
        self.human_delay(0.5, 1.2)

    def mimic_reading(self, duration_seconds=None):
        if duration_seconds is None:
            duration_seconds = random.uniform(1, 3)
        time.sleep(duration_seconds)


class FileExistenceChecker:
    """Handles file existence checking and filename generation"""

    def __init__(self, downloads_dir):
        self.downloads_dir = Path(downloads_dir)
        self.downloads_dir.mkdir(exist_ok=True)

    def extract_report_metadata(self, driver, report_link):
        """
        Extract metadata from the report table row to generate filename
        Returns: dict with report_id, report_type, date_filed, year
        """
        try:
            # Get report ID from the link text
            report_id = report_link.text.strip()

            # Find the parent row to extract other metadata
            parent_row = report_link.find_element(By.XPATH, "./ancestor::tr[1]")
            cells = parent_row.find_elements(By.TAG_NAME, "td")

            metadata = {
                'report_id': report_id,
                'report_type': 'Unknown_Report',
                'date_filed': 'Unknown_Date',
                'year': '2025'  # Default year
            }

            # Extract report type and date from table cells
            for cell in cells:
                cell_text = cell.text.strip()

                # Look for date patterns (MM/DD/YYYY or MM-DD-YYYY)
                date_match = re.search(r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})', cell_text)
                if date_match:
                    date_str = date_match.group(1)
                    # Convert to consistent format
                    date_str = date_str.replace('/', '-')
                    metadata['date_filed'] = date_str
                    # Extract year
                    year_match = re.search(r'(\d{4})', date_str)
                    if year_match:
                        metadata['year'] = year_match.group(1)

                # Look for report type (contains "Report" or "Amendment")
                if 'report' in cell_text.lower() or 'amendment' in cell_text.lower():
                    # Clean up report type for filename
                    report_type = cell_text.strip()
                    # Remove extra whitespace and replace spaces with underscores
                    report_type = re.sub(r'\s+', '_', report_type)
                    # Remove special characters except underscores and hyphens
                    report_type = re.sub(r'[^\w\-_]', '', report_type)
                    metadata['report_type'] = report_type

            print(f"Extracted metadata: {metadata}")
            return metadata

        except Exception as e:
            print(f"Error extracting metadata: {e}")
            return {
                'report_id': report_link.text.strip(),
                'report_type': 'Unknown_Report',
                'date_filed': 'Unknown_Date',
                'year': '2025'
            }

    def generate_filename(self, committee_name, metadata):
        """
        Generate filename using the naming convention:
        Francis_Howell_Families_[YEAR]_[REPORT_TYPE]_[DATE]_[ID].pdf
        """
        # Clean committee name
        clean_committee = re.sub(r'\s+', '_', committee_name.strip())
        clean_committee = re.sub(r'[^\w\-_]', '', clean_committee)

        filename = f"{clean_committee}_{metadata['year']}_{metadata['report_type']}_{metadata['date_filed']}_{metadata['report_id']}.pdf"
        return filename

    def file_exists(self, filename):
        """Check if file already exists in downloads directory"""
        file_path = self.downloads_dir / filename
        exists = file_path.exists()
        if exists:
            file_size = file_path.stat().st_size
            print(f"File exists: {filename} ({file_size:,} bytes)")
        return exists

    def get_existing_files(self):
        """Get list of existing PDF files in downloads directory"""
        existing_files = list(self.downloads_dir.glob("*.pdf"))
        return [f.name for f in existing_files]


def download_pdf_with_save_as(stealth, downloads_dir, target_filename):
    """
    🚨 ACTUAL DOWNLOAD FUNCTION 🚨
    Downloads PDF using pyautogui Save-As dialog

    This function WILL:
    1. Wait for PDF to load in browser
    2. Press Ctrl+S to open Save dialog
    3. Type the full file path
    4. Press Enter to save the file
    5. Wait for download completion

    Returns True if successful, False otherwise
    """
    try:
        print(f"🚨 STARTING ACTUAL DOWNLOAD: {target_filename}")

        # Wait for PDF to load
        time.sleep(5)

        # Use Ctrl+S to open Save-As dialog
        print("  → Pressing Ctrl+S to open Save dialog...")
        pyautogui.hotkey('ctrl', 's')
        time.sleep(2)

        # Clear filename field and type target filename
        print("  → Typing filename...")
        pyautogui.hotkey('ctrl', 'a')  # Select all
        time.sleep(0.5)

        # Type the full path
        full_path = str(downloads_dir / target_filename)
        pyautogui.typewrite(full_path, interval=0.05)
        time.sleep(1)

        # Press Enter to save
        print("  → Pressing Enter to save...")
        pyautogui.press('enter')
        time.sleep(2)

        # Wait for download to complete (check for file existence)
        print("  → Waiting for download to complete...")
        max_wait = 30
        wait_time = 0
        while wait_time < max_wait:
            if (downloads_dir / target_filename).exists():
                file_size = (downloads_dir / target_filename).stat().st_size
                if file_size > 1000:  # File is substantial
                    print(f"✅ DOWNLOAD SUCCESSFUL: {target_filename} ({file_size:,} bytes)")
                    return True
            time.sleep(1)
            wait_time += 1

        print(f"❌ DOWNLOAD FAILED or TIMED OUT: {target_filename}")
        return False

    except Exception as e:
        print(f"❌ ERROR DURING DOWNLOAD: {e}")
        return False


def run_step_6_with_file_check():
    """
    🚨 MAIN FUNCTION - WILL DOWNLOAD ACTUAL PDF FILES 🚨

    This function will:
    1. Open Chrome browser
    2. Navigate to MEC website
    3. Search for Francis Howell Families committee
    4. Find 2025 reports
    5. Check which files already exist
    6. DOWNLOAD PDFs that don't exist (limited to 3 for testing)
    """
    downloads_dir = Path.cwd() / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    # Initialize file checker
    file_checker = FileExistenceChecker(downloads_dir)

    print("🚨 === MEC PDF Scraper - Step 6: WILL DOWNLOAD FILES === 🚨")
    print(f"Downloads directory: {downloads_dir.absolute()}")
    print("⚠️  This script WILL download PDF files to your computer!")
    print("⚠️  Press Ctrl+C now if you don't want to download files.")

    # 5 second warning
    for i in range(5, 0, -1):
        print(f"Starting in {i} seconds...")
        time.sleep(1)

    # Show existing files
    existing_files = file_checker.get_existing_files()
    print(f"Existing files in directory: {len(existing_files)}")
    for f in existing_files[:5]:  # Show first 5
        print(f"  - {f}")
    if len(existing_files) > 5:
        print(f"  ... and {len(existing_files) - 5} more")

    # Chrome setup
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--user-agent=Mozilla/5.0')

    # Disable automatic PDF downloads so Save-As dialog appears
    prefs = {
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    stealth = EnhancedStealthBrowser(driver)

    try:
        # Navigate to search page
        print("🌐 Navigating to MEC search page...")
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        stealth.mimic_reading(1.5)

        # Search for committee
        print("🔍 Searching for 'Francis Howell Families'...")
        wait = WebDriverWait(driver, 10)
        committee_input = wait.until(EC.presence_of_element_located(("name", "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm")))
        committee_input.clear()
        for c in "Francis Howell Families":
            committee_input.send_keys(c)
            time.sleep(random.uniform(0.05,0.15))
        stealth.human_delay(1,2)

        search_button = driver.find_element("name", "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
        stealth.human_click(search_button)
        stealth.mimic_reading(2)

        # Open committee page
        print("📋 Opening committee page...")
        results_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements("partial link text", "C2116")
        stealth.human_click(mecid_links[0])
        stealth.mimic_reading(2)

        # Go to Reports tab
        print("📊 Navigating to Reports tab...")
        reports_link = driver.find_element("link text", "Reports")
        stealth.human_click(reports_link)
        stealth.mimic_reading(2)

        # Expand 2025 section
        print("📅 Expanding 2025 reports section...")
        main_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
        expand_buttons = main_table.find_elements("css selector", "input[id*='ImgRptRight']")
        year_labels = main_table.find_elements("css selector", "span[id*='lblYear']")

        # Find and click 2025 expand button
        for i, label in enumerate(year_labels):
            if "2025" in label.text:
                print(f"Found 2025 section at index {i}")
                stealth.human_click(expand_buttons[i])
                stealth.mimic_reading(3)
                break

        # Find all report links in 2025 section
        print("🔗 Finding report links...")
        time.sleep(2)

        # Look for report links (numeric IDs)
        report_links = driver.find_elements("css selector", "a[href*='RptViewer.aspx']")
        print(f"Found {len(report_links)} report links")

        # Process each report
        committee_name = "Francis Howell Families"
        downloads_attempted = 0
        downloads_successful = 0
        files_skipped = 0

        for i, report_link in enumerate(report_links):
            print(f"\n--- Processing Report {i+1}/{len(report_links)} ---")

            # Extract metadata for this report
            metadata = file_checker.extract_report_metadata(driver, report_link)

            # Generate filename
            target_filename = file_checker.generate_filename(committee_name, metadata)
            print(f"Target filename: {target_filename}")

            # Check if file already exists
            if file_checker.file_exists(target_filename):
                print(f"✅ SKIPPING: File already exists - {target_filename}")
                files_skipped += 1
                continue

            print(f"🚨 WILL DOWNLOAD: {target_filename}")
            downloads_attempted += 1

            # Click report link to open PDF
            original_window = driver.current_window_handle
            stealth.human_click(report_link)
            stealth.mimic_reading(2)

            # Handle new window/tab
            all_windows = driver.window_handles
            if len(all_windows) > 1:
                # Switch to new window
                for window in all_windows:
                    if window != original_window:
                        driver.switch_to.window(window)
                        break

                # 🚨 ACTUAL DOWNLOAD HAPPENS HERE 🚨
                success = download_pdf_with_save_as(stealth, downloads_dir, target_filename)

                if success:
                    downloads_successful += 1
                    print(f"✅ SUCCESS: Downloaded {target_filename}")
                else:
                    print(f"❌ FAILED: Could not download {target_filename}")

                # Close PDF window and return to main window
                driver.close()
                driver.switch_to.window(original_window)
                stealth.mimic_reading(1)

            # 🚨 TESTING LIMIT - REMOVE FOR PRODUCTION 🚨
            if downloads_attempted >= 3:
                print(f"\n⚠️ TESTING LIMIT: Stopping at 3 downloads")
                print(f"   Remove this limit for production use!")
                break

        # Summary
        print(f"\n=== DOWNLOAD SUMMARY ===")
        print(f"Total reports found: {len(report_links)}")
        print(f"Files skipped (already exist): {files_skipped}")
        print(f"Downloads attempted: {downloads_attempted}")
        print(f"Downloads successful: {downloads_successful}")
        print(f"Downloads failed: {downloads_attempted - downloads_successful}")

        # Show final directory contents
        final_files = file_checker.get_existing_files()
        print(f"\nFinal directory contents: {len(final_files)} files")

    except Exception as e:
        print(f"❌ ERROR DURING EXECUTION: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("🔒 Browser closed.")


if __name__ == "__main__":
    print("🚨" * 20)
    print("⚠️  WARNING: This script WILL download PDF files!")
    print("⚠️  It will save files to ./downloads/ directory")
    print("⚠️  Limited to 3 downloads for testing")
    print("🚨" * 20)

    response = input("\nDo you want to proceed with downloads? (yes/no): ").lower().strip()
    if response in ['yes', 'y']:
        run_step_6_with_file_check()
    else:
        print("❌ Download cancelled by user.")