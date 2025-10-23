#!/usr/bin/env python3
"""
Email Extraction Script

Extract emails from GitHub profiles and prepare for Clay enrichment
Current: 14% email coverage (8,477 emails for 60,045 people)
Target: 50% email coverage (75,000+ emails for 150K people)

Strategies:
1. Extract emails from existing GitHub profiles in database
2. Export list of people without emails for Clay enrichment
3. Generate email candidates based on name + company patterns
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Config
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import csv
import re


class EmailExtractor:
    def __init__(self):
        self.conn = Config.get_pooled_connection()
        self.stats = {
            'github_emails_found': 0,
            'github_emails_added': 0,
            'export_count': 0,
            'pattern_suggestions': 0,
            'errors': 0
        }
        self.export_path = Path(__file__).parent.parent / "exports"
        self.export_path.mkdir(exist_ok=True)
    
    def run(self):
        """Run all extraction strategies"""
        print("="*80)
        print("📧 Email Extraction & Enrichment Prep")
        print("="*80)
        print(f"Started at: {datetime.now()}")
        print()
        
        # Get initial stats
        initial_coverage = self.get_email_coverage()
        print(f"Initial email coverage: {initial_coverage['with_email']:,} / {initial_coverage['total_people']:,} "
              f"({initial_coverage['percentage']:.2f}%)")
        print()
        
        # Strategy 1: Extract from GitHub profiles
        print("Strategy 1: Extracting emails from GitHub profiles...")
        self.extract_from_github()
        print(f"  ✓ Found {self.stats['github_emails_found']:,} emails")
        print(f"  ✓ Added {self.stats['github_emails_added']:,} new email records")
        print()
        
        # Strategy 2: Export for Clay enrichment
        print("Strategy 2: Preparing export for Clay enrichment...")
        export_file = self.export_for_clay()
        print(f"  ✓ Exported {self.stats['export_count']:,} people to: {export_file}")
        print()
        
        # Strategy 3: Generate email pattern suggestions
        print("Strategy 3: Generating email pattern suggestions...")
        suggestions_file = self.generate_email_patterns()
        print(f"  ✓ Generated {self.stats['pattern_suggestions']:,} suggestions to: {suggestions_file}")
        print()
        
        # Final stats
        final_coverage = self.get_email_coverage()
        
        print("="*80)
        print("📊 Results")
        print("="*80)
        print(f"Initial coverage:  {initial_coverage['with_email']:,} ({initial_coverage['percentage']:.2f}%)")
        print(f"Final coverage:    {final_coverage['with_email']:,} ({final_coverage['percentage']:.2f}%)")
        print(f"New emails:        +{final_coverage['with_email'] - initial_coverage['with_email']:,}")
        print(f"Improvement:       +{final_coverage['percentage'] - initial_coverage['percentage']:.2f}%")
        print()
        
        remaining_to_50 = int(initial_coverage['total_people'] * 0.5) - final_coverage['with_email']
        if remaining_to_50 > 0:
            print(f"To reach 50% target: Need {remaining_to_50:,} more emails")
            print(f"→ Use Clay to enrich: {export_file}")
            print(f"→ Or use email patterns from: {suggestions_file}")
        else:
            print("🎉 50% target achieved!")
        
        print("="*80)
        
        Config.return_connection(self.conn)
    
    def get_email_coverage(self) -> dict:
        """Get current email coverage statistics"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT p.person_id) as total_people,
                COUNT(DISTINCT pe.person_id) as with_email
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
        """)
        
        result = cursor.fetchone()
        cursor.close()
        
        total = result['total_people']
        with_email = result['with_email'] or 0
        percentage = (with_email / total * 100) if total > 0 else 0
        
        return {
            'total_people': total,
            'with_email': with_email,
            'without_email': total - with_email,
            'percentage': percentage
        }
    
    def extract_from_github(self):
        """Extract emails from GitHub profiles and add to person_email"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Find GitHub profiles with emails where person doesn't have that email yet
        query = """
            SELECT 
                gp.person_id,
                gp.github_email as github_email,
                gp.github_username
            FROM github_profile gp
            WHERE gp.person_id IS NOT NULL
            AND gp.github_email IS NOT NULL
            AND gp.github_email != ''
            AND gp.github_email NOT LIKE '%noreply.github.com%'
            AND NOT EXISTS (
                SELECT 1 FROM person_email pe 
                WHERE pe.person_id = gp.person_id 
                AND LOWER(pe.email) = LOWER(gp.github_email)
            )
        """
        
        try:
            cursor.execute(query)
            github_emails = cursor.fetchall()
            self.stats['github_emails_found'] = len(github_emails)
            
            # Insert new emails
            added = 0
            for row in github_emails:
                try:
                    cursor.execute("""
                        INSERT INTO person_email (person_id, email, email_type, is_primary)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (person_id, email) DO NOTHING
                    """, (
                        row['person_id'],
                        row['github_email'].lower(),
                        'github',
                        False  # Don't make GitHub emails primary by default
                    ))
                    
                    if cursor.rowcount > 0:
                        added += 1
                
                except Exception as e:
                    print(f"  ⚠️ Error adding email for {row['github_username']}: {e}")
                    self.stats['errors'] += 1
                    continue
            
            self.conn.commit()
            self.stats['github_emails_added'] = added
            
        except Exception as e:
            print(f"  ⚠️ Error extracting GitHub emails: {e}")
            self.stats['errors'] += 1
            self.conn.rollback()
        
        cursor.close()
    
    def export_for_clay(self) -> str:
        """Export people without emails for Clay enrichment"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get people without emails, prioritizing those with GitHub profiles and recent employment
        query = """
            SELECT 
                p.person_id,
                p.full_name,
                p.linkedin_url,
                p.location,
                p.headline,
                c.company_name as current_company,
                c.website as company_website,
                gp.github_username,
                e.title as current_title
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
            LEFT JOIN employment e ON p.person_id = e.person_id AND e.end_date IS NULL
            LEFT JOIN company c ON e.company_id = c.company_id
            WHERE pe.person_id IS NULL
            ORDER BY 
                CASE WHEN gp.github_profile_id IS NOT NULL THEN 1 ELSE 2 END,
                CASE WHEN e.employment_id IS NOT NULL THEN 1 ELSE 2 END,
                p.person_id
            LIMIT 50000
        """
        
        cursor.execute(query)
        people = cursor.fetchall()
        
        # Export to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.export_path / f"people_need_email_enrichment_{timestamp}.csv"
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            if people:
                writer = csv.DictWriter(f, fieldnames=people[0].keys())
                writer.writeheader()
                writer.writerows(people)
        
        self.stats['export_count'] = len(people)
        cursor.close()
        
        return str(filename)
    
    def generate_email_patterns(self) -> str:
        """Generate likely email patterns for people based on name + company"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Get people with companies but no emails
        query = """
            SELECT 
                p.person_id,
                p.full_name,
                c.company_name,
                c.website,
                e.title
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
            JOIN employment e ON p.person_id = e.person_id
            JOIN company c ON e.company_id = c.company_id
            WHERE pe.person_id IS NULL
            AND e.end_date IS NULL
            AND c.website IS NOT NULL
            LIMIT 20000
        """
        
        cursor.execute(query)
        people = cursor.fetchall()
        
        suggestions = []
        
        for person in people:
            # Extract domain from company website
            domain = self._extract_domain(person['website'])
            
            if not domain:
                continue
            
            # Generate email patterns
            patterns = self._generate_email_patterns(person['full_name'], domain)
            
            suggestions.append({
                'person_id': person['person_id'],
                'full_name': person['full_name'],
                'company_name': person['company_name'],
                'domain': domain,
                'email_pattern_1': patterns[0] if len(patterns) > 0 else '',
                'email_pattern_2': patterns[1] if len(patterns) > 1 else '',
                'email_pattern_3': patterns[2] if len(patterns) > 2 else '',
                'email_pattern_4': patterns[3] if len(patterns) > 3 else '',
                'title': person['title']
            })
        
        # Export to CSV
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = self.export_path / f"email_pattern_suggestions_{timestamp}.csv"
        
        if suggestions:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=suggestions[0].keys())
                writer.writeheader()
                writer.writerows(suggestions)
        
        self.stats['pattern_suggestions'] = len(suggestions)
        cursor.close()
        
        return str(filename)
    
    def _extract_domain(self, website: str) -> str:
        """Extract domain from website URL"""
        if not website:
            return ""
        
        # Remove protocol
        domain = re.sub(r'^https?://', '', website)
        domain = re.sub(r'^www\.', '', domain)
        
        # Remove path
        domain = domain.split('/')[0]
        
        # Remove port
        domain = domain.split(':')[0]
        
        return domain.lower()
    
    def _generate_email_patterns(self, full_name: str, domain: str) -> list:
        """
        Generate common email patterns from name and domain
        
        Examples:
            "John Smith" @ "company.com" →
            - john.smith@company.com
            - john@company.com
            - jsmith@company.com
            - smithj@company.com
        """
        if not full_name or not domain:
            return []
        
        # Normalize and split name
        name_parts = re.sub(r'[^a-zA-Z\s]', '', full_name.lower()).split()
        
        if len(name_parts) < 2:
            first = name_parts[0] if name_parts else ""
            return [f"{first}@{domain}"] if first else []
        
        first = name_parts[0]
        last = name_parts[-1]
        
        patterns = [
            f"{first}.{last}@{domain}",           # john.smith@company.com
            f"{first}{last}@{domain}",             # johnsmith@company.com
            f"{first}@{domain}",                   # john@company.com
            f"{first[0]}{last}@{domain}",         # jsmith@company.com
            f"{first}{last[0]}@{domain}",         # johns@company.com
            f"{last}.{first}@{domain}",           # smith.john@company.com
            f"{first}_{last}@{domain}",           # john_smith@company.com
            f"{first}-{last}@{domain}",           # john-smith@company.com
        ]
        
        return patterns


def main():
    """Main execution"""
    extractor = EmailExtractor()
    extractor.run()


if __name__ == "__main__":
    main()

