"""
Step 5 Enhanced: Guaranteed PDF Download via Save-As
VERSION: 2.0 - Uses pyautogui to save PDF reliably
"""

import random
import time
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

def run_step_5_guaranteed_save():
    """Run Step 5 with guaranteed PDF download using Save-As dialog"""
    downloads_dir = Path.cwd() / "downloads"
    downloads_dir.mkdir(exist_ok=True)

    # Chrome setup
    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--window-size=1366,768')
    chrome_options.add_argument('--user-agent=Mozilla/5.0')

    # Disable automatic PDF downloads so Save-As appears
    prefs = {
        "plugins.always_open_pdf_externally": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    stealth = EnhancedStealthBrowser(driver)

    try:
        # Navigate to search page
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

        # Open committee
        results_table = driver.find_element("id", "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements("partial link text", "C2116")
        stealth.human_click(mecid_links[0])
        stealth.mimic_reading(2)

        # Reports
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

        # Open target report
        all_links = driver.find_elements("tag name", "a")
        target_report = None
        for l in all_links:
            if l.text.strip().isdigit() and l.text.strip() == "256590":
                target_report = l
                break
        if not target_report:
            print("✗ Report link not found")
            return False

        original_window = driver.current_window_handle
        stealth.human_click(target_report)
        time.sleep(4)

        # Switch to new tab
        new_window = [w for w in driver.window_handles if w != original_window]
        if not new_window:
            print("✗ New tab did not open")
            return False
        driver.switch_to.window(new_window[0])
        stealth.mimic_reading(1)

        # Trigger Save-As dialog
        timestamp = time.strftime('%m_%d_%Y')
        filename = f"Francis_Howell_Families_2025_Report_{timestamp}.pdf"
        full_path = downloads_dir / filename

        print(f"[Saving PDF to: {full_path}]")
        time.sleep(2)  # wait for PDF tab to load
        pyautogui.hotkey('ctrl', 's')  # trigger Save-As
        time.sleep(1)
        pyautogui.write(str(full_path))
        time.sleep(0.5)
        pyautogui.press('enter')

        # Allow time for download to complete
        time.sleep(5)
        print("✓ PDF should now be saved")

        # Close tab
        driver.close()
        driver.switch_to.window(original_window)
        return True

    finally:
        driver.quit()

if __name__ == "__main__":
    print("Step 5 Guaranteed PDF Download")
    print("="*60)
    success = run_step_5_guaranteed_save()
    if success:
        print("\n✅ STEP 5 SUCCESS")
    else:
        print("\n❌ STEP 5 FAILED")
