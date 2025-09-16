"""
Anti-Detection MEC Scraper - Multi-Session Approach

This version uses separate browser sessions for each year to evade bot detection.
Includes longer pauses and human-like behavior patterns.

Usage:
    python stealth_main.py single "Francis Howell Families" --max-downloads 999

VERSION: 2.5 - Anti-Detection Multi-Session - 2025-09-16
"""

import argparse
import sys
import json
import time
import random
from pathlib import Path
from typing import List, Dict
from datetime import datetime

# Add src directory to path so we can import our modules
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from mec_scraper import MECReportScraper
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from config import DOWNLOADS_DIR, SCRAPER_CONFIG
except ImportError:
    DOWNLOADS_DIR = Path("downloads")
    SCRAPER_CONFIG = {'page_load_timeout': 30}


class StealthMECScraper:
    """Anti-detection scraper that uses separate sessions for each year"""

    def __init__(self, headless: bool = True, output_dir: str = None, max_downloads: int = 3):
        self.headless = headless
        self.output_dir = Path(output_dir) if output_dir else DOWNLOADS_DIR
        self.output_dir.mkdir(exist_ok=True)
        self.max_downloads = max_downloads

    def reconnaissance_run(self, committee_name: str) -> Dict:
        """
        Phase 1: Reconnaissance - gather info about available years and reports
        """
        print(f"Phase 1: Reconnaissance for {committee_name}")
        print("=" * 50)

        # Create a temporary scraper just for reconnaissance
        recon_scraper = MECReportScraper(
            headless=self.headless,
            output_dir=self.output_dir,
            max_downloads=0  # No downloads during recon
        )

        try:
            # Search for committee
            search_results = recon_scraper.search_committee(committee_name)

            if not search_results:
                print("No committees found")
                return {}

            committee = search_results[0]
            print(f"Found committee: {committee['committee_name']} (MECID: {committee['mecid']})")

            # Get reports info (but don't download)
            reports = recon_scraper.get_committee_reports(committee['committee_url'], committee['committee_name'])

            # Organize by year
            year_summary = {}
            for report in reports:
                year = report['year']
                if year not in year_summary:
                    year_summary[year] = []
                year_summary[year].append({
                    'report_id': report['report_id'],
                    'report_name': report['report_name'],
                    'report_date': report['report_date']
                })

            # Print summary
            print(f"\nReconnaissance Summary:")
            total_reports = len(reports)
            print(f"   Total reports found: {total_reports}")

            for year in sorted(year_summary.keys(), reverse=True):
                report_count = len(year_summary[year])
                print(f"   {year}: {report_count} reports")

            print(f"\nStrategy: Will use {len(year_summary)} separate sessions (one per year)")

            return {
                'committee': committee,
                'year_summary': year_summary,
                'total_reports': total_reports
            }

        finally:
            recon_scraper.close()
            print("Reconnaissance session closed")

    def harvest_year(self, committee: Dict, year: str, expected_reports: List[Dict], session_num: int,
                     total_sessions: int) -> List[Dict]:
        """
        Phase 2: Harvest a specific year using a fresh browser session
        """
        print(
            f"\nPhase 2: Session {session_num}/{total_sessions} - Harvesting {year} ({len(expected_reports)} reports)")
        print("-" * 50)

        # Longer random delay between sessions (30-90 seconds)
        if session_num > 1:  # Skip delay for first session
            delay = random.uniform(30.0, 90.0)
            print(f"Anti-detection delay: {delay:.1f} seconds")

            # Show countdown for long delays
            if delay > 60:
                for remaining in range(int(delay), 0, -10):
                    print(f"   Waiting... {remaining}s remaining")
                    time.sleep(10)
                time.sleep(delay % 10)
            else:
                time.sleep(delay)

        # Create fresh scraper for this year only
        year_scraper = MECReportScraper(
            headless=self.headless,
            output_dir=self.output_dir,
            max_downloads=self.max_downloads
        )

        try:
            # Navigate fresh to committee page
            reports = year_scraper.get_single_year_reports(
                committee['committee_url'],
                committee['committee_name'],
                year
            )

            # Filter to only this year's reports
            year_reports = [r for r in reports if r['year'] == year]

            downloaded_count = len([r for r in year_reports if r.get('local_file')])
            print(f"Harvested {len(year_reports)} reports from {year} ({downloaded_count} downloaded)")

            return year_reports

        except Exception as e:
            print(f"Error harvesting {year}: {e}")
            return []

        finally:
            year_scraper.close()
            print(f"{year} session closed")

    def extract_committee_reports_stealth(self, committee_name: str) -> List[Dict]:
        """
        Main stealth extraction using multi-session approach
        """
        print("STEALTH MODE: Multi-Session Anti-Detection Scraper")
        print("=" * 60)
        print("This will take 30+ minutes to avoid detection")
        print("Each year will use a fresh browser session with delays")
        print("")

        # Phase 1: Reconnaissance
        recon_data = self.reconnaissance_run(committee_name)

        if not recon_data:
            return []

        committee = recon_data['committee']
        year_summary = recon_data['year_summary']

        # Phase 2: Harvest each year separately
        all_reports = []
        years_to_process = sorted(year_summary.keys(), reverse=True)  # Start with newest

        for i, year in enumerate(years_to_process, 1):
            expected_reports = year_summary[year]

            year_reports = self.harvest_year(
                committee,
                year,
                expected_reports,
                session_num=i,
                total_sessions=len(years_to_process)
            )

            # Convert to the expected format
            for report in year_reports:
                all_reports.append({
                    'committee': committee,
                    'report': report,
                    'local_file': report.get('local_file'),
                    'download_timestamp': report.get('download_timestamp')
                })

        print(f"\nSTEALTH EXTRACTION COMPLETE")
        print(f"Total reports processed: {len(all_reports)}")

        # Show downloaded files summary
        downloaded = [r for r in all_reports if r.get('local_file')]
        if downloaded:
            print(f"Successfully downloaded: {len(downloaded)} files")

        return all_reports


