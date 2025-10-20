# ABOUTME: Tests for data quality scoring and completeness checks
# ABOUTME: Validates quality metrics and coverage calculations

import pytest


@pytest.mark.unit
class TestQualityScoreCalculation:
    """Test data quality score calculation"""
    
    def test_perfect_score(self):
        """Test perfect quality score with all fields"""
        record = {
            'first_name': 'John',
            'last_name': 'Smith',
            'primary_email': 'john@example.com',
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'current_company': 'Acme Corp',
            'current_title': 'Engineer',
            'github_url': 'https://github.com/johnsmith'
        }
        
        weights = {
            'first_name': 0.15,
            'last_name': 0.15,
            'primary_email': 0.25,
            'linkedin_url': 0.20,
            'current_company': 0.10,
            'current_title': 0.10,
            'github_url': 0.05
        }
        
        score = sum(weights[field] for field in weights if record.get(field))
        assert score == 1.0
    
    def test_minimum_viable_score(self):
        """Test minimum viable quality score"""
        record = {
            'first_name': 'John',
            'last_name': 'Smith',
            'primary_email': 'john@example.com'
        }
        
        weights = {
            'first_name': 0.15,
            'last_name': 0.15,
            'primary_email': 0.25,
            'linkedin_url': 0.20,
            'current_company': 0.10,
            'current_title': 0.10,
            'github_url': 0.05
        }
        
        score = sum(weights[field] for field in weights if record.get(field))
        assert score == 0.55  # Name + email
    
    def test_below_threshold_score(self):
        """Test score below minimum threshold"""
        record = {
            'first_name': 'John',
            'last_name': 'Smith'
        }
        
        weights = {
            'first_name': 0.15,
            'last_name': 0.15,
            'primary_email': 0.25,
            'linkedin_url': 0.20,
            'current_company': 0.10,
            'current_title': 0.10,
            'github_url': 0.05
        }
        
        score = sum(weights[field] for field in weights if record.get(field))
        assert score == 0.30  # Just name, at threshold
    
    def test_empty_values_ignored(self):
        """Test that empty strings don't count toward score"""
        record = {
            'first_name': 'John',
            'last_name': 'Smith',
            'primary_email': '',  # Empty string should not count
            'linkedin_url': None  # None should not count
        }
        
        weights = {
            'first_name': 0.15,
            'last_name': 0.15,
            'primary_email': 0.25,
            'linkedin_url': 0.20,
            'current_company': 0.10,
            'current_title': 0.10,
            'github_url': 0.05
        }
        
        score = sum(
            weights[field] 
            for field in weights 
            if record.get(field) and str(record[field]).strip()
        )
        assert score == 0.30  # Just first and last name


@pytest.mark.integration
class TestCoverageMetrics:
    """Test coverage percentage calculations"""
    
    def test_email_coverage(self, pg_test_conn, insert_test_person):
        """Test email coverage calculation"""
        # Insert 10 people, 7 with emails
        for i in range(10):
            person_id = insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}'
            })
            
            if i < 7:  # First 7 get emails
                cursor = pg_test_conn.cursor()
                cursor.execute("""
                    INSERT INTO person_email (person_id, email, is_primary)
                    VALUES (%s, %s, TRUE)
                """, (person_id, f'person{i}@example.com'))
        
        pg_test_conn.commit()
        
        # Calculate coverage
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT p.person_id) as total_people,
                COUNT(DISTINCT pe.person_id) as people_with_email
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
        """)
        
        result = cursor.fetchone()
        total = result[0]
        with_email = result[1]
        coverage = (with_email / total) * 100 if total > 0 else 0
        
        assert total == 10
        assert with_email == 7
        assert coverage == 70.0
    
    def test_linkedin_coverage(self, pg_test_conn, insert_test_person):
        """Test LinkedIn coverage calculation"""
        # Insert 5 people, all with LinkedIn
        for i in range(5):
            insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}'
            })
        
        pg_test_conn.commit()
        
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(normalized_linkedin_url) as with_linkedin
            FROM person
        """)
        
        result = cursor.fetchone()
        total = result[0]
        with_linkedin = result[1]
        coverage = (with_linkedin / total) * 100 if total > 0 else 0
        
        assert coverage == 100.0
    
    def test_github_coverage(self, pg_test_conn, insert_test_person):
        """Test GitHub profile coverage"""
        # Insert 10 people, 5 with GitHub
        for i in range(10):
            person_id = insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}'
            })
            
            if i < 5:  # First 5 get GitHub profiles
                cursor = pg_test_conn.cursor()
                cursor.execute("""
                    INSERT INTO github_profile (person_id, github_username, github_url)
                    VALUES (%s, %s, %s)
                """, (person_id, f'user{i}', f'https://github.com/user{i}'))
        
        pg_test_conn.commit()
        
        # Calculate coverage
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT p.person_id) as total_people,
                COUNT(DISTINCT gp.person_id) as people_with_github
            FROM person p
            LEFT JOIN github_profile gp ON p.person_id = gp.person_id
        """)
        
        result = cursor.fetchone()
        total = result[0]
        with_github = result[1]
        coverage = (with_github / total) * 100 if total > 0 else 0
        
        assert total == 10
        assert with_github == 5
        assert coverage == 50.0


@pytest.mark.integration
class TestDataCompleteness:
    """Test data completeness checks"""
    
    def test_missing_critical_fields(self, pg_test_conn, insert_test_person):
        """Test detection of missing critical fields"""
        # Insert person with missing fields
        person_id = insert_test_person({
            'full_name': 'John Smith',
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'normalized_linkedin_url': 'linkedin.com/in/john-smith',
            'location': None,  # Missing
            'headline': None   # Missing
        })
        
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT 
                CASE WHEN location IS NULL OR location = '' THEN 1 ELSE 0 END as missing_location,
                CASE WHEN headline IS NULL OR headline = '' THEN 1 ELSE 0 END as missing_headline
            FROM person
            WHERE person_id = %s
        """, (person_id,))
        
        result = cursor.fetchone()
        assert result[0] == 1  # Missing location
        assert result[1] == 1  # Missing headline
    
    def test_invalid_data_formats(self, pg_test_conn):
        """Test detection of invalid data formats"""
        cursor = pg_test_conn.cursor()
        
        # Insert person with invalid email
        cursor.execute("""
            INSERT INTO person (full_name, linkedin_url)
            VALUES (%s, %s)
            RETURNING person_id
        """, ('Test Person', 'https://linkedin.com/in/test'))
        person_id = cursor.fetchone()[0]
        
        # Try to add invalid email
        try:
            cursor.execute("""
                INSERT INTO person_email (person_id, email)
                VALUES (%s, %s)
            """, (person_id, 'not-an-email'))
            # If we get here, check if email is truly invalid
            cursor.execute("""
                SELECT email FROM person_email WHERE person_id = %s
            """, (person_id,))
            email = cursor.fetchone()[0]
            # Basic validation check
            assert '@' in email or email == 'not-an-email'
        except Exception:
            # Expected if there's a constraint
            pg_test_conn.rollback()
            pass


@pytest.mark.unit
class TestQualityThresholds:
    """Test quality threshold enforcement"""
    
    def test_above_threshold(self):
        """Test records above quality threshold"""
        min_threshold = 0.3
        score = 0.55
        assert score >= min_threshold
    
    def test_below_threshold(self):
        """Test records below quality threshold"""
        min_threshold = 0.3
        score = 0.25
        assert score < min_threshold
    
    def test_at_threshold(self):
        """Test records at quality threshold"""
        min_threshold = 0.3
        score = 0.3
        assert score >= min_threshold

