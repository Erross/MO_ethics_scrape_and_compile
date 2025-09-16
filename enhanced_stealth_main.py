"""
Enhanced Anti-Detection MEC Scraper - Single Session Architecture

Features:
- Single browser session (no multiple reconnections)
- Offline file existence checking
- Human-like browsing simulation
- Extended tab reading times
- Progressive year processing

Usage:
    python enhanced_stealth_main.py single "Francis Howell Families" --max-downloads 999
    python enhanced_stealth_main.py single "Francis Howell Families" --test

VERSION: 2.8 - Single Session Architecture & Enhanced Stealth - 2025-09-16
"""

import argparse
import sys
import json
import time
import random
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import re

# Add src directory to path
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from mec_scraper import MECReportScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

try:
    from config import DOWNLOADS_DIR, SCRAPER_CONFIG
except ImportError:
    DOWNLOADS_DIR = Path("downloads")
    SCRAPER_CONFIG = {'page_load_timeout': 30}


class RecaptchaDetected(Exception):
    """Custom exception for reCAPTCHA detection"""
    pass


class SingleSessionScraper:
    """Single session scraper with enhanced anti-detection"""

    def __init__(self, headless: bool = True, output_dir: str = None, max_downloads: int = 3, test_mode: bool = False):
        self.headless = headless
        self.output_dir = Path(output_dir) if output_dir else DOWNLOADS_DIR
        self.output_dir.mkdir(exist_ok=True)
        self.max_downloads = max_downloads
        self.test_mode = test_mode

        # Enhanced timing for stealth
        self.page_read_time = (45, 90)  # Simulate reading time 45-90 seconds
        self.click_delay = (2, 6)       # Delay before clicks 2-6 seconds
        self.type_delay = (3, 7)        # Delay between typing 3-7 seconds
        self.year_process_delay = (30, 60)  # Between years 30-60 seconds

        # Progress tracking
        self.total_discovered = 0
        self.total_existing = 0
        self.total_downloaded = 0
        self.total_would_download = 0

        print(f"Mode: {'TEST (Discovery Only)' if test_mode else 'DOWNLOAD'}")
        print(f"Output directory: {self.output_dir}")
        print(f"Stealth Mode: Extended delays, tab reading simulation")

    def human_delay(self, delay_range: Tuple[int, int], description: str = ""):
        """Human-like delay with countdown"""
        delay = random.uniform(*delay_range)
        if description:
            print(f"   {description}: {delay:.1f}s")

        if delay > 30:
            # Show countdown for longer delays
            remaining = int(delay)
            while remaining > 0:
                print(f"   Waiting... {remaining}s remaining", end='\r')
                time.sleep(min(10, remaining))
                remaining -= 10
            print(" " * 30, end='\r')  # Clear countdown
        else:
            time.sleep(delay)

    def generate_consistent_filename(self, committee_name: str, report_name: str, report_date: str,
                                   report_id: str) -> str:
        """Generate filename using EXACT same logic as MECReportScraper"""
        safe_committee_name = "".join(c for c in committee_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_report_name = "".join(c for c in report_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_date = report_date.replace('/', '-').replace('\\', '-')

        filename = f"{safe_committee_name}_{safe_report_name}_{safe_date}_{report_id}.pdf"
        filename = re.sub(r'[_\s]+', '_', filename)
        filename = filename.replace('__', '_')

        return filename

    def check_file_exists_offline(self, committee_name: str, report_name: str, report_date: str,
                                 report_id: str) -> Tuple[bool, str]:
        """Check if file exists locally without web access"""
        expected_filename = self.generate_consistent_filename(committee_name, report_name, report_date, report_id)
        file_path = self.output_dir / expected_filename

        exists = file_path.exists()
        if exists:
            file_size = file_path.stat().st_size
            if file_size > 1000:  # At least 1KB
                return True, str(file_path)
            else:
                # Delete incomplete file
                try:
                    file_path.unlink()
                    print(f"     Removed incomplete file: {expected_filename}")
                except:
                    pass

        return False, str(file_path)

    def check_for_recaptcha(self, driver) -> bool:
        """Enhanced reCAPTCHA detection"""
        try:
            recaptcha_indicators = [
                "recaptcha", "captcha", "verify you are human",
                "Something went wrong while validating the reCAPTCHA",
                "blocked", "suspicious activity"
            ]

            page_source = driver.page_source.lower()
            page_text = driver.find_element(By.TAG_NAME, "body").text.lower()

            for indicator in recaptcha_indicators:
                if indicator in page_source or indicator in page_text:
                    return True

            # Check for reCAPTCHA elements
            recaptcha_elements = [
                "//div[contains(@class, 'recaptcha')]",
                "//iframe[contains(@src, 'recaptcha')]",
                "//*[contains(text(), 'reCAPTCHA')]",
                "//*[contains(text(), 'verify you are human')]",
                "//div[contains(@class, 'blocked')]"
            ]

            for xpath in recaptcha_elements:
                try:
                    if driver.find_elements(By.XPATH, xpath):
                        return True
                except:
                    continue

            return False

        except Exception as e:
            print(f"Warning: Could not check for reCAPTCHA: {e}")
            return False

    def extract_committee_reports_single_session(self, committee_name: str) -> List[Dict]:
        """
        SINGLE SESSION: Do everything in one browser session with offline planning
        """
        print("ENHANCED SINGLE SESSION MODE: Offline Planning + One Browser Session")
        print("=" * 70)
        if self.test_mode:
            print("Features: Offline analysis, human-like browsing simulation")
        else:
            print("Features: Offline planning, single session downloads, anti-detection")
        print("")

        # Phase 1: Quick Reconnaissance (metadata only)
        print("Phase 1: Quick Metadata Collection")
        print("=" * 40)

        recon_data = self.quick_reconnaissance(committee_name)
        if not recon_data:
            return []

        committee = recon_data['committee']
        all_reports_metadata = recon_data['all_reports']

        # Phase 2: Offline File Analysis
        print(f"\nPhase 2: Offline File Analysis")
        print("=" * 35)

        download_plan = self.create_offline_download_plan(committee_name, all_reports_metadata)

        print(f"Total reports discovered: {download_plan['total_reports']}")
        print(f"Files already exist: {download_plan['existing_count']}")
        print(f"Files needed: {download_plan['needed_count']}")

        if download_plan['needed_count'] == 0:
            print("\nAll files already downloaded - no browser session needed!")
            return self.format_results(committee, all_reports_metadata, download_plan)

        if self.test_mode:
            print(f"\nTEST MODE: Would download {download_plan['needed_count']} files")
            return self.format_results(committee, all_reports_metadata, download_plan)

        # Phase 3: Single Download Session (only if needed)
        print(f"\nPhase 3: Single Download Session")
        print("=" * 35)
        print(f"Downloading {download_plan['needed_count']} files in one session...")

        download_results = self.execute_single_session_downloads(committee, download_plan)

        # Final results
        final_results = self.format_results(committee, all_reports_metadata, download_plan, download_results)

        # Summary
        print(f"\nSINGLE SESSION COMPLETE")
        if self.test_mode:
            print(f"Total reports: {self.total_discovered}")
            print(f"Already exist: {self.total_existing}")
            print(f"Would download: {self.total_would_download}")
        else:
            print(f"Total reports: {len(final_results)}")
            print(f"Already existed: {self.total_existing}")
            print(f"Successfully downloaded: {self.total_downloaded}")

        return final_results

    def quick_reconnaissance(self, committee_name: str) -> Dict:
        """Quick metadata-only reconnaissance"""
        recon_scraper = MECReportScraper(
            headless=self.headless,
            output_dir=self.output_dir,
            max_downloads=0
        )

        try:
            search_results = recon_scraper.search_committee(committee_name)
            if not search_results:
                print("No committees found")
                return {}

            committee = search_results[0]
            print(f"Found committee: {committee['committee_name']} (MECID: {committee['mecid']})")

            # Get all report metadata quickly
            reports = recon_scraper.get_committee_reports(committee['committee_url'], committee['committee_name'])

            print(f"Collected metadata for {len(reports)} reports")
            return {
                'committee': committee,
                'all_reports': reports
            }

        finally:
            recon_scraper.close()

    def create_offline_download_plan(self, committee_name: str, all_reports: List[Dict]) -> Dict:
        """Create download plan by checking files offline"""
        plan = {
            'total_reports': len(all_reports),
            'existing_count': 0,
            'needed_count': 0,
            'existing_files': [],
            'needed_downloads': [],
            'by_year': {}
        }

        for report in all_reports:
            year = report['year']
            if year not in plan['by_year']:
                plan['by_year'][year] = {'existing': [], 'needed': []}

            # Check if file exists offline
            exists, filepath = self.check_file_exists_offline(
                committee_name,
                report['report_name'],
                report['report_date'],
                report['report_id']
            )

            if exists:
                plan['existing_count'] += 1
                plan['existing_files'].append(report)
                plan['by_year'][year]['existing'].append(report)
                print(f"   EXISTS: {report['year']} - {report['report_id']} - {report['report_name'][:50]}")
            else:
                plan['needed_count'] += 1
                plan['needed_downloads'].append(report)
                plan['by_year'][year]['needed'].append(report)
                if self.test_mode:
                    print(f"   WOULD DOWNLOAD: {report['year']} - {report['report_id']} - {report['report_name'][:50]}")
                else:
                    print(f"   NEED: {report['year']} - {report['report_id']} - {report['report_name'][:50]}")

        self.total_discovered = plan['total_reports']
        self.total_existing = plan['existing_count']
        self.total_would_download = plan['needed_count']

        return plan

    def execute_single_session_downloads(self, committee: Dict, plan: Dict) -> Dict:
        """Execute all downloads in a single browser session with enhanced stealth"""
        print("Opening browser for single download session...")

        session_scraper = MECReportScraper(
            headless=self.headless,
            output_dir=self.output_dir,
            max_downloads=999  # No artificial limits
        )

        download_results = {'successful': [], 'failed': []}

        try:
            # Navigate to committee page
            print(f"Navigating to committee page...")
            session_scraper.driver.get(committee['committee_url'])

            # Human-like page load wait
            self.human_delay(self.page_read_time, "Reading page content")

            # Check for reCAPTCHA after initial load
            if self.check_for_recaptcha(session_scraper.driver):
                raise RecaptchaDetected("reCAPTCHA detected on initial page load")

            # Navigate to Reports tab with human-like behavior
            print("Clicking Reports tab...")
            self.human_delay(self.click_delay, "Preparing to click")

            wait = WebDriverWait(session_scraper.driver, SCRAPER_CONFIG['page_load_timeout'])
            reports_tab = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, "Reports")))
            reports_tab.click()

            # Extended page reading time after clicking Reports
            self.human_delay(self.page_read_time, "Reading reports page")

            # Check for reCAPTCHA after Reports click
            if self.check_for_recaptcha(session_scraper.driver):
                raise RecaptchaDetected("reCAPTCHA detected after clicking Reports")

            # Process each year that has needed downloads
            years_with_downloads = [year for year, data in plan['by_year'].items() if data['needed']]
            years_with_downloads.sort(reverse=True)  # Start with newest

            for i, year in enumerate(years_with_downloads):
                needed_reports = plan['by_year'][year]['needed']
                print(f"\nProcessing {year}: {len(needed_reports)} downloads needed")

                # Human delay between years
                if i > 0:
                    self.human_delay(self.year_process_delay, f"Thinking before {year}")

                # Expand year section with stealth
                year_results = self.process_year_with_stealth(
                    session_scraper, committee['committee_name'], year, needed_reports
                )

                download_results['successful'].extend(year_results['successful'])
                download_results['failed'].extend(year_results['failed'])

                # Update counters
                self.total_downloaded += len(year_results['successful'])

                print(f"   {year} complete: {len(year_results['successful'])} downloaded, {len(year_results['failed'])} failed")

                # Check for reCAPTCHA between years
                if self.check_for_recaptcha(session_scraper.driver):
                    print(f"reCAPTCHA detected after {year} - stopping downloads")
                    break

        except RecaptchaDetected as e:
            print(f"reCAPTCHA detected: {e}")
            print("Stopping download session gracefully")
        except Exception as e:
            print(f"Unexpected error in download session: {e}")
        finally:
            session_scraper.close()
            print("Browser session closed")

        return download_results

    def simulate_document_reading(self, driver):
        """Simulate human reading behavior on the PDF page"""
        try:
            # Stay on the PDF tab for 45-75 seconds total
            reading_time = random.uniform(45, 75)
            print(f"     Simulating document reading: {reading_time:.1f}s")

            # Scroll down the page gradually
            scroll_actions = 4 + random.randint(0, 3)  # 4-7 scroll actions
            time_per_scroll = reading_time / scroll_actions

            for i in range(scroll_actions):
                # Scroll down by a random amount
                scroll_pixels = random.randint(200, 500)
                driver.execute_script(f"window.scrollBy(0, {scroll_pixels});")

                # Pause as if reading
                scroll_delay = random.uniform(time_per_scroll * 0.7, time_per_scroll * 1.3)
                time.sleep(scroll_delay)

                # Occasionally scroll back up a bit (like re-reading)
                if random.random() < 0.3:  # 30% chance
                    back_scroll = random.randint(50, 150)
                    driver.execute_script(f"window.scrollBy(0, -{back_scroll});")
                    time.sleep(2)

            # Sometimes scroll back to top (like reviewing)
            if random.random() < 0.4:  # 40% chance
                driver.execute_script("window.scrollTo(0, 0);")
                time.sleep(3)

            print(f"     Finished reading document")

        except Exception as e:
            print(f"     Could not simulate reading: {e}")
            # Fall back to simple delay
            time.sleep(60)

    def process_year_with_stealth(self, scraper, committee_name: str, year: str, needed_reports: List[Dict]) -> Dict:
        """Process a single year with maximum stealth"""
        results = {'successful': [], 'failed': []}

        try:
            print(f"   Expanding {year} section...")
            self.human_delay(self.click_delay, "Preparing to expand year")

            # Find and click year expansion
            year_expanded = self.expand_year_with_stealth(scraper.driver, year)
            if not year_expanded:
                print(f"   Could not expand {year}")
                return results

            # Extended wait for content to load + human reading time
            self.human_delay((8, 15), "Waiting for content + reading")

            # Check for reCAPTCHA after expansion
            if self.check_for_recaptcha(scraper.driver):
                raise RecaptchaDetected(f"reCAPTCHA after expanding {year}")

            # Detect report links
            report_links = scraper._detect_report_links(year)
            if not report_links:
                print(f"   No report links found for {year}")
                return results

            print(f"   Found {len(report_links)} report links in {year}")

            # Process each needed report
            for i, needed_report in enumerate(needed_reports):
                if self.max_downloads > 0 and len(results['successful']) >= self.max_downloads:
                    print(f"   Reached download limit for {year}")
                    break

                print(f"   Downloading {i+1}/{len(needed_reports)}: {needed_report['report_id']}")

                # Find matching link
                report_element = None
                for element, href, text, source in report_links:
                    if text == needed_report['report_id']:
                        report_element = element
                        break

                if not report_element:
                    print(f"     Could not find link for {needed_report['report_id']}")
                    results['failed'].append(needed_report)
                    continue

                # Human delay before download
                if i > 0:
                    self.human_delay((15, 30), "Considering next download")

                # Attempt download with enhanced monitoring
                try:
                    downloaded_file = scraper._download_single_report_with_monitoring(
                        report_element, committee_name, year,
                        needed_report['report_id'],
                        needed_report['report_name'],
                        needed_report['report_date']
                    )

                    if downloaded_file:
                        results['successful'].append({
                            **needed_report,
                            'downloaded_file': downloaded_file,
                            'download_timestamp': datetime.now().isoformat()
                        })
                        print(f"     SUCCESS: {downloaded_file}")

                        # Simulate human reading behavior - scroll through the PDF
                        print(f"     Reading document...")
                        self.simulate_document_reading(scraper.driver)

                    else:
                        results['failed'].append(needed_report)
                        print(f"     FAILED: Download returned None")

                    # Check for reCAPTCHA after each download
                    if self.check_for_recaptcha(scraper.driver):
                        raise RecaptchaDetected(f"reCAPTCHA after downloading {needed_report['report_id']}")

                except Exception as e:
                    print(f"     ERROR: {e}")
                    results['failed'].append(needed_report)

                    # Check if error might be reCAPTCHA related
                    if self.check_for_recaptcha(scraper.driver):
                        raise RecaptchaDetected(f"reCAPTCHA during download error")

        except RecaptchaDetected:
            raise  # Re-raise for handling at higher level
        except Exception as e:
            print(f"   Error processing {year}: {e}")

        return results

    def expand_year_with_stealth(self, driver, year: str) -> bool:
        """Expand year section with human-like behavior"""
        try:
            # Look for year spans and buttons
            year_spans = driver.find_elements(By.XPATH, "//span[contains(@class, 'year-span') or contains(text(), '20')]")

            for span in year_spans:
                if year in span.text:
                    # Human-like delay before clicking
                    time.sleep(random.uniform(1.0, 3.0))
                    driver.execute_script("arguments[0].click();", span)
                    return True

            # Alternative method - look for expand buttons
            expand_buttons = driver.find_elements(By.XPATH, f"//input[@value='+' and preceding::span[contains(text(), '{year}')]]")
            if expand_buttons:
                time.sleep(random.uniform(1.0, 3.0))
                driver.execute_script("arguments[0].click();", expand_buttons[0])
                return True

            return False
        except Exception as e:
            print(f"     Error expanding {year}: {e}")
            return False

    def format_results(self, committee: Dict, all_reports: List[Dict], plan: Dict, download_results: Dict = None) -> List[Dict]:
        """Format final results"""
        results = []

        for report in all_reports:
            result = {
                'committee': committee,
                'report': report,
                'local_file': None,
                'download_timestamp': None,
                'already_exists': False,
                'would_download': False
            }

            # Check if file existed before downloads
            if report in plan['existing_files']:
                result['already_exists'] = True
                result['local_file'] = "existed_before_session"

            # Check if downloaded in this session
            elif download_results:
                for downloaded in download_results['successful']:
                    if downloaded['report_id'] == report['report_id']:
                        result['local_file'] = downloaded['downloaded_file']
                        result['download_timestamp'] = downloaded['download_timestamp']
                        break

            # Test mode indication
            elif self.test_mode and report in plan['needed_downloads']:
                result['would_download'] = True

            results.append(result)

        return results


