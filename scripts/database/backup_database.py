#!/usr/bin/env python3
# ABOUTME: Automated backup system for talent intelligence database
# ABOUTME: Creates timestamped backups with rotation and integrity verification

"""
Automated Database Backup System

Features:
- Creates timestamped backups
- Verifies backup integrity
- Rotates old backups (keeps last 30 days)
- Can be run manually or via cron
- Compresses backups to save space
"""

import sqlite3
import shutil
import gzip
from pathlib import Path
from datetime import datetime, timedelta
import hashlib
import json
import sys

class DatabaseBackup:
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.db_path = self.script_dir / "talent_intelligence.db"
        self.backup_dir = self.script_dir / "backups"
        self.backup_log = self.backup_dir / "backup_log.json"
        self.retention_days = 30
        
        # Create backup directory if it doesn't exist
        self.backup_dir.mkdir(exist_ok=True)
        
    def calculate_checksum(self, filepath):
        """Calculate SHA256 checksum of a file"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def create_backup(self):
        """Create a new backup of the database"""
        if not self.db_path.exists():
            print(f"❌ Database not found: {self.db_path}")
            return False
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"talent_intelligence_backup_{timestamp}.db"
        backup_path = self.backup_dir / backup_name
        compressed_path = self.backup_dir / f"{backup_name}.gz"
        
        try:
            # Step 1: Create backup using SQLite's backup API (safe for active databases)
            print(f"📦 Creating backup: {backup_name}")
            
            # Connect to both databases
            source_conn = sqlite3.connect(self.db_path)
            backup_conn = sqlite3.connect(backup_path)
            
            # Use SQLite's backup API
            with backup_conn:
                source_conn.backup(backup_conn)
            
            source_conn.close()
            backup_conn.close()
            
            # Step 2: Verify backup integrity
            print("🔍 Verifying backup integrity...")
            
            # Quick integrity check - can we query it?
            test_conn = sqlite3.connect(backup_path)
            cursor = test_conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM people")
            people_count = cursor.fetchone()[0]
            test_conn.close()
            
            print(f"✅ Backup verified: {people_count} people in database")
            
            # Step 3: Compress the backup
            print("🗜️  Compressing backup...")
            with open(backup_path, 'rb') as f_in:
                with gzip.open(compressed_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Calculate sizes
            original_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            compressed_size = compressed_path.stat().st_size / (1024 * 1024)  # MB
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            print(f"📊 Compressed from {original_size:.1f}MB to {compressed_size:.1f}MB ({compression_ratio:.1f}% reduction)")
            
            # Remove uncompressed backup
            backup_path.unlink()
            
            # Step 4: Calculate checksum
            checksum = self.calculate_checksum(compressed_path)
            
            # Step 5: Log the backup
            self.log_backup({
                'timestamp': timestamp,
                'filename': f"{backup_name}.gz",
                'size_mb': compressed_size,
                'checksum': checksum,
                'people_count': people_count,
                'created_at': datetime.now().isoformat()
            })
            
            print(f"✅ Backup complete: {compressed_path.name}")
            print(f"   Checksum: {checksum[:16]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Backup failed: {e}")
            # Clean up partial backup if it exists
            if backup_path.exists():
                backup_path.unlink()
            if compressed_path.exists():
                compressed_path.unlink()
            return False
    
    def log_backup(self, backup_info):
        """Log backup information"""
        logs = []
        
        if self.backup_log.exists():
            with open(self.backup_log, 'r') as f:
                logs = json.load(f)
        
        logs.append(backup_info)
        
        # Keep only last 100 backup logs
        logs = logs[-100:]
        
        with open(self.backup_log, 'w') as f:
            json.dump(logs, f, indent=2)
    
    def rotate_backups(self):
        """Remove backups older than retention period"""
        print(f"\n🔄 Rotating backups older than {self.retention_days} days...")
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        removed_count = 0
        removed_size = 0
        
        for backup_file in self.backup_dir.glob("talent_intelligence_backup_*.db.gz"):
            # Extract timestamp from filename
            try:
                timestamp_str = backup_file.stem.replace("talent_intelligence_backup_", "").replace(".db", "")
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                
                if file_date < cutoff_date:
                    size_mb = backup_file.stat().st_size / (1024 * 1024)
                    removed_size += size_mb
                    backup_file.unlink()
                    removed_count += 1
                    print(f"   🗑️  Removed: {backup_file.name} ({size_mb:.1f}MB)")
                    
            except Exception as e:
                print(f"   ⚠️  Could not process {backup_file.name}: {e}")
        
        if removed_count > 0:
            print(f"✅ Removed {removed_count} old backups, freed {removed_size:.1f}MB")
        else:
            print("✅ No old backups to remove")
    
    def list_backups(self):
        """List all existing backups"""
        print("\n📋 Existing backups:")
        
        backups = list(self.backup_dir.glob("talent_intelligence_backup_*.db.gz"))
        
        if not backups:
            print("   No backups found")
            return
        
        backups.sort()
        total_size = 0
        
        for backup_file in backups:
            size_mb = backup_file.stat().st_size / (1024 * 1024)
            total_size += size_mb
            
            # Extract timestamp
            timestamp_str = backup_file.stem.replace("talent_intelligence_backup_", "").replace(".db", "")
            try:
                file_date = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                age_days = (datetime.now() - file_date).days
                print(f"   • {backup_file.name} ({size_mb:.1f}MB, {age_days} days old)")
            except:
                print(f"   • {backup_file.name} ({size_mb:.1f}MB)")
        
        print(f"\n   Total: {len(backups)} backups, {total_size:.1f}MB")
    
    def restore_backup(self, backup_filename=None):
        """Restore a backup (interactive)"""
        if not backup_filename:
            # Show available backups
            backups = sorted(self.backup_dir.glob("talent_intelligence_backup_*.db.gz"))
            
            if not backups:
                print("❌ No backups available")
                return False
            
            print("\nAvailable backups:")
            for i, backup in enumerate(backups[-10:], 1):  # Show last 10
                size_mb = backup.stat().st_size / (1024 * 1024)
                print(f"  {i}. {backup.name} ({size_mb:.1f}MB)")
            
            try:
                choice = int(input("\nEnter number to restore (0 to cancel): "))
                if choice == 0:
                    return False
                backup_path = backups[-10:][choice - 1]
            except (ValueError, IndexError):
                print("❌ Invalid choice")
                return False
        else:
            backup_path = self.backup_dir / backup_filename
            if not backup_path.exists():
                print(f"❌ Backup not found: {backup_filename}")
                return False
        
        print(f"\n⚠️  WARNING: This will replace the current database with {backup_path.name}")
        confirm = input("Are you sure? (type 'yes' to confirm): ")
        
        if confirm.lower() != 'yes':
            print("Restore cancelled")
            return False
        
        try:
            # Create a safety backup of current database
            print("Creating safety backup of current database...")
            safety_backup = self.db_path.with_suffix('.safety_backup.db')
            shutil.copy2(self.db_path, safety_backup)
            
            # Decompress and restore
            print(f"Restoring from {backup_path.name}...")
            with gzip.open(backup_path, 'rb') as f_in:
                with open(self.db_path, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Verify restored database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM people")
            people_count = cursor.fetchone()[0]
            conn.close()
            
            print(f"✅ Database restored successfully ({people_count} people)")
            
            # Remove safety backup
            safety_backup.unlink()
            
            return True
            
        except Exception as e:
            print(f"❌ Restore failed: {e}")
            # Try to restore safety backup
            if safety_backup.exists():
                shutil.copy2(safety_backup, self.db_path)
                print("Original database restored from safety backup")
                safety_backup.unlink()
            return False
    
    def run_backup(self):
        """Main backup process"""
        print("=" * 60)
        print("🔐 Talent Intelligence Database Backup System")
        print("=" * 60)
        
        # Create new backup
        if self.create_backup():
            # Rotate old backups
            self.rotate_backups()
            
            # List current backups
            self.list_backups()
            
            print("\n✅ Backup process complete!")
            return True
        else:
            print("\n❌ Backup process failed!")
            return False

def setup_cron():
    """Print instructions for setting up automated backups"""
    print("""
