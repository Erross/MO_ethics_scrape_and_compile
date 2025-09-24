"""
Step 2: Navigate to Reports Tab
Builds on Step 1 success - finds and clicks the Reports tab on the committee page

VERSION: 1.0 - Foundation Step 2
"""


def run_step1_and_step2():
    """Run Step 1 (search committee) then Step 2 (navigate to Reports tab)"""

    print("=== RUNNING STEP 1 + STEP 2 ===")

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

        # STEP 1: Get to committee page (we know this works)
        print("STEP 1: Getting to committee page...")
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0")
        time.sleep(3)

        # Fill search form
        wait = WebDriverWait(driver, 10)
        committee_input = wait.until(
            EC.presence_of_element_located((By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm"))
        )
        committee_input.clear()
        committee_input.send_keys("Francis Howell Families")

        search_button = driver.find_element(By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
        search_button.click()
        time.sleep(4)

        # Click MECID link
        results_table = driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_gvResults")
        mecid_links = results_table.find_elements(By.PARTIAL_LINK_TEXT, "C2116")
        mecid_links[0].click()
        time.sleep(3)

        # Verify we're on committee page
        current_url = driver.current_url
        if "CommInfo.aspx" in current_url and "C211676" in current_url:
            print("   ✓ Step 1 complete - on committee page")
        else:
            print("   ✗ Step 1 failed - not on committee page")
            driver.quit()
            return False

        # STEP 2: Navigate to Reports tab
        print("\nSTEP 2: Looking for Reports tab...")

        # Method 1: Look for link with text "Reports"
        try:
            reports_link = driver.find_element(By.LINK_TEXT, "Reports")
            print("   ✓ Found Reports link (method 1)")

            print("   Clicking Reports tab...")
            reports_link.click()
            time.sleep(3)

            # Check if we're on reports page
            current_url = driver.current_url
            print(f"   Current URL: {current_url}")

            # Look for indicators that we're on reports page
            page_source = driver.page_source.lower()
            reports_indicators = ["reports", "report", "filing"]

            found_indicator = False
            for indicator in reports_indicators:
                if indicator in page_source:
                    print(f"   ✓ Found '{indicator}' on page - likely on reports section")
                    found_indicator = True
                    break

            if found_indicator:
                print("\n🎉 STEP 2 SUCCESS! 🎉")
                print("Successfully navigated to Reports tab")
                print("Ready for Step 3: Find and expand year sections")

                print("\nKeeping browser open for 10 seconds to see reports page...")
                time.sleep(10)

                driver.quit()
                return True
            else:
                print("   ? Clicked Reports but not sure if we're on right page")

        except Exception as e:
            print(f"   ✗ Method 1 failed: {e}")

            # Method 2: Look for partial text match
            try:
                print("   Trying method 2: partial text match...")
                all_links = driver.find_elements(By.TAG_NAME, "a")

                reports_link = None
                for link in all_links:
                    if "report" in link.text.lower():
                        reports_link = link
                        print(f"   Found potential reports link: '{link.text}'")
                        break

                if reports_link:
                    reports_link.click()
                    time.sleep(3)
                    print("   ✓ Clicked potential reports link")
                else:
                    print("   ✗ Could not find any reports-related links")

            except Exception as e2:
                print(f"   ✗ Method 2 also failed: {e2}")

        # Show all available links for debugging
        print("\n   Available links on committee page:")
        try:
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for i, link in enumerate(all_links[:10]):  # Show first 10 links
                link_text = link.text.strip()
                if link_text:  # Only show non-empty link text
                    print(f"     {i + 1}. '{link_text}'")
        except:
            pass

        print("\nKeeping browser open for debugging...")
        time.sleep(15)
        driver.quit()
        return False

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_step2_only():
    """
    Alternative: Test Step 2 by manually navigating to a committee page first
    Useful if we want to test just the Reports tab functionality
    """
    print("=== TESTING STEP 2 ONLY ===")
    print("(Manually going to Francis Howell Families page)")

    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.by import By
        from webdriver_manager.chrome import ChromeDriverManager
        import time

        chrome_options = Options()
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--window-size=1920,1080')

        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Go directly to Francis Howell Families committee page
        print("Going directly to committee page...")
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CommInfo.aspx?MECID=C211676")
        time.sleep(5)

        print("Looking for Reports tab...")
        try:
            reports_link = driver.find_element(By.LINK_TEXT, "Reports")
            print("   ✓ Found Reports tab")

            reports_link.click()
            time.sleep(3)
            print("   ✓ Clicked Reports tab")

            print("\nStep 2 complete! Keeping browser open...")
            time.sleep(15)

        except Exception as e:
            print(f"   ✗ Could not find Reports tab: {e}")

            # Show available links
            print("   Available links:")
            all_links = driver.find_elements(By.TAG_NAME, "a")
            for link in all_links[:10]:
                if link.text.strip():
                    print(f"     - '{link.text.strip()}'")

            time.sleep(15)

        driver.quit()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    print("Step 2: Navigate to Reports Tab")
    print("=" * 40)
    print("Choose test method:")
    print("1. Run Step 1 + Step 2 together")
    print("2. Test Step 2 only (go directly to committee page)")

    choice = input("Enter 1 or 2: ")

    if choice == "1":
        success = run_step1_and_step2()
        if success:
            print("\n✅ STEP 1 + 2 COMPLETE - Ready for Step 3!")
        else:
            print("\n❌ FAILED - Need to debug")
    elif choice == "2":
        test_step2_only()
    else:
        print("Invalid choice")