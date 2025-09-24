"""
Step 4: Expand a Specific Year Section and Find Reports
Builds on Steps 1-3 success, adds year expansion with continued anti-detection

VERSION: 1.0 - Controlled Expansion
"""

import random
import time
from selenium.webdriver.common.action_chains import ActionChains


class StealthBrowser:
    """Helper class for human-like browser interactions"""

    def __init__(self, driver):
        self.driver = driver
        self.actions = ActionChains(driver)

    def human_delay(self, min_seconds=1, max_seconds=3):
        """Random delay to mimic human reading/thinking time"""
        delay = random.uniform(min_seconds, max_seconds)
        print(f"   [Thinking for {delay:.1f}s...]")
        time.sleep(delay)

    def slow_scroll_to_element(self, element):
        """Slowly scroll to an element like a human would"""
        print("   [Scrolling to element...]")
        self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth'});", element)
        time.sleep(random.uniform(1, 2))

    def human_click(self, element):
        """Click an element with human-like behavior"""
        print("   [Moving to element and clicking...]")

        # Move mouse to element first
        self.actions.move_to_element(element).perform()
        self.human_delay(0.5, 1.2)

        # Click
        element.click()
        self.human_delay(0.8, 1.5)

    def mimic_reading(self, duration_seconds=None):
        """Mimic human reading behavior with time delays"""
        if duration_seconds is None:
            duration_seconds = random.uniform(2, 5)

        print(f"   [Reading page for {duration_seconds:.1f}s...]")
        time.sleep(duration_seconds)


def run_steps_1_2_3_4():
    """Run Steps 1-4: Get to reports page and expand 2025 section"""

    print("=== STEPS 1-4: EXPAND YEAR SECTION ===")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager

        # Stealth browser setup
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        chrome_options.add_argument('--window-size=1366,768')
        chrome_options.add_argument(
            '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        stealth = StealthBrowser(driver)

        # STEPS 1-3: Get to reports page (we know this works)
        print("STEPS 1-3: Getting to reports page...")

        # Step 1: Search
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        stealth.mimic_reading(2)

        wait = WebDriverWait(driver, 10)
        committee_input = wait.until(
            EC.presence_of_element_located((By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm"))
        )

        committee_input.clear()
        for char in "Francis Howell Families":
            committee_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        stealth.human_delay(1, 2)

        search_button = driver.find_element(By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
        stealth.human_click(search_button)
        stealth.mimic_reading(2)

        # Click MECID
        results_table = driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements(By.PARTIAL_LINK_TEXT, "C2116")
        stealth.human_click(mecid_links[0])

        # Step 2: Reports tab
        stealth.mimic_reading(2)
        reports_link = driver.find_element(By.LINK_TEXT, "Reports")
        stealth.human_click(reports_link)
        stealth.mimic_reading(3)

        print("   ✓ Steps 1-3 complete")

        # STEP 4: Expand year section
        print("\nSTEP 4: Expanding 2025 year section...")

        # Find the main reports table
        main_table = driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
        stealth.slow_scroll_to_element(main_table)
        stealth.mimic_reading(2)

        # Find expand buttons and year labels
        expand_buttons = main_table.find_elements(By.CSS_SELECTOR, "input[id*='ImgRptRight']")
        year_labels = main_table.find_elements(By.CSS_SELECTOR, "span[id*='lblYear']")

        print(f"   Found {len(expand_buttons)} expand buttons")
        print(f"   Found {len(year_labels)} year labels")

        # Find 2025 section
        target_expand_button = None
        for i, year_label in enumerate(year_labels):
            year_text = year_label.text.strip()
            print(f"   Year label {i}: '{year_text}'")

            if "2025" in year_text:
                if i < len(expand_buttons):
                    target_expand_button = expand_buttons[i]
                    print(f"   ✓ Found 2025 expand button at index {i}")
                    break

        if target_expand_button:
            print("   Expanding 2025 section...")

            # Scroll to the expand button
            stealth.slow_scroll_to_element(target_expand_button)
            stealth.human_delay(1, 2)

            # Click the expand button
            stealth.human_click(target_expand_button)

            # Wait for content to load
            print("   [Waiting for 2025 reports to load...]")
            time.sleep(5)  # Give time for dynamic content to load

            # STEP 4 VERIFICATION: Look for individual reports
            print("\n   STEP 4 VERIFICATION: Looking for individual reports...")

            try:
                # Look for report links that are now visible
                # Based on project knowledge, these should be numeric links or btn-link class

                # Method 1: Look for numeric links (report IDs)
                all_links = driver.find_elements(By.TAG_NAME, "a")
                numeric_links = [link for link in all_links if link.text.strip().isdigit()]

                print(f"   Found {len(numeric_links)} numeric links (potential reports)")

                # Show first few numeric links
                for i, link in enumerate(numeric_links[:5]):
                    link_text = link.text.strip()
                    print(f"     Report {i + 1}: {link_text}")

                # Method 2: Look for btn-link class elements
                btn_links = driver.find_elements(By.CSS_SELECTOR, "a.btn-link")
                print(f"   Found {len(btn_links)} btn-link elements")

                # Method 3: Look for Generator.aspx links (PDF generation)
                generator_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='Generator.aspx']")
                print(f"   Found {len(generator_links)} Generator.aspx links")

                if numeric_links or btn_links or generator_links:
                    print("\n   🎉 STEP 4 SUCCESS! 🎉")
                    print(f"   Successfully expanded 2025 and found {len(numeric_links)} potential reports")
                    print("   Ready for Step 5: Click on a specific report")

                    # Show some examples of what we found
                    if numeric_links:
                        print(f"   Example report IDs: {[link.text.strip() for link in numeric_links[:3]]}")

                else:
                    print("   ? Expanded 2025 but no report links found yet")
                    print("   May need more time for content to load")

            except Exception as e:
                print(f"   Error verifying reports: {e}")

        else:
            print("   ✗ Could not find 2025 expand button")

            # Show what year labels we did find
            print("   Available year labels:")
            for i, label in enumerate(year_labels):
                print(f"     {i}: '{label.text.strip()}'")

        # Keep browser open for inspection
        print(f"\nKeeping browser open for 20 seconds...")
        print("You should now see the 2025 section expanded with individual reports")
        time.sleep(20)

        driver.quit()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("Step 4: Expand Year Section")
    print("=" * 40)
    print("Goal: Expand 2025 section and find individual reports")
    print("-" * 40)

    success = run_steps_1_2_3_4()

    if success:
        print("\n✅ STEP 4 COMPLETE")
        print("Ready for Step 5: Click specific report and download")
    else:
        print("\n❌ STEP 4 FAILED")