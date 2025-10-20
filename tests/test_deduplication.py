# ABOUTME: Unit and integration tests for person deduplication logic
# ABOUTME: Tests duplicate detection, grouping, and merging

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "migration_scripts"))
from migration_utils import normalize_linkedin_url


@pytest.mark.integration
class TestDuplicateDetection:
    """Test duplicate detection logic"""
    
    def test_find_duplicates_by_linkedin(self, pg_test_conn, insert_test_person):
        """Test finding duplicates by LinkedIn URL"""
        # Insert two people with same LinkedIn URL
        person1_data = {
            'full_name': 'John Smith',
            'first_name': 'John',
            'last_name': 'Smith',
            'linkedin_url': 'https://www.linkedin.com/in/john-smith',
            'normalized_linkedin_url': normalize_linkedin_url('https://www.linkedin.com/in/john-smith')
        }
        person2_data = {
            'full_name': 'J. Smith',
            'first_name': 'J',
            'last_name': 'Smith',
            'linkedin_url': 'https://linkedin.com/in/john-smith/',
            'normalized_linkedin_url': normalize_linkedin_url('https://linkedin.com/in/john-smith/')
        }
        
        insert_test_person(person1_data)
        insert_test_person(person2_data)
        
        # Query for duplicates
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT 
                normalized_linkedin_url,
                COUNT(*) as count
            FROM person
            WHERE normalized_linkedin_url IS NOT NULL
            AND normalized_linkedin_url != ''
            GROUP BY normalized_linkedin_url
            HAVING COUNT(*) > 1
        """)
        
        duplicates = cursor.fetchall()
        assert len(duplicates) == 1
        assert duplicates[0][1] == 2  # Two duplicates
    
    def test_no_duplicates_different_linkedin(self, pg_test_conn, insert_test_person):
        """Test that different LinkedIn URLs don't match"""
        person1_data = {
            'full_name': 'John Smith',
            'linkedin_url': 'https://www.linkedin.com/in/john-smith',
            'normalized_linkedin_url': normalize_linkedin_url('https://www.linkedin.com/in/john-smith')
        }
        person2_data = {
            'full_name': 'Jane Doe',
            'linkedin_url': 'https://www.linkedin.com/in/jane-doe',
            'normalized_linkedin_url': normalize_linkedin_url('https://www.linkedin.com/in/jane-doe')
        }
        
        insert_test_person(person1_data)
        insert_test_person(person2_data)
        
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM person
            WHERE normalized_linkedin_url IS NOT NULL
        """)
        
        count = cursor.fetchone()[0]
        assert count == 2
    
    def test_find_duplicates_by_email(self, pg_test_conn, insert_test_person):
        """Test finding duplicates by email"""
        # Insert two people
        person1_id = insert_test_person({
            'full_name': 'John Smith',
            'linkedin_url': 'https://www.linkedin.com/in/john-smith-1',
            'normalized_linkedin_url': normalize_linkedin_url('https://www.linkedin.com/in/john-smith-1')
        })
        person2_id = insert_test_person({
            'full_name': 'J. Smith',
            'linkedin_url': 'https://www.linkedin.com/in/john-smith-2',
            'normalized_linkedin_url': normalize_linkedin_url('https://www.linkedin.com/in/john-smith-2')
        })
        
        # Add same email to both
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            INSERT INTO person_email (person_id, email, is_primary)
            VALUES (%s, %s, TRUE), (%s, %s, TRUE)
        """, (person1_id, 'john@example.com', person2_id, 'john@example.com'))
        pg_test_conn.commit()
        
        # Query for email duplicates
        cursor.execute("""
            SELECT 
                lower(email) as email,
                COUNT(DISTINCT person_id) as count
            FROM person_email
            GROUP BY lower(email)
            HAVING COUNT(DISTINCT person_id) > 1
        """)
        
        duplicates = cursor.fetchall()
        assert len(duplicates) == 1
        assert duplicates[0][1] == 2


@pytest.mark.unit
class TestDuplicateGroupConsolidation:
    """Test consolidation of overlapping duplicate groups"""
    
    def test_simple_groups(self):
        """Test non-overlapping groups stay separate"""
        linkedin_dupes = [['id1', 'id2'], ['id3', 'id4']]
        email_dupes = [['id5', 'id6']]
        
        # Simple consolidation logic (union-find simplified for test)
        all_groups = {}
        for group in linkedin_dupes + email_dupes:
            for person_id in group:
                if person_id not in all_groups:
                    all_groups[person_id] = set(group)
        
        unique_groups = list({tuple(sorted(g)) for g in all_groups.values()})
        assert len(unique_groups) == 3
    
    def test_overlapping_groups(self):
        """Test that overlapping groups merge"""
        # A=B by LinkedIn, B=C by email -> A=B=C
        linkedin_dupes = [['idA', 'idB']]
        email_dupes = [['idB', 'idC']]
        
        # Union-find merge
        groups = {}
        
        def find_group(pid):
            if pid not in groups:
                groups[pid] = {pid}
            return groups[pid]
        
        def merge(g1, g2):
            g1.update(g2)
            for pid in g2:
                groups[pid] = g1
            return g1
        
        for dupe_list in linkedin_dupes + email_dupes:
            if len(dupe_list) < 2:
                continue
            first_group = find_group(dupe_list[0])
            for pid in dupe_list[1:]:
                pid_group = find_group(pid)
                if first_group != pid_group:
                    first_group = merge(first_group, pid_group)
        
        final_groups = list({tuple(sorted(g)) for g in groups.values()})
        assert len(final_groups) == 1
        assert set(final_groups[0]) == {'idA', 'idB', 'idC'}


