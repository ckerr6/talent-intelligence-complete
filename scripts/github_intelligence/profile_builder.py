#!/usr/bin/env python3
"""
ABOUTME: Builds comprehensive GitHub profiles by fetching all available data from GitHub API.
ABOUTME: Aggregates user data, repos, events, organizations, and activity patterns.
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from scripts.github_intelligence.github_client import GitHubClient


class ProfileBuilder:
    """
    Builds comprehensive GitHub profiles from API data.
    
    Fetches:
    - User profile (basic info)
    - All repositories
    - Recent events (activity)
    - Organizations
    - Language statistics
    - Contribution patterns
    """
    
    def __init__(self, github_client: Optional[GitHubClient] = None):
        """
        Initialize profile builder.
        
        Args:
            github_client: Configured GitHubClient instance
        """
        self.client = github_client or GitHubClient()
    
    def build_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Build comprehensive profile for a GitHub user.
        
        Args:
            username: GitHub username
        
        Returns:
            Dictionary with all extracted data or None if user not found
        """
        print(f"\n🔍 Building profile for @{username}...")
        
        # Fetch user profile
        user = self.client.get_user(username)
        if not user:
            print(f"   ❌ User not found: {username}")
            return None
        
        print(f"   ✅ Found: {user.get('name', username)}")
        
        # Build comprehensive profile
        profile = {
            'username': username,
            'fetched_at': datetime.now().isoformat(),
            'user': user,
            'repos': [],
            'events': [],
            'orgs': [],
            'language_stats': {},
            'activity_summary': {},
            'contribution_summary': {}
        }
        
        # Fetch repos
        print(f"   📦 Fetching repositories...")
        repos = self.client.get_user_repos(username)
        profile['repos'] = repos
        print(f"      Found {len(repos)} repos")
        
        # Fetch recent events
        print(f"   📊 Fetching recent activity...")
        events = self.client.get_user_events(username)
        profile['events'] = events
        print(f"      Found {len(events)} recent events")
        
        # Fetch organizations
        print(f"   🏢 Fetching organizations...")
        orgs = self.client.get_user_orgs(username)
        profile['orgs'] = orgs
        print(f"      Member of {len(orgs)} organizations")
        
        # Aggregate language statistics
        print(f"   💻 Analyzing languages...")
        profile['language_stats'] = self._aggregate_languages(repos)
        print(f"      {len(profile['language_stats'])} languages used")
        
        # Analyze activity patterns
        print(f"   ⚡ Analyzing activity patterns...")
        profile['activity_summary'] = self._analyze_activity(events)
        
        # Analyze contributions
        print(f"   📈 Analyzing contributions...")
        profile['contribution_summary'] = self._analyze_contributions(repos, user)
        
        print(f"   ✅ Profile complete for @{username}\n")
        
        return profile
    
    def _aggregate_languages(self, repos: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Aggregate language statistics across all repos.
        
        Args:
            repos: List of repository data
        
        Returns:
            Dictionary of {language: bytes_of_code}
        """
        language_totals = {}
        
        for repo in repos:
            if repo.get('fork', False):
                continue  # Skip forks
            
            owner = repo['owner']['login']
            repo_name = repo['name']
            
            # Fetch language stats for this repo
            languages = self.client.get_repo_languages(owner, repo_name)
            
            for lang, bytes_count in languages.items():
                language_totals[lang] = language_totals.get(lang, 0) + bytes_count
        
        # Sort by bytes
        return dict(sorted(language_totals.items(), key=lambda x: x[1], reverse=True))
    
    def _analyze_activity(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze activity patterns from recent events.
        
        Args:
            events: List of event data
        
        Returns:
            Summary of activity patterns
        """
        if not events:
            return {
                'total_events': 0,
                'event_types': {},
                'active_repos': [],
                'recent_activity': False
            }
        
        # Count event types
        event_types = {}
        active_repos = set()
        
        for event in events:
            event_type = event.get('type', 'Unknown')
            event_types[event_type] = event_types.get(event_type, 0) + 1
            
            if 'repo' in event:
                active_repos.add(event['repo']['name'])
        
        # Check if recently active (within last 7 days)
        most_recent_event = events[0] if events else None
        recent_activity = False
        
        if most_recent_event and 'created_at' in most_recent_event:
            event_time = datetime.fromisoformat(most_recent_event['created_at'].replace('Z', '+00:00'))
            days_ago = (datetime.now(event_time.tzinfo) - event_time).days
            recent_activity = days_ago <= 7
        
        return {
            'total_events': len(events),
            'event_types': event_types,
            'active_repos': list(active_repos),
            'active_repo_count': len(active_repos),
            'recent_activity': recent_activity,
            'most_common_event': max(event_types.items(), key=lambda x: x[1])[0] if event_types else None
        }
    
    def _analyze_contributions(self, repos: List[Dict[str, Any]], user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze contribution metrics.
        
        Args:
            repos: List of repository data
            user: User profile data
        
        Returns:
            Summary of contributions
        """
        owned_repos = [r for r in repos if not r.get('fork', False)]
        forked_repos = [r for r in repos if r.get('fork', False)]
        
        total_stars = sum(r.get('stargazers_count', 0) for r in owned_repos)
        total_forks = sum(r.get('forks_count', 0) for r in owned_repos)
        total_watchers = sum(r.get('watchers_count', 0) for r in owned_repos)
        
        # Find most popular repos
        popular_repos = sorted(
            owned_repos,
            key=lambda r: r.get('stargazers_count', 0),
            reverse=True
        )[:5]
        
        # Find recently updated repos
        recent_repos = sorted(
            repos,
            key=lambda r: r.get('updated_at', ''),
            reverse=True
        )[:5]
        
        return {
            'public_repos': user.get('public_repos', 0),
            'owned_repos': len(owned_repos),
            'forked_repos': len(forked_repos),
            'total_stars_earned': total_stars,
            'total_forks': total_forks,
            'total_watchers': total_watchers,
            'followers': user.get('followers', 0),
            'following': user.get('following', 0),
            'top_repos': [
                {
                    'name': r['name'],
                    'stars': r.get('stargazers_count', 0),
                    'forks': r.get('forks_count', 0),
                    'description': r.get('description', '')
                }
                for r in popular_repos
            ],
            'recently_active_repos': [
                {
                    'name': r['name'],
                    'updated_at': r.get('updated_at', ''),
                    'language': r.get('language', 'Unknown')
                }
                for r in recent_repos
            ]
        }
    
    def build_lightweight_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """
        Build lightweight profile (just user data, no deep dive).
        Useful for quickly checking many users.
        
        Args:
            username: GitHub username
        
        Returns:
            Basic profile data
        """
        user = self.client.get_user(username)
        if not user:
            return None
        
        return {
            'username': username,
            'name': user.get('name'),
            'email': user.get('email'),
            'company': user.get('company'),
            'location': user.get('location'),
            'bio': user.get('bio'),
            'blog': user.get('blog'),
            'twitter_username': user.get('twitter_username'),
            'public_repos': user.get('public_repos', 0),
            'followers': user.get('followers', 0),
            'following': user.get('following', 0),
            'created_at': user.get('created_at'),
            'updated_at': user.get('updated_at'),
            'fetched_at': datetime.now().isoformat()
        }


def main():
    """
    Test profile builder on sample users.
    """
    # Sample GitHub usernames to test
    test_users = [
        'vitalik',      # Vitalik Buterin (Ethereum)
        'haydenadams',  # Hayden Adams (Uniswap)
        'gakonst',      # Georgios Konstantopoulos (Paradigm)
    ]
    
    client = GitHubClient()
    builder = ProfileBuilder(client)
    
    for username in test_users:
        profile = builder.build_profile(username)
        
        if profile:
            print(f"✅ Profile built for @{username}")
            print(f"   Languages: {list(profile['language_stats'].keys())[:5]}")
            print(f"   Repos: {profile['contribution_summary']['public_repos']}")
            print(f"   Stars: {profile['contribution_summary']['total_stars_earned']}")
            print(f"   Organizations: {len(profile['orgs'])}")
        else:
            print(f"❌ Failed to build profile for @{username}")
    
    # Print rate limit status
    client.print_rate_limit_status()


if __name__ == '__main__':
    main()

