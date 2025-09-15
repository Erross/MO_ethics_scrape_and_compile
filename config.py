"""
Configuration settings for MEC Campaign Finance Scraper
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"
CACHE_DIR = PROJECT_ROOT / "cache"
LOGS_DIR = PROJECT_ROOT / "logs"

# Create directories if they don't exist
for directory in [DOWNLOADS_DIR, CACHE_DIR, LOGS_DIR]:
    directory.mkdir(exist_ok=True)

# MEC Website URLs
MEC_BASE_URL = "https://mec.mo.gov"
MEC_SEARCH_URL = "https://mec.mo.gov/MEC/Campaign_Finance/CFSearch.aspx"

# Scraper settings
SCRAPER_CONFIG = {
    'headless': True,  # Set to False for debugging
    'page_load_timeout': 30,
    'download_timeout': 60,
    'delay_between_requests': 2,  # seconds
    'max_retries': 3,
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

# Logging configuration
LOGGING_CONFIG = {
    'level': 'INFO',
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'file': LOGS_DIR / 'mec_scraper.log'
}

# Database settings (if using SQLite storage)
DATABASE_CONFIG = {
    'db_path': PROJECT_ROOT / 'mec_data.db',
    'enable_db_storage': True
}

# Cache settings
CACHE_CONFIG = {
    'enable_cache': True,
    'cache_ttl_hours': 24,
    'cache_search_results': True,
    'cache_committee_info': True
}