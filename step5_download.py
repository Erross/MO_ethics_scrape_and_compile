"""
Step 5: Simple Timing Approach
VERSION: 5.4 - Simple and reliable: Wait for generation complete + fixed time

The complex detection was failing. Let's use the simple approach:
1. Wait for "generating" text to disappear
2. Wait additional 10 seconds for PDF to render
3. Attempt download
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
    """Simple approach: Just wait for generation text to disappear"""
    print(f"      Waiting for generation to complete (max {max_wait}s)...")

    start_time = time.time()

    while (time.time() - start_time) < max_wait:
        try:
            elapsed = int(time.time() - start_time)

            # Check for generation indicators
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
                    print(f"        {elapsed}s: Still generating...")
                time.sleep(2)
                continue
            else:
                # Generation complete!
                print(f"        {elapsed}s: Generation complete!")
                return True

        except Exception as e:
            elapsed = int(time.time() - start_time)
            if elapsed % 15 == 0:
                print(f"        Error at {elapsed}s: {e}")
            time.sleep(2)

    print(f"      TIMEOUT: Generation did not complete in {max_wait}s")
    return False


def download_pdf_simple(downloads_dir, target_filename):
    """Simple PDF download using Ctrl+S"""
    try:
        print(f"      Attempting download: {target_filename}")

        # Open save dialog
        print(f"        Opening Save dialog...")
        pyautogui.hotkey('ctrl', 's')
        time.sleep(3)

        # Clear and type path
        print(f"        Typing filename...")
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.5)

        full_path = str(downloads_dir / target_filename)
        pyautogui.write(full_path, interval=0.03)
        time.sleep(2)

        # Save
        print(f"        Saving file...")
        pyautogui.press('enter')

        # Wait for file
        print(f"        Waiting for file creation...")
        for i in range(20):
            time.sleep(1)
            if (downloads_dir / target_filename).exists():
                file_size = (downloads_dir / target_filename).stat().st_size
                print(f"        SUCCESS: {file_size:,} bytes")
                return True, file_size
            if i % 5 == 0 and i > 0:
                print(f"          Still waiting... {i}s")

        print(f"        FAILED: File not created")
        return False, 0

    except Exception as e:
        print(f"        ERROR: {e}")
        return False, 0


def run_step_5_simple_timing():
    """Step 5: Simple timing approach"""

    downloads_dir = Path.cwd() / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    print("=== Step 5: Simple Timing Approach ===")
    print("Wait for generation complete + 10 seconds, then download")

    # Chrome setup - KEEP PDFs in browser
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--user-agent=Mozilla/5.0')

    # CRITICAL: Keep PDFs in Chrome viewer
    prefs = {
        "plugins.always_open_pdf_externally": False,
        "download.default_directory": str(downloads_dir)
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    stealth = EnhancedStealthBrowser(driver)

    try:
        # Navigate to reports (same as before)
        print("\n1-4. Navigating to reports...")
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        stealth.mimic_reading(1.5)

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

        results_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements("partial link text", "C2116")
        stealth.human_click(mecid_links[0])
        stealth.mimic_reading(2)

        reports_link = driver.find_element("link text", "Reports")
        stealth.human_click(reports_link)
        stealth.mimic_reading(2)

        # Expand 2025
        main_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
        expand_buttons = main_table.find_elements("css selector", "input[id*='ImgRptRight']")
        year_labels = main_table.find_elements("css selector", "span[id*='lblYear']")

        for i, label in enumerate(year_labels):
            if "2025" in label.text.strip() and i < len(expand_buttons):
                stealth.human_click(expand_buttons[i])
                break
        time.sleep(3)

        # Find reports
        print("5. Finding report links...")
        all_links = driver.find_elements("tag name", "a")
        report_links = []
        for link in all_links:
            link_text = link.text.strip()
            if link_text.isdigit() and len(link_text) >= 5:
                report_links.append(link)

        print(f"   Found {len(report_links)} report links")

        if not report_links:
            print("   ERROR: No reports found!")
            return False

        # Test with first report
        target_report = report_links[0]
        report_id = target_report.text.strip()
        target_filename = f"FHF_2025_Simple_{report_id}.pdf"

        print(f"6. Testing with report {report_id}")
        print(f"   Target: {target_filename}")

        # Click report
        print(f"7. Clicking report link...")
        original_window = driver.current_window_handle
        stealth.human_click(target_report)

        # Wait for new tab
        print(f"8. Waiting for new tab...")
        new_window = None
        for wait_time in range(1, 10):
            time.sleep(1)
            all_windows = driver.window_handles
            for window in all_windows:
                if window != original_window:
                    new_window = window
                    break
            if new_window:
                print(f"   New tab opened after {wait_time}s")
                break

        if not new_window:
            print("   ERROR: No new tab opened")
            return False

        # Switch to PDF tab
        print(f"9. Switching to PDF tab...")
        driver.switch_to.window(new_window)

        current_url = driver.current_url
        print(f"   URL: {current_url[:80]}...")

        # SIMPLE APPROACH: Wait for generation, then fixed time
        print(f"10. Waiting for generation to complete...")
        generation_done = wait_for_generation_complete_simple(driver, max_wait=60)

        if not generation_done:
            print("    Generation failed or timed out")
            driver.close()
            driver.switch_to.window(original_window)
            return False

        # FIXED WAIT: Additional time for PDF rendering
        render_wait = 10
        print(f"11. Generation complete! Waiting {render_wait}s for PDF rendering...")
        time.sleep(render_wait)

        # Attempt download
        print(f"12. Attempting download...")
        success, file_size = download_pdf_simple(downloads_dir, target_filename)

        # Cleanup
        driver.close()
        driver.switch_to.window(original_window)

        if success:
            print(f"\n✅ STEP 5 SUCCESS!")
            print(f"File: {target_filename}")
            print(f"Size: {file_size:,} bytes")

            # Quick validation
            if file_size > 5000:
                print(f"File size looks good - likely valid PDF")
                return True
            else:
                print(f"File size small - might be error page")
                return False
        else:
            print(f"\n❌ Download failed")
            return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        try:
            driver.quit()
        except:
            pass


if __name__ == "__main__":
    print("Step 5: Simple Timing Approach")
    print("=" * 40)
    print("No complex detection - just wait for generation + 10s")
    print("-" * 40)

    success = run_step_5_simple_timing()

    if success:
        print("\n🎉 SUCCESS! Ready to scale to multiple files")
    else:
        print("\n🔧 Still need debugging")