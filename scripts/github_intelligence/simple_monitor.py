#!/usr/bin/env python3
# ABOUTME: Simple monitor for GitHub intelligence enrichment progress
# ABOUTME: Shows enrichment stats and recent activity

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import get_db_context
import time

def show_stats():
    """Display enrichment statistics"""
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Total enriched
        cursor.execute("SELECT COUNT(*) FROM github_intelligence")
        total = cursor.fetchone()[0]
        
        # By seniority
        cursor.execute("""
            SELECT inferred_seniority, COUNT(*) 
            FROM github_intelligence 
            WHERE inferred_seniority IS NOT NULL
            GROUP BY inferred_seniority
            ORDER BY COUNT(*) DESC
        """)
        seniority = cursor.fetchall()
        
        # Recent
        cursor.execute("""
            SELECT gi.github_profile_id, gp.github_username, gi.inferred_seniority
            FROM github_intelligence gi
            JOIN github_profile gp ON gi.github_profile_id = gp.github_profile_id
            ORDER BY gi.updated_at DESC
            LIMIT 5
        """)
        recent = cursor.fetchall()
        
        print("\n" + "="*60)
        print(f"📊 GitHub Intelligence Enrichment Status")
        print("="*60)
        print(f"\n✅ Total Enriched: {total}")
        
        if seniority:
            print("\n📈 By Seniority:")
            for level, count in seniority:
                print(f"   {level}: {count}")
        
        if recent:
            print("\n🕐 Last 5 Enriched:")
            for _, username, level in recent:
                print(f"   @{username} - {level}")
        
        print("\n" + "="*60)

if __name__ == "__main__":
    try:
        show_stats()
    except KeyboardInterrupt:
        print("\n\nStopped")
    except Exception as e:
        print(f"Error: {e}")





