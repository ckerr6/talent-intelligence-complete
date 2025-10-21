#!/usr/bin/env python3
# ABOUTME: Fix GitHub profiles table schema to support all enrichment fields
# ABOUTME: Adds missing columns and migrates existing data safely

"""
GitHub Schema Fix Script

This script updates the github_profiles table to include all columns
needed for the enrichment process, while preserving existing data.
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from config import Config, log_message

def fix_github_schema():
    """Add missing columns to github_profiles table"""
    
    db_path = Config.DB_PATH
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("🔧 Fixing GitHub profiles schema...")
    print()
    
    # First, let's see what columns currently exist
    cursor.execute("PRAGMA table_info(github_profiles)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    print(f"📊 Existing columns: {', '.join(sorted(existing_columns))}")
    print()
    
    # Define all columns we need
    required_columns = {
        'github_profile_id': 'TEXT PRIMARY KEY',
        'person_id': 'TEXT',
        'github_username': 'TEXT',
        'github_name': 'TEXT',
        'github_email': 'TEXT',
        'github_company': 'TEXT',
        'github_location': 'TEXT',
        'github_bio': 'TEXT',  # This was missing!
        'personal_website': 'TEXT',
        'twitter_username': 'TEXT',
        'public_repos': 'INTEGER',
        'public_gists': 'INTEGER',
        'followers': 'INTEGER',
        'following': 'INTEGER',
        'created_at': 'TEXT',
        'updated_at': 'TEXT',
        'hireable': 'INTEGER',
        'languages_json': 'TEXT',  # JSON string of language usage
        'top_language': 'TEXT',    # Most used language
        'profile_url': 'TEXT',
        'contribution_count': 'INTEGER',
        'last_contribution_date': 'TEXT',
        'enrichment_status': 'TEXT',  # 'pending', 'enriched', 'failed'
        'enrichment_attempts': 'INTEGER DEFAULT 0',
        'last_enrichment_attempt': 'TEXT'
    }
    
    # Add missing columns
    columns_added = []
    for column_name, column_type in required_columns.items():
        if column_name not in existing_columns:
            # Extract just the type without constraints for ALTER TABLE
            type_only = column_type.split()[0] if ' ' in column_type else column_type
            
            # Skip PRIMARY KEY columns (can't add after table creation)
            if 'PRIMARY KEY' in column_type:
                continue
            
            try:
                # Add DEFAULT for certain columns
                if column_name in ['enrichment_attempts']:
                    cursor.execute(f"ALTER TABLE github_profiles ADD COLUMN {column_name} INTEGER DEFAULT 0")
                elif column_name in ['enrichment_status']:
                    cursor.execute(f"ALTER TABLE github_profiles ADD COLUMN {column_name} TEXT DEFAULT 'pending'")
                else:
                    cursor.execute(f"ALTER TABLE github_profiles ADD COLUMN {column_name} {type_only}")
                columns_added.append(column_name)
                print(f"  ✅ Added column: {column_name}")
            except sqlite3.OperationalError as e:
                print(f"  ⚠️  Could not add {column_name}: {e}")
    
    if columns_added:
        print(f"\n✅ Added {len(columns_added)} missing columns")
        conn.commit()
    else:
        print("\n✅ All required columns already exist")
    
    # Create indexes if they don't exist
    print("\n🔍 Creating indexes...")
    
    indexes = [
        ("idx_github_profiles_person_id", "github_profiles(person_id)"),
        ("idx_github_profiles_username", "github_profiles(github_username)"),
        ("idx_github_profiles_status", "github_profiles(enrichment_status)"),
        ("idx_github_profiles_company", "github_profiles(github_company)"),
    ]
    
    for index_name, index_def in indexes:
        try:
            cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {index_def}")
            print(f"  ✅ Index ready: {index_name}")
        except sqlite3.OperationalError as e:
            print(f"  ⚠️  Index issue: {e}")
    
    conn.commit()
    
    # Check if we need to migrate data from social_profiles
    print("\n🔄 Checking for GitHub profiles to migrate...")
    
    cursor.execute("""
        SELECT COUNT(*) 
        FROM social_profiles sp
        WHERE sp.platform = 'github'
        AND sp.profile_url IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM github_profiles gp 
            WHERE gp.person_id = sp.person_id
        )
    """)
    
    profiles_to_migrate = cursor.fetchone()[0]
    
    if profiles_to_migrate > 0:
        print(f"  Found {profiles_to_migrate} GitHub profiles to migrate from social_profiles")
        
        # Migrate profiles
        cursor.execute("""
            INSERT OR IGNORE INTO github_profiles (github_profile_id, person_id, profile_url, github_username, created_at, updated_at, enrichment_status)
            SELECT 
                'gh_' || substr(hex(randomblob(6)), 1, 12) as github_profile_id,
                sp.person_id,
                sp.profile_url,
                CASE 
                    WHEN sp.username IS NOT NULL THEN sp.username
                    WHEN sp.profile_url LIKE '%github.com/%' THEN 
                        substr(sp.profile_url, 
                            instr(sp.profile_url, 'github.com/') + 11,
                            CASE 
                                WHEN instr(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11), '/') > 0
                                THEN instr(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11), '/') - 1
                                ELSE length(substr(sp.profile_url, instr(sp.profile_url, 'github.com/') + 11))
                            END
                        )
                    ELSE NULL
                END as github_username,
                datetime('now') as created_at,
                datetime('now') as updated_at,
                'pending' as enrichment_status
            FROM social_profiles sp
            WHERE sp.platform = 'github'
            AND sp.profile_url IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 FROM github_profiles gp 
                WHERE gp.person_id = sp.person_id
            )
        """)
        
        migrated = cursor.rowcount
        conn.commit()
        print(f"  ✅ Migrated {migrated} profiles to github_profiles table")
    else:
        print("  ✅ No profiles need migration")
    
    # Get statistics
    print("\n📊 GitHub Profiles Statistics:")
    
    cursor.execute("SELECT COUNT(*) FROM github_profiles")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE enrichment_status = 'enriched'")
    enriched = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE enrichment_status = 'pending'")
    pending = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM github_profiles WHERE enrichment_status = 'failed'")
    failed = cursor.fetchone()[0]
    
    print(f"  Total profiles:    {total:,}")
    print(f"  Enriched:          {enriched:,}")
    print(f"  Pending:           {pending:,}")
    print(f"  Failed:            {failed:,}")
    
    # Verify schema is complete
    cursor.execute("PRAGMA table_info(github_profiles)")
    final_columns = {row[1] for row in cursor.fetchall()}
    
    print(f"\n📋 Final schema has {len(final_columns)} columns")
    
    # Close connection
    conn.close()
    
    print("\n✅ Schema fix complete!")
    return True


def test_enrichment_columns():
    """Test that all required columns exist"""
    conn = sqlite3.connect(Config.DB_PATH)
    cursor = conn.cursor()
    
    print("\n🧪 Testing column availability...")
    
    test_data = {
        'github_profile_id': 'test_123',
        'person_id': 'test_person',
        'github_username': 'testuser',
        'github_name': 'Test User',
        'github_email': 'test@example.com',
        'github_company': 'Test Corp',
        'github_location': 'San Francisco',
        'github_bio': 'Test bio text',  # This was failing before
        'personal_website': 'https://example.com',
        'twitter_username': 'testtwitter',
        'public_repos': 10,
        'public_gists': 5,
        'followers': 100,
        'following': 50,
        'hireable': 1,
        'languages_json': '{"Python": 10, "JavaScript": 5}',
        'top_language': 'Python',
        'profile_url': 'https://github.com/testuser',
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }
    
    try:
        # Try to insert test data
        columns = ', '.join(test_data.keys())
        placeholders = ', '.join(['?' for _ in test_data])
        
        # Use INSERT OR REPLACE to handle if test record exists
        query = f"INSERT OR REPLACE INTO github_profiles ({columns}) VALUES ({placeholders})"
        cursor.execute(query, list(test_data.values()))
        
        # Clean up test data
        cursor.execute("DELETE FROM github_profiles WHERE github_profile_id = 'test_123'")
        conn.commit()
        
        print("  ✅ All enrichment columns are working!")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"  ❌ Column test failed: {e}")
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    print("="*60)
    print("🔧 GitHub Schema Fix Utility")
    print("="*60)
    print()
    
    # Run the fix
    if fix_github_schema():
        # Test it worked
        if test_enrichment_columns():
            print("\n✅ Database is ready for enrichment!")
            print("\nYou can now run:")
            print("  python3 github_enrichment.py --test")
            print("\nOr for full enrichment:")
            print("  python3 github_enrichment.py")
        else:
            print("\n⚠️  Schema was updated but test failed. Check the error above.")
    else:
        print("\n❌ Schema fix failed!")
