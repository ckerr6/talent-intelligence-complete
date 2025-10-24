#!/usr/bin/env python3
"""
Enrichment Queue Progress Monitor
==================================
Real-time monitoring dashboard for PhantomBuster LinkedIn enrichment

Features:
- Overall queue status and success rate
- Recent activity (completions and failures)
- Processing speed and ETA
- Error analysis

Author: AI Assistant
Date: October 24, 2025
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import get_db_connection


class EnrichmentMonitor:
    """Monitor enrichment queue progress"""
    
    def __init__(self):
        self.conn = get_db_connection(use_pool=False)
        self.cursor = self.conn.cursor()
    
    def get_overall_stats(self) -> Dict:
        """Get overall queue statistics"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) FILTER (WHERE status = 'completed') as completed,
                COUNT(*) FILTER (WHERE status = 'failed') as failed,
                COUNT(*) FILTER (WHERE status = 'in_progress') as in_progress,
                COUNT(*) FILTER (WHERE status = 'pending') as pending,
                COUNT(*) as total,
                ROUND(
                    100.0 * COUNT(*) FILTER (WHERE status = 'completed') / 
                    NULLIF(COUNT(*) FILTER (WHERE status IN ('completed', 'failed')), 0),
                    2
                ) as success_rate_pct
            FROM enrichment_queue
        """)
        
        return dict(self.cursor.fetchone())
    
    def get_priority_breakdown(self):
        """Get status by priority"""
        self.cursor.execute("""
            SELECT 
                priority,
                status,
                COUNT(*) as count
            FROM enrichment_queue
            GROUP BY priority, status
            ORDER BY priority DESC, status
        """)
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_recent_activity(self, hours: int = 1):
        """Get recent completions and failures"""
        self.cursor.execute("""
            SELECT 
                p.full_name,
                eq.status,
                eq.last_attempt,
                eq.attempts,
                eq.error_message
            FROM enrichment_queue eq
            JOIN person p ON eq.person_id = p.person_id
            WHERE eq.last_attempt > NOW() - INTERVAL '%s hours'
            ORDER BY eq.last_attempt DESC
            LIMIT 20
        """ % hours)
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_processing_rate(self, hours: int = 1):
        """Calculate profiles processed per hour"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as processed
            FROM enrichment_queue
            WHERE last_attempt > NOW() - INTERVAL '%s hours'
            AND status IN ('completed', 'failed')
        """ % hours)
        
        result = self.cursor.fetchone()
        processed = result['processed'] if result else 0
        
        return processed / hours if processed > 0 else 0
    
    def get_error_summary(self):
        """Get common error types"""
        self.cursor.execute("""
            SELECT 
                SUBSTRING(error_message FROM 1 FOR 100) as error_type,
                COUNT(*) as count
            FROM enrichment_queue
            WHERE status = 'failed'
            AND error_message IS NOT NULL
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT 10
        """)
        
        return [dict(row) for row in self.cursor.fetchall()]
    
    def get_retry_candidates(self):
        """Get failed profiles that can be retried"""
        self.cursor.execute("""
            SELECT 
                COUNT(*) as retry_count
            FROM enrichment_queue
            WHERE status = 'failed'
            AND attempts < 3
        """)
        
        result = self.cursor.fetchone()
        return result['retry_count'] if result else 0
    
    def close(self):
        """Close connection"""
        if self.conn:
            self.conn.close()


def format_duration(seconds: float) -> str:
    """Format duration in human-readable form"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f}m"
    elif seconds < 86400:
        return f"{seconds/3600:.1f}h"
    else:
        return f"{seconds/86400:.1f}d"


