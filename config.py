#!/usr/bin/env python3
# ABOUTME: Central configuration management for talent intelligence system
# ABOUTME: Handles environment variables, paths, and settings

"""
Configuration Management System

This module provides centralized configuration for the entire talent database.
Replaces hardcoded paths and settings throughout the codebase.

Updated: October 20, 2025 - Post-migration to PostgreSQL
Primary database: PostgreSQL 'talent' @ localhost:5432
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
    
    # Connection pooling settings
    PG_POOL_MIN = int(os.environ.get('PG_POOL_MIN', '5'))
    PG_POOL_MAX = int(os.environ.get('PG_POOL_MAX', '50'))
    _connection_pool = None
    
    # ============================================================================
    # PRIMARY DATABASE: PostgreSQL 'talent' (Consolidated Oct 2025)
    # ============================================================================
    # The primary database is now PostgreSQL 'talent' with:
    #   - 32,515 people
    #   - 91,722 companies
    #   - 203,076 employment records
    #   - 1,014 emails (person_email table)
    #   - 17,534 GitHub profiles (github_profile table)
    #
    # All SQLite databases have been archived to: archived_databases/
    # ============================================================================
    
    # PostgreSQL connection settings
    DB_TYPE = 'postgresql'  # 'postgresql' or 'sqlite' (legacy)
    PG_HOST = os.environ.get('PGHOST', 'localhost')
    PG_PORT = os.environ.get('PGPORT', '5432')
    PG_DATABASE = os.environ.get('PGDATABASE', 'talent')
    PG_USER = os.environ.get('PGUSER', os.environ.get('USER'))
    PG_PASSWORD = os.environ.get('PGPASSWORD', '')  # Optional, usually not needed for local
    
    # Legacy SQLite path (archived - for reference only)
    SQLITE_DB_PATH = BASE_DIR / "talent_intelligence.db"
    ARCHIVED_DB_PATH = BASE_DIR / "archived_databases" / "sqlite" / "talent_intelligence.db"
    
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
            'data_dir_exists': cls.DATA_DIR.exists(),
            'github_token_set': bool(cls.GITHUB_TOKEN and cls.GITHUB_TOKEN != 'your_token_here'),
            'backup_dir_exists': cls.BACKUP_DIR.exists(),
            'log_dir_writable': cls.LOG_DIR.exists() and os.access(cls.LOG_DIR, os.W_OK)
        }
        
        # Check PostgreSQL connection
        if cls.DB_TYPE == 'postgresql':
            try:
                import psycopg2
                conn = psycopg2.connect(
                    host=cls.PG_HOST,
                    port=cls.PG_PORT,
                    database=cls.PG_DATABASE,
                    user=cls.PG_USER,
                    password=cls.PG_PASSWORD
                )
                conn.close()
                checks['database_connection'] = True
            except Exception as e:
                checks['database_connection'] = False
        else:
            # Legacy SQLite check
            checks['database_connection'] = cls.SQLITE_DB_PATH.exists()
        
        return checks
    
    @classmethod
    def get_status(cls) -> str:
        """Get configuration status summary"""
        checks = cls.validate_environment()
        
        if cls.DB_TYPE == 'postgresql':
            status = f"""
Configuration Status (Post-Migration)
======================================
Base Directory:     {cls.BASE_DIR}

PRIMARY DATABASE: PostgreSQL 'talent'
-------------------------------------
Host:               {cls.PG_HOST}:{cls.PG_PORT}
Database:           {cls.PG_DATABASE}
User:               {cls.PG_USER}
Connection:         {'✅ Connected' if checks.get('database_connection') else '❌ Failed'}

Contents (as of Oct 20, 2025):
  - 32,515 people
  - 91,722 companies
  - 203,076 employment records
  - 1,014 emails (person_email table)
  - 17,534 GitHub profiles (github_profile table)

Configuration:
-------------------------------------
GitHub Token:       {'✅ Configured' if checks['github_token_set'] else '❌ Not set or invalid'}
Backup Directory:   {'✅' if checks['backup_dir_exists'] else '❌'}
Logs Writable:      {'✅' if checks['log_dir_writable'] else '❌'}

Archived Databases:
  SQLite: {cls.ARCHIVED_DB_PATH}
  PostgreSQL dumps: {cls.BASE_DIR / 'archived_databases' / 'postgresql_dumps'}

CSV Sources Found:
"""
        else:
            # Legacy SQLite mode
            status = f"""
