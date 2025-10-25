#!/usr/bin/env python3
"""
ABOUTME: Analyzes collaboration networks and relationships between developers.
ABOUTME: Identifies collaborators, tracks shared projects, and maps influence networks.
"""

import sys
import os
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.github_intelligence.github_client import GitHubClient


class NetworkAnalyzer:
    """
    Analyzes collaboration networks on GitHub.
    
    Analyzes:
    - Shared repository contributors
    - Organization memberships
    - Collaboration strength (number of shared projects)
    - Influence paths (who works with whom)
    - Key collaborators
    """
    
    def __init__(self, github_client: Optional[GitHubClient] = None):
        """
        Initialize network analyzer.
        
        Args:
            github_client: Configured GitHubClient instance
        """
        self.client = github_client or GitHubClient()
    
    def analyze_network(self, profile_data: Dict[str, Any], deep: bool = False) -> Dict[str, Any]:
        """
        Analyze collaboration network for a developer.
        
        Args:
            profile_data: Complete profile data from ProfileBuilder
            deep: If True, fetch additional data from GitHub API (slower but more complete)
        
        Returns:
            Dictionary with network analysis
        """
        username = profile_data.get('username')
        repos = profile_data.get('repos', [])
        orgs = profile_data.get('orgs', [])
        user = profile_data.get('user', {})
        
        print(f"🕸️  Analyzing network for @{username}...")
        
        # Find collaborators from contributed repos
        collaborators = self._find_collaborators(username, repos, deep=deep)
        
        # Calculate influence score
        influence_score = self._calculate_influence(user, repos, len(collaborators))
        
        # Identify key collaborators (top N by collaboration strength)
        top_collaborators = sorted(
            collaborators.values(),
            key=lambda x: x['collaboration_strength'],
            reverse=True
        )[:20]
        
        # Organization analysis
        org_info = self._analyze_organizations(orgs)
        
        print(f"   ✅ Found {len(collaborators)} collaborators")
        print(f"   ✅ Influence score: {influence_score}/100")
        
        return {
            'total_collaborators': len(collaborators),
            'top_collaborators': top_collaborators,
            'all_collaborators': collaborators,
            'organizations': org_info,
            'influence_score': influence_score,
            'network_size': len(collaborators) + len(orgs),
            'collaboration_summary': self._create_summary(collaborators, orgs)
        }
    
    def _find_collaborators(self, username: str, repos: List[Dict[str, Any]], 
                           deep: bool = False) -> Dict[str, Dict[str, Any]]:
        """
        Find collaborators by analyzing shared repositories.
        
        Args:
            username: GitHub username
            repos: User's repositories
            deep: If True, fetch contributors from GitHub API
        
        Returns:
            Dictionary of {collaborator_username: collaboration_data}
        """
        collaborators = {}
        
        # Focus on repos user has contributed to (not just owned)
        contributed_repos = [r for r in repos if not r.get('fork', False) or r.get('contributions', 0) > 0]
        
        # Limit to most significant repos to avoid excessive API calls
        significant_repos = sorted(
            contributed_repos,
            key=lambda r: (r.get('stargazers_count', 0), r.get('forks_count', 0)),
            reverse=True
        )[:10]  # Top 10 repos
        
        for repo in significant_repos:
            repo_name = repo['full_name']
            owner, name = repo_name.split('/')
            
            if deep:
                # Fetch contributors from API
                print(f"      Fetching contributors for {repo_name}...")
                contributors = self.client.get_repo_contributors(owner, name)
                
                for contributor in contributors[:30]:  # Top 30 contributors
                    contrib_username = contributor.get('login')
                    
                    if contrib_username == username:
                        continue  # Skip self
                    
                    if contrib_username not in collaborators:
                        collaborators[contrib_username] = {
                            'username': contrib_username,
                            'shared_repos': [],
                            'collaboration_strength': 0,
                            'avatar_url': contributor.get('avatar_url'),
                            'contributions': 0
                        }
                    
                    collaborators[contrib_username]['shared_repos'].append(repo_name)
                    collaborators[contrib_username]['collaboration_strength'] += 1
                    collaborators[contrib_username]['contributions'] += contributor.get('contributions', 0)
        
        return collaborators
    
    def _analyze_organizations(self, orgs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Analyze organization memberships.
        
        Args:
            orgs: List of organizations
        
        Returns:
            List of organization info
        """
        org_info = []
        
        for org in orgs:
            org_info.append({
                'name': org.get('login'),
                'description': org.get('description'),
                'avatar_url': org.get('avatar_url'),
                'url': org.get('html_url')
            })
        
        return org_info
    
    def _calculate_influence(self, user: Dict[str, Any], repos: List[Dict[str, Any]], 
                            collaborator_count: int) -> int:
        """
        Calculate influence score (0-100).
        
        Based on:
        - Followers
        - Stars earned
        - Collaborators
        - Repo impact
        """
        score = 0
        
        # Followers (max 30 points)
        followers = user.get('followers', 0)
        score += min(followers / 100, 30)
        
        # Stars earned (max 30 points)
        total_stars = sum(r.get('stargazers_count', 0) for r in repos if not r.get('fork', False))
        score += min(total_stars / 100, 30)
        
        # Network size (max 25 points)
        score += min(collaborator_count / 20, 25)
        
        # Popular repos (max 15 points)
        popular_repos = sum(1 for r in repos if r.get('stargazers_count', 0) > 100)
        score += min(popular_repos * 3, 15)
        
        return min(int(score), 100)
    
    def _create_summary(self, collaborators: Dict[str, Dict[str, Any]], 
                       orgs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create summary of collaboration network.
        """
        # Find most common collaboration patterns
        collaboration_counts = defaultdict(int)
        for collab in collaborators.values():
            collaboration_counts[collab['collaboration_strength']] += 1
        
        # Find most collaborated-with person
        if collaborators:
            top_collab = max(collaborators.values(), key=lambda x: x['collaboration_strength'])
            top_collaborator = {
                'username': top_collab['username'],
                'shared_repos': len(top_collab['shared_repos'])
            }
        else:
            top_collaborator = None
        
        return {
            'total_unique_collaborators': len(collaborators),
            'total_organizations': len(orgs),
            'top_collaborator': top_collaborator,
            'organization_names': [org['name'] for org in orgs]
        }
    
    def find_connection_path(self, from_username: str, to_username: str, 
                            max_depth: int = 3) -> Optional[List[str]]:
        """
        Find connection path between two developers (future feature).
        
        This would implement a breadth-first search through the collaboration graph.
        For now, returns None (not implemented).
        
        Args:
            from_username: Starting developer
            to_username: Target developer
            max_depth: Maximum path length
        
        Returns:
            List of usernames forming the path, or None if no path found
        """
        # TODO: Implement BFS through collaboration graph
        # This requires building a full graph of collaborations first
        return None
    
    def get_network_summary_text(self, network_data: Dict[str, Any]) -> str:
        """
        Generate human-readable network summary.
        
        Args:
            network_data: Output from analyze_network
        
        Returns:
            Text summary
        """
        collab_count = network_data['total_collaborators']
        influence = network_data['influence_score']
        orgs = network_data['organizations']
        summary_data = network_data['collaboration_summary']
        
        summary = f"Network of {collab_count} collaborators"
        
        if orgs:
            org_names = [org['name'] for org in orgs[:3]]
            summary += f", member of {len(orgs)} organizations ({', '.join(org_names)})"
        
        summary += f". Influence score: {influence}/100"
        
        if summary_data['top_collaborator']:
            top = summary_data['top_collaborator']
            summary += f". Most frequent collaborator: @{top['username']} ({top['shared_repos']} shared repos)"
        
        return summary


def main():
    """
    Test network analyzer with sample data.
    """
    # Sample profile data
    sample_profile = {
        'username': 'test_dev',
        'user': {
            'login': 'test_dev',
            'followers': 500,
            'following': 200
        },
        'repos': [
            {
                'full_name': 'test_dev/project1',
                'fork': False,
                'stargazers_count': 150,
                'forks_count': 20
            },
            {
                'full_name': 'some_org/big_project',
                'fork': False,
                'stargazers_count': 5000,
                'contributions': 50
            }
        ],
        'orgs': [
            {
                'login': 'some_company',
                'description': 'A great company',
                'html_url': 'https://github.com/some_company'
            }
        ]
    }
    
    analyzer = NetworkAnalyzer()
    result = analyzer.analyze_network(sample_profile, deep=False)
    
    print("\n🕸️  Network Analysis:")
    print(f"   Collaborators: {result['total_collaborators']}")
    print(f"   Organizations: {len(result['organizations'])}")
    print(f"   Influence Score: {result['influence_score']}/100")
    
    summary = analyzer.get_network_summary_text(result)
    print(f"\n   Summary: {summary}")


if __name__ == '__main__':
    main()

