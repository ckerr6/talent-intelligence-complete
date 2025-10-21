#!/usr/bin/env python3
"""
Run Ecosystem Schema Migration

Applies the 02_ecosystem_schema.sql migration to add ecosystem tracking tables.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from config import Config, get_db_connection
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)


def run_migration():
    """Run the ecosystem schema migration"""
    
    migration_file = Path(__file__).parent / 'migration_scripts' / '02_ecosystem_schema.sql'
    
    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False
    
    logger.info("Connecting to database...")
    conn = get_db_connection(use_pool=False)
    cursor = conn.cursor()
    
    try:
        logger.info(f"Reading migration from {migration_file}")
        with open(migration_file, 'r') as f:
            sql = f.read()
        
        logger.info("Executing migration...")
        cursor.execute(sql)
        conn.commit()
        
        logger.info("✅ Migration completed successfully!")
        
        # Verify tables were created
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name IN ('crypto_ecosystem', 'ecosystem_repository', 
                               'company_ecosystem', 'person_ecosystem_activity')
            ORDER BY table_name
        """)
        
        tables = [row['table_name'] for row in cursor.fetchall()]
        logger.info(f"Created tables: {', '.join(tables)}")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        conn.rollback()
        return False
        
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)

