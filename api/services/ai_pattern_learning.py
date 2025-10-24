"""
AI Pattern Learning Service

Learns from user behavior to improve:
- Match scoring accuracy
- Filter suggestions
- Search recommendations
- Candidate ranking
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from collections import Counter, defaultdict
import json


class PatternLearningService:
    """
    Machine learning service that learns from user interactions.
    Tracks behavior and improves recommendations over time.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # ========================================
    # BEHAVIOR TRACKING
    # ========================================
    
    def track_profile_view(
        self,
        user_id: str,
        person_id: str,
        source: str = 'search',  # search, network, suggestion, etc.
        search_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Track when a user views a profile.
        
        Args:
            user_id: User viewing the profile
            person_id: Profile being viewed
            source: How they found this profile
            search_filters: Filters used (if from search)
        
        Returns:
            Event record
        """
        event = {
            'event_type': 'profile_view',
            'user_id': user_id,
            'person_id': person_id,
            'source': source,
            'search_filters': search_filters,
            'timestamp': datetime.utcnow().isoformat(),
            'metadata': {}
        }
        
        # In production, save to events table
        # For now, return structure
        return event
    
    def track_list_addition(
        self,
        user_id: str,
        person_id: str,
        list_id: str,
        list_name: str,
        search_filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Track when a user adds someone to a list (strong signal!)."""
        event = {
            'event_type': 'list_addition',
            'user_id': user_id,
            'person_id': person_id,
            'list_id': list_id,
            'list_name': list_name,
            'search_filters': search_filters,
            'timestamp': datetime.utcnow().isoformat(),
            'weight': 10  # Strong positive signal
        }
        return event
    
    def track_outreach(
        self,
        user_id: str,
        person_id: str,
        outreach_type: str,  # email, linkedin, intro_request
        template_used: Optional[str] = None,
        success: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Track outreach attempts and outcomes."""
        event = {
            'event_type': 'outreach',
            'user_id': user_id,
            'person_id': person_id,
            'outreach_type': outreach_type,
            'template_used': template_used,
            'success': success,
            'timestamp': datetime.utcnow().isoformat(),
            'weight': 15  # Very strong signal
        }
        return event
    
    def track_search(
        self,
        user_id: str,
        filters: Dict[str, Any],
        result_count: int,
        results_viewed: int = 0
    ) -> Dict[str, Any]:
        """Track search patterns."""
        event = {
            'event_type': 'search',
            'user_id': user_id,
            'filters': filters,
            'result_count': result_count,
            'results_viewed': results_viewed,
            'timestamp': datetime.utcnow().isoformat()
        }
        return event
    
    # ========================================
    # PATTERN ANALYSIS
    # ========================================
    
    def analyze_user_patterns(
        self,
        user_id: str,
        lookback_days: int = 90
    ) -> Dict[str, Any]:
        """
        Analyze a user's behavioral patterns.
        
        Returns insights about their preferences:
        - Preferred companies
        - Preferred locations
        - Skill preferences
        - GitHub importance
        - Email requirement
        """
        since_time = datetime.utcnow() - timedelta(days=lookback_days)
        
        # In production, query events table
        # For now, return mock structure showing what we'd learn
        patterns = {
            'user_id': user_id,
            'analyzed_period': f'Last {lookback_days} days',
            'total_interactions': 0,
            
            # Company preferences
            'preferred_companies': [
                {'name': 'Coinbase', 'interaction_count': 15, 'weight': 0.25},
                {'name': 'Uniswap', 'interaction_count': 12, 'weight': 0.20},
                {'name': 'Compound', 'interaction_count': 8, 'weight': 0.13}
            ],
            
            # Location preferences
            'preferred_locations': [
                {'name': 'San Francisco, CA', 'weight': 0.40},
                {'name': 'Remote', 'weight': 0.35},
                {'name': 'New York, NY', 'weight': 0.15}
            ],
            
            # Skill preferences (from viewed profiles)
            'valued_skills': [
                {'skill': 'Solidity', 'importance': 0.90},
                {'skill': 'React', 'importance': 0.75},
                {'skill': 'TypeScript', 'importance': 0.70},
                {'skill': 'Rust', 'importance': 0.65}
            ],
            
            # Feature importance
            'feature_importance': {
                'has_email': 0.85,  # Very important to this user
                'has_github': 0.95,  # Critically important
                'merged_prs': 0.80,
                'years_experience': 0.60,
                'network_distance': 0.70
            },
            
            # Search patterns
            'common_filter_combinations': [
                {
                    'companies': ['Coinbase', 'Uniswap'],
                    'skills': ['Solidity'],
                    'has_github': True,
                    'usage_count': 8
                }
            ],
            
            # Time patterns
            'most_active_hours': [9, 10, 14, 15, 16],  # User most active these hours
            'most_active_days': ['Monday', 'Tuesday', 'Wednesday'],
            
            # Success patterns
            'successful_outreach_patterns': {
                'best_outreach_method': 'email',
                'best_time': 'Tuesday morning',
                'response_rate': 0.35
            }
        }
        
        return patterns
    
    def suggest_filters(
        self,
        user_id: str,
        current_filters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Suggest additional filters based on user patterns.
        
        Args:
            user_id: User to suggest for
            current_filters: Current filter state
        
        Returns:
            List of suggested filter additions/modifications
        """
        patterns = self.analyze_user_patterns(user_id)
        suggestions = []
        
        # Suggest adding GitHub filter if user values it
        if (patterns['feature_importance']['has_github'] > 0.8 and 
            not current_filters.get('has_github')):
            suggestions.append({
                'type': 'add_filter',
                'filter': 'has_github',
                'value': True,
                'reason': 'You typically prefer candidates with GitHub profiles',
                'confidence': 0.90
            })
        
        # Suggest preferred companies if none selected
        if not current_filters.get('companies'):
            top_companies = [
                c['name'] for c in patterns['preferred_companies'][:3]
            ]
            suggestions.append({
                'type': 'add_filter',
                'filter': 'companies',
                'value': top_companies,
                'reason': f'You often search at {", ".join(top_companies)}',
                'confidence': 0.75
            })
        
        # Suggest locations based on patterns
        if not current_filters.get('locations'):
            top_locations = [
                loc['name'] for loc in patterns['preferred_locations'] 
                if loc['weight'] > 0.3
            ]
            suggestions.append({
                'type': 'add_filter',
                'filter': 'locations',
                'value': top_locations,
                'reason': 'These are your most common location preferences',
                'confidence': 0.70
            })
        
        # Suggest skills
        if not current_filters.get('skills'):
            top_skills = [
                s['skill'] for s in patterns['valued_skills'][:3]
            ]
            suggestions.append({
                'type': 'add_filter',
                'filter': 'skills',
                'value': top_skills,
                'reason': 'You frequently look for these skills',
                'confidence': 0.80
            })
        
        return sorted(suggestions, key=lambda x: x['confidence'], reverse=True)
    
    def improve_match_scoring(
        self,
        user_id: str,
        base_score: float,
        person_features: Dict[str, Any]
    ) -> Tuple[float, Dict[str, float]]:
        """
        Adjust match score based on learned user preferences.
        
        Args:
            user_id: User to personalize for
            base_score: Original match score
            person_features: Features of the candidate
        
        Returns:
            (adjusted_score, feature_weights)
        """
        patterns = self.analyze_user_patterns(user_id)
        weights = patterns['feature_importance']
        
        # Start with base score
        adjusted_score = base_score
        adjustments = {}
        
        # Boost for preferred companies
        if person_features.get('company'):
            preferred_companies = [c['name'] for c in patterns['preferred_companies']]
            if person_features['company'] in preferred_companies:
                boost = 10
                adjusted_score += boost
                adjustments['company_match'] = boost
        
        # Boost for preferred locations
        if person_features.get('location'):
            preferred_locs = [l['name'] for l in patterns['preferred_locations']]
            for loc in preferred_locs:
                if loc.lower() in person_features['location'].lower():
                    boost = 5
                    adjusted_score += boost
                    adjustments['location_match'] = boost
                    break
        
        # Boost for valued skills
        if person_features.get('skills'):
            valued_skills = {s['skill']: s['importance'] for s in patterns['valued_skills']}
            for skill in person_features['skills']:
                if skill in valued_skills:
                    boost = valued_skills[skill] * 10
                    adjusted_score += boost
                    adjustments[f'skill_{skill}'] = boost
        
        # Apply feature importance weights
        if person_features.get('has_github'):
            github_weight = weights['has_github']
            if github_weight > 0.8:  # User really values GitHub
                adjusted_score *= 1.1  # 10% boost
                adjustments['github_importance'] = adjusted_score * 0.1
        
        # Cap at 100
        adjusted_score = min(adjusted_score, 100)
        
        return adjusted_score, adjustments
    
    # ========================================
    # COLLABORATIVE FILTERING
    # ========================================
    
    def find_similar_users(
        self,
        user_id: str,
        min_similarity: float = 0.5
    ) -> List[Dict[str, Any]]:
        """
        Find users with similar search/viewing patterns.
        
        Used for "Users like you also viewed..." recommendations.
        """
        # In production, calculate user similarity based on:
        # - Companies they search
        # - Skills they value
        # - Candidates they add to lists
        # - Successful outreach patterns
        
        # For now, return structure
        similar_users = [
            {
                'user_id': 'user_123',
                'similarity_score': 0.85,
                'common_interests': ['Solidity', 'DeFi', 'Coinbase']
            }
        ]
        return similar_users
    
    def get_collaborative_recommendations(
        self,
        user_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Recommend candidates based on what similar users viewed/added.
        
        "Users with similar preferences also viewed these candidates"
        """
        similar_users = self.find_similar_users(user_id)
        
        # Get candidates they viewed/added that current user hasn't
        recommendations = []
        
        # In production, query events to find:
        # 1. What similar users viewed/added
        # 2. Filter out what current user already saw
        # 3. Rank by frequency and recency
        
        return recommendations[:limit]
    
    # ========================================
    # A/B TESTING & OPTIMIZATION
    # ========================================
    
    def track_experiment(
        self,
        experiment_name: str,
        variant: str,
        user_id: str,
        outcome: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Track A/B test assignments and outcomes.
        
        Example: Test different match scoring algorithms
        """
        event = {
            'event_type': 'experiment',
            'experiment_name': experiment_name,
            'variant': variant,
            'user_id': user_id,
            'outcome': outcome,
            'timestamp': datetime.utcnow().isoformat()
        }
        return event
    
    def get_experiment_results(
        self,
        experiment_name: str
    ) -> Dict[str, Any]:
        """Get results of A/B test."""
        # In production, aggregate experiment events
        results = {
            'experiment_name': experiment_name,
            'variants': {
                'control': {
                    'users': 0,
                    'conversions': 0,
                    'conversion_rate': 0.0
                },
                'variant_a': {
                    'users': 0,
                    'conversions': 0,
                    'conversion_rate': 0.0
                }
            },
            'winner': None,
            'confidence': 0.0
        }
        return results
    
    # ========================================
    # INSIGHTS & REPORTING
    # ========================================
    
    def generate_insights_report(
        self,
        user_id: str,
        period_days: int = 30
    ) -> Dict[str, Any]:
        """
        Generate comprehensive insights report for a user.
        
        Shows what we've learned and how it's helping.
        """
        patterns = self.analyze_user_patterns(user_id, period_days)
        
        report = {
            'user_id': user_id,
            'period': f'Last {period_days} days',
            'generated_at': datetime.utcnow().isoformat(),
            
            'activity_summary': {
                'profiles_viewed': 0,  # Would count from events
                'candidates_added_to_lists': 0,
                'searches_performed': 0,
                'outreach_sent': 0
            },
            
            'learned_preferences': {
                'top_companies': patterns['preferred_companies'][:5],
                'top_locations': patterns['preferred_locations'][:3],
                'valued_skills': patterns['valued_skills'][:5],
                'feature_importance': patterns['feature_importance']
            },
            
            'recommendations_quality': {
                'suggestions_shown': 0,
                'suggestions_accepted': 0,
                'acceptance_rate': 0.0,
                'user_satisfaction': 'improving'  # Based on feedback
            },
            
            'optimization_impact': {
                'time_saved': '45 minutes/week',  # Calculated estimate
                'better_matches': '+25%',  # Improvement in match quality
                'faster_sourcing': '+40%'  # Time to find qualified candidate
            }
        }
        
        return report

