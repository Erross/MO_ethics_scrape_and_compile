"""
Missouri Ethics Commission Campaign Finance Report Scraper

This module provides functionality to search for committees and download
their quarterly campaign finance reports from the MEC website.

VERSION: 2.0 - Updated 2025-09-15 14:40 EST
- Fixed btn-link selector approach
- Added 5-second wait after expansion
- Removed committee_dir undefined error
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
from config import SCRAPER_CONFIG, MEC_SEARCH_URL, DOWNLOADS_DIR, CACHE_DIR, LOGGING_CONFIG


class MECReportScraper:
    """
    Main scraper class for extracting campaign finance reports from Missouri Ethics Commission
    VERSION: 2.0 - 2025-09-15 14:40 EST
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

        self.logger.info("MEC Scraper v2.0 initialized - 2025-09-15 14:40 EST")

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
        VERSION 2.0 - Fixed btn-link detection with proper wait times

        Args:
            committee_url: URL to committee information page

        Returns:
            List of report information dictionaries
        """
        self.logger.info(f"[v2.0] Getting reports from: {committee_url}")

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
            self.logger.info("[v2.0] Looking for reports table...")

            try:
                reports_table = self.driver.find_element(By.ID, "ContentPlaceHolder_ContentPlaceHolder1_grvReportOutside")
                self.logger.info("[v2.0] Found main reports table")
            except NoSuchElementException:
                self.logger.error("[v2.0] Could not find main reports table")
                return []

            # Process each year one at a time to avoid stale element issues
            years_to_process = ['2025', '2024', '2023', '2022', '2021']

            for year in years_to_process:
                try:
                    self.logger.info(f"[v2.0] Processing year: {year}")

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
                    self.logger.info(f"[v2.0] Waiting 5 seconds for {year} content to load...")
                    time.sleep(5)

                    # Look for report links using NEW v2.0 selectors
                    self.logger.info(f"[v2.0] Looking for report links in {year}...")

                    potential_report_links = []

                    # Method 1: Look for btn-link class (from user's manual inspection)
                    btn_links = self.driver.find_elements(By.CSS_SELECTOR, "a.btn-link")
                    self.logger.info(f"[v2.0] Found {len(btn_links)} btn-link elements for {year}")

                    for link in btn_links:
                        href = link.get_attribute('href')
                        text = link.text.strip()
                        data_cpid = link.get_attribute('data-cpid')

                        if text and (data_cpid or text.isdigit()):
                            potential_report_links.append((href or f"javascript:void(0)", text))
                            self.logger.info(f"[v2.0] Found btn-link report: {text} (data-cpid: {data_cpid})")

                    # Method 2: Look for links with grvReports in ID
                    if not potential_report_links:
                        grvreport_links = self.driver.find_elements(By.CSS_SELECTOR, "a[id*='grvReports']")
                        self.logger.info(f"[v2.0] Found {len(grvreport_links)} grvReports links for {year}")

                        for link in grvreport_links:
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            if text:
                                potential_report_links.append((href or f"javascript:void(0)", text))
                                self.logger.info(f"[v2.0] Found grvReports link: {text}")

                    # Method 3: Look for blue underlined links in tables
                    if not potential_report_links:
                        blue_links = self.driver.find_elements(By.CSS_SELECTOR, "table a[style*='color:Blue']")
                        self.logger.info(f"[v2.0] Found {len(blue_links)} blue table links for {year}")

                        for link in blue_links:
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            if text and text.isdigit():
                                potential_report_links.append((href or f"javascript:void(0)", text))
                                self.logger.info(f"[v2.0] Found blue link: {text}")

                    # Add found reports to collection
                    for report_url, report_text in potential_report_links:
                        all_reports.append({
                            'year': year,
                            'report_name': report_text,
                            'report_url': report_url
                        })
                        self.logger.info(f"[v2.0] Added report: {year} - {report_text}")

                    if not potential_report_links:
                        self.logger.warning(f"[v2.0] No report links found for year {year} after expansion")

                        # Debug: show what links ARE present
                        all_links_in_page = self.driver.find_elements(By.TAG_NAME, "a")
                        self.logger.debug(f"[v2.0] Total links on page after expanding {year}: {len(all_links_in_page)}")

                        # Show some example links for debugging
                        for i, link in enumerate(all_links_in_page[:5]):
                            link_text = link.text.strip()[:20]
                            link_id = link.get_attribute('id')
                            link_class = link.get_attribute('class')
                            if link_text or link_id:
                                self.logger.debug(f"  [v2.0] Link {i}: text='{link_text}' id='{link_id}' class='{link_class}'")

                except Exception as e:
                    self.logger.error(f"[v2.0] Error processing year {year}: {e}")
                    continue

            self.logger.info(f"[v2.0] Found {len(all_reports)} total reports")
            return all_reports

        except Exception as e:
            self.logger.error(f"[v2.0] Error getting reports: {e}")
            import traceback
            traceback.print_exc()
            return []

    def _extract_year_from_text(self, text: str) -> str:
        """Extract 4-digit year from text"""
        year_match = re.search(r'\b(20\d{2})\b', text)
        return year_match.group(1) if year_match else "unknown"

    def download_report(self, report_url: str, filename: str, committee_dir: Path) -> Optional[str]:
        """
        Download a specific report PDF by handling the dynamic generation process

        Args:
            report_url: URL to the report generator page
            filename: Desired filename for the download
            committee_dir: Directory to save the file

        Returns:
            Path to downloaded file or None if failed
        """
        committee_dir.mkdir(parents=True, exist_ok=True)
        filepath = committee_dir / filename

        try:
            self.logger.info(f"Processing dynamic PDF generation for: {filename}")

            # Store the current window handle
            main_window = self.driver.current_window_handle

            # Click the report link (this will open a new tab)
            self.driver.get(report_url)

            # Wait for the page to load and check if it's a generator page
            time.sleep(3)

            # Check if we're on a PDF generation page
            page_source = self.driver.page_source.lower()

            if "generating report" in page_source or "may take several minutes" in page_source:
                self.logger.info(f"PDF generation started for {filename}, waiting for completion...")

                # Wait for PDF generation to complete (up to 5 minutes)
                max_wait_time = 300  # 5 minutes
                wait_interval = 10   # Check every 10 seconds
                waited_time = 0

                while waited_time < max_wait_time:
                    time.sleep(wait_interval)
                    waited_time += wait_interval

                    # Check if page has changed to show PDF
                    current_url = self.driver.current_url
                    page_source = self.driver.page_source.lower()

                    # Check if PDF is ready (URL might change or page content changes)
                    if ("pdf" in current_url.lower() or
                        "application/pdf" in self.driver.execute_script("return document.contentType;") or
                        len(page_source) < 1000):  # PDF pages typically have minimal HTML

                        self.logger.info(f"PDF generation completed for {filename}")
                        break

                    # Check for error messages
                    if "error" in page_source or "not found" in page_source:
                        self.logger.error(f"Error generating PDF for {filename}")
                        return None

                    self.logger.debug(f"Still waiting for PDF generation... ({waited_time}/{max_wait_time} seconds)")

                if waited_time >= max_wait_time:
                    self.logger.error(f"Timeout waiting for PDF generation: {filename}")
                    return None

            # At this point, we should have a PDF. Try to download it.
            # Method 1: If the current page is a PDF, download it directly
            try:
                current_url = self.driver.current_url
                response = self.session.get(current_url, timeout=30, stream=True)

                # Check if response is actually a PDF
                content_type = response.headers.get('content-type', '').lower()
                if 'pdf' in content_type or response.content.startswith(b'%PDF'):

                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    file_size = filepath.stat().st_size
                    if file_size > 1000:  # Ensure file is not empty/error page
                        self.logger.info(f"Downloaded PDF: {filename} ({file_size:,} bytes)")
                        return str(filepath)
                    else:
                        self.logger.warning(f"Downloaded file too small, may be error: {filename}")
                        filepath.unlink()  # Delete empty file

            except Exception as e:
                self.logger.debug(f"Direct download failed: {e}")

            self.logger.error(f"All download methods failed for: {filename}")
            return None

        except Exception as e:
            self.logger.error(f"Error processing report {filename}: {e}")
            return None

    def extract_all_reports_for_committee(self, committee_name: str, output_subdir: str = None) -> List[Dict]:
        """
        Complete workflow: search committee, get all reports, download them

        Args:
            committee_name: Name of committee to search for
            output_subdir: Optional subdirectory name for this committee

        Returns:
            List of downloaded file information
        """
        self.logger.info(f"[v2.0] Starting extraction for committee: {committee_name}")

        # Search for committee
        search_results = self.search_committee(committee_name)

        if not search_results:
            self.logger.warning("No committees found")
            return []

        all_downloaded_files = []

        for committee in search_results:
            self.logger.info(f"Processing: {committee['committee_name']} (MECID: {committee['mecid']})")

            # Create committee-specific directory
            if output_subdir:
                committee_dir = self.output_dir / output_subdir
            else:
                safe_name = re.sub(r'[<>:"/\\|?*]', '_', committee['committee_name'])
                committee_dir = self.output_dir / f"{committee['mecid']}_{safe_name}"

            # Save committee metadata
            self._save_committee_metadata(committee, committee_dir)

            # Get all reports for this committee
            if committee['committee_url']:
                reports = self.get_committee_reports(committee['committee_url'])

                # For now, just return the found reports without downloading
                # (we can add downloading later once link detection works)
                for report in reports:
                    all_downloaded_files.append({
                        'committee': committee,
                        'report': report,
                        'local_file': None,  # Not downloaded yet
                        'download_timestamp': datetime.now().isoformat()
                    })
            else:
                self.logger.warning(f"No committee URL found for {committee['mecid']}")

        self.logger.info(f"[v2.0] Extraction complete. Found {len(all_downloaded_files)} reports")
        return all_downloaded_files

    def _save_committee_metadata(self, committee: Dict, committee_dir: Path):
        """Save committee metadata to JSON file"""
        committee_dir.mkdir(parents=True, exist_ok=True)
        metadata_file = committee_dir / "committee_metadata.json"

        metadata = {
            **committee,
            'extraction_timestamp': datetime.now().isoformat(),
            'scraper_version': '2.0'
        }

        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

    def _generate_filename(self, committee: Dict, report: Dict) -> str:
        """Generate a clean filename for the report"""
        # Clean report name
        clean_report_name = re.sub(r'[<>:"/\\|?*]', '_', report['report_name'])
        clean_report_name = re.sub(r'\s+', '_', clean_report_name.strip())

        # Generate filename: MECID_YEAR_ReportName.pdf
        filename = f"{committee['mecid']}_{report['year']}_{clean_report_name}.pdf"

        # Ensure it ends with .pdf
        if not filename.lower().endswith('.pdf'):
            filename += '.pdf'

        return filename

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
        List of downloaded file information
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
        print(f"  - {result['report']['year']} - {result['report']['report_name']}")

# VERSION: 2.0 - Updated 2025-09-15 14:40 EST
# Changes: Fixed btn-link selector, added 5-second wait, removed committee_dir error