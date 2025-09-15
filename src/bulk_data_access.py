"""
Alternative data access methods for Missouri Ethics Commission data

This module provides functions to access MEC data through bulk downloads
and third-party processed datasets when available.
"""

import logging
import requests
import pandas as pd
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Add parent directory to path to import config
sys.path.append(str(Path(__file__).parent.parent))
from config import CACHE_DIR, DATABASE_CONFIG

logger = logging.getLogger(__name__)


class MECBulkDataAccess:
    """
    Access MEC data through bulk download methods and alternative sources
    """

    def __init__(self, cache_dir: Path = None):
        self.cache_dir = cache_dir or CACHE_DIR
        self.cache_dir.mkdir(exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def check_mec_csv_endpoints(self) -> Dict[str, Dict]:
        """
        Check if MEC has any accessible CSV download endpoints

        Returns:
            Dictionary of endpoint URLs and their accessibility status
        """
        potential_endpoints = [
            "https://www.mec.mo.gov/MEC/Campaign_Finance/CF_ContrCSV.aspx",
            "https://www.mec.mo.gov/MEC/Campaign_Finance/CF_ExpendCSV.aspx",
            "https://www.mec.mo.gov/MEC/Campaign_Finance/CF_CommitteeCSV.aspx",
            "https://www.mec.mo.gov/MEC/Campaign_Finance/CFSearchResults.aspx"
        ]

        results = {}

        for endpoint in potential_endpoints:
            try:
                logger.info(f"Checking endpoint: {endpoint}")
                response = self.session.head(endpoint, timeout=10)

                results[endpoint] = {
                    'status_code': response.status_code,
                    'accessible': response.status_code == 200,
                    'content_type': response.headers.get('content-type', 'unknown'),
                    'content_length': response.headers.get('content-length', 'unknown')
                }

                if response.status_code == 200:
                    logger.info(f"✓ Accessible: {endpoint}")
                else:
                    logger.warning(f"✗ Not accessible ({response.status_code}): {endpoint}")

            except Exception as e:
                results[endpoint] = {
                    'status_code': None,
                    'accessible': False,
                    'error': str(e)
                }
                logger.error(f"Error checking {endpoint}: {e}")

        return results

    def get_accountability_project_info(self) -> Dict:
        """
        Get information about The Accountability Project's processed MEC data

        Returns:
            Information about accessing their processed datasets
        """
        return {
            'organization': 'The Accountability Project',
            'description': 'Processed Missouri contributions data from MEC (2011-2022)',
            'github_repo': 'https://github.com/irworkshop/accountability_datacleaning',
            'documentation': 'https://github.com/irworkshop/accountability_datacleaning/blob/master/state/mo/contribs/docs/mo_contribs_diary.md',
            'dataset_page': 'https://publicaccountability.org/datasets/356/mo-contributions/',
            'data_types': [
                'Campaign contributions',
                'Contributor information',
                'Committee information',
                'Expenditure data'
            ],
            'coverage': '2011-2022',
            'format': 'Processed CSV files',
            'access_method': 'Contact organization or check GitHub for download links'
        }

    def get_alternative_data_sources(self) -> Dict[str, Dict]:
        """
        Get information about alternative sources for Missouri campaign finance data

        Returns:
            Dictionary of alternative data sources and their details
        """
        sources = {
            'followthemoney_org': {
                'name': 'Follow the Money (National Institute on Money in Politics)',
                'url': 'https://www.followthemoney.org/state/missouri',
                'description': 'Comprehensive state campaign finance database',
                'data_types': ['Contributions', 'Expenditures', 'Candidate information'],
                'api_available': True,
                'api_docs': 'https://www.followthemoney.org/our-data/apis',
                'coverage': 'Current and historical',
                'cost': 'Free for research use'
            },
            'opensecrets_org': {
                'name': 'OpenSecrets (Center for Responsive Politics)',
                'url': 'https://www.opensecrets.org/states/summary.php?state=MO',
                'description': 'Federal and some state campaign finance data',
                'data_types': ['Federal contributions', 'Lobbying', 'Some state data'],
                'api_available': True,
                'api_docs': 'https://www.opensecrets.org/api/',
                'coverage': 'Primarily federal data',
                'cost': 'Free'
            },
            'ballotpedia': {
                'name': 'Ballotpedia',
                'url': 'https://ballotpedia.org/Missouri_campaign_finance',
                'description': 'Political information and some campaign finance data',
                'data_types': ['Candidate information', 'Election results', 'Some finance data'],
                'api_available': False,
                'coverage': 'Current elections',
                'cost': 'Free'
            },
            'fec_gov': {
                'name': 'Federal Election Commission',
                'url': 'https://www.fec.gov/data/',
                'description': 'Federal campaign finance data (for federal candidates)',
                'data_types': ['Federal contributions', 'Federal expenditures', 'Committee data'],
                'api_available': True,
                'api_docs': 'https://api.open.fec.gov/',
                'coverage': 'Federal elections only',
                'cost': 'Free'
            }
        }

        return sources

    def try_bulk_download(self, endpoint_url: str, filename: str = None) -> Optional[Path]:
        """
        Attempt to download data from a bulk endpoint

        Args:
            endpoint_url: URL to attempt download from
            filename: Optional filename (will be auto-generated if not provided)

        Returns:
            Path to downloaded file or None if failed
        """
        if not filename:
            filename = f"mec_bulk_data_{endpoint_url.split('/')[-1]}"

        cache_file = self.cache_dir / filename

        try:
            logger.info(f"Attempting bulk download from: {endpoint_url}")

            response = self.session.get(endpoint_url, timeout=60)
            response.raise_for_status()

            # Check if we got actual data (not an error page)
            if len(response.content) < 1000:
                logger.warning(f"Response too small ({len(response.content)} bytes), may be error page")
                return None

            # Save to cache
            with open(cache_file, 'wb') as f:
                f.write(response.content)

            logger.info(f"Successfully downloaded: {cache_file}")
            return cache_file

        except Exception as e:
            logger.error(f"Bulk download failed: {e}")
            return None

    def analyze_committee_coverage(self, committee_name: str) -> Dict:
        """
        Analyze what data sources might have information about a specific committee

        Args:
            committee_name: Name of committee to analyze

        Returns:
            Analysis of potential data coverage
        """
        analysis = {
            'committee_name': committee_name,
            'potential_sources': [],
            'recommendations': []
        }

        # Check if it's a federal committee (would be in FEC data)
        federal_indicators = ['for congress', 'for senate', 'for president', 'federal', 'pac']
        is_likely_federal = any(indicator in committee_name.lower() for indicator in federal_indicators)

        if is_likely_federal:
            analysis['potential_sources'].append({
                'source': 'FEC',
                'likelihood': 'High',
                'reason': 'Committee name suggests federal activity'
            })

        # All Missouri committees should be in MEC data
        analysis['potential_sources'].append({
            'source': 'Missouri Ethics Commission (Primary)',
            'likelihood': 'High',
            'reason': 'All Missouri committees must file with MEC'
        })

        # May be in Follow the Money
        analysis['potential_sources'].append({
            'source': 'Follow the Money',
            'likelihood': 'Medium',
            'reason': 'Comprehensive state database, but coverage varies'
        })

        # Generate recommendations
        analysis['recommendations'] = [
            'Start with MEC scraper for complete quarterly reports',
            'Check Follow the Money API for contribution summaries',
            'Cross-reference with FEC data if federal activity suspected',
            'Use Accountability Project data for historical analysis'
        ]

        return analysis


def get_data_access_strategy(committee_name: str) -> Dict:
    """
    Get a comprehensive data access strategy for a specific committee

    Args:
        committee_name: Name of committee

    Returns:
        Recommended data access strategy
    """
    bulk_access = MECBulkDataAccess()

    strategy = {
        'committee_name': committee_name,
        'primary_method': 'MEC Web Scraping',
        'primary_reason': 'Most complete data with full quarterly reports',
        'alternative_methods': [],
        'bulk_data_status': {},
        'coverage_analysis': {}
    }

    # Check bulk endpoints
    strategy['bulk_data_status'] = bulk_access.check_mec_csv_endpoints()

    # Get alternative sources
    alt_sources = bulk_access.get_alternative_data_sources()
    strategy['alternative_methods'] = [
        {
            'source': details['name'],
            'url': details['url'],
            'use_case': 'Cross-reference and historical analysis'
        }
        for details in alt_sources.values()
    ]

    # Analyze committee coverage
    strategy['coverage_analysis'] = bulk_access.analyze_committee_coverage(committee_name)

    return strategy


if __name__ == "__main__":
    # Test the bulk data access functionality
    print("=== MEC Bulk Data Access Test ===")

    bulk_access = MECBulkDataAccess()

    # Check CSV endpoints
    print("\n1. Checking MEC CSV endpoints...")
    csv_status = bulk_access.check_mec_csv_endpoints()
    for endpoint, status in csv_status.items():
        print(f"   {endpoint}: {'✓' if status['accessible'] else '✗'}")

    # Get alternative sources
    print("\n2. Alternative data sources:")
    alt_sources = bulk_access.get_alternative_data_sources()
    for source_key, source_info in alt_sources.items():
        print(f"   - {source_info['name']}: {source_info['description']}")

    # Analyze a specific committee
    print("\n3. Committee analysis:")
    committee = "Francis Howell Families"
    analysis = bulk_access.analyze_committee_coverage(committee)
    print(f"   Committee: {committee}")
    for source in analysis['potential_sources']:
        print(f"   - {source['source']}: {source['likelihood']} likelihood")

    # Get comprehensive strategy
    print(f"\n4. Data access strategy for '{committee}':")
    strategy = get_data_access_strategy(committee)
    print(f"   Primary method: {strategy['primary_method']}")
    print(f"   Reason: {strategy['primary_reason']}")