# Add the single year method to MECReportScraper
def get_single_year_reports(self, committee_url: str, committee_name: str, target_year: str) -> List[Dict]:
    """
    Enhanced method to get reports for a single year only with human-like behavior
    """
    self.logger.info(f"[STEALTH] Getting reports for {target_year} only from: {committee_url}")

    try:
        # Navigate to committee page
        self.driver.get(committee_url)

        # Random pause after page load (human-like)
        time.sleep(random.uniform(2.0, 4.0))

        wait = WebDriverWait(self.driver, SCRAPER_CONFIG['page_load_timeout'])

        # Click on Reports tab
        reports_tab = wait.until(
            EC.element_to_be_clickable((By.LINK_TEXT, "Reports"))
        )

        # Human-like pause before clicking
        time.sleep(random.uniform(1.0, 2.0))
        reports_tab.click()

        # Longer pause after clicking reports tab
        time.sleep(random.uniform(3.0, 5.0))

        # Process only the target year
        self.logger.info(f"[STEALTH] Processing target year: {target_year}")

        # Find and expand the target year section
        expand_success = self._expand_year_section_stealth(target_year)

        if not expand_success:
            self.logger.warning(f"[STEALTH] Could not expand {target_year} section")
            return []

        # Longer pause after expanding section
        time.sleep(random.uniform(5.0, 8.0))

        # Detect report links for this year
        potential_links = self._detect_report_links(target_year)

        if not potential_links:
            self.logger.warning(f"[STEALTH] NO REPORT LINKS FOUND for {target_year}")
            return []

        self.logger.info(f"[STEALTH] Found {len(potential_links)} report links for {target_year}")

        # Extract report details and download with delays
        enhanced_reports = []
        for element, href, text, source in potential_links:
            report_details = self._extract_report_details_from_table(text, target_year)

            report_data = {
                'element': element,
                'year': target_year,
                'report_id': text,
                'report_name': report_details['name'],
                'report_date': report_details['date'],
                'report_url': href,
                'detection_method': source
            }

            enhanced_reports.append(report_data)
            self.logger.info(
                f"[STEALTH] ADDED REPORT: {target_year} - {text} - {report_details['name']} ({report_details['date']})")

        # Download files if enabled
        if self.max_downloads > 0:
            download_count = min(len(enhanced_reports), self.max_downloads)
            reports_to_download = enhanced_reports[:download_count]

            self.logger.info(f"[STEALTH] Downloading {len(reports_to_download)} files from {target_year}")

            for i, report in enumerate(reports_to_download):
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
                        report['local_file'] = downloaded_file
                        report['download_timestamp'] = datetime.now().isoformat()
                        self.logger.info(f"[STEALTH] Downloaded: {downloaded_file}")

                    # Longer pause between downloads within same session (10-20 seconds)
                    if i < len(reports_to_download) - 1:
                        download_delay = random.uniform(10.0, 20.0)
                        self.logger.info(f"[STEALTH] Download delay: {download_delay:.1f}s")
                        time.sleep(download_delay)

                except Exception as e:
                    self.logger.error(f"[STEALTH] Download error for {report['report_id']}: {e}")

        return enhanced_reports

    except Exception as e:
        self.logger.error(f"[STEALTH] Error getting single year reports: {e}")
        return []


