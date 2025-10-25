#!/usr/bin/env python3
"""
ABOUTME: Language ecosystem aggregation script
ABOUTME: Analyzes existing GitHub profile data to build language leaderboards
"""

import sys
import os
sys.path.insert(0, '/Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete')

from config import get_db_context
import json
from collections import defaultdict

def analyze_language_ecosystems():
    """Aggregate language data from existing enriched profiles"""
    
    print("🔍 Analyzing language ecosystems from existing data...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Get all enriched profiles with language data
        cursor.execute("""
            SELECT 
                gi.primary_languages,
                gi.inferred_seniority,
                gi.influence_score,
                gp.github_username
            FROM github_intelligence gi
            JOIN github_profile gp ON gi.github_profile_id = gp.github_profile_id
            WHERE gi.primary_languages IS NOT NULL
        """)
        
        results = cursor.fetchall()
        
        # Aggregate by language
        language_stats = defaultdict(lambda: {
            'developer_count': 0,
            'total_influence': 0,
            'seniority_distribution': defaultdict(int),
            'developers': []
        })
        
        for row in results:
            if isinstance(row, dict):
                langs = row['primary_languages']
                seniority = row['inferred_seniority']
                influence = row['influence_score']
                username = row['github_username']
            else:
                langs = row[0]
                seniority = row[1]
                influence = row[2]
                username = row[3]
            
            # Parse JSON if it's a string
            if isinstance(langs, str):
                langs = json.loads(langs)
            
            # Count each language (weighted by usage %)
            for lang, data in langs.items():
                percentage = data.get('percentage', 0)
                
                # Only count if they use this language significantly (>5%)
                if percentage > 5:
                    language_stats[lang]['developer_count'] += 1
                    language_stats[lang]['total_influence'] += influence or 0
                    language_stats[lang]['seniority_distribution'][seniority] += 1
                    language_stats[lang]['developers'].append({
                        'username': username,
                        'percentage': percentage,
                        'seniority': seniority
                    })
        
        # Calculate aggregate metrics
        leaderboard = []
        for lang, stats in language_stats.items():
            dev_count = stats['developer_count']
            avg_influence = stats['total_influence'] / dev_count if dev_count > 0 else 0
            
            leaderboard.append({
                'language': lang,
                'developer_count': dev_count,
                'avg_influence': round(avg_influence, 1),
                'seniority_distribution': dict(stats['seniority_distribution']),
                'top_developers': sorted(
                    stats['developers'], 
                    key=lambda x: x['percentage'], 
                    reverse=True
                )[:10]
            })
        
        # Sort by developer count
        leaderboard.sort(key=lambda x: x['developer_count'], reverse=True)
        
        print(f"\n✅ Analyzed {len(leaderboard)} languages from {len(results)} enriched profiles\n")
        
        # Print top 15
        print("="*80)
        print("🏆 LANGUAGE ECOSYSTEM LEADERBOARD")
        print("="*80)
        print(f"{'Rank':<6} {'Language':<20} {'Developers':<12} {'Avg Influence':<15} {'Top Seniority'}")
        print("-"*80)
        
        for i, lang_data in enumerate(leaderboard[:15], 1):
            lang = lang_data['language']
            dev_count = lang_data['developer_count']
            avg_inf = lang_data['avg_influence']
            
            # Find most common seniority
            seniority_dist = lang_data['seniority_distribution']
            top_seniority = max(seniority_dist.items(), key=lambda x: x[1])[0] if seniority_dist else 'N/A'
            
            print(f"{i:<6} {lang:<20} {dev_count:<12} {avg_inf:<15} {top_seniority}")
        
        print("="*80)
        
        # Store in database for API access
        store_language_metrics(leaderboard)
        
        return leaderboard

def store_language_metrics(leaderboard):
    """Store aggregated language metrics in database"""
    
    print("\n💾 Storing language metrics in database...")
    
    with get_db_context() as conn:
        cursor = conn.cursor()
        
        # Create table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS language_ecosystem_metrics (
                language TEXT PRIMARY KEY,
                developer_count INTEGER,
                avg_influence FLOAT,
                seniority_distribution JSONB,
                top_developers JSONB,
                last_updated TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Insert/update data
        for lang_data in leaderboard:
            cursor.execute("""
                INSERT INTO language_ecosystem_metrics 
                (language, developer_count, avg_influence, seniority_distribution, top_developers)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (language) 
                DO UPDATE SET
                    developer_count = EXCLUDED.developer_count,
                    avg_influence = EXCLUDED.avg_influence,
                    seniority_distribution = EXCLUDED.seniority_distribution,
                    top_developers = EXCLUDED.top_developers,
                    last_updated = NOW()
            """, (
                lang_data['language'],
                lang_data['developer_count'],
                lang_data['avg_influence'],
                json.dumps(lang_data['seniority_distribution']),
                json.dumps(lang_data['top_developers'])
            ))
        
        conn.commit()
        print(f"✅ Stored {len(leaderboard)} language ecosystems in database")

if __name__ == "__main__":
    try:
        leaderboard = analyze_language_ecosystems()
        print("\n🎉 Language leaderboard ready!")
        print("   Access via API: http://localhost:8000/api/market/languages")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

