# ABOUTME: Pytest configuration and fixtures for test suite
# ABOUTME: Provides database connections, sample data, and test utilities

import pytest
import psycopg2
import sqlite3
from pathlib import Path
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List
from faker import Faker

# Import config
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config

fake = Faker()


@pytest.fixture(scope="session")
def test_db_name():
    """Test database name"""
    return "talent_test"


@pytest.fixture(scope="session")
def pg_test_connection_params(test_db_name):
    """PostgreSQL test database connection parameters"""
    return {
        'host': Config.PG_HOST,
        'port': Config.PG_PORT,
        'database': test_db_name,
        'user': Config.PG_USER,
        'password': Config.PG_PASSWORD
    }


@pytest.fixture(scope="session")
def create_test_database(test_db_name):
    """Create test database once per session"""
    # Connect to default postgres database to create test database
    conn = psycopg2.connect(
        host=Config.PG_HOST,
        port=Config.PG_PORT,
        database='postgres',
        user=Config.PG_USER,
        password=Config.PG_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Drop test database if exists
    cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
    
    # Create test database
    cursor.execute(f"CREATE DATABASE {test_db_name}")
    
    cursor.close()
    conn.close()
    
    yield test_db_name
    
    # Cleanup: drop test database after all tests
    conn = psycopg2.connect(
        host=Config.PG_HOST,
        port=Config.PG_PORT,
        database='postgres',
        user=Config.PG_USER,
        password=Config.PG_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    cursor.execute(f"DROP DATABASE IF EXISTS {test_db_name}")
    cursor.close()
    conn.close()


@pytest.fixture(scope="session")
def pg_test_schema(create_test_database, pg_test_connection_params):
    """Create test database schema"""
    conn = psycopg2.connect(**pg_test_connection_params)
    cursor = conn.cursor()
    
    # Read and execute schema from migration script
    schema_file = Path(__file__).parent.parent / "migration_scripts" / "01_schema_enhancement.sql"
    
    if schema_file.exists():
        with open(schema_file, 'r') as f:
            schema_sql = f.read()
            cursor.execute(schema_sql)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    yield
    
    # No cleanup needed - database will be dropped


@pytest.fixture
def pg_test_conn(pg_test_schema, pg_test_connection_params):
    """PostgreSQL test connection (function scope - cleaned between tests)"""
    conn = psycopg2.connect(**pg_test_connection_params)
    conn.autocommit = False
    
    yield conn
    
    # Rollback any uncommitted changes
    conn.rollback()
    
    # Clean up test data
    cursor = conn.cursor()
    cursor.execute("TRUNCATE person CASCADE")
    cursor.execute("TRUNCATE company CASCADE")
    cursor.execute("TRUNCATE migration_log CASCADE")
    conn.commit()
    
    cursor.close()
    conn.close()


@pytest.fixture
def sqlite_test_db():
    """SQLite test database (temporary)"""
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Create basic schema for testing
    cursor.execute("""
        CREATE TABLE people (
            person_id TEXT PRIMARY KEY,
            first_name TEXT,
            last_name TEXT,
            primary_email TEXT,
            location TEXT,
            data_quality_score REAL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE social_profiles (
            profile_id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT,
            platform TEXT,
            profile_url TEXT,
            FOREIGN KEY (person_id) REFERENCES people(person_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE emails (
            email_id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT,
            email TEXT,
            email_type TEXT,
            is_primary INTEGER,
            FOREIGN KEY (person_id) REFERENCES people(person_id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE employment (
            employment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            person_id TEXT,
            company_name TEXT,
            title TEXT,
            is_current INTEGER,
            FOREIGN KEY (person_id) REFERENCES people(person_id)
        )
    """)
    
    conn.commit()
    
    yield conn
    
    conn.close()
    shutil.rmtree(temp_dir)


@pytest.fixture
def sample_person_data() -> Dict:
    """Generate sample person data"""
    return {
        'full_name': fake.name(),
        'first_name': fake.first_name(),
        'last_name': fake.last_name(),
        'linkedin_url': f"https://www.linkedin.com/in/{fake.user_name()}",
        'location': fake.city(),
        'headline': fake.job(),
        'description': fake.text(max_nb_chars=200)
    }


@pytest.fixture
def sample_people_data() -> List[Dict]:
    """Generate multiple sample people"""
    return [
        {
            'full_name': fake.name(),
            'first_name': fake.first_name(),
            'last_name': fake.last_name(),
            'linkedin_url': f"https://www.linkedin.com/in/{fake.user_name()}",
            'location': fake.city(),
            'headline': fake.job(),
            'description': fake.text(max_nb_chars=200)
        }
        for _ in range(10)
    ]


@pytest.fixture
def sample_company_data() -> Dict:
    """Generate sample company data"""
    return {
        'company_name': fake.company(),
        'linkedin_url': f"https://www.linkedin.com/company/{fake.company().lower().replace(' ', '-')}",
        'website': fake.url(),
        'industry': fake.bs(),
        'description': fake.catch_phrase()
    }


@pytest.fixture
def sample_email_data() -> Dict:
    """Generate sample email data"""
    return {
        'email': fake.email(),
        'email_type': 'work',
        'is_primary': True
    }


@pytest.fixture
def sample_github_profile_data() -> Dict:
    """Generate sample GitHub profile data"""
    username = fake.user_name()
    return {
        'github_username': username,
        'github_name': fake.name(),
        'github_url': f"https://github.com/{username}",
        'bio': fake.text(max_nb_chars=100),
        'followers': fake.random_int(min=0, max=1000),
        'following': fake.random_int(min=0, max=500),
        'public_repos': fake.random_int(min=0, max=100)
    }


@pytest.fixture
def mock_github_api_response():
    """Mock GitHub API response"""
    username = fake.user_name()
    return {
        'login': username,
        'name': fake.name(),
        'bio': fake.text(max_nb_chars=100),
        'followers': fake.random_int(min=0, max=1000),
        'following': fake.random_int(min=0, max=500),
        'public_repos': fake.random_int(min=0, max=100),
        'html_url': f"https://github.com/{username}",
        'avatar_url': f"https://avatars.githubusercontent.com/u/{fake.random_int(min=1000, max=999999)}",
        'created_at': fake.iso8601(),
        'updated_at': fake.iso8601()
    }


@pytest.fixture
def insert_test_person(pg_test_conn):
    """Helper to insert test person into PostgreSQL"""
    def _insert(person_data: Dict):
        cursor = pg_test_conn.cursor()
        
        cursor.execute("""
            INSERT INTO person 
            (full_name, first_name, last_name, linkedin_url, normalized_linkedin_url, 
             location, headline, description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING person_id
        """, (
            person_data.get('full_name'),
            person_data.get('first_name'),
            person_data.get('last_name'),
            person_data.get('linkedin_url'),
            person_data.get('normalized_linkedin_url') or person_data.get('linkedin_url', '').lower(),
            person_data.get('location'),
            person_data.get('headline'),
            person_data.get('description')
        ))
        
        person_id = cursor.fetchone()[0]
        pg_test_conn.commit()
        
        return person_id
    
    return _insert


@pytest.fixture
def insert_test_company(pg_test_conn):
    """Helper to insert test company into PostgreSQL"""
    def _insert(company_data: Dict):
        cursor = pg_test_conn.cursor()
        
        cursor.execute("""
            INSERT INTO company 
            (company_name, linkedin_url, normalized_linkedin_url, website, industry, description)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING company_id
        """, (
            company_data.get('company_name'),
            company_data.get('linkedin_url'),
            company_data.get('normalized_linkedin_url') or company_data.get('linkedin_url', '').lower(),
            company_data.get('website'),
            company_data.get('industry'),
            company_data.get('description')
        ))
        
        company_id = cursor.fetchone()[0]
        pg_test_conn.commit()
        
        return company_id
    
    return _insert