To set up automated daily backups, add this to your crontab:

1. Open crontab:
   crontab -e

2. Add this line for daily backups at 2 AM:
   0 2 * * * cd /Users/charlie.kerr/Documents/CK\ Docs/FINAL_DATABASE && /usr/bin/python3 backup_database.py --auto

3. Or for hourly backups during work hours (9 AM - 6 PM):
   0 9-18 * * * cd /Users/charlie.kerr/Documents/CK\ Docs/FINAL_DATABASE && /usr/bin/python3 backup_database.py --auto

4. Save and exit the crontab editor
""")

def main():
    """Main entry point"""
    backup = DatabaseBackup()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--auto':
            # Automated mode (for cron)
            sys.exit(0 if backup.run_backup() else 1)
        elif sys.argv[1] == '--restore':
            # Restore mode
            backup_file = sys.argv[2] if len(sys.argv) > 2 else None
            sys.exit(0 if backup.restore_backup(backup_file) else 1)
        elif sys.argv[1] == '--list':
            # List backups
            backup.list_backups()
            sys.exit(0)
        elif sys.argv[1] == '--setup-cron':
            # Show cron setup instructions
            setup_cron()
            sys.exit(0)
    else:
        # Interactive mode
        print("Database Backup Options:")
        print("1. Create backup now")
        print("2. Restore from backup")
        print("3. List existing backups")
        print("4. Setup automated backups (cron)")
        print("0. Exit")
        
        choice = input("\nEnter choice: ").strip()
        
        if choice == '1':
            backup.run_backup()
        elif choice == '2':
            backup.restore_backup()
        elif choice == '3':
            backup.list_backups()
        elif choice == '4':
            setup_cron()
        elif choice == '0':
            print("Goodbye!")
        else:
            print("Invalid choice")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nBackup cancelled by user")
        sys.exit(1)
