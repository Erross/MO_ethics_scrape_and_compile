"""
Step 6: Download 3 Files
VERSION: 6.0 - Scales up the working Step 5 approach to handle 3 reports

Uses the proven simple timing approach that worked in Step 5
"""

import random
import time
import pyautogui
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from webdriver_manager.chrome import ChromeDriverManager


class EnhancedStealthBrowser:
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


def wait_for_generation_complete_simple(driver, max_wait=60):
    """Wait for generation to complete - proven approach from Step 5"""
    print(f"        Waiting for generation (max {max_wait}s)...")

    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        try:
            elapsed = int(time.time() - start_time)

            page_source = driver.page_source.lower()
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()

            generation_indicators = [
                "generating report",
                "this may take several minutes",
                "% completed",
                "gathering the required information"
            ]

            still_generating = any(indicator in page_source or indicator in page_text
                                   for indicator in generation_indicators)

            if still_generating:
                if elapsed % 10 == 0:
                    print(f"          {elapsed}s: Still generating...")
                time.sleep(2)
                continue
            else:
                print(f"          {elapsed}s: Generation complete!")
                return True

        except Exception as e:
            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0:
                print(f"          Error at {elapsed}s: {e}")
            time.sleep(2)

    print(f"        TIMEOUT: Generation did not complete in {max_wait}s")
    return False


def download_pdf_simple(downloads_dir, target_filename):
    """Simple PDF download - proven approach from Step 5"""
    try:
        print(f"        Downloading: {target_filename}")

        pyautogui.hotkey('ctrl', 's')
        time.sleep(3)

        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)

        full_path = str(downloads_dir / target_filename)
        pyautogui.write(full_path, interval=0.03)
        time.sleep(2)

        pyautogui.press('enter')

        # Wait for file
        for i in range(20):
            time.sleep(1)
            if (downloads_dir / target_filename).exists():
                file_size = (downloads_dir / target_filename).stat().st_size
                print(f"          SUCCESS: {file_size:,} bytes")
                return True, file_size

        print(f"          FAILED: File not created")
        return False, 0

    except Exception as e:
        print(f"          ERROR: {e}")
        return False, 0


def download_single_report(driver, stealth, report_link, downloads_dir, report_num, total_reports):
    """Download a single report using proven Step 5 approach"""

    report_id = report_link.text.strip()
    target_filename = f"FHF_2025_Step6_{report_id}.pdf"

    print(f"\n  --- Report {report_num}/{total_reports}: {report_id} ---")
    print(f"      Target: {target_filename}")

    # Check if already exists
    if (downloads_dir / target_filename).exists():
        existing_size = (downloads_dir / target_filename).stat().st_size
        print(f"      SKIP: File exists ({existing_size:,} bytes)")
        return True, existing_size

    try:
        original_window = driver.current_window_handle

        # Click report
        print(f"      Clicking report link...")
        stealth.human_click(report_link)

        # Wait for new tab
        new_window = None
        for wait_time in range(1, 10):
            time.sleep(1)
            all_windows = driver.window_handles
            for window in all_windows:
                if window != original_window:
                    new_window = window
                    break
            if new_window:
                print(f"        New tab opened after {wait_time}s")
                break

        if not new_window:
            print(f"        ERROR: No new tab opened")
            return False, 0

        # Switch to PDF tab
        driver.switch_to.window(new_window)

        # Wait for generation complete
        generation_done = wait_for_generation_complete_simple(driver, max_wait=60)

        if not generation_done:
            print(f"        ERROR: Generation failed")
            driver.close()
            driver.switch_to.window(original_window)
            return False, 0

        # Wait for rendering
        render_wait = 10
        print(f"        Waiting {render_wait}s for PDF rendering...")
        time.sleep(render_wait)

        # Download
        success, file_size = download_pdf_simple(downloads_dir, target_filename)

        # Clean up
        driver.close()
        driver.switch_to.window(original_window)

        if success:
            print(f"      SUCCESS: Downloaded {target_filename}")
        else:
            print(f"      FAILED: Could not download {target_filename}")

        return success, file_size

    except Exception as e:
        print(f"      ERROR: {e}")
        try:
            driver.switch_to.window(original_window)
        except:
            pass
        return False, 0


