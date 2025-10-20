# ABOUTME: Tests for secure query functions
# ABOUTME: Validates parameterized queries and SQL injection prevention

import pytest
import sqlite3


@pytest.mark.unit
class TestSQLInjectionPrevention:
    """Test that parameterized queries prevent SQL injection"""
    
    def test_parameterized_company_search(self, sqlite_test_db):
        """Test company search uses parameters correctly"""
        # Insert test data
        cursor = sqlite_test_db.cursor()
        cursor.execute("""
            INSERT INTO people (person_id, first_name, last_name, primary_email)
            VALUES ('id1', 'John', 'Smith', 'john@acme.com')
        """)
        cursor.execute("""
            INSERT INTO employment (person_id, company_name, title, is_current)
            VALUES ('id1', 'Acme Corp', 'Engineer', 1)
        """)
        sqlite_test_db.commit()
        
        # Try legitimate search
        company = "Acme"
        cursor.execute("""
            SELECT p.first_name, p.last_name, e.company_name
            FROM people p
            JOIN employment e ON p.person_id = e.person_id
            WHERE LOWER(e.company_name) LIKE LOWER(?)
        """, (f'%{company}%',))
        
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][2] == 'Acme Corp'
        
        # Try injection attempt (should find nothing, not execute malicious code)
        malicious = "'; DROP TABLE people; --"
        cursor.execute("""
            SELECT p.first_name, p.last_name, e.company_name
            FROM people p
            JOIN employment e ON p.person_id = e.person_id
            WHERE LOWER(e.company_name) LIKE LOWER(?)
        """, (f'%{malicious}%',))
        
        results = cursor.fetchall()
        assert len(results) == 0
        
        # Verify table still exists
        cursor.execute("SELECT COUNT(*) FROM people")
        assert cursor.fetchone()[0] == 1
    
    def test_parameterized_email_domain_search(self, sqlite_test_db):
        """Test email domain search is parameterized"""
        cursor = sqlite_test_db.cursor()
        cursor.execute("""
            INSERT INTO people (person_id, first_name, last_name, primary_email)
            VALUES ('id1', 'John', 'Smith', 'john@example.com')
        """)
        sqlite_test_db.commit()
        
        # Legitimate search
        domain = "example.com"
        cursor.execute("""
            SELECT first_name, last_name, primary_email
            FROM people
            WHERE primary_email LIKE ?
        """, (f'%@{domain}',))
        
        results = cursor.fetchall()
        assert len(results) == 1
        
        # Injection attempt
        malicious = "example.com' OR '1'='1"
        cursor.execute("""
            SELECT first_name, last_name, primary_email
            FROM people
            WHERE primary_email LIKE ?
        """, (f'%@{malicious}',))
        
        results = cursor.fetchall()
        assert len(results) == 0  # Should find nothing


@pytest.mark.integration
class TestQueryResults:
    """Test query result formatting and accuracy"""
    
    def test_search_by_company(self, pg_test_conn, insert_test_person, insert_test_company):
        """Test searching people by company"""
        # Insert test data
        person_id = insert_test_person({
            'full_name': 'John Smith',
            'first_name': 'John',
            'last_name': 'Smith',
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'normalized_linkedin_url': 'linkedin.com/in/john-smith'
        })
        
        company_id = insert_test_company({
            'company_name': 'Acme Corporation',
            'linkedin_url': 'https://linkedin.com/company/acme',
            'normalized_linkedin_url': 'linkedin.com/company/acme'
        })
        
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            INSERT INTO employment (person_id, company_id, title, is_current)
            VALUES (%s, %s, %s, TRUE)
        """, (person_id, company_id, 'Software Engineer'))
        pg_test_conn.commit()
        
        # Search by company
        cursor.execute("""
            SELECT p.first_name, p.last_name, c.company_name, e.title
            FROM person p
            JOIN employment e ON p.person_id = e.person_id
            JOIN company c ON e.company_id = c.company_id
            WHERE LOWER(c.company_name) LIKE LOWER(%s)
        """, ('%acme%',))
        
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'John'
        assert results[0][1] == 'Smith'
        assert 'Acme' in results[0][2]
        assert results[0][3] == 'Software Engineer'
    
    def test_search_by_location(self, pg_test_conn, insert_test_person):
        """Test searching people by location"""
        insert_test_person({
            'full_name': 'John Smith',
            'location': 'San Francisco, CA',
            'linkedin_url': 'https://linkedin.com/in/john-smith',
            'normalized_linkedin_url': 'linkedin.com/in/john-smith'
        })
        
        insert_test_person({
            'full_name': 'Jane Doe',
            'location': 'New York, NY',
            'linkedin_url': 'https://linkedin.com/in/jane-doe',
            'normalized_linkedin_url': 'linkedin.com/in/jane-doe'
        })
        
        pg_test_conn.commit()
        
        # Search for SF people
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT full_name, location
            FROM person
            WHERE LOWER(location) LIKE LOWER(%s)
        """, ('%san francisco%',))
        
        results = cursor.fetchall()
        assert len(results) == 1
        assert results[0][0] == 'John Smith'


