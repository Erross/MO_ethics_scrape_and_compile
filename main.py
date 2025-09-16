"""
Main entry point for MEC Campaign Finance Scraper

This script provides different modes of operation:
1. Single committee extraction
2. Batch committee extraction
3. Data access strategy analysis
4. Bulk data exploration

VERSION: 2.3 - Updated 2025-09-15 - Added max-downloads support
"""

import argparse
import sys
import json
from pathlib import Path
from typing import List

# Add src directory to path so we can import our modules
project_root = Path(__file__).parent
sys.path.append(str(project_root / "src"))
sys.path.append(str(project_root))

from mec_scraper import MECReportScraper, extract_committee_reports
from bulk_data_access import MECBulkDataAccess, get_data_access_strategy
from config import DOWNLOADS_DIR, SCRAPER_CONFIG


def extract_single_committee(committee_name: str, headless: bool = True, output_dir: str = None, max_downloads: int = 3) -> None:
    """Extract reports for a single committee"""
    print(f"🔍 Extracting reports for: {committee_name}")
    print(f"📁 Output directory: {output_dir or DOWNLOADS_DIR}")
    print(f"🖥️  Headless mode: {headless}")
    print(f"⬇️  Max downloads per year: {max_downloads}")
    print("-" * 50)

    try:
        results = extract_committee_reports(
            committee_name=committee_name,
            output_dir=output_dir,
            headless=headless,
            max_downloads=max_downloads
        )

        if results:
            print(f"\n✅ Successfully found {len(results)} reports:")
            for result in results:
                committee = result['committee']['committee_name']
                report = result['report']
                print(f"   📄 {committee} - {report['year']} - {report['report_name']} ({report['report_date']})")
                if result.get('local_file'):
                    print(f"      📂 Downloaded: {result['local_file']}")
                else:
                    print(f"      📄 Report ID: {report['report_id']}")
        else:
            print(f"\n❌ No reports found for '{committee_name}'")
            print("   💡 Try checking the committee name spelling or search on the MEC website first")

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        print("   💡 Try running with --no-headless flag to see what's happening in the browser")


def extract_batch_committees(committee_file: str, headless: bool = True, output_dir: str = None, max_downloads: int = 3) -> None:
    """Extract reports for multiple committees from a file"""
    committee_file_path = Path(committee_file)

    if not committee_file_path.exists():
        print(f"❌ Committee file not found: {committee_file}")
        return

    # Read committee names from file (one per line)
    try:
        with open(committee_file_path, 'r', encoding='utf-8') as f:
            committees = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"❌ Error reading committee file: {e}")
        return

    print(f"📋 Found {len(committees)} committees to process")
    print(f"📁 Output directory: {output_dir or DOWNLOADS_DIR}")
    print(f"⬇️  Max downloads per committee per year: {max_downloads}")
    print("-" * 50)

    total_reports = 0
    successful_committees = 0

    for i, committee_name in enumerate(committees, 1):
        print(f"\n[{i}/{len(committees)}] Processing: {committee_name}")

        try:
            results = extract_committee_reports(
                committee_name=committee_name,
                output_dir=output_dir,
                headless=headless,
                max_downloads=max_downloads
            )

            if results:
                print(f"   ✅ Found {len(results)} reports")
                total_reports += len(results)
                successful_committees += 1

                # Show downloaded files
                downloaded = [r for r in results if r.get('local_file')]
                if downloaded:
                    print(f"   📄 Downloaded {len(downloaded)} files")
            else:
                print(f"   ⚠️  No reports found")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n📊 Batch processing complete:")
    print(f"   ✅ Successful committees: {successful_committees}/{len(committees)}")
    print(f"   📄 Total reports found: {total_reports}")


def analyze_data_strategy(committee_name: str) -> None:
    """Analyze data access strategy for a committee"""
    print(f"🔍 Analyzing data access strategy for: {committee_name}")
    print("-" * 50)

    try:
        strategy = get_data_access_strategy(committee_name)

        print(f"\n📋 Primary Method: {strategy['primary_method']}")
        print(f"💡 Reason: {strategy['primary_reason']}")

        print(f"\n🌐 Alternative Data Sources:")
        for alt_method in strategy['alternative_methods']:
            print(f"   • {alt_method['source']}")
            print(f"     URL: {alt_method['url']}")
            print(f"     Use case: {alt_method['use_case']}")

        print(f"\n📊 Bulk Data Endpoints:")
        if strategy['bulk_data_endpoints']:
            for endpoint in strategy['bulk_data_endpoints']:
                print(f"   • {endpoint['name']}: {endpoint['url']}")
                print(f"     Description: {endpoint['description']}")
        else:
            print("   No bulk data endpoints available for this committee type")

        print(f"\n💡 Recommendation:")
        print(f"   {strategy['recommendation']}")

    except Exception as e:
        print(f"❌ Error analyzing data strategy: {e}")


