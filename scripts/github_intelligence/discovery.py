#!/usr/bin/env python3
"""
ABOUTME: Discovers new GitHub developers via organizations and repository contributors.
ABOUTME: Focuses on high-value targets like crypto/DeFi/AI companies and projects.
"""

import sys
import os
from typing import List, Dict, Any, Set, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.github_intelligence.github_client import GitHubClient
from config import get_db_context


class DeveloperDiscovery:
    """
    Discovers GitHub developers to enrich.
    
    Discovery sources:
    - GitHub organization members
    - Repository contributors (especially popular repos)
    - Collaborators of known high-value developers
    """
    
    # High-value organizations to target
    TARGET_ORGANIZATIONS = [
        # Crypto/DeFi
        'Uniswap', 'aave', 'compound-finance', 'MakerDAO', 'curvefi',
        'coinbase', 'ConsenSys', 'ethereum', 'OpenZeppelin',
        'paradigmxyz', 'a16z-crypto',
        
        # Layer 2
        'OffchainLabs', 'ethereum-optimism', 'matter-labs', 'starkware-libs',
        
        # AI/ML
        'openai', 'anthropics', 'huggingface', 'facebookresearch', 'google-research',
        
        # Notable tech companies
        'vercel', 'netlify', 'supabase', 'stripe', 'github',
    ]
    
    # High-value repositories to mine for contributors
    TARGET_REPOS = [
        'ethereum/go-ethereum',
        'foundry-rs/foundry',
        'paradigmxyz/reth',
        'OpenZeppelin/openzeppelin-contracts',
        'Uniswap/v4-core',
        'aave/aave-v3-core',
    ]
    
    def __init__(self, github_client: Optional[GitHubClient] = None):
        """
        Initialize discovery system.
        
        Args:
            github_client: Configured GitHubClient instance
        """
        self.client = github_client or GitHubClient()
    
    def discover_from_organization(self, org_name: str, limit: Optional[int] = None) -> List[str]:
        """
        Discover developers from a GitHub organization.
        
        Args:
            org_name: GitHub organization name
            limit: Maximum number of members to return
        
        Returns:
            List of GitHub usernames
        """
        print(f"\n🔍 Discovering developers from @{org_name}...")
        
        members = self.client.get_org_members(org_name)
        
        if not members:
            print(f"   ⚠️  No members found for {org_name}")
            return []
        
        usernames = [member['login'] for member in members]
        
        if limit:
            usernames = usernames[:limit]
        
        print(f"   ✅ Found {len(usernames)} developers")
        
        return usernames
    
    def discover_from_repository(self, repo_full_name: str, limit: Optional[int] = None) -> List[str]:
        """
        Discover developers from repository contributors.
        
        Args:
            repo_full_name: Repository name (owner/repo format)
            limit: Maximum number of contributors to return
        
        Returns:
            List of GitHub usernames
        """
        print(f"\n🔍 Discovering contributors to {repo_full_name}...")
        
        owner, repo = repo_full_name.split('/')
        contributors = self.client.get_repo_contributors(owner, repo)
        
        if not contributors:
            print(f"   ⚠️  No contributors found for {repo_full_name}")
            return []
        
        usernames = [contrib['login'] for contrib in contributors]
        
        if limit:
            usernames = usernames[:limit]
        
        print(f"   ✅ Found {len(usernames)} contributors")
        
        return usernames
    
    def discover_batch(self, organizations: List[str], repositories: List[str] = None,
                      limit_per_source: int = 50) -> List[str]:
        """
        Discover developers from multiple organizations and repositories.
        
        Args:
            organizations: List of organization names
            repositories: List of repository full names (owner/repo)
            limit_per_source: Maximum developers to discover per source
        
        Returns:
            Unique list of discovered usernames
        """
        discovered = set()
        
        # Discover from organizations
        for org in organizations:
            try:
                members = self.discover_from_organization(org, limit=limit_per_source)
                discovered.update(members)
            except Exception as e:
                print(f"   ❌ Error discovering from {org}: {e}")
        
        # Discover from repositories
        if repositories:
            for repo in repositories:
                try:
                    contributors = self.discover_from_repository(repo, limit=limit_per_source)
                    discovered.update(contributors)
                except Exception as e:
                    print(f"   ❌ Error discovering from {repo}: {e}")
        
        discovered_list = list(discovered)
        print(f"\n✨ Total unique developers discovered: {len(discovered_list)}")
        
        return discovered_list
    
    def discover_high_value_targets(self, limit_per_org: int = 30) -> List[str]:
        """
        Discover developers from curated high-value organizations.
        
        Args:
            limit_per_org: Maximum developers per organization
        
        Returns:
            List of discovered usernames
        """
        print("=" * 60)
        print("🎯 Discovering High-Value Crypto/DeFi/AI Developers")
        print("=" * 60)
        
        return self.discover_batch(
            organizations=self.TARGET_ORGANIZATIONS[:10],  # Start with top 10
            repositories=self.TARGET_REPOS[:5],  # And top 5 repos
            limit_per_source=limit_per_org
        )
    
    def filter_already_enriched(self, usernames: List[str]) -> List[str]:
        """
        Filter out developers we've already enriched.
        
        Args:
            usernames: List of GitHub usernames
        
        Returns:
            List of usernames not yet in github_intelligence table
        """
        if not usernames:
            return []
        
        print(f"\n🔍 Checking which developers need enrichment...")
        
        with get_db_context() as conn:
            cursor = conn.cursor()
            
            # Check which usernames exist in github_profile
            placeholders = ','.join(['%s'] * len(usernames))
            cursor.execute(f"""
                SELECT gp.github_username
                FROM github_profile gp
                WHERE gp.github_username = ANY(%s)
            """, (usernames,))
            
            existing_profiles = {row[0] for row in cursor.fetchall()}
            
            # Check which have intelligence data
            cursor.execute(f"""
                SELECT gp.github_username
                FROM github_profile gp
                INNER JOIN github_intelligence gi ON gp.github_profile_id = gi.github_profile_id
                WHERE gp.github_username = ANY(%s)
            """, (usernames,))
            
            enriched_profiles = {row[0] for row in cursor.fetchall()}
        
        # Return usernames that don't have intelligence data yet
        not_enriched = [u for u in usernames if u not in enriched_profiles]
        
        print(f"   {len(existing_profiles)} already in database")
        print(f"   {len(enriched_profiles)} already enriched")
        print(f"   ✅ {len(not_enriched)} need enrichment")
        
        return not_enriched
    
    def prioritize_targets(self, usernames: List[str]) -> List[Dict[str, Any]]:
        """
        Prioritize discovered developers by estimated value.
        
        Args:
            usernames: List of GitHub usernames
        
        Returns:
            List of {username, priority_score} sorted by priority
        """
        print(f"\n📊 Prioritizing {len(usernames)} discovered developers...")
        
        prioritized = []
        
        for username in usernames[:100]:  # Limit API calls
            # Fetch lightweight profile
            user = self.client.get_user(username)
            
            if not user:
                continue
            
            # Calculate priority score
            priority = self._calculate_priority(user)
            
            prioritized.append({
                'username': username,
                'priority_score': priority,
                'followers': user.get('followers', 0),
                'public_repos': user.get('public_repos', 0),
                'company': user.get('company', '')
            })
        
        # Sort by priority
        prioritized.sort(key=lambda x: x['priority_score'], reverse=True)
        
        print(f"   ✅ Prioritized {len(prioritized)} developers")
        
        return prioritized
    
    def _calculate_priority(self, user: Dict[str, Any]) -> int:
        """
        Calculate priority score for a developer.
        
        Higher score = higher priority to enrich.
        
        Based on:
        - Followers (community recognition)
        - Public repos (activity level)
        - Has company (currently employed)
        - Bio present (engaged with profile)
        """
        score = 0
        
        # Followers
        followers = user.get('followers', 0)
        score += min(followers // 10, 50)  # Max 50 points
        
        # Public repos
        repos = user.get('public_repos', 0)
        score += min(repos // 2, 30)  # Max 30 points
        
        # Has company
        if user.get('company'):
            score += 10
        
        # Has bio
        if user.get('bio'):
            score += 5
        
        # Has email (very valuable)
        if user.get('email'):
            score += 10
        
        return score


def main():
    """
    Test discovery system.
    """
    client = GitHubClient()
    discovery = DeveloperDiscovery(client)
    
    # Test 1: Discover from single organization
    print("\n" + "="*60)
    print("TEST 1: Discover from Uniswap")
    print("="*60)
    uniswap_devs = discovery.discover_from_organization('Uniswap', limit=10)
    print(f"Sample: {uniswap_devs[:5]}")
    
    # Test 2: Discover high-value targets
    print("\n" + "="*60)
    print("TEST 2: Discover high-value targets")
    print("="*60)
    # Uncomment to test full discovery:
    # high_value = discovery.discover_high_value_targets(limit_per_org=10)
    # print(f"Total discovered: {len(high_value)}")
    
    # Test 3: Filter already enriched
    print("\n" + "="*60)
    print("TEST 3: Filter already enriched")
    print("="*60)
    not_enriched = discovery.filter_already_enriched(uniswap_devs)
    print(f"Need enrichment: {len(not_enriched)}")
    
    client.print_rate_limit_status()


if __name__ == '__main__':
    main()

