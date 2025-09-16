"""
Missouri Ethics Commission Campaign Finance Report Scraper

This module provides functionality to search for committees and download
their quarterly campaign finance reports from the MEC website.

VERSION: 2.2 - Updated 2025-09-15 - FIXED DATE EXTRACTION + CONFIGURABLE DOWNLOADS
- Fixed table extraction to properly parse report names and dates
- Configurable download limits via command line
- Improved HTML parsing for nested table structures
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
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
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
    VERSION: 2.2 - Fixed Date Extraction + Configurable Downloads
    """

    def __init__(self, headless: bool = None, output_dir: str = None, max_downloads: int = 3):
        """
        Initialize the MEC scraper

        Args:
            headless: Whether to run browser in headless mode (default from config)
            output_dir: Directory to save downloaded reports (default from config)
            max_downloads: Maximum number of files to download per year (default 3)
        """
        self.headless = headless if headless is not None else SCRAPER_CONFIG['headless']
        self.output_dir = Path(output_dir) if output_dir else DOWNLOADS_DIR
        self.output_dir.mkdir(exist_ok=True)
        self.max_downloads = max_downloads

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

        self.logger.info(f"MEC Scraper v2.2 initialized - 2025-09-15 with fixed date extraction (max downloads: {max_downloads})")

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

        # Configure downloads to go to our output directory
        prefs = {
            "download.default_directory": str(self.output_dir.absolute()),
            "download.prompt_for_download": False,
            "download.directory_upgrade": True,
            "safebrowsing.enabled": True,
            "plugins.always_open_pdf_externally": True  # Don't display PDFs in browser
        }
        chrome_options.add_experimental_option("prefs", prefs)

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

    def get_committee_reports(self, committee_url: str, committee_name: str = "Unknown") -> List[Dict]:
        """
        Navigate to committee page and extract all available reports
        VERSION 2.2 - FIXED DATE EXTRACTION + CONFIGURABLE DOWNLOADS

        Args:
            committee_url: URL to committee information page
            committee_name: Committee name for file naming

        Returns:
            List of report information dictionaries
        """
        self.logger.info(f"[v2.2] Getting reports from: {committee_url}")

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
            self.logger.info("[v2.2] Looking for reports table...")

            try:
                reports_table = self.driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
                self.logger.info("[v2.2] Found main reports table")
            except NoSuchElementException:
                self.logger.error("[v2.2] Could not find main reports table")
                return []

            # Process each year one at a time to avoid stale element issues
            years_to_process = ['2025', '2024', '2023', '2022', '2021']

            for year in years_to_process:
                try:
                    self.logger.info(f"[v2.2] Processing year: {year}")

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

                    # CRITICAL: Wait 5 seconds for content to load
                    self.logger.info(f"[v2.2] Waiting 5 seconds for {year} content to load...")
                    time.sleep(5)

                    # ENHANCED LINK DETECTION
                    self.logger.info(f"[v2.2] === ENHANCED LINK DETECTION FOR {year} ===")

                    potential_report_links = []

                    # Method 1: Look for btn-link class
                    btn_links = self.driver.find_elements(By.CSS_SELECTOR, "a.btn-link")
                    self.logger.info(f"[v2.2] Found {len(btn_links)} 'a.btn-link' elements for {year}")

                    for link in btn_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        data_cpid = link.get_attribute('data-cpid')
                        link_id = link.get_attribute('id')

                        if text and (data_cpid or text.isdigit()):
                            potential_report_links.append((link, href or f"javascript:void(0)", text, f"btn-link id={link_id} cpid={data_cpid}"))

                    # Method 2: Look for data-cpid attribute directly
                    cpid_links = self.driver.find_elements(By.CSS_SELECTOR, "a[data-cpid]")
                    for link in cpid_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        data_cpid = link.get_attribute('data-cpid')
                        link_id = link.get_attribute('id')

                        if text and data_cpid:
                            potential_report_links.append((link, href or f"javascript:void(0)", text, f"data-cpid id={link_id} cpid={data_cpid}"))

                    # Remove duplicates but keep the element reference
                    unique_links = {}
                    for element, href, text, source in potential_report_links:
                        key = text
                        if key not in unique_links:
                            unique_links[key] = (element, href, text, source)

                    self.logger.info(f"[v2.2] Found {len(unique_links)} unique report links for {year}")

                    # Extract full report details from table rows
                    enhanced_reports = []
                    for element, href, text, source in unique_links.values():
                        # Find the table row containing this report to get full details
                        report_details = self._extract_report_details_from_table_fixed(text, year)

                        enhanced_reports.append({
                            'element': element,
                            'year': year,
                            'report_id': text,
                            'report_name': report_details['name'],
                            'report_date': report_details['date'],
                            'report_url': href,
                            'detection_method': source
                        })
                        self.logger.info(f"[v2.2] ADDED REPORT: {year} - {text} - {report_details['name']} ({report_details['date']}) (via {source})")

                    # Add to collection
                    all_reports.extend(enhanced_reports)

                    # Download files if we have any and haven't exceeded limit
                    if unique_links and self.max_downloads > 0:
                        download_count = min(len(enhanced_reports), self.max_downloads)
                        test_reports = enhanced_reports[:download_count]
                        self.logger.info(f"[v2.2] === DOWNLOADING {len(test_reports)} FILES FROM {year} ===")

                        for i, report in enumerate(test_reports):
                            self.logger.info(f"[v2.2] Will download {i+1}/{len(test_reports)}: {report['report_id']} - {report['report_name']}")

                            try:
                                downloaded_file = self._download_single_report_with_monitoring(
                                    report['element'],
                                    committee_name,
                                    report['year'],
                                    report['report_id'],
                                    report['report_name'],
                                    report['report_date']
                                )
                                if downloaded_file:
                                    self.logger.info(f"[v2.2] SUCCESS {i+1}/{len(test_reports)}: Downloaded {downloaded_file}")
                                else:
                                    self.logger.warning(f"[v2.2] FAILED {i+1}/{len(test_reports)}: Could not download {report['report_id']}")

                                # Brief pause between downloads
                                if i < len(test_reports) - 1:
                                    self.logger.info(f"[v2.2] Waiting 3 seconds before next download...")
                                    time.sleep(3)

                            except Exception as e:
                                self.logger.error(f"[v2.2] Error downloading {report['report_id']}: {e}")

                    if not unique_links:
                        self.logger.warning(f"[v2.2] NO REPORT LINKS FOUND for year {year}")

                except Exception as e:
                    self.logger.error(f"[v2.2] Error processing year {year}: {e}")
                    continue

            self.logger.info(f"[v2.2] === FINAL SUMMARY ===")
            self.logger.info(f"[v2.2] Found {len(all_reports)} total reports across all years")
            return all_reports

        except Exception as e:
            self.logger.error(f"[v2.2] Error getting reports: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_report_details_from_table_fixed(self, report_id: str, year: str) -> Dict[str, str]:
        """
        FIXED: Extract full report name and date from the table row using proper HTML structure

        Args:
            report_id: The numeric report ID
            year: The year being processed

        Returns:
            Dictionary with 'name' and 'date' keys
        """
        try:
            self.logger.info(f"[v2.2] EXTRACTING TABLE DETAILS for report {report_id}")

            # Use XPath to find the exact link with this report ID, then get its parent row
            try:
                # Find the link with the report ID
                report_link = self.driver.find_element(By.XPATH, f"//a[normalize-space(text())='{report_id}']")

                # Get the parent table row
                parent_row = report_link.find_element(By.XPATH, "./ancestor::tr[1]")

                # Get all cells in this row
                cells = parent_row.find_elements(By.TAG_NAME, "td")

                self.logger.info(f"[v2.2] Found row with {len(cells)} cells for report {report_id}")

                if len(cells) >= 3:
                    # Cell 0: Report ID (already have this)
                    # Cell 1: Report Name (in a span)
                    # Cell 2: Date Filed (in a span)

                    # Extract report name from second cell
                    report_name = "Unknown Report"
                    second_cell = cells[1]

                    # Try to find span with report name
                    name_spans = second_cell.find_elements(By.TAG_NAME, "span")
                    if name_spans:
                        report_name = name_spans[0].text.strip()
                        self.logger.info(f"[v2.2] Found report name in span: '{report_name}'")
                    else:
                        # Fallback to cell text
                        report_name = second_cell.text.strip()
                        self.logger.info(f"[v2.2] Using cell text for report name: '{report_name}'")

                    # Extract date from third cell
                    report_date = year
                    if len(cells) > 2:
                        third_cell = cells[2]

                        # Try to find span with date
                        date_spans = third_cell.find_elements(By.TAG_NAME, "span")
                        if date_spans:
                            report_date = date_spans[0].text.strip()
                            self.logger.info(f"[v2.2] Found report date in span: '{report_date}'")
                        else:
                            # Fallback to cell text
                            report_date = third_cell.text.strip()
                            self.logger.info(f"[v2.2] Using cell text for report date: '{report_date}'")

                    # Clean up extracted data
                    if not report_name or report_name.lower() in ['', 'unknown report']:
                        report_name = f"Report_{report_id}"
                    if not report_date or report_date.lower() in ['', 'unknown date']:
                        report_date = year

                    self.logger.info(f"[v2.2] SUCCESSFULLY EXTRACTED: Name='{report_name}', Date='{report_date}'")

                    return {
                        'name': report_name,
                        'date': report_date
                    }

                else:
                    self.logger.warning(f"[v2.2] Row has insufficient cells ({len(cells)}) for report {report_id}")

            except Exception as e:
                self.logger.warning(f"[v2.2] XPath method failed: {e}")

            # Final fallback - use defaults
            self.logger.warning(f"[v2.2] Could not extract table details for report {report_id}, using defaults")
            return {
                'name': f"Report_{report_id}",
                'date': year
            }

        except Exception as e:
            self.logger.error(f"[v2.2] Error extracting report details: {e}")
            return {
                'name': f"Report_{report_id}",
                'date': year
            }

    def _download_single_report_with_monitoring(self, report_link, committee_name: str, year: str,
                                                report_id: str, report_name: str, report_date: str) -> Optional[str]:
        """
        Download a single PDF report with active download monitoring and robust renaming

        Args:
            report_link: Selenium WebElement for the report link
            committee_name: Name of committee
            year: Report year
            report_id: Report ID
            report_name: Full report name from table
            report_date: Report date from table

        Returns:
            Filename of downloaded file or None if failed
        """
        self.logger.info(f"[v2.2] === DOWNLOAD MONITORING START ===")
        self.logger.info(f"[v2.2] Downloading: {report_name} (ID: {report_id}) - {report_date}")

        try:
            # Generate safe filename from report details
            safe_committee_name = "".join(c for c in committee_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_report_name = "".join(c for c in report_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_date = report_date.replace('/', '-').replace('\\', '-')  # Replace slashes with dashes

            # Create a clean filename
            filename = f"{safe_committee_name}_{safe_report_name}_{safe_date}_{report_id}.pdf"
            # Remove any double spaces or underscores
            filename = re.sub(r'[_\s]+', '_', filename)
            filename = filename.replace('__', '_')

            filepath = self.output_dir / filename

            self.logger.info(f"[v2.2] Target filename: {filename}")

            # Store current window handle and take snapshot of existing files
            original_window = self.driver.current_window_handle

            # Get all PDF files before download (with their modification times)
            initial_files = {}
            for pdf_file in self.output_dir.glob("*.pdf"):
                try:
                    initial_files[pdf_file.name] = pdf_file.stat().st_mtime
                except:
                    pass

            self.logger.info(f"[v2.2] Files before download: {list(initial_files.keys())}")

            # Click the report link (opens new tab)
            self.logger.info(f"[v2.2] Clicking report link for {report_id}")
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
                self.logger.error(f"[v2.2] No new tab opened for report {report_id}")
                return None

            self.driver.switch_to.window(new_window)
            current_url = self.driver.current_url
            self.logger.info(f"[v2.2] Switched to new tab: {current_url}")

            # ACTIVE DOWNLOAD MONITORING
            self.logger.info(f"[v2.2] === Starting active download monitoring ===")

            max_wait_time = 120  # 2 minutes maximum
            check_interval = 8    # Check every 8 seconds
            elapsed_time = 0
            download_detected = False

            while elapsed_time < max_wait_time and not download_detected:
                self.logger.info(f"[v2.2] Monitoring for download... ({elapsed_time}s elapsed)")

                # Get current PDF files
                current_files = {}
                for pdf_file in self.output_dir.glob("*.pdf"):
                    try:
                        current_files[pdf_file.name] = pdf_file.stat().st_mtime
                    except:
                        pass

                # Find new or modified files
                new_or_modified_files = []
                for filename_check, mtime in current_files.items():
                    if filename_check not in initial_files or mtime > initial_files.get(filename_check, 0):
                        new_or_modified_files.append(self.output_dir / filename_check)

                if new_or_modified_files:
                    # Download detected!
                    newest_file = max(new_or_modified_files, key=lambda p: p.stat().st_mtime)
                    file_size = newest_file.stat().st_size

                    self.logger.info(f"[v2.2] *** DOWNLOAD DETECTED! New file: {newest_file.name} ({file_size:,} bytes) ***")

                    # Verify file size is reasonable
                    if file_size > 1000:  # At least 1KB
                        download_detected = True

                        # ROBUST RENAMING WITH RETRY LOGIC
                        success = self._rename_file_with_retry(newest_file, filepath, filename)
                        if success:
                            self.logger.info(f"[v2.2] SUCCESS: Download and rename complete - {filename}")
                        else:
                            self.logger.warning(f"[v2.2] Download successful but rename failed - using original name: {newest_file.name}")
                            filename = newest_file.name

                        break
                    else:
                        self.logger.warning(f"[v2.2] Downloaded file too small ({file_size} bytes), continuing to monitor...")
                        try:
                            newest_file.unlink()  # Delete small file
                        except:
                            pass

                if not download_detected:
                    time.sleep(check_interval)
                    elapsed_time += check_interval

            # Close the PDF tab and return to original window
            self.logger.info(f"[v2.2] Closing PDF tab and returning to original window")
            self.driver.close()
            self.driver.switch_to.window(original_window)

            if download_detected:
                return filename
            else:
                self.logger.warning(f"[v2.2] Download monitoring timed out after {max_wait_time}s for report {report_id}")
                return None

        except Exception as e:
            self.logger.error(f"[v2.2] Error in download monitoring: {e}")
            # Ensure we return to original window
            try:
                if len(self.driver.window_handles) > 1:
                    self.driver.close()
                    self.driver.switch_to.window(original_window)
            except:
                pass
            return None

    def _rename_file_with_retry(self, source_file: Path, target_file: Path, target_filename: str, max_retries: int = 5) -> bool:
        """
        Attempt to rename a file with retry logic to handle file locking issues

        Args:
            source_file: Path to the downloaded file
            target_file: Path where file should be renamed to
            target_filename: Target filename for logging
            max_retries: Maximum number of retry attempts

        Returns:
            True if rename successful, False otherwise
        """
        for attempt in range(max_retries):
            try:
                self.logger.info(f"[v2.2] Rename attempt {attempt + 1}/{max_retries}: '{source_file.name}' -> '{target_filename}'")

                # Wait a moment for file to be fully written
                time.sleep(2)

                # If target file already exists, remove it first
                if target_file.exists():
                    target_file.unlink()
                    self.logger.info(f"[v2.2] Removed existing target file")

                # Attempt the rename
                source_file.rename(target_file)

                # Verify the rename worked
                if target_file.exists() and not source_file.exists():
                    final_size = target_file.stat().st_size
                    self.logger.info(f"[v2.2] RENAME SUCCESS: {target_filename} ({final_size:,} bytes)")
                    return True
                else:
                    self.logger.warning(f"[v2.2] Rename verification failed on attempt {attempt + 1}")

            except PermissionError as e:
                self.logger.warning(f"[v2.2] Permission error on attempt {attempt + 1}: {e}")
                time.sleep(3)  # Wait longer for file locking to clear

            except FileNotFoundError as e:
                self.logger.error(f"[v2.2] Source file disappeared during rename attempt {attempt + 1}: {e}")
                return False

            except Exception as e:
                self.logger.warning(f"[v2.2] Unexpected error on rename attempt {attempt + 1}: {e}")
                time.sleep(2)

        self.logger.error(f"[v2.2] Failed to rename file after {max_retries} attempts")
        return False

    def extract_all_reports_for_committee(self, committee_name: str, output_subdir: str = None) -> List[Dict]:
        """
        Complete workflow: search committee, get all reports
        VERSION 2.2 - Fixed date extraction + configurable downloads

        Args:
            committee_name: Name of committee to search for
            output_subdir: Optional subdirectory name for this committee

        Returns:
            List of found report information
        """
        self.logger.info(f"[v2.2] Starting extraction for committee: {committee_name}")

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

            # Get all reports for this committee (with configurable downloads)
            if committee['committee_url']:
                reports = self.get_committee_reports(committee['committee_url'], committee['committee_name'])

                # Return found reports
                for report in reports:
                    all_found_reports.append({
                        'committee': committee,
                        'report': report,
                        'local_file': None,  # Would be set if download was successful
                        'download_timestamp': datetime.now().isoformat()
                    })
            else:
                self.logger.warning(f"No committee URL found for {committee['mecid']}")

        self.logger.info(f"[v2.2] Extraction complete. Found {len(all_found_reports)} reports")
        return all_found_reports

    def _save_committee_metadata(self, committee: Dict, committee_dir: Path):
        """Save committee metadata to JSON file"""
        committee_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = committee_dir / "committee_metadata.json"

        metadata = {
            **committee,
            'extraction_timestamp': datetime.now().isoformat(),
            'scraper_version': '2.2'
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
def extract_committee_reports(committee_name: str, output_dir: str = None, headless: bool = True, max_downloads: int = 3) -> List[Dict]:
    """
    Convenience function to extract all reports for a committee

    Args:
        committee_name: Name of committee to search for
        output_dir: Directory to save reports (optional)
        headless: Whether to run in headless mode
        max_downloads: Maximum number of files to download per year

    Returns:
        List of found report information
    """
    scraper = MECReportScraper(headless=headless, output_dir=output_dir, max_downloads=max_downloads)

    try:
        return scraper.extract_all_reports_for_committee(committee_name)
    finally:
        scraper.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='MEC Report Scraper v2.2')
    parser.add_argument('command', choices=['single'], help='Command to run')
    parser.add_argument('committee_name', help='Name of committee to search for')
    parser.add_argument('--no-headless', action='store_true', help='Run browser in visible mode')
    parser.add_argument('--max-downloads', type=int, default=3, help='Maximum downloads per year (default: 3)')
    parser.add_argument('--output-dir', help='Output directory for downloads')

    args = parser.parse_args()

    print(f"🏛️  Missouri Ethics Commission Campaign Finance Scraper")
    print("=" * 60)
    print(f"🔍 Extracting reports for: {args.committee_name}")
    print(f"📁 Output directory: {args.output_dir or 'downloads'}")
    print(f"🖥️  Headless mode: {not args.no_headless}")
    print(f"⬇️  Max downloads per year: {args.max_downloads}")
    print("-" * 50)

    results = extract_committee_reports(
        committee_name=args.committee_name,
        output_dir=args.output_dir,
        headless=not args.no_headless,
        max_downloads=args.max_downloads
    )

    print(f"\n📊 Found {len(results)} reports:")
    for result in results:
        report = result['report']
        print(f"  📄 {report['year']} - {report['report_name']} ({report['report_date']}) [ID: {report['report_id']}]")

# VERSION: 2.2 - Fixed Date Extraction + Configurable Downloads - 2025-09-15