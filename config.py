#!/usr/bin/env python3
# ABOUTME: Central configuration management for talent intelligence system
# ABOUTME: Handles environment variables, paths, and settings

"""
Configuration Management System

This module provides centralized configuration for the entire talent database.
Replaces hardcoded paths and settings throughout the codebase.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import json
from datetime import datetime

# Load environment variables from .env file
def load_env_file():
    """Load .env file if it exists"""
    env_path = Path(__file__).parent / ".env"
    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key.strip(), value.strip())

# Load environment variables
load_env_file()

class Config:
    """Central configuration class"""
    
    # Base paths
    BASE_DIR = Path(__file__).parent.resolve()
    DATA_DIR = BASE_DIR.parent  # /Users/charlie.kerr/Documents/CK Docs
    
    # Database paths
    DB_PATH = BASE_DIR / "talent_intelligence.db"
    BACKUP_DIR = BASE_DIR / "backups"
    
    # CSV source directories
    CSV_SOURCES = {
        'merged_output': DATA_DIR / "merged_output",
        'csv_organized': DATA_DIR / "CSV_Final_Organized",
        'github_csvs': BASE_DIR,
        'validation': DATA_DIR / "validation"
    }
    
    # Log files
    LOG_DIR = BASE_DIR / "logs"
    LOG_DIR.mkdir(exist_ok=True)
    
    IMPORT_LOG = LOG_DIR / "import.log"
    ENRICHMENT_LOG = LOG_DIR / "enrichment.log"
    API_LOG = LOG_DIR / "api.log"
    ERROR_LOG = LOG_DIR / "errors.log"
    
    # Report files
    REPORTS_DIR = BASE_DIR / "reports"
    REPORTS_DIR.mkdir(exist_ok=True)
    
    DATA_QUALITY_REPORT = REPORTS_DIR / "data_quality_report.txt"
    DEDUPLICATION_REPORT = REPORTS_DIR / "deduplication_report.txt"
    GITHUB_ENRICHMENT_REPORT = REPORTS_DIR / "github_enrichment_report.txt"
    COMPANY_QUALITY_REPORT = REPORTS_DIR / "company_quality_report.txt"
    
    # API Configuration
    GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN')
    GITHUB_API_BASE = 'https://api.github.com'
    GITHUB_RATE_LIMIT_BUFFER = 100
    GITHUB_REQUEST_DELAY = 0.72  # seconds between requests (5000/hour)
    
    # Processing configuration
    BATCH_SIZE = 5000  # Records to process at once
    CHECKPOINT_EVERY = 100  # Commit database every N records
    MIN_QUALITY_THRESHOLD = 0.3  # Minimum data quality score
    
    # Backup configuration
    BACKUP_RETENTION_DAYS = 30
    BACKUP_COMPRESSION = True
    
    # Deduplication settings
    DEDUP_AGGRESSIVE = False  # If True, merge more aggressively
    DEDUP_CONFIDENCE_THRESHOLD = 0.8  # Confidence needed for auto-merge
    
    # Export settings
    EXPORT_DIR = BASE_DIR / "exports"
    EXPORT_DIR.mkdir(exist_ok=True)
    
    @classmethod
    def get_csv_files(cls, category: str = None) -> list:
        """Get list of CSV files from specified category or all categories"""
        csv_files = []
        
        if category and category in cls.CSV_SOURCES:
            source_dir = cls.CSV_SOURCES[category]
            if source_dir.exists():
                csv_files.extend(source_dir.glob("*.csv"))
        else:
            # Get from all sources
            for source_dir in cls.CSV_SOURCES.values():
                if source_dir.exists():
                    csv_files.extend(source_dir.glob("*.csv"))
        
        return sorted(csv_files)
    
    @classmethod
    def get_github_csv_patterns(cls) -> Dict[str, str]:
        """Get patterns for identifying GitHub CSV files"""
        return {
            'contributors': ['contributor', 'github_contributor'],
            'organizations': ['github_org', 'organization', 'company_github'],
            'profiles': ['github_profile', 'github_user']
        }
    
    @classmethod
    def validate_environment(cls) -> Dict[str, bool]:
        """Check that all required configuration is present"""
        checks = {
            'database_exists': cls.DB_PATH.exists(),
            'data_dir_exists': cls.DATA_DIR.exists(),
            'github_token_set': bool(cls.GITHUB_TOKEN and cls.GITHUB_TOKEN != 'your_token_here'),
            'backup_dir_exists': cls.BACKUP_DIR.exists(),
            'log_dir_writable': cls.LOG_DIR.exists() and os.access(cls.LOG_DIR, os.W_OK)
        }
        
        return checks
    
    @classmethod
    def get_status(cls) -> str:
        """Get configuration status summary"""
        checks = cls.validate_environment()
        
        status = f"""
