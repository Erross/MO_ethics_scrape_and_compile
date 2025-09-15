"""
Debug script specifically for year section expansion on the reports page
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


def debug_year_sections():
    """Debug the year section expansion functionality"""

    print("🔍 Debugging Year Section Expansion")
    print("=" * 60)

    # Setup browser
    chrome_options = Options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate directly to the Francis Howell Families reports page
        committee_url = "https://mec.mo.gov/MEC/Campaign_Finance/CommInfo.aspx?MECID=C211676"
        print(f"1. Navigating to: {committee_url}")
        driver.get(committee_url)

        # Click Reports tab
        print("2. Clicking Reports tab...")
        wait = WebDriverWait(driver, 10)
        reports_tab = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Reports")))
        reports_tab.click()
        time.sleep(3)

        print("3. Analyzing year section structure...")

        # Look for all elements containing "2025"
        print("\n--- Elements containing '2025' ---")
        elements_2025 = driver.find_elements(By.XPATH, "//*[contains(text(), '2025')]")
        print(f"Found {len(elements_2025)} elements containing '2025':")

        for i, elem in enumerate(elements_2025):
            tag = elem.tag_name
            text = elem.text.strip()[:50] + "..." if len(elem.text.strip()) > 50 else elem.text.strip()
            elem_id = elem.get_attribute('id')
            elem_class = elem.get_attribute('class')
            onclick = elem.get_attribute('onclick')
            role = elem.get_attribute('role')

            print(f"  Element {i + 1}:")
            print(f"    Tag: {tag}")
            print(f"    Text: '{text}'")
            print(f"    ID: {elem_id}")
            print(f"    Class: {elem_class}")
            print(f"    Onclick: {onclick}")
            print(f"    Role: {role}")
            print()

        # Look for elements in the Electronic Reports section specifically
        print("--- Elements in Electronic Reports section ---")
        try:
            reports_section = driver.find_element(By.XPATH,
                                                  "//h3[contains(text(), 'Electronic Reports')] | //*[contains(text(), 'Electronic Reports')]/../..")
            print("Found Electronic Reports section")

            # Find all clickable elements within this section
            clickable_in_section = reports_section.find_elements(By.XPATH,
                                                                 ".//*[@onclick or @role='button' or contains(@class, 'btn') or contains(@class, 'click') or contains(@class, 'expand') or contains(@class, 'collaps')]")

            print(f"Found {len(clickable_in_section)} potentially clickable elements in reports section:")
            for i, elem in enumerate(clickable_in_section):
                tag = elem.tag_name
                text = elem.text.strip()
                elem_id = elem.get_attribute('id')
                elem_class = elem.get_attribute('class')
                onclick = elem.get_attribute('onclick')

                print(f"  Clickable {i + 1}:")
                print(f"    Tag: {tag}, Text: '{text}', ID: {elem_id}")
                print(f"    Class: {elem_class}, Onclick: {onclick}")
                print()

        except Exception as e:
            print(f"Could not find Electronic Reports section: {e}")

        # Try to find the actual year buttons/divs
        print("--- Looking for year buttons/divs specifically ---")

        # Look for elements with IDs or classes that might indicate year sections
        year_selectors = [
            "*[id*='2025']",
            "*[class*='2025']",
            "*[id*='year']",
            "*[class*='year']",
            "*[class*='expand']",
            "*[class*='collaps']",
            "div[onclick]",
            "span[onclick]",
            "*[style*='cursor:pointer']"
        ]

        for selector in year_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    print(f"Selector '{selector}' found {len(elements)} elements:")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        text = elem.text.strip()[:30] + "..." if len(elem.text.strip()) > 30 else elem.text.strip()
                        print(f"    {i + 1}: {elem.tag_name} - '{text}' - ID: {elem.get_attribute('id')}")
                    print()
            except Exception as e:
                print(f"Error with selector '{selector}': {e}")

        # Check current page HTML around the year sections
        print("--- HTML structure around 2025 ---")
        try:
            year_2025_elem = driver.find_element(By.XPATH, "//*[contains(text(), '2025')]")
            # Get parent element HTML
            parent_html = year_2025_elem.find_element(By.XPATH, "..").get_attribute('outerHTML')
            print("Parent element HTML:")
            print(parent_html[:500] + "..." if len(parent_html) > 500 else parent_html)
            print()
        except Exception as e:
            print(f"Could not get HTML structure: {e}")

        # Try manual clicking test
        print("--- Manual clicking test ---")
        print("Looking for the most likely clickable year element...")

        # Try to find and click the 2025 element
        possible_2025_elements = [
            "//span[text()='2025']",
            "//div[text()='2025']",
            "//*[text()='2025' and (@onclick or contains(@class, 'click') or @role='button')]",
            "//*[contains(text(), '2025')][@onclick]"
        ]

        for xpath in possible_2025_elements:
            try:
                elements = driver.find_elements(By.XPATH, xpath)
                if elements:
                    print(f"Found {len(elements)} elements with XPath: {xpath}")

                    # Try clicking the first one
                    elem = elements[0]
                    print(f"Attempting to click: {elem.tag_name} with text '{elem.text}'")

                    # Scroll into view
                    driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                    time.sleep(1)

                    # Try click
                    elem.click()
                    time.sleep(3)

                    # Check if anything changed
                    report_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='Generator.aspx']")
                    print(f"After click: Found {len(report_links)} report generator links")

                    if report_links:
                        print("SUCCESS! Year section expanded and found report links:")
                        for i, link in enumerate(report_links[:3]):
                            print(f"  Report {i + 1}: {link.text} -> {link.get_attribute('href')}")
                        break
                    else:
                        print("Click didn't reveal report links, trying next element...")

            except Exception as e:
                print(f"Error with XPath {xpath}: {e}")

        print("\n" + "=" * 60)
        print("Keeping browser open for 30 seconds for manual inspection...")
        print("Try manually clicking on the 2025 section to see what happens")
        time.sleep(30)

    except Exception as e:
        print(f"Error during debugging: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()


if __name__ == "__main__":
    debug_year_sections()