def print_dashboard():
    """Print monitoring dashboard"""
    monitor = EnrichmentMonitor()
    
    print("=" * 80)
    print("PHANTOMBUSTER ENRICHMENT QUEUE MONITOR")
    print("=" * 80)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Overall stats
    stats = monitor.get_overall_stats()
    print("📊 OVERALL STATUS")
    print("-" * 80)
    print(f"Total profiles:       {stats['total']:,}")
    print(f"  ✅ Completed:       {stats['completed']:,} ({stats['completed']/stats['total']*100:.1f}%)")
    print(f"  ⏳ Pending:         {stats['pending']:,} ({stats['pending']/stats['total']*100:.1f}%)")
    print(f"  🔄 In Progress:     {stats['in_progress']:,}")
    print(f"  ❌ Failed:          {stats['failed']:,} ({stats['failed']/stats['total']*100:.1f}%)")
    print()
    
    if stats['success_rate_pct']:
        print(f"Success Rate:         {stats['success_rate_pct']:.1f}%")
    print()
    
    # Priority breakdown
    priority_data = monitor.get_priority_breakdown()
    if priority_data:
        print("📈 BY PRIORITY")
        print("-" * 80)
        current_priority = None
        for row in priority_data:
            if row['priority'] != current_priority:
                if current_priority is not None:
                    print()
                current_priority = row['priority']
                print(f"Priority {row['priority']}:")
            
            status_icon = {
                'completed': '✅',
                'pending': '⏳',
                'in_progress': '🔄',
                'failed': '❌'
            }.get(row['status'], '❓')
            
            print(f"  {status_icon} {row['status']:12} {row['count']:,}")
        print()
    
    # Processing rate
    rate_1h = monitor.get_processing_rate(1)
    rate_24h = monitor.get_processing_rate(24)
    
    if rate_1h > 0 or rate_24h > 0:
        print("⚡ PROCESSING RATE")
        print("-" * 80)
        if rate_1h > 0:
            print(f"Last hour:            {rate_1h:.1f} profiles/hour")
            if stats['pending'] > 0:
                eta_hours = stats['pending'] / rate_1h
                print(f"ETA (at current rate): {format_duration(eta_hours * 3600)}")
        if rate_24h > 0:
            print(f"Last 24 hours:        {rate_24h:.1f} profiles/hour")
        print()
    
    # Recent activity
    recent = monitor.get_recent_activity(1)
    if recent:
        print("🕐 RECENT ACTIVITY (Last hour)")
        print("-" * 80)
        for item in recent[:10]:
            status_icon = {
                'completed': '✅',
                'failed': '❌',
                'in_progress': '🔄'
            }.get(item['status'], '❓')
            
            time_str = item['last_attempt'].strftime('%H:%M:%S') if item['last_attempt'] else 'N/A'
            name_truncated = item['full_name'][:40] if item['full_name'] else 'Unknown'
            
            print(f"{status_icon} {time_str} | {name_truncated:40} | Attempts: {item['attempts']}")
            
            if item['error_message']:
                error_truncated = item['error_message'][:70]
                print(f"   Error: {error_truncated}")
        print()
    
    # Error summary
    errors = monitor.get_error_summary()
    if errors:
        print("⚠️  ERROR SUMMARY (Top failures)")
        print("-" * 80)
        for error in errors:
            print(f"  [{error['count']:3}x] {error['error_type']}")
        print()
    
    # Retry candidates
    retry_count = monitor.get_retry_candidates()
    if retry_count > 0:
        print("🔄 RETRY CANDIDATES")
        print("-" * 80)
        print(f"{retry_count:,} failed profiles with < 3 attempts can be retried")
        print()
    
    print("=" * 80)
    print("💡 Tips:")
    print("  - Run: python phantombuster_linkedin_enrichment.py --batch-size 50")
    print("  - Monitor logs: tail -f ../logs/phantombuster_enrichment.log")
    print("  - Query queue: psql postgresql://localhost/talent -f ../sql/queries/enrichment_monitor.sql")
    print("=" * 80)
    
    monitor.close()


if __name__ == "__main__":
    try:
        print_dashboard()
    except KeyboardInterrupt:
        print("\n\nMonitoring interrupted.")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

