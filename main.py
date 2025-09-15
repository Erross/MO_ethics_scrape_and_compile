"""
Main entry point for MEC Campaign Finance Scraper

This script provides different modes of operation:
1. Single committee extraction
2. Batch committee extraction
3. Data access strategy analysis
4. Bulk data exploration
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


def extract_single_committee(committee_name: str, headless: bool = True, output_dir: str = None) -> None:
    """Extract reports for a single committee"""
    print(f"🔍 Extracting reports for: {committee_name}")
    print(f"📁 Output directory: {output_dir or DOWNLOADS_DIR}")
    print(f"🖥️  Headless mode: {headless}")
    print("-" * 50)

    try:
        results = extract_committee_reports(
            committee_name=committee_name,
            output_dir=output_dir,
            headless=headless
        )

        if results:
            print(f"\n✅ Successfully downloaded {len(results)} reports:")
            for result in results:
                committee_name = result['committee']['committee_name']
                report_name = result['report']['report_name']
                year = result['report']['year']
                file_path = result['local_file']
                print(f"   📄 {committee_name} - {year} - {report_name}")
                print(f"      📂 {file_path}")
        else:
            print(f"\n❌ No reports found for '{committee_name}'")
            print("   💡 Try checking the committee name spelling or search on the MEC website first")

    except Exception as e:
        print(f"\n❌ Error during extraction: {e}")
        print("   💡 Try running with --debug flag for more information")


def extract_batch_committees(committee_file: str, headless: bool = True, output_dir: str = None) -> None:
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
    print("-" * 50)

    total_reports = 0
    successful_committees = 0

    for i, committee_name in enumerate(committees, 1):
        print(f"\n[{i}/{len(committees)}] Processing: {committee_name}")

        try:
            results = extract_committee_reports(
                committee_name=committee_name,
                output_dir=output_dir,
                headless=headless
            )

            if results:
                print(f"   ✅ Downloaded {len(results)} reports")
                total_reports += len(results)
                successful_committees += 1
            else:
                print(f"   ⚠️  No reports found")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    print(f"\n📊 Batch processing complete:")
    print(f"   ✅ Successful committees: {successful_committees}/{len(committees)}")
    print(f"   📄 Total reports downloaded: {total_reports}")


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

        print(f"\n📊 Bulk Data Endpoint Status:")
        for endpoint, status in strategy['bulk_data_status'].items():
            status_icon = "✅" if status['accessible'] else "❌"
            print(f"   {status_icon} {endpoint}")

        print(f"\n🎯 Coverage Analysis:")
        coverage = strategy['coverage_analysis']
        for source in coverage['potential_sources']:
            print(f"   • {source['source']}: {source['likelihood']} likelihood")
            print(f"     Reason: {source['reason']}")

        print(f"\n💡 Recommendations:")
        for rec in coverage['recommendations']:
            print(f"   • {rec}")

    except Exception as e:
        print(f"❌ Error during analysis: {e}")


def explore_bulk_data() -> None:
    """Explore available bulk data options"""
    print("🔍 Exploring MEC bulk data options...")
    print("-" * 50)

    try:
        bulk_access = MECBulkDataAccess()

        # Check CSV endpoints
        print("📊 Checking MEC CSV endpoints:")
        csv_status = bulk_access.check_mec_csv_endpoints()
        accessible_count = sum(1 for status in csv_status.values() if status.get('accessible', False))

        for endpoint, status in csv_status.items():
            status_icon = "✅" if status['accessible'] else "❌"
            print(f"   {status_icon} {endpoint}")
            if status.get('error'):
                print(f"      Error: {status['error']}")

        print(f"\n📈 Summary: {accessible_count}/{len(csv_status)} endpoints accessible")

        # Show alternative sources
        print(f"\n🌐 Alternative Data Sources:")
        alt_sources = bulk_access.get_alternative_data_sources()
        for source_key, source_info in alt_sources.items():
            api_status = "✅ API Available" if source_info.get('api_available') else "❌ No API"
            print(f"   • {source_info['name']} - {api_status}")
            print(f"     {source_info['description']}")
            print(f"     URL: {source_info['url']}")

        # Show Accountability Project info
        print(f"\n📚 Accountability Project Data:")
        ap_info = bulk_access.get_accountability_project_info()
        print(f"   Coverage: {ap_info['coverage']}")
        print(f"   Data types: {', '.join(ap_info['data_types'])}")
        print(f"   GitHub: {ap_info['github_repo']}")

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
        description="Missouri Ethics Commission Campaign Finance Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py single "Francis Howell Families"
  python main.py single "Missouri Republican Party" --no-headless --output ./reports
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

    # Batch committee extraction
    batch_parser = subparsers.add_parser('batch', help='Extract reports for multiple committees')
    batch_parser.add_argument('committee_file', help='File containing committee names (one per line)')
    batch_parser.add_argument('--output', '-o', help='Output directory for downloads')
    batch_parser.add_argument('--no-headless', action='store_true', help='Show browser window (for debugging)')

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

    print("🏛️  Missouri Ethics Commission Campaign Finance Scraper")
    print("=" * 60)

    try:
        if args.command == 'single':
            extract_single_committee(
                committee_name=args.committee_name,
                headless=not args.no_headless,
                output_dir=args.output
            )

        elif args.command == 'batch':
            extract_batch_committees(
                committee_file=args.committee_file,
                headless=not args.no_headless,
                output_dir=args.output
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