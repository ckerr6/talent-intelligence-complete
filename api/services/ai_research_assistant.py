"""
AI Research Assistant Service

Monitors the talent database for:
- New profiles matching user search patterns
- Network changes (job changes, new connections)
- GitHub activity on watched repos
- Rising talent identification
- Pattern detection for better matching
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_
import json

from ..models.database import Person, Employment, GitHubProfile, GitHubContribution
from .ai_pattern_learning import PatternLearningService


class AIResearchAssistant:
    """
    Background intelligence service that monitors and discovers talent.
    Runs as scheduled job to find matches and notify users.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.pattern_service = PatternLearningService(db)
    
    # ========================================
    # MONITORING & DISCOVERY
    # ========================================
    
    def discover_new_matches(
        self,
        user_id: str,
        search_patterns: List[Dict[str, Any]],
        since_hours: int = 24
    ) -> List[Dict[str, Any]]:
        """
        Monitor for new profiles that match user's search patterns.
        
        Args:
            user_id: User to monitor for
            search_patterns: List of saved search criteria
            since_hours: Look for changes in last N hours
        
        Returns:
            List of new matches with relevance scores
        """
        since_time = datetime.utcnow() - timedelta(hours=since_hours)
        new_matches = []
        
        for pattern in search_patterns:
            # Build query based on pattern
            query = self.db.query(Person)
            
            # Filter by company if specified
            if pattern.get('companies'):
                query = query.join(Employment).filter(
                    Employment.company_name.in_(pattern['companies']),
                    Employment.is_current == True
                )
            
            # Filter by location
            if pattern.get('locations'):
                location_filters = [
                    Person.location.ilike(f"%{loc}%") 
                    for loc in pattern['locations']
                ]
                query = query.filter(or_(*location_filters))
            
            # Filter by skills (headline search)
            if pattern.get('skills'):
                skill_filters = [
                    Person.headline.ilike(f"%{skill}%") 
                    for skill in pattern['skills']
                ]
                query = query.filter(or_(*skill_filters))
            
            # Filter by email/GitHub availability
            if pattern.get('has_email'):
                query = query.filter(Person.has_email == True)
            
            if pattern.get('has_github'):
                query = query.filter(Person.has_github == True)
            
            # Only new/updated profiles
            query = query.filter(Person.updated_at >= since_time)
            
            # Execute and score
            candidates = query.limit(50).all()
            
            for person in candidates:
                match_score = self._calculate_pattern_match_score(person, pattern)
                
                if match_score >= 60:  # Minimum threshold
                    new_matches.append({
                        'person_id': person.person_id,
                        'person_name': person.full_name,
                        'headline': person.headline,
                        'location': person.location,
                        'match_score': match_score,
                        'pattern_name': pattern.get('name', 'Unnamed Search'),
                        'reason': self._explain_match(person, pattern),
                        'discovered_at': datetime.utcnow().isoformat()
                    })
        
        return sorted(new_matches, key=lambda x: x['match_score'], reverse=True)
    
    def monitor_job_changes(
        self,
        watched_people: List[str],
        since_hours: int = 168  # 1 week
    ) -> List[Dict[str, Any]]:
        """
        Detect job changes for watched candidates.
        
        Args:
            watched_people: List of person_ids to monitor
            since_hours: Look back window
        
        Returns:
            List of job change events
        """
        since_time = datetime.utcnow() - timedelta(hours=since_hours)
        job_changes = []
        
        for person_id in watched_people:
            person = self.db.query(Person).filter(
                Person.person_id == person_id
            ).first()
            
            if not person:
                continue
            
            # Check for recent employment updates
            recent_employment = self.db.query(Employment).filter(
                Employment.person_id == person_id,
                Employment.updated_at >= since_time,
                Employment.is_current == True
            ).all()
            
            if recent_employment:
                for emp in recent_employment:
                    job_changes.append({
                        'person_id': person_id,
                        'person_name': person.full_name,
                        'event_type': 'job_change',
                        'new_company': emp.company_name,
                        'new_title': emp.title,
                        'detected_at': datetime.utcnow().isoformat(),
                        'relevance': 'high',
                        'action_suggestion': 'Reach out to congratulate on new role'
                    })
        
        return job_changes
    
    def monitor_github_activity(
        self,
        watched_repos: List[str],
        since_hours: int = 168
    ) -> List[Dict[str, Any]]:
        """
        Monitor GitHub activity on specific repos.
        
        Args:
            watched_repos: List of repo names to monitor
            since_hours: Look back window
        
        Returns:
            List of significant GitHub events
        """
        since_time = datetime.utcnow() - timedelta(hours=since_hours)
        activities = []
        
        for repo in watched_repos:
            # Find new contributors to watched repo
            contributions = self.db.query(GitHubContribution).join(
                Person,
                GitHubContribution.person_id == Person.person_id
            ).filter(
                GitHubContribution.repo_name == repo,
                GitHubContribution.updated_at >= since_time,
                GitHubContribution.merged_pr_count > 0
            ).order_by(desc(GitHubContribution.merged_pr_count)).limit(10).all()
            
            for contrib in contributions:
                person = self.db.query(Person).filter(
                    Person.person_id == contrib.person_id
                ).first()
                
                if person:
                    activities.append({
                        'person_id': person.person_id,
                        'person_name': person.full_name,
                        'event_type': 'github_activity',
                        'repo_name': repo,
                        'merged_prs': contrib.merged_pr_count,
                        'stars': contrib.stars,
                        'detected_at': datetime.utcnow().isoformat(),
                        'relevance': 'high' if contrib.merged_pr_count >= 5 else 'medium',
                        'action_suggestion': f'Review contributions to {repo}'
                    })
        
        return activities
    
    def identify_rising_talent(
        self,
        min_github_growth: int = 10,
        since_days: int = 90
    ) -> List[Dict[str, Any]]:
        """
        Identify engineers with rapid GitHub growth.
        
        Args:
            min_github_growth: Minimum PR increase
            since_days: Time window
        
        Returns:
            List of rising talent profiles
        """
        since_time = datetime.utcnow() - timedelta(days=since_days)
        rising_talent = []
        
        # Find profiles with significant recent GitHub activity
        active_profiles = self.db.query(
            Person.person_id,
            Person.full_name,
            Person.headline,
            Person.location,
            GitHubProfile.total_merged_prs,
            GitHubProfile.total_stars_earned,
            func.count(GitHubContribution.contribution_id).label('recent_contributions')
        ).join(
            GitHubProfile,
            Person.person_id == GitHubProfile.person_id
        ).join(
            GitHubContribution,
            Person.person_id == GitHubContribution.person_id
        ).filter(
            GitHubContribution.updated_at >= since_time,
            GitHubProfile.total_merged_prs >= min_github_growth
        ).group_by(
            Person.person_id,
            Person.full_name,
            Person.headline,
            Person.location,
            GitHubProfile.total_merged_prs,
            GitHubProfile.total_stars_earned
        ).having(
            func.count(GitHubContribution.contribution_id) >= 3
        ).order_by(
            desc('recent_contributions')
        ).limit(20).all()
        
        for profile in active_profiles:
            rising_talent.append({
                'person_id': profile.person_id,
                'person_name': profile.full_name,
                'headline': profile.headline,
                'location': profile.location,
                'total_prs': profile.total_merged_prs,
                'total_stars': profile.total_stars_earned,
                'recent_contributions': profile.recent_contributions,
                'growth_indicator': 'high',
                'detected_at': datetime.utcnow().isoformat(),
                'reason': f'{profile.recent_contributions} contributions in last {since_days} days',
                'action_suggestion': 'Review profile and consider reaching out'
            })
        
        return rising_talent
    
    # ========================================
    # NETWORK INTELLIGENCE
    # ========================================
    
    def detect_network_opportunities(
        self,
        user_network: List[str],
        target_person_id: str
    ) -> Dict[str, Any]:
        """
        Analyze network paths to a target candidate.
        
        Args:
            user_network: List of person_ids in user's network
            target_person_id: Target candidate
        
        Returns:
            Network intelligence with intro opportunities
        """
        # This would integrate with your network graph
        # For now, return structure
        return {
            'target_person_id': target_person_id,
            'mutual_connections': [],  # Would query network graph
            'degrees_of_separation': None,
            'strongest_path': [],
            'intro_opportunity': {
                'available': False,
                'confidence': 0,
                'recommended_connector': None,
                'reasoning': ''
            }
        }
    
    # ========================================
    # SCORING & ANALYSIS
    # ========================================
    
    def _calculate_pattern_match_score(
        self,
        person: Person,
        pattern: Dict[str, Any]
    ) -> float:
        """Calculate how well a person matches a search pattern."""
        score = 0
        max_score = 100
        
        # Email availability (30 points)
        if pattern.get('has_email') and person.has_email:
            score += 30
        
        # GitHub availability (20 points)
        if pattern.get('has_github') and person.has_github:
            score += 20
        
        # Company match (20 points)
        if pattern.get('companies'):
            # Would check current employment
            score += 10  # Partial match
        
        # Location match (15 points)
        if pattern.get('locations') and person.location:
            for loc in pattern['locations']:
                if loc.lower() in person.location.lower():
                    score += 15
                    break
        
        # Skill match (15 points)
        if pattern.get('skills') and person.headline:
            matched_skills = sum(
                1 for skill in pattern['skills']
                if skill.lower() in person.headline.lower()
            )
            score += min(15, matched_skills * 5)
        
        return min(score, max_score)
    
    def _explain_match(
        self,
        person: Person,
        pattern: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of why this is a match."""
        reasons = []
        
        if pattern.get('has_email') and person.has_email:
            reasons.append('has email')
        
        if pattern.get('has_github') and person.has_github:
            reasons.append('has GitHub profile')
        
        if pattern.get('companies'):
            reasons.append(f"works at {pattern['companies'][0]}")
        
        if pattern.get('locations') and person.location:
            reasons.append(f"located in {person.location}")
        
        if pattern.get('skills'):
            matched = [s for s in pattern['skills'] if person.headline and s.lower() in person.headline.lower()]
            if matched:
                reasons.append(f"matches skills: {', '.join(matched[:3])}")
        
        return ' • '.join(reasons) if reasons else 'Matches search criteria'
    
    # ========================================
    # BATCH OPERATIONS
    # ========================================
    
    def run_daily_monitoring(
        self,
        user_id: str,
        saved_searches: List[Dict[str, Any]],
        watched_people: List[str],
        watched_repos: List[str]
    ) -> Dict[str, Any]:
        """
        Run all monitoring tasks for a user.
        
        This would be called by a background job scheduler.
        
        Returns:
            Summary of all discoveries
        """
        results = {
            'user_id': user_id,
            'run_at': datetime.utcnow().isoformat(),
            'new_matches': self.discover_new_matches(user_id, saved_searches),
            'job_changes': self.monitor_job_changes(watched_people),
            'github_activity': self.monitor_github_activity(watched_repos),
            'rising_talent': self.identify_rising_talent(),
            'total_notifications': 0
        }
        
        # Count total items to notify
        results['total_notifications'] = (
            len(results['new_matches']) +
            len(results['job_changes']) +
            len(results['github_activity']) +
            len(results['rising_talent'])
        )
        
        return results