Configuration Status
====================
Base Directory:     {cls.BASE_DIR}
Database Path:      {cls.DB_PATH}
Database Exists:    {'✅' if checks['database_exists'] else '❌'}
GitHub Token:       {'✅ Configured' if checks['github_token_set'] else '❌ Not set or invalid'}
Backup Directory:   {'✅' if checks['backup_dir_exists'] else '❌'}
Logs Writable:      {'✅' if checks['log_dir_writable'] else '❌'}

CSV Sources Found:
"""
        for name, path in cls.CSV_SOURCES.items():
            if path.exists():
                csv_count = len(list(path.glob("*.csv")))
                status += f"  {name}: {csv_count} CSV files\n"
            else:
                status += f"  {name}: ❌ Directory not found\n"
        
        return status
    
    @classmethod
    def save_checkpoint(cls, checkpoint_name: str, data: Dict[str, Any]):
        """Save a checkpoint for resuming long-running processes"""
        checkpoint_file = cls.BASE_DIR / f".checkpoint_{checkpoint_name}.json"
        
        data['timestamp'] = datetime.now().isoformat()
        
        with open(checkpoint_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    @classmethod
    def load_checkpoint(cls, checkpoint_name: str) -> Optional[Dict[str, Any]]:
        """Load a checkpoint if it exists"""
        checkpoint_file = cls.BASE_DIR / f".checkpoint_{checkpoint_name}.json"
        
        if checkpoint_file.exists():
            with open(checkpoint_file, 'r') as f:
                return json.load(f)
        
        return None
    
    @classmethod
    def clear_checkpoint(cls, checkpoint_name: str):
        """Clear a checkpoint after successful completion"""
        checkpoint_file = cls.BASE_DIR / f".checkpoint_{checkpoint_name}.json"
        
        if checkpoint_file.exists():
            checkpoint_file.unlink()


# Convenience functions
def get_db_connection():
    """Get a database connection using configured path"""
    import sqlite3
    return sqlite3.connect(Config.DB_PATH)

def log_message(message: str, log_type: str = 'info'):
    """Log a message to the appropriate log file"""
    log_files = {
        'info': Config.IMPORT_LOG,
        'error': Config.ERROR_LOG,
        'api': Config.API_LOG,
        'enrichment': Config.ENRICHMENT_LOG
    }
    
    log_file = log_files.get(log_type, Config.IMPORT_LOG)
    
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {message}\n"
    
    # Always print to console
    print(message)
    
    # Write to log file
    with open(log_file, 'a') as f:
        f.write(log_entry)


if __name__ == "__main__":
    # When run directly, print configuration status
    print(Config.get_status())
    
    # Validate environment
    checks = Config.validate_environment()
    all_good = all(checks.values())
    
    if not all_good:
        print("\n⚠️  Configuration Issues Detected:")
        for check, passed in checks.items():
            if not passed:
                print(f"  ❌ {check}")
        
        if not checks['github_token_set']:
            print("\nTo set GitHub token:")
            print("  1. Edit .env file")
            print("  2. Replace 'your_token_here' with your actual token")
            print("  3. Get token at: https://github.com/settings/tokens")
    else:
        print("\n✅ All configuration checks passed!")
