"""
Step 1: Fixed - Click on MECID link instead of committee name
"""

def search_and_select_committee_fixed():
    print("=== STEP 1: FIXED VERSION ===")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        from webdriver_manager.chrome import ChromeDriverManager
        import time

        # Setup browser
        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        print("1. Going to MEC search page...")
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        time.sleep(3)

        print("2. Filling search form...")
        wait = WebDriverWait(driver, 10)
        committee_input = wait.until(
            EC.presence_of_element_located((By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm"))
        )
        committee_input.clear()
        committee_input.send_keys("Francis Howell Families")

        search_button = driver.find_element(By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
        search_button.click()
        time.sleep(4)

        print("3. Looking for results...")
        results_table = driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        print("   ✓ Found results table")

        print("4. Looking for MECID link (not committee name)...")
        # Look for the MECID link - it should be "C211676"
        mecid_links = results_table.find_elements(By.PARTIAL_LINK_TEXT, "C2116")

        if mecid_links:
            mecid_link = mecid_links[0]  # Take the first one
            mecid_text = mecid_link.text
            print(f"   ✓ Found MECID link: '{mecid_text}'")

            print("5. Clicking on MECID link...")
            mecid_link.click()
            time.sleep(3)

            # Check if we're on committee page
            current_url = driver.current_url
            print(f"   Current URL: {current_url}")

            if "CommInfo.aspx" in current_url and "C211676" in current_url:
                print("   ✓ Successfully navigated to Francis Howell Families committee page!")

                print("\n🎉 STEP 1 SUCCESS! 🎉")
                print("Ready for Step 2: Navigate to Reports tab")

                print("\nKeeping browser open for 10 seconds so you can see the committee page...")
                time.sleep(10)

                driver.quit()
                return True
            else:
                print("   ✗ Not on expected committee page")
        else:
            print("   ✗ Could not find MECID link starting with 'C2116'")
            # Fallback: look for any links that start with 'C'
            all_links = results_table.find_elements(By.TAG_NAME, "a")
            print("   Available links:")
            for link in all_links:
                link_text = link.text.strip()
                if link_text.startswith('C'):
                    print(f"     - {link_text}")

        print("\nKeeping browser open for debugging...")
        time.sleep(15)
        driver.quit()
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing Step 1: Fixed Version")
    print("=" * 40)

    success = search_and_select_committee_fixed()

    if success:
        print("\n✅ STEP 1 COMPLETE - Ready for Step 2!")
    else:
        print("\n❌ STEP 1 FAILED - Need to debug")