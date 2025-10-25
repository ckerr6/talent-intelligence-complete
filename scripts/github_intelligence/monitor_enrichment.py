#!/usr/bin/env python3
"""
Monitor GitHub intelligence enrichment progress in real-time.
Shows stats, recent enrichments, and rate limit status.
"""

import sys
import os
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import get_db_context
from scripts.github_intelligence.github_client import GitHubClient


def clear_screen():
    """Clear terminal screen."""
    os.system('clear' if os.name != 'nt' else 'cls')


def get_enrichment_stats():
    """Get current enrichment statistics."""
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Total enriched
        cursor.execute("SELECT COUNT(*) FROM github_intelligence")
        result = cursor.fetchone()
        total_enriched = result[0] if result else 0
        
        # By seniority
        cursor.execute("""
            SELECT inferred_seniority, COUNT(*) 
            FROM github_intelligence 
            GROUP BY inferred_seniority
            ORDER BY COUNT(*) DESC
        """)
        by_seniority = dict(cursor.fetchall())
        
        # Recent enrichments (last 10)
        cursor.execute("""
            SELECT gp.github_username, gi.inferred_seniority, gi.influence_score, gi.created_at
            FROM github_intelligence gi
            JOIN github_profile gp ON gi.github_profile_id = gp.github_profile_id
            ORDER BY gi.created_at DESC
            LIMIT 10
        """)
        recent = cursor.fetchall()
        
        # Averages
        cursor.execute("""
            SELECT 
                AVG(influence_score) as avg_influence,
                AVG(reachability_score) as avg_reachability
            FROM github_intelligence
        """)
        result = cursor.fetchone()
        if result:
            avg_influence = result[0] if result[0] else 0
            avg_reachability = result[1] if result[1] else 0
        else:
            avg_influence = 0
            avg_reachability = 0
        
        return {
            'total_enriched': total_enriched,
            'by_seniority': by_seniority,
            'recent': recent,
            'avg_influence': avg_influence,
            'avg_reachability': avg_reachability
        }


def monitor_loop(refresh_seconds=5):
    """Monitor enrichment progress continuously."""
    client = GitHubClient()
    
    while True:
        try:
            clear_screen()
            
            print("=" * 80)
            print("🔍 GitHub Intelligence Enrichment Monitor")
            print("=" * 80)
            print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print()
            
            # Get stats
            stats = get_enrichment_stats()
            
            # Overall stats
            print("📊 ENRICHMENT PROGRESS")
            print("-" * 80)
            print(f"Total Enriched: {stats['total_enriched']:,} profiles")
            print(f"Avg Influence: {stats['avg_influence']:.1f}/100")
            print(f"Avg Reachability: {stats['avg_reachability']:.1f}/100")
            print()
            
            # By seniority
            print("👥 BY SENIORITY")
            print("-" * 80)
            for level, count in stats['by_seniority'].items():
                level_name = level or 'Unknown'
                bar = '█' * (count // 10)
                print(f"{level_name:12} {count:5,} {bar}")
            print()
            
            # Recent enrichments
            print("⚡ RECENT ENRICHMENTS (Last 10)")
            print("-" * 80)
            for username, seniority, influence, created_at in stats['recent']:
                seniority = seniority or 'Unknown'
                influence = influence or 0
                time_ago = datetime.now() - created_at
                mins_ago = int(time_ago.total_seconds() / 60)
                print(f"@{username:20} {seniority:12} {influence:3}/100  ({mins_ago}m ago)")
            print()
            
            # Rate limit status
            print("🔌 GITHUB API RATE LIMIT")
            print("-" * 80)
            try:
                rate_status = client.get_rate_limit_status()
                if rate_status and 'rate' in rate_status:
                    remaining = rate_status['rate']['remaining']
                    limit = rate_status['rate']['limit']
                    reset_time = datetime.fromtimestamp(rate_status['rate']['reset'])
                    percentage = (remaining / limit * 100) if limit > 0 else 0
                    
                    print(f"Remaining: {remaining:,} / {limit:,} ({percentage:.1f}%)")
                    print(f"Resets at: {reset_time.strftime('%H:%M:%S')}")
                    
                    # Progress bar
                    bar_length = 50
                    filled = int(bar_length * remaining / limit)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"[{bar}]")
                else:
                    print("Rate limit status unavailable")
            except Exception as e:
                print(f"Error checking rate limit: {e}")
            
            print()
            print("=" * 80)
            print(f"Refreshing every {refresh_seconds} seconds... (Ctrl+C to stop)")
            
            time.sleep(refresh_seconds)
            
        except KeyboardInterrupt:
            print("\n\n👋 Monitoring stopped")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            time.sleep(refresh_seconds)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor GitHub enrichment progress')
    parser.add_argument('--refresh', type=int, default=5, help='Refresh interval in seconds')
    args = parser.parse_args()
    
    monitor_loop(args.refresh)

