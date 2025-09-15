"""
Debug script to find the actual report table structure and links
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


def debug_report_table():
    """Focus on finding the actual report table structure"""

    print("🔍 Debugging Report Table Structure")
    print("=" * 60)

    # Setup browser
    chrome_options = Options()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # Navigate to reports page
        committee_url = "https://mec.mo.gov/MEC/Campaign_Finance/CommInfo.aspx?MECID=C211676"
        print(f"1. Navigating to: {committee_url}")
        driver.get(committee_url)

        # Click Reports tab
        print("2. Clicking Reports tab...")
        wait = WebDriverWait(driver, 10)
        reports_tab = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Reports")))
        reports_tab.click()
        time.sleep(3)

        print("3. Looking for report tables and links...")

        # Look for all tables on the page
        print("\n--- All tables on page ---")
        tables = driver.find_elements(By.TAG_NAME, "table")
        print(f"Found {len(tables)} tables:")

        for i, table in enumerate(tables):
            table_id = table.get_attribute('id')
            table_class = table.get_attribute('class')
            rows = table.find_elements(By.TAG_NAME, "tr")

            print(f"  Table {i + 1}: ID='{table_id}', Class='{table_class}', Rows={len(rows)}")

            # Check if this table contains report-like content
            table_text = table.text
            if any(keyword in table_text.lower() for keyword in ['report', 'quarterly', 'expenditure', 'filing']):
                print(f"    *** This table likely contains reports ***")
                print(f"    First 200 chars: {table_text[:200]}...")

                # Look for links in this table
                links = table.find_elements(By.TAG_NAME, "a")
                print(f"    Links in table: {len(links)}")
                for j, link in enumerate(links[:5]):  # Show first 5 links
                    href = link.get_attribute('href')
                    text = link.text.strip()
                    print(f"      Link {j + 1}: '{text}' -> {href}")
            print()

        # Look for specific report-related elements
        print("--- Looking for report-specific elements ---")

        # Look for elements with IDs containing "report"
        report_elements = driver.find_elements(By.CSS_SELECTOR, "*[id*='report' i], *[id*='Report']")
        print(f"Found {len(report_elements)} elements with 'report' in ID:")
        for elem in report_elements[:10]:  # Show first 10
            elem_id = elem.get_attribute('id')
            elem_tag = elem.tag_name
            elem_text = elem.text.strip()[:50] + "..." if len(elem.text.strip()) > 50 else elem.text.strip()
            print(f"  {elem_tag} ID='{elem_id}': '{elem_text}'")

        # Look for links that might be report downloads
        print(f"\n--- All links on page ---")
        all_links = driver.find_elements(By.TAG_NAME, "a")
        print(f"Found {len(all_links)} total links:")

        report_links = []
        for link in all_links:
            href = link.get_attribute('href')
            text = link.text.strip()

            # Check if this looks like a report link
            if href and any(keyword in href.lower() for keyword in ['generator', 'report', 'mecid']):
                report_links.append((text, href))
                print(f"  Report link: '{text}' -> {href}")
            elif text and any(keyword in text.lower() for keyword in ['report', 'quarterly', 'expenditure']):
                report_links.append((text, href))
                print(f"  Text-based report link: '{text}' -> {href}")

        print(f"\nFound {len(report_links)} potential report links")

        # Try different expansion methods
        print(f"\n--- Trying different expansion methods ---")

        # Method 1: Look for expand/collapse buttons or icons
        expand_elements = driver.find_elements(By.CSS_SELECTOR,
                                               "*[class*='expand'], *[class*='collaps'], *[onclick*='expand'], *[onclick*='collaps']")
        print(f"Found {len(expand_elements)} potential expand/collapse elements")

        # Method 2: Look for elements that might trigger AJAX calls
        ajax_elements = driver.find_elements(By.CSS_SELECTOR, "*[onclick], button, input[type='button']")
        print(f"Found {len(ajax_elements)} elements with onclick or buttons")

        # Method 3: Try clicking on different parts of year sections
        year_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '2025')]/..")
        print(f"Found {len(year_elements)} parent elements of '2025' text")

        for i, elem in enumerate(year_elements[:3]):  # Try first 3
            try:
                print(f"  Trying to click parent element {i + 1}...")
                driver.execute_script("arguments[0].scrollIntoView(true);", elem)
                time.sleep(1)
                elem.click()
                time.sleep(2)

                # Check if new links appeared
                new_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='Generator.aspx']")
                print(f"    After click: {len(new_links)} generator links found")

                if new_links:
                    print(f"    SUCCESS! Found report links:")
                    for j, link in enumerate(new_links[:5]):
                        print(f"      {j + 1}: {link.text} -> {link.get_attribute('href')}")
                    break

            except Exception as e:
                print(f"    Error clicking element {i + 1}: {e}")

        # Method 4: Try executing JavaScript to expand sections
        print(f"\n--- Trying JavaScript expansion ---")

        # Look for JavaScript functions that might expand sections
        page_source = driver.page_source
        if 'expand' in page_source.lower() or 'collapse' in page_source.lower():
            print("Page contains expand/collapse related JavaScript")

            # Try common JavaScript expansion patterns
            js_commands = [
                "document.querySelectorAll('*[onclick*=\"expand\"]').forEach(el => el.click());",
                "document.querySelectorAll('*[class*=\"expand\"]').forEach(el => el.click());",
                "document.querySelectorAll('span').forEach(el => { if(el.textContent.includes('2025')) el.click(); });",
            ]

            for cmd in js_commands:
                try:
                    print(f"  Trying JavaScript: {cmd[:50]}...")
                    driver.execute_script(cmd)
                    time.sleep(2)

                    # Check for new report links
                    new_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='Generator.aspx']")
                    if new_links:
                        print(f"    SUCCESS! JavaScript revealed {len(new_links)} report links")
                        break
                except Exception as e:
                    print(f"    JavaScript error: {e}")

        # Final check - show current state
        print(f"\n--- Final state check ---")
        final_generator_links = driver.find_elements(By.CSS_SELECTOR, "a[href*='Generator.aspx']")
        print(f"Total Generator.aspx links found: {len(final_generator_links)}")

        for i, link in enumerate(final_generator_links):
            text = link.text.strip()
            href = link.get_attribute('href')
            print(f"  Final link {i + 1}: '{text}' -> {href}")

        print("\n" + "=" * 60)
        print("Keeping browser open for 30 seconds...")
        print("Try manually expanding the 2025 section to see what we're missing")
        time.sleep(30)

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        driver.quit()


if __name__ == "__main__":
    debug_report_table()