@pytest.mark.unit
class TestPagination:
    """Test pagination functionality"""
    
    def test_limit_offset(self, pg_test_conn, insert_test_person):
        """Test LIMIT and OFFSET for pagination"""
        # Insert 10 people
        for i in range(10):
            insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}'
            })
        
        pg_test_conn.commit()
        
        # Get first page (5 results)
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT full_name FROM person
            ORDER BY full_name
            LIMIT %s OFFSET %s
        """, (5, 0))
        
        page1 = cursor.fetchall()
        assert len(page1) == 5
        
        # Get second page
        cursor.execute("""
            SELECT full_name FROM person
            ORDER BY full_name
            LIMIT %s OFFSET %s
        """, (5, 5))
        
        page2 = cursor.fetchall()
        assert len(page2) == 5
        
        # Verify no overlap
        page1_names = [r[0] for r in page1]
        page2_names = [r[0] for r in page2]
        assert len(set(page1_names) & set(page2_names)) == 0
    
    def test_pagination_beyond_results(self, pg_test_conn, insert_test_person):
        """Test pagination beyond available results"""
        # Insert only 3 people
        for i in range(3):
            insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}'
            })
        
        pg_test_conn.commit()
        
        # Try to get page 2 (offset 10, limit 10)
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT full_name FROM person
            LIMIT %s OFFSET %s
        """, (10, 10))
        
        results = cursor.fetchall()
        assert len(results) == 0


@pytest.mark.integration
class TestStatisticsQueries:
    """Test database statistics queries"""
    
    def test_count_totals(self, pg_test_conn, insert_test_person, insert_test_company):
        """Test counting total records"""
        # Insert test data
        for i in range(5):
            insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}'
            })
        
        for i in range(3):
            insert_test_company({
                'company_name': f'Company {i}',
                'linkedin_url': f'https://linkedin.com/company/company-{i}',
                'normalized_linkedin_url': f'linkedin.com/company/company-{i}'
            })
        
        pg_test_conn.commit()
        
        # Count people
        cursor = pg_test_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM person")
        person_count = cursor.fetchone()[0]
        assert person_count == 5
        
        # Count companies
        cursor.execute("SELECT COUNT(*) FROM company")
        company_count = cursor.fetchone()[0]
        assert company_count == 3
    
    def test_coverage_statistics(self, pg_test_conn, insert_test_person):
        """Test coverage percentage calculations"""
        # Insert people with varying data completeness
        for i in range(10):
            person_id = insert_test_person({
                'full_name': f'Person {i}',
                'linkedin_url': f'https://linkedin.com/in/person-{i}',
                'normalized_linkedin_url': f'linkedin.com/in/person-{i}',
                'location': f'City {i}' if i < 7 else None,
                'headline': f'Job {i}' if i < 5 else None
            })
            
            # Add email for first 6
            if i < 6:
                cursor = pg_test_conn.cursor()
                cursor.execute("""
                    INSERT INTO person_email (person_id, email)
                    VALUES (%s, %s)
                """, (person_id, f'person{i}@example.com'))
        
        pg_test_conn.commit()
        
        # Calculate statistics
        cursor = pg_test_conn.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(location) as with_location,
                COUNT(headline) as with_headline,
                COUNT(DISTINCT pe.person_id) as with_email
            FROM person p
            LEFT JOIN person_email pe ON p.person_id = pe.person_id
        """)
        
        result = cursor.fetchone()
        assert result[0] == 10  # Total
        assert result[1] == 7   # With location
        assert result[2] == 5   # With headline
        assert result[3] == 6   # With email

