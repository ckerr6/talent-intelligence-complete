"""
GitHub Ingestion Service
Handles ingestion of individual GitHub users and organizations
Matches profiles with existing database records or creates new ones
"""

import os
import uuid
import logging
from typing import Dict, List, Optional, Tuple
import requests
from datetime import datetime
from psycopg2.extras import RealDictCursor
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class GitHubIngestionService:
    """Service for ingesting GitHub users and organizations"""
    
    def __init__(self, db_conn):
        self.db = db_conn
        self.cursor = db_conn.cursor(cursor_factory=RealDictCursor)
        self.github_token = os.environ.get('GITHUB_TOKEN', '')
        self.headers = {
            'Authorization': f'token {self.github_token}' if self.github_token else '',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Stats tracking
        self.stats = {
            'users_processed': 0,
            'profiles_matched': 0,
            'profiles_created': 0,
            'repos_added': 0,
            'contributions_added': 0,
            'errors': []
        }
    
    def ingest_user(self, username: str) -> Dict:
        """
        Ingest a single GitHub user
        
        Args:
            username: GitHub username
            
        Returns:
            Dict with ingestion results and statistics
        """
        logger.info(f"Starting ingestion for GitHub user: {username}")
        
        try:
            # Fetch user data from GitHub API
            user_data = self._fetch_github_user(username)
            if not user_data:
                return {'success': False, 'error': 'User not found on GitHub'}
            
            # Try to match with existing person
            person_id = self._match_or_create_person(user_data)
            
            # Ingest user's OWN repositories
            own_repos = self._fetch_user_repos(username)
            logger.info(f"Found {len(own_repos)} owned repos for {username}")
            for repo in own_repos[:50]:  # Limit to top 50 repos
                self._ingest_repository(repo, person_id, contribution_type='owner')
            
            # Ingest repositories they've CONTRIBUTED to (even if they don't own them)
            contributed_repos = self._fetch_user_starred_and_contributed_repos(username)
            logger.info(f"Found {len(contributed_repos)} contributed repos for {username}")
            for repo in contributed_repos[:100]:  # More generous limit for contributions
                self._ingest_repository(repo, person_id, contribution_type='contributor')
            
            self.db.commit()
            self.stats['users_processed'] += 1
            
            return {
                'success': True,
                'person_id': person_id,
                'stats': self.stats,
                'user_data': {
                    'username': username,
                    'name': user_data.get('name'),
                    'email': user_data.get('email'),
                    'owned_repos': len(own_repos),
                    'contributed_repos': len(contributed_repos)
                }
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error ingesting user {username}: {str(e)}")
            self.stats['errors'].append(str(e))
            return {'success': False, 'error': str(e)}
    
    def ingest_organization(self, org_name: str) -> Dict:
        """
        Ingest an entire GitHub organization
        
        Args:
            org_name: GitHub organization name
            
        Returns:
            Dict with ingestion results and statistics
        """
        logger.info(f"Starting ingestion for GitHub organization: {org_name}")
        
        try:
            # Create or find company for this organization
            company_id = self._find_or_create_company(org_name)
            
            # Fetch organization members
            members = self._fetch_org_members(org_name)
            logger.info(f"Found {len(members)} members in {org_name}")
            
            # Fetch organization repositories
            repos = self._fetch_org_repos(org_name)
            logger.info(f"Found {len(repos)} repositories in {org_name}")
            
            # Process each member
            member_results = []
            for member in members[:100]:  # Limit to first 100 members
                username = member.get('login')
                if username:
                    result = self.ingest_user(username)
                    member_results.append(result)
            
            # Process organization repositories
            for repo in repos:
                self._ingest_org_repository(repo, org_name)
            
            self.db.commit()
            
            return {
                'success': True,
                'company_id': company_id,
                'organization': org_name,
                'members_processed': len(member_results),
                'repos_processed': len(repos),
                'stats': self.stats
            }
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error ingesting organization {org_name}: {str(e)}")
            self.stats['errors'].append(str(e))
            return {'success': False, 'error': str(e)}
    
    def _fetch_github_user(self, username: str) -> Optional[Dict]:
        """Fetch user data from GitHub API"""
        try:
            response = requests.get(
                f'https://api.github.com/users/{username}',
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching GitHub user {username}: {str(e)}")
            return None
    
    def _fetch_user_repos(self, username: str) -> List[Dict]:
        """Fetch user's repositories from GitHub API"""
        try:
            response = requests.get(
                f'https://api.github.com/users/{username}/repos',
                headers=self.headers,
                params={'sort': 'updated', 'per_page': 100},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching repos for {username}: {str(e)}")
            return []
    
    def _fetch_org_members(self, org_name: str) -> List[Dict]:
        """Fetch organization members from GitHub API"""
        try:
            response = requests.get(
                f'https://api.github.com/orgs/{org_name}/members',
                headers=self.headers,
                params={'per_page': 100},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching members for {org_name}: {str(e)}")
            return []
    
    def _fetch_org_repos(self, org_name: str) -> List[Dict]:
        """Fetch organization repositories from GitHub API"""
        try:
            response = requests.get(
                f'https://api.github.com/orgs/{org_name}/repos',
                headers=self.headers,
                params={'per_page': 100},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error fetching repos for {org_name}: {str(e)}")
            return []
    
    def _match_or_create_person(self, user_data: Dict) -> str:
        """
        Match GitHub user with existing person or create new one
        
        Matching strategy:
        1. Check github_profile.github_username for exact match
        2. Check person_email.email against user_data['email']
        3. Check person.full_name fuzzy match with user_data['name']
        4. If no match, create new person with [GitHub] prefix
        
        Returns:
            person_id (UUID string)
        """
        username = user_data.get('login')
        email = user_data.get('email')
        name = user_data.get('name')
        
        # Strategy 1: Check existing github_profile
        if username:
            self.cursor.execute("""
                SELECT person_id FROM github_profile
                WHERE github_username = %s
                LIMIT 1
            """, (username,))
            result = self.cursor.fetchone()
            if result:
                logger.info(f"Matched {username} via github_username")
                self.stats['profiles_matched'] += 1
                return str(result['person_id'])
        
        # Strategy 2: Check by email
        if email:
            self.cursor.execute("""
                SELECT person_id FROM person_email
                WHERE LOWER(email) = LOWER(%s)
                LIMIT 1
            """, (email,))
            result = self.cursor.fetchone()
            if result:
                logger.info(f"Matched {username} via email: {email}")
                self.stats['profiles_matched'] += 1
                # Link GitHub profile to existing person
                self._create_github_profile(result['person_id'], user_data)
                return str(result['person_id'])
        
        # Strategy 3: Fuzzy name match (if name is substantial)
        if name and len(name.split()) >= 2:
            self.cursor.execute("""
                SELECT person_id, full_name FROM person
                WHERE full_name IS NOT NULL
                AND LENGTH(full_name) > 5
                LIMIT 1000
            """)
            people = self.cursor.fetchall()
            
            best_match = None
            best_score = 0
            for person in people:
                score = fuzz.ratio(name.lower(), person['full_name'].lower())
                if score > best_score and score >= 85:  # 85% similarity threshold
                    best_score = score
                    best_match = person
            
            if best_match:
                logger.info(f"Matched {username} via fuzzy name match (score: {best_score})")
                self.stats['profiles_matched'] += 1
                # Link GitHub profile to existing person
                self._create_github_profile(best_match['person_id'], user_data)
                return str(best_match['person_id'])
        
        # No match found - create new person
        person_id = self._create_person_from_github(user_data)
        self._create_github_profile(person_id, user_data)
        self.stats['profiles_created'] += 1
        logger.info(f"Created new person for {username}")
        
        return person_id
    
    def _create_person_from_github(self, user_data: Dict) -> str:
        """Create a new person record from GitHub data"""
        username = user_data.get('login')
        name = user_data.get('name') or f'[GitHub] {username}'
        bio = user_data.get('bio')
        location = user_data.get('location')
        
        person_id = str(uuid.uuid4())
        
        self.cursor.execute("""
            INSERT INTO person (
                person_id, full_name, headline, location, description
            ) VALUES (
                %s, %s, %s, %s, %s
            )
            RETURNING person_id
        """, (person_id, name, bio, location, f'GitHub user: {username}'))
        
        # Add email if available
        email = user_data.get('email')
        if email:
            self.cursor.execute("""
                INSERT INTO person_email (person_id, email, email_type, is_primary, source)
                VALUES (%s, %s, 'personal', true, 'github_ingestion')
                ON CONFLICT DO NOTHING
            """, (person_id, email))
        
        return person_id
    
    def _create_github_profile(self, person_id: str, user_data: Dict) -> str:
        """Create or update github_profile record"""
        self.cursor.execute("""
            INSERT INTO github_profile (
                person_id, github_username, github_name, github_email,
                followers, following, public_repos, bio, location,
                avatar_url, created_at_github, updated_at_github, source
            ) VALUES (
                %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'manual_ingestion'
            )
            ON CONFLICT (github_username) 
            DO UPDATE SET
                person_id = EXCLUDED.person_id,
                github_name = EXCLUDED.github_name,
                github_email = EXCLUDED.github_email,
                followers = EXCLUDED.followers,
                following = EXCLUDED.following,
                public_repos = EXCLUDED.public_repos,
                bio = EXCLUDED.bio,
                location = EXCLUDED.location,
                updated_at_github = EXCLUDED.updated_at_github
            RETURNING github_profile_id
        """, (
            person_id,
            user_data.get('login'),
            user_data.get('name'),
            user_data.get('email'),
            user_data.get('followers', 0),
            user_data.get('following', 0),
            user_data.get('public_repos', 0),
            user_data.get('bio'),
            user_data.get('location'),
            user_data.get('avatar_url'),
            user_data.get('created_at'),
            user_data.get('updated_at')
        ))
        
        result = self.cursor.fetchone()
        return str(result['github_profile_id'])
    
    def _ingest_repository(self, repo_data: Dict, person_id: str, contribution_type: str = 'owner') -> Optional[str]:
        """Ingest a repository and create contribution record"""
        try:
            # Create or update repository
            self.cursor.execute("""
                INSERT INTO github_repository (
                    full_name, owner_username, repo_name, description, language,
                    stars, forks, created_at_github, updated_at_github, homepage_url, is_fork
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (full_name)
                DO UPDATE SET
                    stars = EXCLUDED.stars,
                    forks = EXCLUDED.forks,
                    updated_at_github = EXCLUDED.updated_at_github,
                    is_fork = EXCLUDED.is_fork
                RETURNING repo_id
            """, (
                repo_data.get('full_name'),
                repo_data.get('owner', {}).get('login'),
                repo_data.get('name'),
                repo_data.get('description'),
                repo_data.get('language'),
                repo_data.get('stargazers_count', 0),
                repo_data.get('forks_count', 0),
                repo_data.get('created_at'),
                repo_data.get('updated_at'),
                repo_data.get('homepage'),
                repo_data.get('fork', False)
            ))
            
            repo_id = self.cursor.fetchone()['repo_id']
            self.stats['repos_added'] += 1
            
            # Create contribution record
            self.cursor.execute("""
                SELECT github_profile_id FROM github_profile
                WHERE person_id = %s::uuid
                LIMIT 1
            """, (person_id,))
            
            github_profile = self.cursor.fetchone()
            if github_profile:
                self.cursor.execute("""
                    INSERT INTO github_contribution (
                        github_profile_id, repo_id, contribution_count
                    ) VALUES (
                        %s, %s, 1
                    )
                    ON CONFLICT (github_profile_id, repo_id)
                    DO UPDATE SET 
                        contribution_count = github_contribution.contribution_count + 1
                """, (github_profile['github_profile_id'], repo_id))
                
                self.stats['contributions_added'] += 1
            
            return str(repo_id)
            
        except Exception as e:
            logger.error(f"Error ingesting repository {repo_data.get('full_name')}: {str(e)}")
            return None
    
    def _ingest_org_repository(self, repo_data: Dict, org_name: str) -> Optional[str]:
        """Ingest organization repository"""
        return self._ingest_repository(repo_data, None)
    
    def _find_or_create_company(self, org_name: str) -> str:
        """Find existing company or create new one for GitHub organization"""
        # Try to find existing company
        self.cursor.execute("""
            SELECT company_id FROM company
            WHERE LOWER(company_name) = LOWER(%s)
            OR LOWER(github_org) = LOWER(%s)
            LIMIT 1
        """, (org_name, org_name))
        
        result = self.cursor.fetchone()
        if result:
            return str(result['company_id'])
        
        # Create new company
        company_id = str(uuid.uuid4())
        self.cursor.execute("""
            INSERT INTO company (company_id, company_name, github_org, source)
            VALUES (%s, %s, %s, 'github_ingestion')
            RETURNING company_id
        """, (company_id, org_name, org_name))
        
        return str(self.cursor.fetchone()['company_id'])
    
    def _fetch_user_starred_and_contributed_repos(self, username: str) -> List[Dict]:
        """
        Fetch repositories the user has contributed to (not just owned)
        Uses the user's events to find repos they've actually worked on
        """
        try:
            contributed_repos = {}
            
            # Fetch user's recent events (last 300 events, 3 pages)
            for page in range(1, 4):
                response = requests.get(
                    f'https://api.github.com/users/{username}/events',
                    headers=self.headers,
                    params={'per_page': 100, 'page': page},
                    timeout=10
                )
                response.raise_for_status()
                events = response.json()
                
                if not events:
                    break
                
                # Extract repos from events (PushEvent, PullRequestEvent, IssuesEvent, etc.)
                for event in events:
                    if event.get('repo'):
                        repo_name = event['repo']['name']
                        # Fetch full repo details
                        if repo_name not in contributed_repos:
                            try:
                                repo_response = requests.get(
                                    f'https://api.github.com/repos/{repo_name}',
                                    headers=self.headers,
                                    timeout=10
                                )
                                if repo_response.status_code == 200:
                                    contributed_repos[repo_name] = repo_response.json()
                            except:
                                continue
            
            logger.info(f"Found {len(contributed_repos)} contributed repos from events for {username}")
            return list(contributed_repos.values())
            
        except Exception as e:
            logger.error(f"Error fetching contributed repos for {username}: {str(e)}")
            return []
    
    def get_stats(self) -> Dict:
        """Get ingestion statistics"""
        return self.stats

