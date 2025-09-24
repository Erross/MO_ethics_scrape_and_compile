print("=== STEP 1 SIMPLE TEST ===")
print("Starting...")

try:
    print("1. Importing modules...")
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.chrome.service import Service
    from webdriver_manager.chrome import ChromeDriverManager
    import time

    print("2. Setting up browser...")
    chrome_options = Options()
    # Don't use headless - we want to see what happens
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')

    print("3. Starting browser...")
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    print("4. Browser opened! Going to MEC search page...")
    mec_url = "https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx#gsc.tab=0"
    driver.get(mec_url)

    print("5. Waiting for page to load...")
    time.sleep(5)

    print("6. Current URL:", driver.current_url)
    print("7. Page title:", driver.title)

    print("8. Looking for committee input field...")
    try:
        from selenium.webdriver.common.by import By

        committee_input = driver.find_element(By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm")
        print("   ✓ Found committee input field!")

        print("9. Entering 'Francis Howell Families'...")
        committee_input.clear()
        committee_input.send_keys("Francis Howell Families")
        print("   ✓ Text entered!")

    except Exception as e:
        print(f"   ✗ Could not find input field: {e}")

    print("10. Keeping browser open for 10 seconds so you can see...")
    time.sleep(10)

    print("11. Closing browser...")
    driver.quit()

    print("=== SUCCESS! ===")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback

    traceback.print_exc()

print("Script finished.")