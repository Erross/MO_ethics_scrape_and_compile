"""
Enhanced debugging to see exactly what Selenium sees vs manual browsing
"""

import sys
import time
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


def debug_selenium_vs_manual():
    """Compare what Selenium sees vs manual browsing"""

    print("🔍 Enhanced Selenium Debugging")
    print("=" * 60)

    # Setup browser exactly like the scraper does
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(30)

    try:
        print("1. Navigating to MEC search page...")
        start_time = time.time()
        driver.get("https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx")
        load_time = time.time() - start_time
        print(f"   ✅ Page loaded in {load_time:.2f} seconds")

        print(f"2. Current URL: {driver.current_url}")
        print(f"3. Page title: '{driver.title}'")

        # Wait for page to be fully loaded
        print("4. Waiting for page to be fully loaded...")
        wait = WebDriverWait(driver, 10)

        # Check if page is actually loaded by looking for body
        try:
            wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
            print("   ✅ Body element found")
        except:
            print("   ❌ No body element found - page may not have loaded")

        # Take a screenshot for debugging
        screenshot_path = project_root / "debug_screenshot.png"
        driver.save_screenshot(str(screenshot_path))
        print(f"   📸 Screenshot saved: {screenshot_path}")

        # Check page source length
        page_source = driver.page_source
        print(f"5. Page source length: {len(page_source)} characters")

        if len(page_source) < 5000:
            print("   ⚠️  Page source seems too short - might be error page")
            print("   First 1000 characters:")
            print(page_source[:1000])

        # Look for specific elements we need
        print("\n6. Searching for committee name input fields...")

        # Method 1: Try exact name we saw in inspector
        input_candidates = [
            "ctl00$ContentPlaceHolder1$ContentPlaceHolder1$txtCommName",
            "ctl00$ContentPlaceHolder1$txtCommName",
            "txtCommName"
        ]

        found_input = None
        for input_name in input_candidates:
            try:
                element = driver.find_element(By.NAME, input_name)
                print(f"   ✅ Found input with name: {input_name}")
                found_input = element
                break
            except:
                print(f"   ❌ No input found with name: {input_name}")

        # Method 2: Try CSS selectors
        if not found_input:
            css_selectors = [
                "input[name*='txtCommName']",
                "input[placeholder*='committee']",
                "input[placeholder*='Committee']",
                "#txtCommName",
                "input[type='text']"
            ]

            for selector in css_selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        print(f"   ✅ Found {len(elements)} elements with selector: {selector}")
                        for i, elem in enumerate(elements):
                            name = elem.get_attribute('name')
                            placeholder = elem.get_attribute('placeholder')
                            print(f"      Element {i + 1}: name='{name}', placeholder='{placeholder}'")
                        found_input = elements[0]
                        break
                    else:
                        print(f"   ❌ No elements found with selector: {selector}")
                except Exception as e:
                    print(f"   ❌ Error with selector {selector}: {e}")

        # Method 3: List ALL input elements
        print("\n7. Listing ALL input elements on page...")
        all_inputs = driver.find_elements(By.TAG_NAME, "input")
        print(f"   Found {len(all_inputs)} total input elements:")

        for i, input_elem in enumerate(all_inputs):
            input_type = input_elem.get_attribute("type")
            input_name = input_elem.get_attribute("name")
            input_id = input_elem.get_attribute("id")
            input_placeholder = input_elem.get_attribute("placeholder")
            input_value = input_elem.get_attribute("value")

            print(f"     Input {i + 1}:")
            print(f"       Type: {input_type}")
            print(f"       Name: {input_name}")
            print(f"       ID: {input_id}")
            print(f"       Placeholder: {input_placeholder}")
            print(f"       Value: {input_value}")
            print()

        # Method 4: Check for forms
        print("8. Checking forms...")
        forms = driver.find_elements(By.TAG_NAME, "form")
        print(f"   Found {len(forms)} forms")

        for i, form in enumerate(forms):
            form_action = form.get_attribute("action")
            form_method = form.get_attribute("method")
            form_id = form.get_attribute("id")
            print(f"     Form {i + 1}: action='{form_action}', method='{form_method}', id='{form_id}'")

        # Method 5: Check if there are any iframes
        print("\n9. Checking for iframes...")
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        print(f"   Found {len(iframes)} iframes")

        if iframes:
            print("   ⚠️  Page contains iframes - search form might be inside one")
            for i, iframe in enumerate(iframes):
                src = iframe.get_attribute("src")
                print(f"     Iframe {i + 1}: src='{src}'")

        # Method 6: Wait and try again (sometimes elements load after initial page load)
        print("\n10. Waiting 5 seconds and trying again...")
        time.sleep(5)

        # Try finding the committee input again
        try:
            committee_input = driver.find_element(By.CSS_SELECTOR, "input[name*='txtCommName']")
            print("    ✅ Found committee input after waiting!")

            # Try to interact with it
            print("    Testing interaction...")
            committee_input.clear()
            committee_input.send_keys("Test Committee")
            print("    ✅ Successfully entered text!")

        except Exception as e:
            print(f"    ❌ Still can't find committee input: {e}")

        # Method 7: Check for JavaScript errors
        print("\n11. Checking browser console for errors...")
        try:
            logs = driver.get_log('browser')
            if logs:
                print(f"   Found {len(logs)} console messages:")
                for log in logs[-5:]:  # Show last 5 messages
                    print(f"     {log['level']}: {log['message']}")
            else:
                print("   No console messages found")
        except Exception as e:
            print(f"   Could not get console logs: {e}")

        print(f"\n12. Current page URL after all checks: {driver.current_url}")

        print("\n" + "=" * 60)
        print("🕐 Keeping browser open for 30 seconds for manual inspection...")
        print("   Please check:")
        print("   1. Does the page look correct?")
        print("   2. Can you see the search form?")
        print("   3. Are there any error messages?")
        print("   4. Does the URL look right?")

        time.sleep(30)

    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()
        print("\n✅ Browser closed. Check the debug_screenshot.png file for what Selenium saw.")


if __name__ == "__main__":
    debug_selenium_vs_manual()