def explore_bulk_data() -> None:
    """Explore available bulk data options"""
    print("🔍 Exploring MEC Bulk Data Access Options")
    print("-" * 50)

    try:
        bulk_access = MECBulkDataAccess()
        available_endpoints = bulk_access.get_available_endpoints()

        print(f"\n📊 Available Data Sources ({len(available_endpoints)} found):")

        for endpoint in available_endpoints:
            print(f"\n• {endpoint['name']}")
            print(f"  URL: {endpoint['url']}")
            print(f"  Method: {endpoint['method']}")
            print(f"  Description: {endpoint['description']}")

            # Test endpoint accessibility
            try:
                ap_info = bulk_access.get_api_info(endpoint['url'])
                print(f"  ✅ Status: Accessible")
                if ap_info:
                    print(f"   Coverage: {ap_info.get('coverage', 'Unknown')}")
                    print(f"   Data types: {', '.join(ap_info.get('data_types', []))}")
                    if ap_info.get('github_repo'):
                        print(f"   GitHub: {ap_info['github_repo']}")
            except Exception as api_e:
                print(f"  ⚠️  Status: {api_e}")

    except Exception as e:
        print(f"❌ Error exploring bulk data: {e}")


def create_sample_committee_file() -> None:
    """Create a sample committee file for batch processing"""
    sample_file = Path("sample_committees.txt")

    sample_committees = [
        "Francis Howell Families",
        "Missouri Republican Party",
        "Citizens for Excellence in Education",
        "Committee to Elect John Doe",
        "Friends of Jane Smith"
    ]

    try:
        with open(sample_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(sample_committees))

        print(f"✅ Created sample committee file: {sample_file}")
        print("   Edit this file with your desired committee names (one per line)")

    except Exception as e:
        print(f"❌ Error creating sample file: {e}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Missouri Ethics Commission Campaign Finance Scraper v2.3",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py single "Francis Howell Families"
  python main.py single "Missouri Republican Party" --no-headless --output ./reports --max-downloads 10
  python main.py single "Francis Howell Families" --max-downloads 999  # Download all files
  python main.py batch committees.txt
  python main.py strategy "Francis Howell Families"
  python main.py explore
  python main.py create-sample
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Single committee extraction
    single_parser = subparsers.add_parser('single', help='Extract reports for a single committee')
    single_parser.add_argument('committee_name', help='Name of the committee to search for')
    single_parser.add_argument('--output', '-o', help='Output directory for downloads')
    single_parser.add_argument('--no-headless', action='store_true', help='Show browser window (for debugging)')
    single_parser.add_argument('--max-downloads', type=int, default=3, help='Maximum downloads per year (default: 3, use 999 for all)')

    # Batch committee extraction
    batch_parser = subparsers.add_parser('batch', help='Extract reports for multiple committees')
    batch_parser.add_argument('committee_file', help='File containing committee names (one per line)')
    batch_parser.add_argument('--output', '-o', help='Output directory for downloads')
    batch_parser.add_argument('--no-headless', action='store_true', help='Show browser window (for debugging)')
    batch_parser.add_argument('--max-downloads', type=int, default=3, help='Maximum downloads per committee per year (default: 3)')

    # Strategy analysis
    strategy_parser = subparsers.add_parser('strategy', help='Analyze data access strategy for a committee')
    strategy_parser.add_argument('committee_name', help='Name of the committee to analyze')

    # Bulk data exploration
    subparsers.add_parser('explore', help='Explore available bulk data options')

    # Create sample file
    subparsers.add_parser('create-sample', help='Create a sample committee file for batch processing')

    # Parse arguments
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    print("🏛️  Missouri Ethics Commission Campaign Finance Scraper v2.3")
    print("=" * 60)

    try:
        if args.command == 'single':
            extract_single_committee(
                committee_name=args.committee_name,
                headless=not args.no_headless,
                output_dir=args.output,
                max_downloads=args.max_downloads
            )

        elif args.command == 'batch':
            extract_batch_committees(
                committee_file=args.committee_file,
                headless=not args.no_headless,
                output_dir=args.output,
                max_downloads=args.max_downloads
            )

        elif args.command == 'strategy':
            analyze_data_strategy(args.committee_name)

        elif args.command == 'explore':
            explore_bulk_data()

        elif args.command == 'create-sample':
            create_sample_committee_file()

    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("   💡 Try running with --no-headless flag to see what's happening in the browser")


if __name__ == "__main__":
    main()