def _expand_year_section_stealth(self, year: str) -> bool:
    """
    Stealth version of year section expansion with human-like delays
    """
    self.logger.info(f"[STEALTH] Attempting to expand year {year} section")

    # Method 1: Standard approach with delays
    try:
        year_spans = self.driver.find_elements(By.CSS_SELECTOR, "span[id*='lblYear']")
        expand_buttons = self.driver.find_elements(By.CSS_SELECTOR, "input[id*='ImgRptRight']")

        self.logger.info(f"[STEALTH] Found {len(year_spans)} year spans, {len(expand_buttons)} expand buttons")

        for i, span in enumerate(year_spans):
            span_text = span.text.strip()
            if span_text == year and i < len(expand_buttons):
                expand_button = expand_buttons[i]

                # Check if already expanded
                button_src = expand_button.get_attribute('src') or ''
                if 'down' in button_src.lower() or 'collapse' in button_src.lower():
                    self.logger.info(f"[STEALTH] Year {year} appears already expanded")
                    return True

                # Human-like interaction: scroll to view, pause, then click
                self.driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                                           expand_button)
                time.sleep(random.uniform(2.0, 4.0))

                self.logger.info(f"[STEALTH] Clicking expand button for {year}")
                self.driver.execute_script("arguments[0].click();", expand_button)

                # Longer wait for expansion with human-like variation
                wait_time = random.uniform(8.0, 12.0)
                self.logger.info(f"[STEALTH] Waiting {wait_time:.1f} seconds for {year} content to load...")
                time.sleep(wait_time)
                return True

    except Exception as e:
        self.logger.warning(f"[STEALTH] Expansion failed for {year}: {e}")

    return False


# Monkey patch the methods onto MECReportScraper
MECReportScraper.get_single_year_reports = get_single_year_reports
MECReportScraper._expand_year_section_stealth = _expand_year_section_stealth


def main():
    """Main CLI interface for stealth scraper"""
    parser = argparse.ArgumentParser(
        description="Stealth MEC Report Scraper v2.5 (Anti-Detection)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python stealth_main.py single "Francis Howell Families" --max-downloads 999
  python stealth_main.py single "Missouri Republican Party" --no-headless --max-downloads 5

Note: This will be slow (30+ minutes) to avoid bot detection.
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Single committee extraction
    single_parser = subparsers.add_parser('single', help='Extract reports for a single committee (stealth mode)')
    single_parser.add_argument('committee_name', help='Name of the committee to search for')
    single_parser.add_argument('--no-headless', action='store_true', help='Show browser window')
    single_parser.add_argument('--max-downloads', type=int, default=3,
                               help='Maximum downloads per year (default: 3, use 999 for all)')
    single_parser.add_argument('--output-dir', help='Output directory for downloads')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    if args.command == 'single':
        print(f"Starting stealth extraction for: {args.committee_name}")
        print(f"Max downloads per year: {args.max_downloads}")
        print(f"Headless mode: {not args.no_headless}")
        print("Warning: This process will take 30+ minutes due to anti-detection delays")
        print("")

        stealth_scraper = StealthMECScraper(
            headless=not args.no_headless,
            output_dir=args.output_dir,
            max_downloads=args.max_downloads
        )

        start_time = datetime.now()
        results = stealth_scraper.extract_committee_reports_stealth(args.committee_name)
        end_time = datetime.now()

        duration = end_time - start_time

        # Show final results
        print(f"\nFINAL RESULTS:")
        print(f"   Committee: {args.committee_name}")
        print(f"   Total reports found: {len(results)}")
        print(f"   Total time: {duration}")

        downloaded_files = [r for r in results if r.get('local_file')]
        if downloaded_files:
            print(f"   Successfully downloaded: {len(downloaded_files)} files")
            print("\nDownloaded files:")
            for result in downloaded_files:
                report = result['report']
                print(f"      {report['year']} - {report['report_name']} ({report['report_date']})")


if __name__ == "__main__":
    main()