#!/usr/bin/env python3
"""
ABOUTME: Infers developer seniority from GitHub activity patterns and behavior.
ABOUTME: Analyzes years active, output volume, leadership signals, and influence metrics.
"""

from typing import Dict, Any, Tuple, List
from datetime import datetime


class SeniorityScorer:
    """
    Infers seniority level from GitHub behavior patterns.
    
    Scoring factors:
    - Years active (account age + activity span)
    - Output volume (commits, PRs, repos)
    - Leadership signals (PR reviews, maintainer status, org memberships)
    - Influence (stars earned, followers, community engagement)
    - Project complexity (technical depth of contributions)
    """
    
    # Seniority thresholds
    THRESHOLDS = {
        'Junior': 0,
        'Mid-Level': 30,
        'Senior': 60,
        'Staff': 90,
        'Principal': 120
    }
    
    def __init__(self):
        pass
    
    def calculate_seniority(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate seniority level from profile data.
        
        Args:
            profile_data: Complete profile data from ProfileBuilder
        
        Returns:
            Dictionary with seniority level, score, and breakdown
        """
        user = profile_data.get('user', {})
        repos = profile_data.get('repos', [])
        events = profile_data.get('events', [])
        orgs = profile_data.get('orgs', [])
        contribution_summary = profile_data.get('contribution_summary', {})
        
        # Calculate individual scores
        experience_score = self._calculate_experience_score(user)
        output_score = self._calculate_output_score(contribution_summary, repos)
        leadership_score = self._calculate_leadership_score(repos, orgs, user)
        influence_score = self._calculate_influence_score(user, contribution_summary)
        complexity_score = self._calculate_complexity_score(repos)
        
        # Total score
        total_score = (
            experience_score +
            output_score +
            leadership_score +
            influence_score +
            complexity_score
        )
        
        # Determine seniority level
        seniority_level = self._score_to_seniority(total_score)
        
        # Calculate confidence
        confidence = self._calculate_confidence(user, repos, events)
        
        return {
            'seniority_level': seniority_level,
            'total_score': round(total_score, 1),
            'confidence': round(confidence, 2),
            'breakdown': {
                'experience': round(experience_score, 1),
                'output': round(output_score, 1),
                'leadership': round(leadership_score, 1),
                'influence': round(influence_score, 1),
                'complexity': round(complexity_score, 1)
            }
        }
    
    def _calculate_experience_score(self, user: Dict[str, Any]) -> float:
        """
        Calculate score based on years of experience.
        
        Max: 50 points
        """
        created_at = user.get('created_at')
        if not created_at:
            return 0
        
        try:
            account_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            years_active = (datetime.now(account_created.tzinfo) - account_created).days / 365.25
            
            # 10 points per year, max 50
            score = min(years_active * 10, 50)
            return score
        except:
            return 0
    
    def _calculate_output_score(self, contribution_summary: Dict[str, Any], repos: List[Dict[str, Any]]) -> float:
        """
        Calculate score based on output volume.
        
        Max: 25 points
        """
        score = 0
        
        # Owned repos (not forks)
        owned_repos = contribution_summary.get('owned_repos', 0)
        score += min(owned_repos * 2, 15)  # Max 15 points
        
        # Activity consistency (repos with recent updates)
        recent_count = 0
        cutoff = datetime.now()
        for repo in repos[:20]:  # Check top 20 recent
            try:
                updated_at = datetime.fromisoformat(repo.get('updated_at', '').replace('Z', '+00:00'))
                if (cutoff - updated_at).days <= 180:  # Active in last 6 months
                    recent_count += 1
            except:
                pass
        
        score += min(recent_count * 0.5, 10)  # Max 10 points
        
        return score
    
    def _calculate_leadership_score(self, repos: List[Dict[str, Any]], orgs: List[Dict[str, Any]], 
                                     user: Dict[str, Any]) -> float:
        """
        Calculate score based on leadership signals.
        
        Max: 35 points
        """
        score = 0
        
        # Organization memberships (working at real companies)
        org_count = len(orgs)
        score += min(org_count * 5, 20)  # Max 20 points
        
        # Maintained repos (owned, non-fork, with activity)
        maintained_count = 0
        for repo in repos:
            if not repo.get('fork', False):
                # Check if they're the owner
                if repo.get('owner', {}).get('login') == user.get('login'):
                    maintained_count += 1
        
        score += min(maintained_count * 1.5, 15)  # Max 15 points
        
        return score
    
    def _calculate_influence_score(self, user: Dict[str, Any], contribution_summary: Dict[str, Any]) -> float:
        """
        Calculate score based on community influence.
        
        Max: 30 points
        """
        score = 0
        
        # Stars earned (community recognition)
        stars = contribution_summary.get('total_stars_earned', 0)
        score += min(stars / 100, 15)  # Max 15 points
        
        # Followers (network size)
        followers = user.get('followers', 0)
        score += min(followers / 100, 10)  # Max 10 points
        
        # Follower to following ratio (influence vs seeking)
        following = user.get('following', 0)
        if following > 0:
            ratio = followers / following
            if ratio > 2:  # More followers than following
                score += min(ratio, 5)  # Max 5 points
        
        return score
    
    def _calculate_complexity_score(self, repos: List[Dict[str, Any]]) -> float:
        """
        Calculate score based on technical complexity.
        
        Max: 15 points
        """
        score = 0
        
        # Count repos with significant complexity indicators
        complex_repos = 0
        
        for repo in repos[:30]:  # Check top 30 repos
            if repo.get('fork', False):
                continue
            
            # Multiple indicators of complexity
            indicators = 0
            
            # Size (larger repos are generally more complex)
            if repo.get('size', 0) > 1000:  # >1MB
                indicators += 1
            
            # Has collaborators (complex enough for team)
            if repo.get('forks_count', 0) > 0:
                indicators += 1
            
            # Has documentation
            if repo.get('has_wiki', False) or repo.get('has_pages', False):
                indicators += 1
            
            # Multiple languages (polyglot projects)
            # This would require additional API calls, skip for now
            
            if indicators >= 2:
                complex_repos += 1
        
        score = min(complex_repos * 1.5, 15)  # Max 15 points
        
        return score
    
    def _score_to_seniority(self, score: float) -> str:
        """
        Convert numerical score to seniority level.
        """
        if score >= self.THRESHOLDS['Principal']:
            return 'Principal'
        elif score >= self.THRESHOLDS['Staff']:
            return 'Staff'
        elif score >= self.THRESHOLDS['Senior']:
            return 'Senior'
        elif score >= self.THRESHOLDS['Mid-Level']:
            return 'Mid-Level'
        else:
            return 'Junior'
    
    def _calculate_confidence(self, user: Dict[str, Any], repos: List[Dict[str, Any]], 
                              events: List[Dict[str, Any]]) -> float:
        """
        Calculate confidence in seniority assessment.
        
        Returns:
            Float between 0 and 1
        """
        confidence = 0.5  # Base confidence
        
        # More data = higher confidence
        
        # Has sufficient repos
        if len(repos) >= 10:
            confidence += 0.1
        
        # Has recent activity
        if len(events) > 0:
            confidence += 0.1
        
        # Account age (older = more reliable)
        created_at = user.get('created_at')
        if created_at:
            try:
                account_created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                years = (datetime.now(account_created.tzinfo) - account_created).days / 365.25
                if years >= 2:
                    confidence += 0.1
                if years >= 5:
                    confidence += 0.1
            except:
                pass
        
        # Has profile info (bio, company, location)
        if user.get('bio'):
            confidence += 0.05
        if user.get('company'):
            confidence += 0.05
        
        return min(confidence, 1.0)
    
    def get_seniority_explanation(self, seniority_data: Dict[str, Any]) -> str:
        """
        Generate human-readable explanation of seniority assessment.
        
        Args:
            seniority_data: Output from calculate_seniority
        
        Returns:
            Explanation string
        """
        level = seniority_data['seniority_level']
        score = seniority_data['total_score']
        breakdown = seniority_data['breakdown']
        confidence = seniority_data['confidence']
        
        # Find strongest factor
        strongest = max(breakdown.items(), key=lambda x: x[1])
        
        explanation = f"Assessed as {level} (score: {score:.0f}, confidence: {confidence:.0%}). "
        explanation += f"Strongest signal: {strongest[0]} ({strongest[1]:.0f} points)."
        
        return explanation


def main():
    """
    Test seniority scorer with sample data.
    """
    # Sample profile data
    sample_profile = {
        'user': {
            'login': 'test_user',
            'created_at': '2018-01-15T00:00:00Z',
            'followers': 500,
            'following': 100,
            'public_repos': 45
        },
        'repos': [{'name': f'repo{i}', 'fork': False, 'size': 1500, 'forks_count': 5} for i in range(20)],
        'events': [{'type': 'PushEvent'} for _ in range(50)],
        'orgs': [{'login': 'company1'}, {'login': 'company2'}],
        'contribution_summary': {
            'owned_repos': 15,
            'total_stars_earned': 1200,
            'followers': 500
        }
    }
    
    scorer = SeniorityScorer()
    result = scorer.calculate_seniority(sample_profile)
    
    print("📊 Seniority Assessment:")
    print(f"   Level: {result['seniority_level']}")
    print(f"   Score: {result['total_score']}")
    print(f"   Confidence: {result['confidence']:.0%}")
    print(f"\n   Breakdown:")
    for factor, score in result['breakdown'].items():
        print(f"      {factor.title()}: {score}")
    
    explanation = scorer.get_seniority_explanation(result)
    print(f"\n   {explanation}")


if __name__ == '__main__':
    main()