def main():
    """Main CLI interface for single session scraper"""
    parser = argparse.ArgumentParser(
        description="Enhanced Single Session MEC Scraper v2.8",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_stealth_main.py single "Francis Howell Families" --max-downloads 999
  python enhanced_stealth_main.py single "Francis Howell Families" --test

Features:
  - Single browser session architecture (no reconnections)
  - Offline file existence checking
  - Human-like browsing simulation (45-90s reading times)
  - Extended delays between actions (2-60s)
  - Test mode for safe discovery
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    single_parser = subparsers.add_parser('single', help='Extract reports (single session mode)')
    single_parser.add_argument('committee_name', help='Name of the committee to search for')
    single_parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    single_parser.add_argument('--max-downloads', type=int, default=999,
                               help='Maximum downloads per year (default: 999 for all)')
    single_parser.add_argument('--output-dir', help='Output directory for downloads')
    single_parser.add_argument('--test', action='store_true',
                               help='Test mode: discovery only, no downloads (avoids reCAPTCHA)')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'single':
        print(f"Single Session Extraction: {args.committee_name}")
        if args.test:
            print("TEST MODE: Discovery only (no downloads)")
        else:
            print(f"Max downloads per year: {args.max_downloads}")
        print(f"Headless mode: {not args.no_headless}")
        print("")

        scraper = SingleSessionScraper(
            headless=not args.no_headless,
            output_dir=args.output_dir,
            max_downloads=args.max_downloads,
            test_mode=args.test
        )

        start_time = datetime.now()
        results = scraper.extract_committee_reports_single_session(args.committee_name)
        end_time = datetime.now()

        duration = end_time - start_time
        print(f"\nTotal execution time: {duration}")


if __name__ == "__main__":
    main()