def run_step_6_three_files():
    """Step 6: Download 3 files using proven Step 5 approach"""

    downloads_dir = Path.cwd() / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    print("=== Step 6: Download 3 Files ===")
    print("Using proven Step 5 timing approach")
    print("Will download 3 reports with progress tracking")

    # Chrome setup - same as working Step 5
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--user-agent=Mozilla/5.0')

    prefs = {
        "plugins.always_open_pdf_externally": False,
        "download.default_directory": str(downloads_dir)
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    stealth = EnhancedStealthBrowser(driver)

    try:
        # Navigate to reports (same as Step 5)
        print("\n1. Navigating to Francis Howell Families reports...")
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        stealth.mimic_reading(1.5)

        wait = WebDriverWait(driver, 10)
        committee_input = wait.until(
            EC.presence_of_element_located(("name", "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm")))
        committee_input.clear()
        for c in "Francis Howell Families":
            committee_input.send_keys(c)
            time.sleep(random.uniform(0.05, 0.15))
        stealth.human_delay(1, 2)

        search_button = driver.find_element("name", "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
        stealth.human_click(search_button)
        stealth.mimic_reading(2)

        results_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements("partial link text", "C2116")
        stealth.human_click(mecid_links[0])
        stealth.mimic_reading(2)

        reports_link = driver.find_element("link text", "Reports")
        stealth.human_click(reports_link)
        stealth.mimic_reading(2)

        # Expand 2025
        print("2. Expanding 2025 section...")
        main_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
        expand_buttons = main_table.find_elements("css selector", "input[id*='ImgRptRight']")
        year_labels = main_table.find_elements("css selector", "span[id*='lblYear']")

        for i, label in enumerate(year_labels):
            if "2025" in label.text.strip() and i < len(expand_buttons):
                stealth.human_click(expand_buttons[i])
                break
        time.sleep(3)

        # Find reports
        print("3. Finding report links...")
        all_links = driver.find_elements("tag name", "a")
        report_links = []
        for link in all_links:
            link_text = link.text.strip()
            if link_text.isdigit() and len(link_text) >= 5:
                report_links.append(link)

        print(f"   Found {len(report_links)} total report links")

        if len(report_links) < 3:
            print(f"   WARNING: Only found {len(report_links)} reports, will download all available")

        # Download up to 3 reports
        target_count = min(3, len(report_links))
        print(f"4. Will attempt to download {target_count} reports")

        successful_downloads = 0
        failed_downloads = 0
        total_size = 0

        for i in range(target_count):
            report_link = report_links[i]

            success, file_size = download_single_report(
                driver, stealth, report_link, downloads_dir, i + 1, target_count
            )

            if success:
                successful_downloads += 1
                total_size += file_size
            else:
                failed_downloads += 1

            # Pause between downloads
            if i < target_count - 1:
                pause_time = 3
                print(f"      Pausing {pause_time}s before next download...")
                time.sleep(pause_time)

        # Final summary
        print(f"\n=== STEP 6 SUMMARY ===")
        print(f"Reports attempted: {target_count}")
        print(f"Successful downloads: {successful_downloads}")
        print(f"Failed downloads: {failed_downloads}")
        print(f"Total data downloaded: {total_size:,} bytes")

        # List final files
        step6_files = list(downloads_dir.glob("FHF_2025_Step6_*.pdf"))
        print(f"\nStep 6 files in directory:")
        for f in step6_files:
            size = f.stat().st_size
            print(f"  {f.name} ({size:,} bytes)")

        success_rate = (successful_downloads / target_count) * 100 if target_count > 0 else 0

        if successful_downloads >= 2:
            print(f"\nSUCCESS: Downloaded {successful_downloads}/{target_count} files ({success_rate:.0f}%)")
            print("Ready for Step 7: Process all reports in 2025")
            return True
        else:
            print(f"\nPARTIAL SUCCESS: Only {successful_downloads}/{target_count} downloads succeeded")
            return False

    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            driver.quit()
        except:
            pass
        print("Browser closed.")


if __name__ == "__main__":
    print("Step 6: Download 3 Files")
    print("=" * 30)

    success = run_step_6_three_files()

    if success:
        print("\nStep 6 COMPLETE - Ready for Step 7!")
    else:
        print("\nStep 6 needs debugging")