#!/usr/bin/env python3
"""
ABOUTME: Assesses how reachable a developer is based on available contact information and activity signals.
ABOUTME: Scores reachability from 0-100 and suggests best contact methods.
"""

from typing import Dict, Any, List, Tuple
from datetime import datetime
import re


class ReachabilityAssessor:
    """
    Assesses how easy it is to reach a developer.
    
    Factors:
    - Contact information availability (email, Twitter, website)
    - Recent activity (responsive developers are active)
    - Bio signals (open to opportunities, hiring, etc.)
    - Engagement patterns (responds to issues/PRs)
    """
    
    def __init__(self):
        # Patterns indicating openness to contact
        self.OPEN_PATTERNS = [
            'hiring', 'available', 'looking for', 'open to',
            'dm me', 'contact me', 'reach out', 'get in touch',
            'consulting', 'freelance', 'open source'
        ]
        
        # Patterns indicating unavailability
        self.CLOSED_PATTERNS = [
            'not hiring', 'no dm', 'do not contact',
            'not available', 'busy', 'on sabbatical'
        ]
    
    def assess_reachability(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess reachability from profile data.
        
        Args:
            profile_data: Complete profile data from ProfileBuilder
        
        Returns:
            Dictionary with reachability score, signals, and best contact method
        """
        user = profile_data.get('user', {})
        events = profile_data.get('events', [])
        repos = profile_data.get('repos', [])
        
        # Calculate score from different signals
        contact_score = self._assess_contact_info(user)
        activity_score = self._assess_activity(events, user)
        bio_score = self._assess_bio_signals(user)
        engagement_score = self._assess_engagement(repos)
        
        total_score = min(
            contact_score + activity_score + bio_score + engagement_score,
            100
        )
        
        # Collect all signals
        signals = []
        
        # Contact information signals
        if user.get('email'):
            signals.append({'signal': 'Public email available', 'weight': 30})
        
        if user.get('twitter_username'):
            signals.append({'signal': 'Twitter account linked', 'weight': 20})
        
        if user.get('blog'):
            signals.append({'signal': 'Personal website', 'weight': 15})
        
        # Activity signals
        if len(events) > 10:
            signals.append({'signal': 'Very active on GitHub', 'weight': 20})
        elif len(events) > 5:
            signals.append({'signal': 'Active on GitHub', 'weight': 10})
        
        # Bio signals
        bio = (user.get('bio') or '').lower()
        for pattern in self.OPEN_PATTERNS:
            if pattern in bio:
                signals.append({'signal': f'Bio mentions: {pattern}', 'weight': 15})
                break
        
        # Determine best contact method
        best_method = self._determine_best_contact(user, total_score)
        
        # Generate outreach tips
        outreach_tips = self._generate_outreach_tips(user, events, repos)
        
        return {
            'reachability_score': int(total_score),
            'reachability_level': self._score_to_level(total_score),
            'signals': signals,
            'best_contact_method': best_method,
            'outreach_tips': outreach_tips,
            'contact_info': self._extract_contact_info(user)
        }
    
    def _assess_contact_info(self, user: Dict[str, Any]) -> float:
        """
        Score based on available contact information.
        
        Max: 50 points
        """
        score = 0
        
        # Public email (strongest signal)
        if user.get('email'):
            score += 30
        
        # Twitter (good for informal contact)
        if user.get('twitter_username'):
            score += 20
        
        # Personal website/blog
        if user.get('blog'):
            score += 15
        
        # Company (can find corporate email)
        if user.get('company'):
            score += 10
        
        return min(score, 50)
    
    def _assess_activity(self, events: List[Dict[str, Any]], user: Dict[str, Any]) -> float:
        """
        Score based on recent activity (active = responsive).
        
        Max: 25 points
        """
        score = 0
        
        # Recent events (active in last 90 days)
        if len(events) > 20:
            score += 20
        elif len(events) > 10:
            score += 15
        elif len(events) > 5:
            score += 10
        elif len(events) > 0:
            score += 5
        
        # Check recency of most recent event
        if events:
            try:
                most_recent = events[0]
                event_time = datetime.fromisoformat(most_recent['created_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now(event_time.tzinfo) - event_time).days
                
                if days_ago <= 7:
                    score += 5
                elif days_ago <= 30:
                    score += 3
            except:
                pass
        
        return min(score, 25)
    
    def _assess_bio_signals(self, user: Dict[str, Any]) -> float:
        """
        Score based on bio content.
        
        Max: 20 points
        """
        bio = (user.get('bio') or '').lower()
        if not bio:
            return 0
        
        score = 0
        
        # Check for openness signals
        for pattern in self.OPEN_PATTERNS:
            if pattern in bio:
                score += 15
                break
        
        # Check for closed signals (negative)
        for pattern in self.CLOSED_PATTERNS:
            if pattern in bio:
                score -= 10
                break
        
        # Has bio at all (shows engagement with profile)
        score += 5
        
        return max(min(score, 20), 0)
    
    def _assess_engagement(self, repos: List[Dict[str, Any]]) -> float:
        """
        Score based on engagement with community.
        
        Max: 15 points
        """
        score = 0
        
        # Has repos with issues enabled (open to community)
        repos_with_issues = sum(1 for r in repos if r.get('has_issues', False))
        if repos_with_issues > 0:
            score += 5
        
        # Has repos with discussions (very engaged)
        repos_with_discussions = sum(1 for r in repos if r.get('has_discussions', False))
        if repos_with_discussions > 0:
            score += 5
        
        # Significant repos (worth reaching out about)
        significant_repos = sum(1 for r in repos if r.get('stargazers_count', 0) > 10)
        if significant_repos > 0:
            score += 5
        
        return min(score, 15)
    
    def _determine_best_contact(self, user: Dict[str, Any], score: float) -> str:
        """
        Determine best method to contact this person.
        """
        if user.get('email'):
            return 'Email'
        elif user.get('twitter_username'):
            return 'Twitter DM'
        elif user.get('blog'):
            website = user['blog']
            if 'linkedin' in website.lower():
                return 'LinkedIn'
            else:
                return 'Website Contact Form'
        elif score > 40:
            return 'GitHub Issue/Discussion'
        else:
            return 'Research Further'
    
    def _extract_contact_info(self, user: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract all available contact information.
        """
        contact = {}
        
        if user.get('email'):
            contact['email'] = user['email']
        
        if user.get('twitter_username'):
            contact['twitter'] = f"@{user['twitter_username']}"
            contact['twitter_url'] = f"https://twitter.com/{user['twitter_username']}"
        
        if user.get('blog'):
            contact['website'] = user['blog']
        
        if user.get('company'):
            contact['company'] = user['company']
        
        contact['github_url'] = user.get('html_url', '')
        
        return contact
    
    def _generate_outreach_tips(self, user: Dict[str, Any], events: List[Dict[str, Any]], 
                                 repos: List[Dict[str, Any]]) -> List[str]:
        """
        Generate tips for effective outreach.
        """
        tips = []
        
        # Activity-based tips
        if len(events) > 10:
            tips.append("Very active on GitHub - likely to see and respond to messages")
        else:
            tips.append("Low recent activity - may need multiple follow-ups")
        
        # Contact method tips
        if user.get('email'):
            tips.append("Direct email is available - use for professional outreach")
        elif user.get('twitter_username'):
            tips.append("Try Twitter DM for more casual initial contact")
        
        # Project-based tips
        if repos:
            top_repo = max(repos, key=lambda r: r.get('stargazers_count', 0))
            if top_repo.get('stargazers_count', 0) > 50:
                tips.append(f"Reference their work on '{top_repo['name']}' - it has {top_repo['stargazers_count']} stars")
        
        # Timing tips
        if events:
            try:
                most_recent = events[0]
                event_time = datetime.fromisoformat(most_recent['created_at'].replace('Z', '+00:00'))
                days_ago = (datetime.now(event_time.tzinfo) - event_time).days
                
                if days_ago <= 7:
                    tips.append("Active in the last week - good time to reach out")
                elif days_ago > 90:
                    tips.append("No recent activity - may be on break or busy with offline work")
            except:
                pass
        
        return tips
    
    def _score_to_level(self, score: float) -> str:
        """
        Convert score to reachability level.
        """
        if score >= 80:
            return 'Very High'
        elif score >= 60:
            return 'High'
        elif score >= 40:
            return 'Medium'
        elif score >= 20:
            return 'Low'
        else:
            return 'Very Low'


def main():
    """
    Test reachability assessor with sample data.
    """
    # Sample profile data - high reachability
    sample_profile_high = {
        'user': {
            'login': 'active_dev',
            'email': 'dev@example.com',
            'twitter_username': 'active_dev',
            'blog': 'https://activedev.io',
            'bio': 'Open source developer. Always open to interesting projects. DM me!',
            'html_url': 'https://github.com/active_dev'
        },
        'events': [{'type': 'PushEvent', 'created_at': '2025-10-24T12:00:00Z'} for _ in range(25)],
        'repos': [
            {'name': 'cool-project', 'stargazers_count': 100, 'has_issues': True},
            {'name': 'another-project', 'stargazers_count': 50, 'has_discussions': True}
        ]
    }
    
    assessor = ReachabilityAssessor()
    result = assessor.assess_reachability(sample_profile_high)
    
    print("📞 Reachability Assessment:")
    print(f"   Score: {result['reachability_score']}/100 ({result['reachability_level']})")
    print(f"   Best Contact Method: {result['best_contact_method']}")
    print(f"\n   Signals:")
    for signal in result['signals']:
        print(f"      • {signal['signal']} ({signal['weight']} points)")
    print(f"\n   Outreach Tips:")
    for tip in result['outreach_tips']:
        print(f"      • {tip}")


if __name__ == '__main__':
    main()


