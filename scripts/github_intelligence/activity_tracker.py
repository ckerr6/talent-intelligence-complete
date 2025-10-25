#!/usr/bin/env python3
"""
ABOUTME: Tracks and analyzes GitHub activity patterns over time.
ABOUTME: Identifies activity trends, consistency, and temporal patterns to understand developer engagement.
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from collections import defaultdict
import statistics


class ActivityTracker:
    """
    Tracks and analyzes GitHub activity patterns.
    
    Analyzes:
    - Activity frequency (commits/week, PRs/month)
    - Active hours and days
    - Consistency and regularity
    - Activity trends (growing/stable/declining)
    - Response patterns
    """
    
    def __init__(self):
        pass
    
    def analyze_activity(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze activity patterns from profile data.
        
        Args:
            profile_data: Complete profile data from ProfileBuilder
        
        Returns:
            Dictionary with activity metrics and patterns
        """
        events = profile_data.get('events', [])
        repos = profile_data.get('repos', [])
        user = profile_data.get('user', {})
        
        if not events:
            return self._empty_activity_summary()
        
        # Parse event timestamps
        event_times = []
        for event in events:
            try:
                event_time = datetime.fromisoformat(event['created_at'].replace('Z', '+00:00'))
                event_times.append(event_time)
            except:
                continue
        
        if not event_times:
            return self._empty_activity_summary()
        
        # Calculate various metrics
        frequency = self._calculate_frequency(event_times)
        temporal_patterns = self._analyze_temporal_patterns(event_times)
        consistency = self._calculate_consistency(event_times)
        trend = self._determine_trend(events, user)
        
        # Find last active date
        last_active = max(event_times)
        days_since_active = (datetime.now(last_active.tzinfo) - last_active).days
        
        return {
            'total_events_90d': len(events),
            'commits_per_week': frequency['commits_per_week'],
            'prs_per_month': frequency['prs_per_month'],
            'events_per_week': frequency['events_per_week'],
            'active_hours': temporal_patterns['active_hours'],
            'active_days': temporal_patterns['active_days'],
            'peak_activity_hour': temporal_patterns['peak_hour'],
            'peak_activity_day': temporal_patterns['peak_day'],
            'consistency_score': consistency,
            'activity_trend': trend['trend'],
            'trend_description': trend['description'],
            'last_active_date': last_active.isoformat(),
            'days_since_active': days_since_active,
            'is_currently_active': days_since_active <= 7,
            'activity_level': self._classify_activity_level(frequency['events_per_week'])
        }
    
    def _calculate_frequency(self, event_times: List[datetime]) -> Dict[str, float]:
        """
        Calculate activity frequency metrics.
        """
        if not event_times:
            return {
                'commits_per_week': 0,
                'prs_per_month': 0,
                'events_per_week': 0
            }
        
        # Calculate time span
        oldest = min(event_times)
        newest = max(event_times)
        days_span = (newest - oldest).days or 1
        weeks_span = days_span / 7
        months_span = days_span / 30
        
        # Count events
        total_events = len(event_times)
        
        # Simple frequency calculations
        events_per_week = total_events / weeks_span if weeks_span > 0 else 0
        
        # Estimate commits and PRs (based on typical ratios)
        commits_per_week = events_per_week * 0.6  # ~60% of events are push events
        prs_per_month = events_per_week * 0.15 * 4  # ~15% are PR events
        
        return {
            'commits_per_week': round(commits_per_week, 1),
            'prs_per_month': round(prs_per_month, 1),
            'events_per_week': round(events_per_week, 1)
        }
    
    def _analyze_temporal_patterns(self, event_times: List[datetime]) -> Dict[str, Any]:
        """
        Analyze when the developer is active (hours/days).
        """
        if not event_times:
            return {
                'active_hours': [],
                'active_days': [],
                'peak_hour': None,
                'peak_day': None
            }
        
        # Count by hour (UTC)
        hour_counts = defaultdict(int)
        day_counts = defaultdict(int)
        
        for event_time in event_times:
            hour_counts[event_time.hour] += 1
            day_counts[event_time.strftime('%A')] += 1
        
        # Sort by frequency
        sorted_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)
        sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
        
        # Get most active hours (top 5)
        active_hours = [hour for hour, count in sorted_hours[:8]]
        
        # Get most active days (top 3)
        active_days = [day for day, count in sorted_days[:5]]
        
        return {
            'active_hours': active_hours,
            'active_days': active_days,
            'peak_hour': sorted_hours[0][0] if sorted_hours else None,
            'peak_day': sorted_days[0][0] if sorted_days else None,
            'hour_distribution': dict(hour_counts),
            'day_distribution': dict(day_counts)
        }
    
    def _calculate_consistency(self, event_times: List[datetime]) -> float:
        """
        Calculate consistency score (0.0 to 1.0).
        
        High consistency = regular, predictable activity
        Low consistency = sporadic, irregular activity
        """
        if len(event_times) < 2:
            return 0.0
        
        # Sort times
        sorted_times = sorted(event_times)
        
        # Calculate gaps between events (in days)
        gaps = []
        for i in range(1, len(sorted_times)):
            gap = (sorted_times[i] - sorted_times[i-1]).total_seconds() / 86400  # Convert to days
            gaps.append(gap)
        
        if not gaps:
            return 0.0
        
        # Calculate coefficient of variation (lower = more consistent)
        mean_gap = statistics.mean(gaps)
        if mean_gap == 0:
            return 1.0
        
        std_gap = statistics.stdev(gaps) if len(gaps) > 1 else 0
        cv = std_gap / mean_gap if mean_gap > 0 else 0
        
        # Convert to 0-1 score (inverse of CV, capped)
        consistency = max(0, min(1, 1 - (cv / 5)))
        
        return round(consistency, 2)
    
    def _determine_trend(self, events: List[Dict[str, Any]], user: Dict[str, Any]) -> Dict[str, str]:
        """
        Determine if activity is growing, stable, or declining.
        """
        if len(events) < 10:
            return {
                'trend': 'Insufficient Data',
                'description': 'Not enough activity data to determine trend'
            }
        
        # Split events into first half and second half
        midpoint = len(events) // 2
        first_half = events[midpoint:]  # More recent (events are reverse chronological)
        second_half = events[:midpoint]  # Older
        
        first_half_count = len(first_half)
        second_half_count = len(second_half)
        
        # Calculate percentage change
        if second_half_count > 0:
            change = ((first_half_count - second_half_count) / second_half_count) * 100
        else:
            change = 0
        
        # Classify trend
        if change > 20:
            trend = 'Growing'
            description = f'Activity increased by {change:.0f}% in recent period'
        elif change < -20:
            trend = 'Declining'
            description = f'Activity decreased by {abs(change):.0f}% in recent period'
        else:
            trend = 'Stable'
            description = 'Activity level is consistent'
        
        return {
            'trend': trend,
            'description': description,
            'change_percentage': round(change, 1)
        }
    
    def _classify_activity_level(self, events_per_week: float) -> str:
        """
        Classify overall activity level.
        """
        if events_per_week >= 20:
            return 'Very High'
        elif events_per_week >= 10:
            return 'High'
        elif events_per_week >= 5:
            return 'Medium'
        elif events_per_week >= 2:
            return 'Low'
        else:
            return 'Very Low'
    
    def _empty_activity_summary(self) -> Dict[str, Any]:
        """
        Return empty activity summary when no data available.
        """
        return {
            'total_events_90d': 0,
            'commits_per_week': 0,
            'prs_per_month': 0,
            'events_per_week': 0,
            'active_hours': [],
            'active_days': [],
            'peak_activity_hour': None,
            'peak_activity_day': None,
            'consistency_score': 0,
            'activity_trend': 'No Data',
            'trend_description': 'No recent activity',
            'last_active_date': None,
            'days_since_active': None,
            'is_currently_active': False,
            'activity_level': 'Inactive'
        }
    
    def get_activity_summary_text(self, activity_data: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of activity.
        
        Args:
            activity_data: Output from analyze_activity
        
        Returns:
            Text summary
        """
        level = activity_data['activity_level']
        trend = activity_data['activity_trend']
        commits_week = activity_data['commits_per_week']
        consistency = activity_data['consistency_score']
        days_since = activity_data.get('days_since_active')
        
        summary = f"{level} activity level"
        
        if commits_week > 0:
            summary += f" with ~{commits_week:.0f} commits/week"
        
        summary += f". Trend: {trend}"
        
        if consistency > 0.7:
            summary += ". Very consistent"
        elif consistency > 0.4:
            summary += ". Moderately consistent"
        else:
            summary += ". Sporadic"
        
        if days_since is not None:
            if days_since <= 7:
                summary += ". Active in last week"
            elif days_since <= 30:
                summary += f". Last active {days_since} days ago"
            else:
                summary += f". No recent activity ({days_since} days)"
        
        return summary


def main():
    """
    Test activity tracker with sample data.
    """
    # Sample profile data
    sample_profile = {
        'user': {
            'login': 'test_dev',
            'created_at': '2020-01-01T00:00:00Z'
        },
        'events': [
            {'created_at': '2025-10-25T14:30:00Z', 'type': 'PushEvent'},
            {'created_at': '2025-10-24T15:00:00Z', 'type': 'PushEvent'},
            {'created_at': '2025-10-23T14:45:00Z', 'type': 'PullRequestEvent'},
            {'created_at': '2025-10-22T16:00:00Z', 'type': 'PushEvent'},
            {'created_at': '2025-10-21T14:30:00Z', 'type': 'PushEvent'},
        ] * 10,  # Repeat for more data
        'repos': []
    }
    
    tracker = ActivityTracker()
    result = tracker.analyze_activity(sample_profile)
    
    print("⚡ Activity Analysis:")
    print(f"   Activity Level: {result['activity_level']}")
    print(f"   Events/week: {result['events_per_week']}")
    print(f"   Commits/week: {result['commits_per_week']}")
    print(f"   Trend: {result['activity_trend']} - {result['trend_description']}")
    print(f"   Consistency: {result['consistency_score']:.0%}")
    print(f"   Peak Hours: {result['active_hours'][:5]}")
    print(f"   Peak Days: {result['active_days']}")
    print(f"   Days Since Active: {result['days_since_active']}")
    
    summary = tracker.get_activity_summary_text(result)
    print(f"\n   Summary: {summary}")


if __name__ == '__main__':
    main()
