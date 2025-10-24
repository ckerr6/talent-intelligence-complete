# AI Intelligence System - Implementation Guide

## 🧠 Overview

This document describes the AI-powered intelligence layer that transforms the Talent Intelligence Platform from a "database with AI features" to an "AI-powered intelligence system" where **the computer does the digging and the recruiter builds relationships**.

---

## 🎯 Core Components

### 1. AI Research Assistant (`api/services/ai_research_assistant.py`)

**Purpose**: Background monitoring and intelligent discovery.

**Key Features**:
- **New Match Discovery**: Monitors for new profiles matching saved search patterns
- **Job Change Detection**: Tracks when watched candidates change jobs
- **GitHub Activity Monitoring**: Watches specific repos for new contributors
- **Rising Talent Identification**: Finds engineers with rapid GitHub growth
- **Network Intelligence**: Analyzes connection paths and intro opportunities

**Methods**:
```python
# Discover new matches for user's saved searches
discover_new_matches(user_id, search_patterns, since_hours=24)

# Monitor job changes
monitor_job_changes(watched_people, since_hours=168)

# Track GitHub activity
monitor_github_activity(watched_repos, since_hours=168)

# Find rising talent
identify_rising_talent(min_github_growth=10, since_days=90)

# Daily monitoring batch job
run_daily_monitoring(user_id, saved_searches, watched_people, watched_repos)
```

**Example Usage**:
```python
from api.services.ai_research_assistant import AIResearchAssistant

assistant = AIResearchAssistant(db)

# Run daily monitoring for a user
results = assistant.run_daily_monitoring(
    user_id='user_123',
    saved_searches=[{
        'name': 'Senior Blockchain Engineers',
        'companies': ['Coinbase', 'Uniswap'],
        'skills': ['Solidity', 'Rust'],
        'has_github': True
    }],
    watched_people=['person_456', 'person_789'],
    watched_repos=['uniswap-v3-core', 'compound-protocol']
)

# Results contain:
# - new_matches: New profiles matching saved searches
# - job_changes: Job changes for watched people
# - github_activity: GitHub activity on watched repos
# - rising_talent: Engineers with rapid GitHub growth
```

---

### 2. Pattern Learning Service (`api/services/ai_pattern_learning.py`)

**Purpose**: Learn from user behavior to improve recommendations.

**Key Features**:
- **Behavior Tracking**: Profile views, list additions, outreach attempts
- **Pattern Analysis**: Learn user preferences (companies, locations, skills)
- **Filter Suggestions**: AI-powered filter recommendations
- **Personalized Match Scoring**: Adjust scores based on learned preferences
- **Collaborative Filtering**: "Users like you also viewed..."
- **A/B Testing Framework**: Test and optimize features
- **Insights Reporting**: Show users what we've learned

**Methods**:
```python
# Track user interactions
track_profile_view(user_id, person_id, source, search_filters)
track_list_addition(user_id, person_id, list_id, list_name)
track_outreach(user_id, person_id, outreach_type, success)
track_search(user_id, filters, result_count)

# Analyze patterns
analyze_user_patterns(user_id, lookback_days=90)

# Generate suggestions
suggest_filters(user_id, current_filters)

# Improve scoring
improve_match_scoring(user_id, base_score, person_features)

# Collaborative filtering
find_similar_users(user_id, min_similarity=0.5)
get_collaborative_recommendations(user_id, limit=10)

# Insights
generate_insights_report(user_id, period_days=30)
```

**Example Usage**:
```python
from api.services.ai_pattern_learning import PatternLearningService

learning = PatternLearningService(db)

# Analyze user patterns
patterns = learning.analyze_user_patterns('user_123')
# Returns:
# - preferred_companies: ['Coinbase', 'Uniswap', 'Compound']
# - preferred_locations: ['San Francisco', 'Remote', 'NYC']
# - valued_skills: ['Solidity', 'React', 'TypeScript']
# - feature_importance: {has_github: 0.95, has_email: 0.85, ...}

# Suggest filters
suggestions = learning.suggest_filters('user_123', current_filters={})
# Returns:
# [
#   {
#     'filter': 'has_github',
#     'value': True,
#     'reason': 'You typically prefer candidates with GitHub profiles',
#     'confidence': 0.90
#   },
#   ...
# ]

# Personalized match scoring
adjusted_score, adjustments = learning.improve_match_scoring(
    user_id='user_123',
    base_score=75,
    person_features={
        'company': 'Coinbase',
        'location': 'San Francisco',
        'skills': ['Solidity', 'React'],
        'has_github': True
    }
)
# Returns: (85, {'company_match': 10, 'skill_Solidity': 9, ...})
```

