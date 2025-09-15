"""
Missouri Ethics Commission Campaign Finance Report Scraper

This module provides functionality to search for committees and download
their quarterly campaign finance reports from the MEC website.

VERSION: 2.1 - Updated 2025-09-15 - ENHANCED LINK DETECTION ONLY
- Built on Version 2.0 foundation
- Enhanced link detection with multiple selectors and debugging
- Added detailed logging of what elements ARE found
- Test clicking ONE link only (no downloads yet)
- Baby steps approach - don't break existing functionality
"""

import logging
import os
import re
import time
import json
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
try:
    from config import SCRAPER_CONFIG, MEC_SEARCH_URL, DOWNLOADS_DIR, CACHE_DIR, LOGGING_CONFIG
except ImportError:
    # Fallback defaults if config.py doesn't exist
    SCRAPER_CONFIG = {
        'headless': True,
        'page_load_timeout': 30,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    MEC_SEARCH_URL = "https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx"
    DOWNLOADS_DIR = Path("downloads")
    CACHE_DIR = Path("cache")
    LOGGING_CONFIG = {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'file': 'mec_scraper.log'
    }


class MECReportScraper:
    """
    Main scraper class for extracting campaign finance reports from Missouri Ethics Commission
    VERSION: 2.1 - Enhanced Link Detection Only
    """

    def __init__(self, headless: bool = None, output_dir: str = None):
        """
        Initialize the MEC scraper

        Args:
            headless: Whether to run browser in headless mode (default from config)
            output_dir: Directory to save downloaded reports (default from config)
        """
        self.headless = headless if headless is not None else SCRAPER_CONFIG['headless']
        self.output_dir = Path(output_dir) if output_dir else DOWNLOADS_DIR
        self.output_dir.mkdir(exist_ok=True)

        # Setup logging
        self._setup_logging()

        # Initialize session for direct downloads
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SCRAPER_CONFIG['user_agent']
        })

        # Initialize browser
        self.driver = None
        self._setup_selenium()

        self.logger.info("MEC Scraper v2.1 initialized - 2025-09-15 with enhanced link detection")

    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, LOGGING_CONFIG['level']),
            format=LOGGING_CONFIG['format'],
            handlers=[
                logging.FileHandler(LOGGING_CONFIG['file']),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)

    def _setup_selenium(self):
        """Setup Selenium WebDriver with automatic ChromeDriver management"""
        chrome_options = Options()

        if self.headless:
            chrome_options.add_argument("--headless")

        # Additional Chrome options for stability
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument(f"--user-agent={SCRAPER_CONFIG['user_agent']}")

        # Automatically download and setup ChromeDriver
        service = Service(ChromeDriverManager().install())

        try:
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            self.driver.set_page_load_timeout(SCRAPER_CONFIG['page_load_timeout'])
            self.logger.info("Chrome WebDriver initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize WebDriver: {e}")
            raise

    def search_committee(self, committee_name: str) -> List[Dict]:
        """
        Search for committees by name

        Args:
            committee_name: Name of committee to search for

        Returns:
            List of committee information dictionaries
        """
        self.logger.info(f"Searching for committee: {committee_name}")

        try:
            # Navigate to search page
            self.driver.get(MEC_SEARCH_URL)

            # Wait for page to load
            wait = WebDriverWait(self.driver, SCRAPER_CONFIG['page_load_timeout'])

            # Find and fill committee name input - using correct element names from debug
            committee_input = wait.until(
                EC.presence_of_element_located((By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$txtComm"))
            )

            committee_input.clear()
            committee_input.send_keys(committee_name)

            # Click search button - using correct element name from debug
            search_button = self.driver.find_element(By.NAME, "ctl00$ctl00$ContentPlaceHolder$ContentPlaceHolder1$btnSearch")
            search_button.click()

            # Wait for results
            time.sleep(3)

            # Parse results
            results = self._parse_search_results()
            self.logger.info(f"Found {len(results)} committee(s)")

            return results

        except TimeoutException:
            self.logger.error("Timeout waiting for search page elements")
            return []
        except Exception as e:
            self.logger.error(f"Error during search: {e}")
            return []

    def _parse_search_results(self) -> List[Dict]:
        """Parse search results table and extract committee information"""
        results = []

        try:
            # Look for results table - try multiple possible IDs based on the pattern we found
            possible_table_ids = [
                "ctl00_ctl00_ContentPlaceHolder_ContentPlaceHolder1_gvResults",
                "ctl00_ContentPlaceHolder1_ContentPlaceHolder1_gvResults",
                "ctl00_ContentPlaceHolder1_gvResults",
                "gvResults"
            ]

            results_table = None
            for table_id in possible_table_ids:
                try:
                    results_table = self.driver.find_element(By.ID, table_id)
                    self.logger.debug(f"Found results table with ID: {table_id}")
                    break
                except NoSuchElementException:
                    continue

            if not results_table:
                # Try finding by CSS selector if ID doesn't work
                try:
                    results_table = self.driver.find_element(By.CSS_SELECTOR, "table[id*='gvResults']")
                    self.logger.debug("Found results table using CSS selector")
                except NoSuchElementException:
                    # Try finding any table that might contain results
                    tables = self.driver.find_elements(By.TAG_NAME, "table")
                    for table in tables:
                        if table.text and ("MECID" in table.text or "Committee" in table.text):
                            results_table = table
                            self.logger.debug("Found results table by content search")
                            break

            if not results_table:
                self.logger.warning("No results table found")
                return []

            rows = results_table.find_elements(By.TAG_NAME, "tr")

            for row in rows[1:]:  # Skip header row
                cells = row.find_elements(By.TAG_NAME, "td")
                if len(cells) >= 6:  # Based on your screenshot columns
                    mecid = cells[0].text.strip()
                    committee_name = cells[1].text.strip()
                    candidate = cells[2].text.strip()
                    treasurer = cells[3].text.strip()
                    deputy_treasurer = cells[4].text.strip()
                    committee_type = cells[5].text.strip()
                    status = cells[6].text.strip() if len(cells) > 6 else ""

                    # Get the link to committee details
                    try:
                        link_element = cells[0].find_element(By.TAG_NAME, "a")
                        committee_url = link_element.get_attribute("href")
                    except NoSuchElementException:
                        committee_url = ""

                    committee_info = {
                        'mecid': mecid,
                        'committee_name': committee_name,
                        'candidate': candidate,
                        'treasurer': treasurer,
                        'deputy_treasurer': deputy_treasurer,
                        'committee_type': committee_type,
                        'status': status,
                        'committee_url': committee_url
                    }

                    results.append(committee_info)
                    self.logger.debug(f"Parsed committee: {mecid} - {committee_name}")

        except NoSuchElementException:
            self.logger.warning("No results table found")

        return results

    def get_committee_reports(self, committee_url: str) -> List[Dict]:
        """
        Navigate to committee page and extract all available reports
        VERSION 2.1 - ENHANCED LINK DETECTION with detailed debugging

        Args:
            committee_url: URL to committee information page

        Returns:
            List of report information dictionaries
        """
        self.logger.info(f"[v2.1] Getting reports from: {committee_url}")

        try:
            # Navigate to committee page
            self.driver.get(committee_url)

            wait = WebDriverWait(self.driver, SCRAPER_CONFIG['page_load_timeout'])

            # Click on Reports tab
            reports_tab = wait.until(
                EC.element_to_be_clickable((By.LINK_TEXT, "Reports"))
            )
            reports_tab.click()

            time.sleep(3)  # Allow page to load

            all_reports = []

            # Find the main reports table
            self.logger.info("[v2.1] Looking for reports table...")

            try:
                reports_table = self.driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
                self.logger.info("[v2.1] Found main reports table")
            except NoSuchElementException:
                self.logger.error("[v2.1] Could not find main reports table")
                return []

            # Process each year one at a time to avoid stale element issues
            years_to_process = ['2025', '2024', '2023', '2022', '2021']

            for year in years_to_process:
                try:
                    self.logger.info(f"[v2.1] Processing year: {year}")

                    # Re-find the expand button for this year (avoid stale elements)
                    expand_button = None
                    try:
                        # Find the expand button for this specific year
                        year_spans = self.driver.find_elements(By.CSS_SELECTOR, "span[id*='lblYear']")
                        for i, span in enumerate(year_spans):
                            if span.text.strip() == year:
                                # Find the corresponding expand button
                                expand_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[id*='ImgRptRight']")
                                if i < len(expand_buttons):
                                    expand_button = expand_buttons[i]
                                    break
                    except Exception as e:
                        self.logger.debug(f"Error finding expand button for {year}: {e}")
                        continue

                    if not expand_button:
                        self.logger.warning(f"Could not find expand button for year {year}")
                        continue

                    # Click to expand this year's section
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", expand_button)
                    time.sleep(1)
                    expand_button.click()

                    # CRITICAL: Wait 5 seconds for content to load (user's feedback)
                    self.logger.info(f"[v2.1] Waiting 5 seconds for {year} content to load...")
                    time.sleep(5)

                    # ENHANCED LINK DETECTION - VERSION 2.1
                    self.logger.info(f"[v2.1] === ENHANCED LINK DETECTION FOR {year} ===")

                    potential_report_links = []

                    # DEBUGGING: First, let's see what elements ARE present on the page
                    self.logger.info(f"[v2.1] === DEBUGGING: What's on the page after expanding {year} ===")

                    # Method 0: Debug - show all links on page
                    all_links = self.driver.find_elements(By.TAG_NAME, "a")
                    self.logger.info(f"[v2.1] DEBUG: Total <a> links on page: {len(all_links)}")

                    # Show first 10 links for debugging
                    for i, link in enumerate(all_links[:10]):
                        link_text = link.text.strip()[:30]  # First 30 chars
                        link_href = link.get_attribute('href') or 'no-href'
                        link_id = link.get_attribute('id') or 'no-id'
                        link_class = link.get_attribute('class') or 'no-class'
                        data_cpid = link.get_attribute('data-cpid') or 'no-data-cpid'
                        self.logger.info(f"[v2.1] DEBUG Link {i}: text='{link_text}' id='{link_id}' class='{link_class}' data-cpid='{data_cpid}'")

                    # Method 1: Look for btn-link class (original approach)
                    btn_links = self.driver.find_elements(By.CSS_SELECTOR, "a.btn-link")
                    self.logger.info(f"[v2.1] Method 1 - Found {len(btn_links)} 'a.btn-link' elements for {year}")

                    for link in btn_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        data_cpid = link.get_attribute('data-cpid')
                        link_id = link.get_attribute('id')

                        if text and (data_cpid or text.isdigit()):
                            potential_report_links.append((href or f"javascript:void(0)", text, f"btn-link id={link_id} cpid={data_cpid}"))
                            self.logger.info(f"[v2.1] Method 1 SUCCESS: {text} (data-cpid: {data_cpid}, id: {link_id})")

                    # Method 2: Look for data-cpid attribute directly
                    cpid_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-cpid]")
                    self.logger.info(f"[v2.1] Method 2 - Found {len(cpid_links)} 'a[data-cpid]' elements for {year}")

                    for link in cpid_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        data_cpid = link.get_attribute('data-cpid')
                        link_id = link.get_attribute('id')

                        if text and data_cpid:
                            potential_report_links.append((href or f"javascript:void(0)", text, f"data-cpid id={link_id} cpid={data_cpid}"))
                            self.logger.info(f"[v2.1] Method 2 SUCCESS: {text} (data-cpid: {data_cpid}, id: {link_id})")

                    # Method 3: Look for links with grvReports in ID
                    grvreport_links = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='grvReports']")
                    self.logger.info(f"[v2.1] Method 3 - Found {len(grvreport_links)} 'a[id*=grvReports]' links for {year}")

                    for link in grvreport_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        link_id = link.get_attribute('id')
                        if text:
                            potential_report_links.append((href or f"javascript:void(0)", text, f"grvReports id={link_id}"))
                            self.logger.info(f"[v2.1] Method 3 SUCCESS: {text} (id: {link_id})")

                    # Method 4: Look for blue underlined links in tables
                    blue_links = self.driver.find_elements(By.CSS_SELECTOR, "table a[style*='color:Blue']")
                    self.logger.info(f"[v2.1] Method 4 - Found {len(blue_links)} 'table a[style*=color:Blue]' links for {year}")

                    for link in blue_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        link_id = link.get_attribute('id')
                        if text and text.isdigit():
                            potential_report_links.append((href or f"javascript:void(0)", text, f"blue-link id={link_id}"))
                            self.logger.info(f"[v2.1] Method 4 SUCCESS: {text} (id: {link_id})")

                    # Method 5: Look for ANY link with numeric text that could be a report ID
                    numeric_links = []
                    for link in all_links:
                        text = link.text.strip()
                        if text and text.isdigit() and len(text) >= 5:  # Report IDs are typically 5+ digits
                            numeric_links.append(link)

                    self.logger.info(f"[v2.1] Method 5 - Found {len(numeric_links)} links with numeric text (5+ digits) for {year}")

                    for link in numeric_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        link_id = link.get_attribute('id')
                        link_class = link.get_attribute('class')
                        potential_report_links.append((href or f"javascript:void(0)", text, f"numeric id={link_id} class={link_class}"))
                        self.logger.info(f"[v2.1] Method 5 SUCCESS: {text} (id: {link_id}, class: {link_class})")

                    # Remove duplicates but keep the source info
                    unique_links = {}
                    for href, text, source in potential_report_links:
                        key = f"{text}_{href}"
                        if key not in unique_links:
                            unique_links[key] = (href, text, source)

                    self.logger.info(f"[v2.1] === FINAL RESULTS FOR {year} ===")
                    self.logger.info(f"[v2.1] Found {len(unique_links)} unique report links for {year}")

                    # Add found reports to collection
                    for href, text, source in unique_links.values():
                        all_reports.append({
                            'year': year,
                            'report_name': text,
                            'report_url': href,
                            'detection_method': source
                        })
                        self.logger.info(f"[v2.1] ADDED REPORT: {year} - {text} (via {source})")

                    # NEW: Test downloading the FIRST link if we found any
                    if unique_links and year == '2025':  # Only test on 2025
                        first_link = list(unique_links.values())[0]
                        href, text, source = first_link
                        self.logger.info(f"[v2.1] === TESTING PDF DOWNLOAD ===")
                        self.logger.info(f"[v2.1] Will download: {text} (detected via {source})")

                        try:
                            # Find the actual element again to click it
                            test_link = None
                            for link in all_links:
                                if link.text.strip() == text:
                                    test_link = link
                                    break

                            if test_link:
                                downloaded_file = self._download_single_report_hybrid(test_link, "Francis Howell Families", year, text)
                                if downloaded_file:
                                    self.logger.info(f"[v2.1] SUCCESS: Downloaded {downloaded_file}")
                                else:
                                    self.logger.warning(f"[v2.1] FAILED: Could not download {text}")
                            else:
                                self.logger.warning(f"[v2.1] Could not find element to click for {text}")

                        except Exception as e:
                            self.logger.error(f"[v2.1] Error downloading {text}: {e}")

                    if not unique_links:
                        self.logger.warning(f"[v2.1] NO REPORT LINKS FOUND for year {year} - this needs investigation")

                except Exception as e:
                    self.logger.error(f"[v2.1] Error processing year {year}: {e}")
                    continue

            self.logger.info(f"[v2.1] === FINAL SUMMARY ===")
            self.logger.info(f"[v2.1] Found {len(all_reports)} total reports across all years")
            return all_reports

        except Exception as e:
            self.logger.error(f"[v2.1] Error getting reports: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_year_from_text(self, text: str) -> str:
        """Extract 4-digit year from text"""
        year_match = re.search(r'\b(20\d{2})\b', text)
        return year_match.group(1) if year_match else "unknown"

    def _download_single_report_hybrid(self, report_link, committee_name: str, year: str, report_id: str) -> Optional[str]:
        """
        Download a single PDF report using hybrid detection approach

        Args:
            report_link: Selenium WebElement for the report link
            committee_name: Name of committee
            year: Report year
            report_id: Report ID

        Returns:
            Filename of downloaded file or None if failed
        """
        self.logger.info(f"[v2.1] === HYBRID PDF DOWNLOAD START ===")
        self.logger.info(f"[v2.1] Downloading report {report_id} for {committee_name} ({year})")

        try:
            # Generate safe filename
            safe_committee_name = "".join(c for c in committee_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            filename = f"{safe_committee_name}_{year}_{report_id}.pdf"
            filepath = self.output_dir / filename

            # Store current window handle
            original_window = self.driver.current_window_handle
            self.logger.info(f"[v2.1] Original window: {original_window}")

            # Click the report link (opens new tab)
            self.logger.info(f"[v2.1] Clicking report link for {report_id}")
            self.driver.execute_script("arguments[0].click();", report_link)

            # Wait for new tab to open
            time.sleep(3)

            # Switch to the new tab
            all_windows = self.driver.window_handles
            new_window = None
            for window in all_windows:
                if window != original_window:
                    new_window = window
                    break

            if not new_window:
                self.logger.error(f"[v2.1] No new tab opened for report {report_id}")
                return None

            self.driver.switch_to.window(new_window)
            current_url = self.driver.current_url
            self.logger.info(f"[v2.1] Switched to new tab: {current_url}")

            # SIMPLE 3-MINUTE TIMER APPROACH
            self.logger.info(f"[v2.1] === Starting 3-minute wait for PDF generation ===")

            max_wait_time = 180  # 3 minutes
            check_interval = 30   # Check every 30 seconds just for logging
            elapsed_time = 0

            while elapsed_time < max_wait_time:
                self.logger.info(f"[v2.1] Waiting for PDF generation... ({elapsed_time}/{max_wait_time}s)")

                # Optional: Check if generating text has disappeared (but don't act on it)
                try:
                    page_source = self.driver.page_source.lower()
                    generating_text_present = ("generating report" in page_source or
                                             "this may take several minutes" in page_source)
                    self.logger.info(f"[v2.1] Status check - Generating text still present: {generating_text_present}")
                except Exception as e:
                    self.logger.info(f"[v2.1] Could not check page status: {e}")

                time.sleep(check_interval)
                elapsed_time += check_interval

            self.logger.info(f"[v2.1] 3-minute wait complete - assuming PDF is ready for download")

            # PDF should be ready now - attempt download
            self.logger.info(f"[v2.1] === PDF READY - Attempting Download ===")

            download_success = False

            # Method 1: Direct URL download
            try:
                current_url = self.driver.current_url
                self.logger.info(f"[v2.1] Download Method 1: Direct URL - {current_url}")

                response = self.session.get(current_url, timeout=30)

                # Check if response is PDF
                content_type = response.headers.get('content-type', '').lower()
                content_starts_with_pdf = response.content.startswith(b'%PDF')

                self.logger.info(f"[v2.1] Response content-type: {content_type}")
                self.logger.info(f"[v2.1] Content starts with PDF marker: {content_starts_with_pdf}")

                if 'pdf' in content_type or content_starts_with_pdf:
                    with open(filepath, 'wb') as f:
                        f.write(response.content)

                    # Verify file size
                    file_size = filepath.stat().st_size
                    if file_size > 1000:  # Reasonable PDF size
                        download_success = True
                        self.logger.info(f"[v2.1] SUCCESS: PDF downloaded via direct URL - {filename} ({file_size:,} bytes)")
                    else:
                        self.logger.warning(f"[v2.1] Downloaded file too small ({file_size} bytes), likely an error page")
                        filepath.unlink()  # Delete small/empty file

            except Exception as e:
                self.logger.warning(f"[v2.1] Download Method 1 failed: {e}")

            # Method 2: Check browser's download folder for auto-downloaded file
            if not download_success:
                self.logger.info(f"[v2.1] Download Method 2: Checking for browser auto-download")
                time.sleep(5)  # Give time for auto-download

                # Look for files with the report ID in the name
                possible_files = list(self.output_dir.glob(f"*{report_id}*.pdf"))
                if possible_files:
                    # Rename to our desired filename
                    downloaded_file = possible_files[0]
                    if downloaded_file != filepath:
                        downloaded_file.rename(filepath)
                    download_success = True
                    file_size = filepath.stat().st_size
                    self.logger.info(f"[v2.1] SUCCESS: PDF auto-downloaded - {filename} ({file_size:,} bytes)")
                else:
                    self.logger.info(f"[v2.1] No auto-downloaded files found")

            # Close the PDF tab and return to original window
            self.logger.info(f"[v2.1] Closing PDF tab and returning to original window")
            self.driver.close()
            self.driver.switch_to.window(original_window)

            if download_success:
                return filename
            else:
                self.logger.warning(f"[v2.1] All download methods failed for report {report_id}")
                return None

        except Exception as e:
            self.logger.error(f"[v2.1] Error in _download_single_report_hybrid: {e}")
            # Ensure we return to original window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
            except:
                pass
            return None

    def extract_all_reports_for_committee(self, committee_name: str, output_subdir: str = None) -> List[Dict]:
        """
        Complete workflow: search committee, get all reports
        VERSION 2.1 - Enhanced link detection only, no downloads yet

        Args:
            committee_name: Name of committee to search for
            output_subdir: Optional subdirectory name for this committee

        Returns:
            List of found report information (no downloads yet)
        """
        self.logger.info(f"[v2.1] Starting extraction for committee: {committee_name}")

        # Search for committee
        search_results = self.search_committee(committee_name)

        if not search_results:
            self.logger.warning("No committees found")
            return []

        all_found_reports = []

        for committee in search_results:
            self.logger.info(f"Processing: {committee['committee_name']} (MECID: {committee['mecid']})")

            # Save committee metadata
            self._save_committee_metadata(committee, self.output_dir)

            # Get all reports for this committee (enhanced detection)
            if committee['committee_url']:
                reports = self.get_committee_reports(committee['committee_url'])

                # Return found reports (no downloads in v2.1)
                for report in reports:
                    all_found_reports.append({
                        'committee': committee,
                        'report': report,
                        'local_file': None,  # Not downloaded in v2.1
                        'download_timestamp': datetime.now().isoformat()
                    })
            else:
                self.logger.warning(f"No committee URL found for {committee['mecid']}")

        self.logger.info(f"[v2.1] Extraction complete. Found {len(all_found_reports)} reports")
        return all_found_reports

    def _save_committee_metadata(self, committee: Dict, committee_dir: Path):
        """Save committee metadata to JSON file"""
        committee_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = committee_dir / "committee_metadata.json"

        metadata = {
            **committee,
            'extraction_timestamp': datetime.now().isoformat(),
            'scraper_version': '2.1'
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def close(self):
        """Clean up resources"""
        if self.driver:
            try:
                self.driver.quit()
                self.logger.info("WebDriver closed successfully")
            except Exception as e:
                self.logger.error(f"Error closing WebDriver: {e}")

        if self.session:
            self.session.close()


# Convenience function for simple usage
def extract_committee_reports(committee_name: str, output_dir: str = None, headless: bool = True) -> List[Dict]:
    """
    Convenience function to extract all reports for a committee

    Args:
        committee_name: Name of committee to search for
        output_dir: Directory to save reports (optional)
        headless: Whether to run in headless mode

    Returns:
        List of found report information
    """
    scraper = MECReportScraper(headless=headless, output_dir=output_dir)

    try:
        return scraper.extract_all_reports_for_committee(committee_name)
    finally:
        scraper.close()


if __name__ == "__main__":
    # Example usage
    committee_name = "Francis Howell Families"

    print(f"Extracting reports for: {committee_name}")
    results = extract_committee_reports(
        committee_name=committee_name,
        headless=False  # Set to True for production
    )

    print(f"\nFound {len(results)} reports:")
    for result in results:
        print(f"  - {result['report']['year']} - {result['report']['report_name']} (via {result['report']['detection_method']})")

# VERSION: 2.1 - Enhanced Link Detection Only - 2025-09-15