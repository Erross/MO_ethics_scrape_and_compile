"""
Step 3: Fixed Stealth Version - Simplified anti-detection without problematic mouse movements
"""

import random
import time
from selenium.webdriver.common.action_chains import ActionChains


class StealthBrowser:
    """Helper class for human-like browser interactions - fixed version"""

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
        print("   [Clicking element...]")

        # Move mouse to element first (without problematic offset movements)
        self.actions.move_to_element(element).perform()
        self.human_delay(0.5, 1.2)

        # Click
        element.click()
        self.human_delay(0.8, 1.5)

    def mimic_reading(self, duration_seconds=None):
        """Mimic human reading behavior with just time delays"""
        if duration_seconds is None:
            duration_seconds = random.uniform(2, 5)

        print(f"   [Reading page for {duration_seconds:.1f}s...]")
        time.sleep(duration_seconds)


def run_steps_1_2_3_fixed():
    """Fixed version with simplified stealth measures"""

    print("=== FIXED STEALTH MODE: STEPS 1 + 2 + 3 ===")

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
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Remove automation indicators
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        stealth = StealthBrowser(driver)

        # STEP 1: Search (with stealth)
        print("\nSTEP 1: Searching for committee...")

        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        stealth.mimic_reading(3)

        wait = WebDriverWait(driver, 10)
        committee_input = wait.until(
            EC.presence_of_element_located((By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm"))
        )

        stealth.slow_scroll_to_element(committee_input)
        stealth.human_delay(1, 2)

        committee_input.clear()
        # Type slowly
        for char in "Francis Howell Families":
            committee_input.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))

        stealth.human_delay(1, 2)

        search_button = driver.find_element(By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
        stealth.human_click(search_button)

        stealth.mimic_reading(3)

        # Click MECID
        results_table = driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements(By.PARTIAL_LINK_TEXT, "C2116")
        stealth.human_click(mecid_links[0])

        print("   ✓ Step 1 complete")

        # STEP 2: Reports tab
        print("\nSTEP 2: Navigating to Reports...")

        stealth.mimic_reading(3)

        reports_link = driver.find_element(By.LINK_TEXT, "Reports")
        stealth.slow_scroll_to_element(reports_link)
        stealth.human_click(reports_link)

        stealth.mimic_reading(4)
        print("   ✓ Step 2 complete")

        # STEP 3: Find year sections
        print("\nSTEP 3: Analyzing reports page structure...")

        stealth.mimic_reading(2)  # "Read" the reports page

        # Look for year content
        page_source = driver.page_source
        years_found = []
        for year in ['2025', '2024', '2023', '2022', '2021']:
            if year in page_source:
                years_found.append(year)

        print(f"   Years found: {years_found}")

        # Look for expand-type elements
        expand_elements_found = 0
        expand_selectors = [
            "input[id*='Img'][id*='Right']",  # Based on your project HTML
            "input[type='image']",
            "span[id*='lblYear']",
            "span.year-span"
        ]

        for selector in expand_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"   Found {len(elements)} elements: {selector}")
                    expand_elements_found += len(elements)
            except:
                pass

        # Look for the main reports table
        try:
            main_table = driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
            print("   ✓ Found main reports table")
        except:
            print("   ? Main reports table not found")

        print(f"\n   STEP 3 ANALYSIS COMPLETE:")
        print(f"   - Years detected: {len(years_found)}")
        print(f"   - Expand elements: {expand_elements_found}")
        print("   - Ready to attempt expansion in Step 4")

        # Manual inspection time
        print("\nKeeping browser open for manual inspection...")
        print("Look for year sections and expand buttons")
        time.sleep(15)

        driver.quit()
        return True

    except Exception as e:
        print(f"ERROR: {e}")
        return False


if __name__ == "__main__":
    print("Step 3: Fixed Stealth Version")
    print("=" * 40)

    success = run_steps_1_2_3_fixed()

    if success:
        print("\n✅ FIXED STEALTH VERSION WORKED")
        print("Ready for Step 4: Expand year sections")
    else:
        print("\n❌ Still failed - need more debugging")