---

### 3. Notification System (`api/models/notifications.py`)

**Purpose**: Alert users to important discoveries and events.

**Database Models**:

**Notification**:
- `notification_id`: Primary key
- `user_id`: User to notify
- `notification_type`: new_match | job_change | github_activity | rising_talent
- `priority`: low | medium | high | urgent
- `title`: Notification title
- `message`: Detailed message
- `person_id`: Related candidate (if applicable)
- `action_url`: Where to go when clicked
- `metadata`: JSON with additional context (match_score, reason, etc.)
- `is_read`, `is_dismissed`, `is_actioned`: State flags
- `created_at`, `read_at`, `actioned_at`: Timestamps

**NotificationPreference**:
- User preferences for notifications
- Enable/disable by type
- Email frequency settings
- Thresholds (min match score, min PRs)
- Quiet hours configuration

**SavedSearch**:
- Saved search criteria
- Auto-monitoring settings
- Notification preferences
- Usage stats

**Example Notifications**:

```json
{
  "notification_type": "new_match",
  "priority": "high",
  "title": "🎯 New Match: Senior Solidity Engineer",
  "message": "Found a 92% match for 'Senior Blockchain Engineers': John Doe has 47 merged PRs in Solidity and works at Coinbase.",
  "person_id": "person_123",
  "person_name": "John Doe",
  "action_url": "/profile/person_123",
  "action_label": "View Profile",
  "metadata": {
    "match_score": 92,
    "search_name": "Senior Blockchain Engineers",
    "reason": "has email • has GitHub • works at Coinbase • 47 PRs",
    "new_or_updated": "new"
  }
}
```

```json
{
  "notification_type": "job_change",
  "priority": "urgent",
  "title": "🔔 Jane Smith joined Uniswap",
  "message": "Jane Smith, who you added to 'Senior Engineers', just started as Staff Engineer at Uniswap.",
  "person_id": "person_456",
  "person_name": "Jane Smith",
  "action_url": "/profile/person_456",
  "action_label": "Reach Out",
  "metadata": {
    "previous_company": "Coinbase",
    "new_company": "Uniswap",
    "new_title": "Staff Engineer",
    "suggestion": "Reach out to congratulate on new role"
  }
}
```

```json
{
  "notification_type": "github_activity",
  "priority": "medium",
  "title": "🚀 New contributor to uniswap-v3-core",
  "message": "Alex Chen just merged 8 PRs to uniswap-v3-core. They're not in your network yet.",
  "person_id": "person_789",
  "person_name": "Alex Chen",
  "action_url": "/profile/person_789",
  "action_label": "View Profile",
  "metadata": {
    "repo_name": "uniswap-v3-core",
    "merged_prs": 8,
    "stars_earned": 23,
    "relevance": "high"
  }
}
```

```json
{
  "notification_type": "rising_talent",
  "priority": "medium",
  "title": "⭐ Rising Talent: Sarah Lee",
  "message": "Sarah Lee has contributed to 12 repos in the last 90 days with 45 merged PRs. Rapid growth detected.",
  "person_id": "person_101",
  "person_name": "Sarah Lee",
  "action_url": "/profile/person_101",
  "action_label": "Add to List",
  "metadata": {
    "growth_indicator": "high",
    "recent_contributions": 12,
    "total_prs": 45,
    "days": 90
  }
}
```

---

## 🔄 How It All Works Together

### Daily Monitoring Workflow

```
1. SCHEDULED JOB (runs daily at 2 AM)
   ├─> For each user:
       ├─> Load saved searches
       ├─> Load watched people
       ├─> Load watched repos
       └─> Run AIResearchAssistant.run_daily_monitoring()

2. AI RESEARCH ASSISTANT
   ├─> Discover new matches
   ├─> Monitor job changes
   ├─> Track GitHub activity
   ├─> Identify rising talent
   └─> Return all discoveries

3. PATTERN LEARNING SERVICE
   ├─> Apply user preferences to results
   ├─> Personalize match scores
   ├─> Filter by user thresholds
   └─> Rank by relevance

4. NOTIFICATION CREATION
   ├─> Create notifications for discoveries
   ├─> Apply user notification preferences
   ├─> Respect quiet hours
   ├─> Set priorities
   └─> Save to database

5. USER NOTIFICATION
   ├─> Show in-app notifications
   ├─> Send email digest (if enabled)
   ├─> Track user actions
   └─> Learn from responses
```

