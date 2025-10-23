#!/usr/bin/env python3
"""
GitHub Linkage Blitz - Dramatically improve GitHub → Person matching

Current: 4.2% linkage (4,210 of 100,883 GitHub profiles linked)
Target: 30%+ linkage (30,000+ links)

Strategies:
1. Email-based matching (github_profile.email → person_email.email)
2. Fuzzy name + location matching using Levenshtein distance
3. Name + company + dates overlap matching
4. GitHub username pattern matching (firstname.lastname, firstlast, etc.)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from typing import List, Dict, Tuple, Optional
import re


def normalize_name(name: str) -> str:
    """Normalize name for matching"""
    if not name:
        return ""
    
    # Convert to lowercase
    name = name.lower()
    
    # Remove special characters but keep spaces
    name = re.sub(r'[^a-z\s]', '', name)
    
    # Collapse multiple spaces
    name = re.sub(r'\s+', ' ', name).strip()
    
    return name


def levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance between two strings"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def similarity_score(s1: str, s2: str) -> float:
    """Calculate similarity score between two strings (0-1)"""
    if not s1 or not s2:
        return 0.0
    
    max_len = max(len(s1), len(s2))
    if max_len == 0:
        return 1.0
    
    distance = levenshtein_distance(s1, s2)
    return 1.0 - (distance / max_len)


def extract_username_patterns(full_name: str) -> List[str]:
    """
    Extract possible GitHub username patterns from a full name
    
    Examples:
        "John Smith" → ["johnsmith", "john.smith", "john-smith", "smithjohn", "jsmith"]
    """
    if not full_name:
        return []
    
    # Normalize and split name
    parts = normalize_name(full_name).split()
    
    if len(parts) < 2:
        return [parts[0]] if parts else []
    
    first = parts[0]
    last = parts[-1]
    
    patterns = [
        f"{first}{last}",           # johnsmith
        f"{first}.{last}",           # john.smith
        f"{first}-{last}",           # john-smith
        f"{first}_{last}",           # john_smith
        f"{last}{first}",           # smithjohn
        f"{first[0]}{last}",        # jsmith
        f"{first}{last[0]}",        # johns
    ]
    
    return patterns


class GitHubLinkageBlitz:
    def __init__(self):
        self.conn = Config.get_pooled_connection()
        self.stats = {
            'email_matches': 0,
            'fuzzy_name_matches': 0,
            'username_matches': 0,
            'company_overlap_matches': 0,
            'total_new_links': 0,
            'total_processed': 0,
            'errors': 0
        }
    
    def run(self):
        """Run all matching strategies"""
        print("="*80)
        print("🚀 GitHub Linkage Blitz")
        print("="*80)
        print(f"Started at: {datetime.now()}")
        print()
        
        # Get initial stats
        initial_linkage = self.get_linkage_stats()
        print(f"Initial linkage: {initial_linkage['linked']} / {initial_linkage['total']} "
              f"({initial_linkage['percentage']:.2f}%)")
        print()
        
        # Strategy 1: Email-based matching
        print("Strategy 1: Email-based matching...")
        self.match_by_email()
        print(f"  ✓ New links: {self.stats['email_matches']}")
        print()
        
        # Strategy 2: Fuzzy name + location matching
        print("Strategy 2: Fuzzy name + location matching...")
        self.match_by_fuzzy_name()
        print(f"  ✓ New links: {self.stats['fuzzy_name_matches']}")
        print()
        
        # Strategy 3: Username pattern matching
        print("Strategy 3: Username pattern matching...")
        self.match_by_username_patterns()
        print(f"  ✓ New links: {self.stats['username_matches']}")
        print()
        
        # Strategy 4: Company + name overlap
        print("Strategy 4: Company + name overlap matching...")
        self.match_by_company_overlap()
        print(f"  ✓ New links: {self.stats['company_overlap_matches']}")
        print()
        
        # Final stats
        final_linkage = self.get_linkage_stats()
        
        print("="*80)
        print("📊 Results")
        print("="*80)
        print(f"Initial linkage:  {initial_linkage['linked']:,} ({initial_linkage['percentage']:.2f}%)")
        print(f"Final linkage:    {final_linkage['linked']:,} ({final_linkage['percentage']:.2f}%)")
        print(f"New links:        +{final_linkage['linked'] - initial_linkage['linked']:,}")
        print(f"Improvement:      +{final_linkage['percentage'] - initial_linkage['percentage']:.2f}%")
        print()
        print("Breakdown by strategy:")
        print(f"  - Email matches:          {self.stats['email_matches']:,}")
        print(f"  - Fuzzy name matches:     {self.stats['fuzzy_name_matches']:,}")
        print(f"  - Username matches:       {self.stats['username_matches']:,}")
        print(f"  - Company overlap:        {self.stats['company_overlap_matches']:,}")
        print(f"  - Errors:                 {self.stats['errors']:,}")
        print()
        
        if final_linkage['percentage'] >= 30:
            print("🎉 Target achieved! (30%+ linkage)")
        else:
            print(f"📈 Progress made. Gap to 30%: {30 - final_linkage['percentage']:.2f}%")
        
        print("="*80)
        
        Config.return_connection(self.conn)
    
    def get_linkage_stats(self) -> Dict:
        """Get current GitHub linkage statistics"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(person_id) as linked
            FROM github_profile
        """)
        
        result = cursor.fetchone()
        cursor.close()
        
        total = result['total']
        linked = result['linked']
        percentage = (linked / total * 100) if total > 0 else 0
        
        return {
            'total': total,
            'linked': linked,
            'unlinked': total - linked,
            'percentage': percentage
        }
    
    def match_by_email(self):
        """Match GitHub profiles to people by email address"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Find GitHub profiles with emails that match person emails
        query = """
            UPDATE github_profile gp
            SET person_id = pe.person_id
            FROM person_email pe
            WHERE gp.github_email IS NOT NULL
            AND gp.github_email != ''
            AND gp.person_id IS NULL
            AND LOWER(gp.github_email) = LOWER(pe.email)
            RETURNING gp.github_profile_id
        """
        
        try:
            cursor.execute(query)
            self.stats['email_matches'] = cursor.rowcount
            self.conn.commit()
        except Exception as e:
            print(f"  ⚠️ Error in email matching: {e}")
            self.stats['errors'] += 1
            self.conn.rollback()
        
        cursor.close()
    
    def match_by_fuzzy_name(self):
        """Match by fuzzy name similarity + location"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        print("  → Fetching unlinked GitHub profiles...")
        # Get unlinked GitHub profiles with names (limit to avoid hang)
        cursor.execute("""
            SELECT github_profile_id, github_name, location
            FROM github_profile
            WHERE person_id IS NULL
            AND github_name IS NOT NULL
            AND github_name != ''
            LIMIT 5000
        """)
        
        github_profiles = cursor.fetchall()
        print(f"  → Processing {len(github_profiles)} GitHub profiles...")
        
        matches = 0
        batch = []
        
        # MUCH MORE EFFICIENT: Use SQL to do approximate matching
        print("  → Using database-driven fuzzy matching...")
        
        for i, gp in enumerate(github_profiles):
            if i % 500 == 0:
                print(f"    Progress: {i}/{len(github_profiles)} profiles checked, {matches} matches found")
            
            github_name_norm = normalize_name(gp['github_name'])
            
            if not github_name_norm or len(github_name_norm) < 3:
                continue
            
            # Extract first and last name parts
            name_parts = github_name_norm.split()
            if len(name_parts) < 2:
                continue
            
            first = name_parts[0]
            last = name_parts[-1]
            
            # Use SQL LIKE with name parts for much faster filtering
            # Then do similarity check only on filtered results
            cursor.execute("""
                SELECT person_id, full_name, location
                FROM person
                WHERE LOWER(full_name) LIKE %s
                OR LOWER(full_name) LIKE %s
                OR LOWER(full_name) LIKE %s
                LIMIT 20
            """, (f"{first}%{last}%", f"{last}%{first}%", f"%{first} {last}%"))
            
            candidates = cursor.fetchall()
            
            best_match = None
            best_score = 0.0
            
            for person in candidates:
                person_name_norm = normalize_name(person['full_name'])
                
                # Calculate name similarity
                name_similarity = similarity_score(github_name_norm, person_name_norm)
                
                # Boost score if locations match
                location_boost = 0.0
                if gp.get('location') and person.get('location'):
                    gh_loc = normalize_name(gp['location'])
                    p_loc = normalize_name(person['location'])
                    if gh_loc and p_loc and (gh_loc in p_loc or p_loc in gh_loc):
                        location_boost = 0.15
                
                total_score = name_similarity + location_boost
                
                # Require high confidence for matching
                if total_score > 0.85 and total_score > best_score:
                    best_score = total_score
                    best_match = person['person_id']
            
            if best_match:
                batch.append((best_match, gp['github_profile_id']))
                matches += 1
                
                # Batch update every 100 matches
                if len(batch) >= 100:
                    self._update_batch(batch, cursor)
                    batch = []
                    print(f"    ✓ Batch updated: {matches} total matches so far")
        
        # Update remaining
        if batch:
            self._update_batch(batch, cursor)
        
        self.stats['fuzzy_name_matches'] = matches
        cursor.close()
    
    def match_by_username_patterns(self):
        """Match GitHub profiles by username patterns derived from person names"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get people without GitHub profiles
        cursor.execute("""
            SELECT p.person_id, p.full_name
            FROM person p
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
            WHERE gp.person_id IS NULL
            AND p.full_name IS NOT NULL
            LIMIT 10000
        """)
        
        people = cursor.fetchall()
        
        matches = 0
        batch = []
        
        for person in people:
            # Generate possible usernames
            patterns = extract_username_patterns(person['full_name'])
            
            if not patterns:
                continue
            
            # Look for matching GitHub usernames
            for pattern in patterns:
                cursor.execute("""
                    SELECT github_profile_id
                    FROM github_profile
                    WHERE person_id IS NULL
                    AND LOWER(github_username) = %s
                    LIMIT 1
                """, (pattern,))
                
                result = cursor.fetchone()
                
                if result:
                    batch.append((person['person_id'], result['github_profile_id']))
                    matches += 1
                    break  # Stop after first match
            
            # Batch update every 100 matches
            if len(batch) >= 100:
                self._update_batch(batch, cursor)
                batch = []
        
        # Update remaining
        if batch:
            self._update_batch(batch, cursor)
        
        self.stats['username_matches'] = matches
        cursor.close()
    
    def match_by_company_overlap(self):
        """Match by company employment overlap + name similarity"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # This is more complex - find GitHub profiles where repo org names match employment companies
        query = """
            SELECT DISTINCT
                gp.github_profile_id,
                gp.github_name,
                gr.full_name as repo_name,
                SPLIT_PART(gr.full_name, '/', 1) as org_name
            FROM github_profile gp
            JOIN github_contribution gc ON gp.github_profile_id = gc.github_profile_id
            JOIN github_repository gr ON gc.repo_id = gr.repo_id
            WHERE gp.person_id IS NULL
            AND gp.github_name IS NOT NULL
            AND gr.full_name LIKE '%/%'
            LIMIT 5000
        """
        
        cursor.execute(query)
        github_data = cursor.fetchall()
        
        matches = 0
        batch = []
        
        for gp in github_data:
            github_name_norm = normalize_name(gp['github_name'])
            org_name = gp['org_name'].lower()
            
            # Find people who worked at companies matching the org name
            cursor.execute("""
                SELECT DISTINCT p.person_id, p.full_name
                FROM person p
                JOIN employment e ON p.person_id = e.person_id
                JOIN company c ON e.company_id = c.company_id
                WHERE LOWER(c.company_name) LIKE %s
                OR LOWER(c.company_name) LIKE %s
                LIMIT 20
            """, (f"%{org_name}%", f"{org_name}%"))
            
            people = cursor.fetchall()
            
            for person in people:
                person_name_norm = normalize_name(person['full_name'])
                name_similarity = similarity_score(github_name_norm, person_name_norm)
                
                # Require moderate similarity since company match adds confidence
                if name_similarity > 0.75:
                    batch.append((person['person_id'], gp['github_profile_id']))
                    matches += 1
                    break
            
            # Batch update every 100 matches
            if len(batch) >= 100:
                self._update_batch(batch, cursor)
                batch = []
        
        # Update remaining
        if batch:
            self._update_batch(batch, cursor)
        
        self.stats['company_overlap_matches'] = matches
        cursor.close()
    
    def _update_batch(self, batch: List[Tuple[str, str]], cursor):
        """Update a batch of GitHub profile → person links"""
        try:
            for person_id, github_profile_id in batch:
                cursor.execute("""
                    UPDATE github_profile
                    SET person_id = %s
                    WHERE github_profile_id = %s
                    AND person_id IS NULL
                """, (person_id, github_profile_id))
            
            self.conn.commit()
        except Exception as e:
            print(f"  ⚠️ Error updating batch: {e}")
            self.stats['errors'] += 1
            self.conn.rollback()


def main():
    """Main execution"""
    blitz = GitHubLinkageBlitz()
    blitz.run()


if __name__ == "__main__":
    main()