Configuration Status (LEGACY MODE)
===================================
Base Directory:     {cls.BASE_DIR}
Database Path:      {cls.SQLITE_DB_PATH}
Database Exists:    {'✅' if checks.get('database_connection') else '❌'}
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
    
    @classmethod
    def get_connection_pool(cls):
        """
        Get or create connection pool for PostgreSQL
        Uses SimpleConnectionPool for thread-safe connection management
        """
        if cls.DB_TYPE != 'postgresql':
            raise ValueError("Connection pooling only available for PostgreSQL")
        
        if cls._connection_pool is None:
            import psycopg2.pool
            
            try:
                cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                    cls.PG_POOL_MIN,
                    cls.PG_POOL_MAX,
                    host=cls.PG_HOST,
                    port=cls.PG_PORT,
                    database=cls.PG_DATABASE,
                    user=cls.PG_USER,
                    password=cls.PG_PASSWORD,
                    connect_timeout=5,
                    options='-c statement_timeout=300s'  # 5 minute max per query
                )
                print(f"✅ Connection pool created (min={cls.PG_POOL_MIN}, max={cls.PG_POOL_MAX})")
            except Exception as e:
                print(f"❌ Failed to create connection pool: {e}")
                raise
        
        return cls._connection_pool
    
    @classmethod
    def close_connection_pool(cls):
        """Close all connections in the pool"""
        if cls._connection_pool is not None:
            cls._connection_pool.closeall()
            cls._connection_pool = None
            print("✅ Connection pool closed")
    
    @classmethod
    def get_pooled_connection(cls):
        """
        Get a connection from the pool
        
        Usage:
            conn = Config.get_pooled_connection()
            try:
                # Use connection
                cursor = conn.cursor()
                ...
            finally:
                Config.return_connection(conn)
        """
        pool = cls.get_connection_pool()
        return pool.getconn()
    
    @classmethod
    def return_connection(cls, conn):
        """Return a connection to the pool"""
        if cls._connection_pool is not None:
            cls._connection_pool.putconn(conn)
    
    @classmethod
    def check_pool_health(cls):
        """Check health of connection pool"""
        if cls._connection_pool is None:
            return {"status": "not_initialized", "connections": 0}
        
        try:
            # Try to get and return a connection
            conn = cls.get_pooled_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            cls.return_connection(conn)
            
            return {
                "status": "healthy",
                "pool_size": f"{cls.PG_POOL_MIN}-{cls.PG_POOL_MAX}"
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e)
            }


# Convenience functions
def get_db_connection(use_pool=True):
    """Get a database connection using configured settings
    
    Args:
        use_pool: If True and PostgreSQL, use connection pool. If False, create new connection.
    
    Returns:
        Connection object for the configured database type
        
    Note: After migration (Oct 2025), this returns a PostgreSQL connection
          to the 'talent' database. For legacy SQLite access, use get_sqlite_connection().
          When using pooled connections, remember to call Config.return_connection(conn)
          when done, or use with get_db_context() context manager.
    """
    if Config.DB_TYPE == 'postgresql':
        import psycopg2
        import psycopg2.extras
        
        if use_pool:
            try:
                conn = Config.get_pooled_connection()
            except Exception:
                # Fallback to direct connection if pool fails
                conn = psycopg2.connect(
                    host=Config.PG_HOST,
                    port=Config.PG_PORT,
                    database=Config.PG_DATABASE,
                    user=Config.PG_USER,
                    password=Config.PG_PASSWORD
                )
        else:
            conn = psycopg2.connect(
                host=Config.PG_HOST,
                port=Config.PG_PORT,
                database=Config.PG_DATABASE,
                user=Config.PG_USER,
                password=Config.PG_PASSWORD
            )
        
        # Use RealDictCursor for dict-like row access
        conn.cursor_factory = psycopg2.extras.RealDictCursor
        return conn
    else:
        # Legacy SQLite mode
        import sqlite3
        sqlite3.register_adapter(bool, int)
        sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
        conn = sqlite3.connect(Config.SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row  # Dict-like row access
        return conn


def get_db_context():
    """
    Context manager for database connections with automatic cleanup
    
    Usage:
        with get_db_context() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM person")
            # Connection automatically returned to pool when done
    """
    from contextlib import contextmanager
    
    @contextmanager
    def _context():
        conn = get_db_connection(use_pool=True)
        try:
            yield conn
        finally:
            if Config.DB_TYPE == 'postgresql':
                Config.return_connection(conn)
            else:
                conn.close()
    
    return _context()

def get_sqlite_connection():
    """Get a connection to the archived SQLite database
    
    For accessing legacy SQLite data after migration.
    """
    import sqlite3
    sqlite3.register_adapter(bool, int)
    sqlite3.register_converter("BOOLEAN", lambda v: bool(int(v)))
    conn = sqlite3.connect(Config.SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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