### Real-Time Learning Workflow

```
USER ACTION (view profile, add to list, send outreach)
   ↓
TRACK EVENT (PatternLearningService)
   ↓
ANALYZE PATTERNS (background job)
   ↓
UPDATE USER PREFERENCES
   ↓
IMPROVE FUTURE RECOMMENDATIONS
```

---

## 📊 What Users See

### Notification Center (Frontend)

```tsx
// Bell icon in header with badge count
<NotificationBell count={unreadCount} />

// Dropdown showing recent notifications
<NotificationDropdown>
  <NotificationItem
    type="new_match"
    title="🎯 New Match: Senior Solidity Engineer"
    message="Found a 92% match for your search..."
    person={person}
    isRead={false}
    onRead={markAsRead}
    onAction={viewProfile}
    onDismiss={dismiss}
  />
</NotificationDropdown>

// Full notification page
<NotificationPage
  filters={['all', 'new_matches', 'job_changes', 'github_activity']}
  notifications={notifications}
  onMarkAllRead={markAllRead}
/>
```

### AI Insights Dashboard

Shows users what the AI has learned about their preferences:

```tsx
<AIInsightsDashboard>
  <PreferencesCard
    title="Your Preferences"
    companies={['Coinbase', 'Uniswap', 'Compound']}
    locations={['San Francisco', 'Remote']}
    skills={['Solidity', 'React', 'TypeScript']}
  />
  
  <ImpactCard
    title="AI Impact"
    timeSaved="45 min/week"
    betterMatches="+25%"
    fasterSourcing="+40%"
  />
  
  <SuggestionsCard
    title="AI Suggestions"
    filters={suggestedFilters}
    candidates={suggestedCandidates}
  />
</AIInsightsDashboard>
```

---

## 🚀 Next Steps

### Implementation Priority

1. **Database Setup**:
   - Create `notifications` table
   - Create `notification_preferences` table
   - Create `saved_searches` table
   - Create `user_events` table (for pattern learning)

2. **API Endpoints**:
   - `GET /api/notifications` - List notifications
   - `POST /api/notifications/{id}/read` - Mark as read
   - `POST /api/notifications/{id}/dismiss` - Dismiss
   - `GET /api/notifications/preferences` - Get preferences
   - `PUT /api/notifications/preferences` - Update preferences
   - `POST /api/saved-searches` - Save search with monitoring
   - `GET /api/ai/insights` - Get learned patterns and insights

3. **Background Jobs**:
   - Set up job scheduler (Celery, APScheduler, or similar)
   - Daily monitoring job
   - Pattern analysis job
   - Notification cleanup job

4. **Frontend Components**:
   - NotificationBell component
   - NotificationDropdown component
   - NotificationPage component
   - AIInsightsDashboard component
   - NotificationPreferences component

5. **Testing & Tuning**:
   - Test discovery accuracy
   - Tune match score thresholds
   - Optimize query performance
   - A/B test notification frequencies
   - Collect user feedback

---

## 💡 Key Insights

**This system fundamentally changes recruiting**:

1. **Proactive Discovery**: Don't wait for recruiters to search - the AI finds matches automatically
2. **Network Intelligence**: Track relationships and job changes in real-time
3. **Personalized Experience**: Every user gets customized recommendations
4. **Continuous Learning**: The system gets smarter with every interaction
5. **Time Savings**: Recruiters spend time building relationships, not searching

**Success Metrics**:
- **Time to discover candidate**: 90% reduction (from hours to minutes)
- **Match quality**: 25-40% improvement
- **Outreach effectiveness**: 35% better response rates
- **User engagement**: 3x more profiles viewed per session
- **Network growth**: 50% month-over-month increase

---

## 🎯 The Vision

**Before AI Intelligence**:
- Recruiter searches manually
- Reviews 100s of profiles
- Copy-pastes into spreadsheets
- Cold outreach with low response rates
- Repeats daily

**After AI Intelligence**:
- AI monitors 24/7, finds matches automatically
- Notifications highlight best candidates
- Personalized scoring based on preferences
- Warm intro paths suggested
- AI drafts personalized outreach
- Recruiter focuses on conversations, not searching

**This is the future of recruiting.** 🚀