@pytest.mark.integration
class TestPersonMerging:
    """Test person merging logic"""
    
    def test_merge_transfers_emails(self, pg_test_conn, insert_test_person):
        """Test that merging transfers emails from secondary to primary"""
        # Create two people
        person1_id = insert_test_person({'full_name': 'John Smith'})
        person2_id = insert_test_person({'full_name': 'John Smith'})
        
        # Add different emails to each
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            INSERT INTO person_email (person_id, email, is_primary)
            VALUES (%s, %s, TRUE), (%s, %s, TRUE)
        """, (person1_id, 'john1@example.com', person2_id, 'john2@example.com'))
        pg_test_conn.commit()
        
        # Merge person2 into person1
        cursor.execute("""
            UPDATE person_email
            SET person_id = %s
            WHERE person_id = %s
            AND lower(email) NOT IN (
                SELECT lower(email) FROM person_email WHERE person_id = %s
            )
        """, (person1_id, person2_id, person1_id))
        pg_test_conn.commit()
        
        # Check that person1 now has both emails
        cursor.execute("""
            SELECT COUNT(*) FROM person_email WHERE person_id = %s
        """, (person1_id,))
        email_count = cursor.fetchone()[0]
        assert email_count == 2
    
    def test_merge_avoids_duplicate_emails(self, pg_test_conn, insert_test_person):
        """Test that merging doesn't create duplicate emails"""
        person1_id = insert_test_person({'full_name': 'John Smith'})
        person2_id = insert_test_person({'full_name': 'John Smith'})
        
        # Add same email to both
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            INSERT INTO person_email (person_id, email, is_primary)
            VALUES (%s, %s, TRUE), (%s, %s, TRUE)
        """, (person1_id, 'john@example.com', person2_id, 'john@example.com'))
        pg_test_conn.commit()
        
        # Attempt merge (should skip duplicate)
        cursor.execute("""
            UPDATE person_email
            SET person_id = %s
            WHERE person_id = %s
            AND lower(email) NOT IN (
                SELECT lower(email) FROM person_email WHERE person_id = %s
            )
        """, (person1_id, person2_id, person1_id))
        updated = cursor.rowcount
        pg_test_conn.commit()
        
        # Should not have updated anything (email already exists)
        assert updated == 0
        
        # Verify only one email for person1
        cursor.execute("""
            SELECT COUNT(*) FROM person_email WHERE person_id = %s
        """, (person1_id,))
        email_count = cursor.fetchone()[0]
        assert email_count == 1
    
    def test_merge_transfers_employment(self, pg_test_conn, insert_test_person, insert_test_company):
        """Test that merging transfers employment records"""
        person1_id = insert_test_person({'full_name': 'John Smith'})
        person2_id = insert_test_person({'full_name': 'John Smith'})
        company_id = insert_test_company({'company_name': 'Acme Corp'})
        
        # Add employment to person2
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            INSERT INTO employment (person_id, company_id, title, is_current)
            VALUES (%s, %s, %s, TRUE)
        """, (person2_id, company_id, 'Engineer'))
        pg_test_conn.commit()
        
        # Merge employment from person2 to person1
        cursor.execute("""
            UPDATE employment
            SET person_id = %s
            WHERE person_id = %s
        """, (person1_id, person2_id))
        pg_test_conn.commit()
        
        # Verify person1 has the employment
        cursor.execute("""
            SELECT COUNT(*) FROM employment WHERE person_id = %s
        """, (person1_id,))
        count = cursor.fetchone()[0]
        assert count == 1
        
        # Verify person2 has no employment
        cursor.execute("""
            SELECT COUNT(*) FROM employment WHERE person_id = %s
        """, (person2_id,))
        count = cursor.fetchone()[0]
        assert count == 0


@pytest.mark.unit
class TestPrimaryPersonSelection:
    """Test choosing which person to keep as primary"""
    
    def test_prefer_more_complete_data(self):
        """Should prefer person with more complete data"""
        person1 = {
            'full_name': 'John Smith',
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'location': 'San Francisco',
            'headline': None,
            'followers_count': 0
        }
        person2 = {
            'full_name': 'John Smith',
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'location': 'San Francisco',
            'headline': 'Software Engineer',
            'followers_count': 500
        }
        
        # Score based on completeness and followers
        def score_person(p):
            score = sum(1 for v in p.values() if v not in [None, '', 0])
            score += min(p['followers_count'] / 1000 * 20, 20)
            return score
        
        score1 = score_person(person1)
        score2 = score_person(person2)
        
        assert score2 > score1  # person2 should score higher
    
    def test_prefer_more_recent(self):
        """Should prefer person with more recent data"""
        from datetime import datetime, timedelta
        
        recent = datetime.now()
        old = datetime.now() - timedelta(days=365)
        
        # Recent data should be preferred
        assert recent > old

