# AI Workflows Specification

## Overview

This document details the specific workflows and data pipelines for each AI system. These workflows transform the Talent Intelligence Platform from a search tool into an AI-powered intelligence layer.

## Workflow 1: Profile Analysis Pipeline

**Trigger:** User views a profile
**Goal:** Generate comprehensive AI insights automatically

### Pipeline Steps

```
1. Profile View Detected
   ↓
2. Check Cache
   ├─ Hit → Return cached summary
   └─ Miss → Continue to generation
   ↓
3. Gather Context
   ├─ Person data (name, headline, location)
   ├─ Employment history (roles, companies, duration)
   ├─ GitHub profile (stats, repos, PRs)
   ├─ Network data (connections, mutual contacts)
   └─ Email availability
   ↓
4. Generate AI Summary (Background)
   ├─ Career summary
   ├─ Technical assessment
   ├─ Key strengths
   ├─ Ideal roles
   └─ Potential concerns
   ↓
5. Calculate Match Score
   ├─ Email availability: +30
   ├─ GitHub presence: +20
   ├─ Merged PRs: +2 each
   ├─ Network distance: -10 per degree
   ├─ Years experience: +5 per year (cap at 25)
   └─ Normalize to 0-100
   ↓
6. Find Similar Candidates
   ├─ Generate profile embedding
   ├─ Vector similarity search
   └─ Return top 10
   ↓
7. Cache Results (7 days)
   ↓
8. Show Notification
   "✨ AI insights ready"
```

### Code Example

```python
# api/services/profile_analysis_pipeline.py

class ProfileAnalysisPipeline:
    def __init__(self):
        self.cache = Redis()
        self.llm = OpenAI()
        self.vector_store = VectorStore()
        
    async def analyze_profile(self, person_id: str) -> dict:
        """Run complete profile analysis"""
        
        # Check cache first
        cache_key = f"profile_analysis:{person_id}"
        cached = await self.cache.get(cache_key)
        if cached:
            return json.loads(cached)
        
        # Gather context
        context = await self.gather_context(person_id)
        
        # Run analyses in parallel
        summary, match_score, similar = await asyncio.gather(
            self.generate_summary(context),
            self.calculate_match_score(context),
            self.find_similar_candidates(context)
        )
        
        result = {
            "summary": summary,
            "match_score": match_score,
            "similar_candidates": similar,
            "generated_at": datetime.now().isoformat()
        }
        
        # Cache for 7 days
        await self.cache.set(cache_key, json.dumps(result), ex=7*24*3600)
        
        return result
    
    async def generate_summary(self, context: dict) -> dict:
        """Generate AI profile summary"""
        
        prompt = f"""
        Analyze this technical candidate:
        
        Name: {context['person']['full_name']}
        Current Role: {context['person']['headline']}
        Location: {context['person']['location']}
        
        Employment History:
        {self._format_employment(context['employment'])}
        
        GitHub Activity:
        - Repos: {context['github']['public_repos']}
        - Merged PRs: {context['github']['total_merged_prs']}
        - Languages: {', '.join(context['github']['top_languages'])}
        - Notable contributions: {self._format_repos(context['github_contributions'])}
        
        Provide a recruiter-friendly assessment:
        1. Executive Summary (2-3 sentences)
        2. Key Strengths (3-5 bullet points)
        3. Technical Domains (list)
        4. Ideal Roles (2-3 role types)
        5. Career Trajectory (brief assessment)
        6. Recruiter Notes (any concerns or highlights)
        
        Return as JSON.
        """
        
        response = await self.llm.generate(
            prompt,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.content)
```

## Workflow 2: Network Intelligence Pipeline

**Trigger:** Daily background job
**Goal:** Identify network changes and opportunities

### Pipeline Steps

```
1. Scheduled Job (Daily 2am)
   ↓
2. Identify Changes (Last 24h)
   ├─ New GitHub contributions
   ├─ Job changes (LinkedIn scraping)
   ├─ New connections added
   └─ New profiles matching saved searches
   ↓
3. Analyze Significance
   ├─ Is this person being watched?
   ├─ Is this company being tracked?
   ├─ Does this match any saved search?
   └─ Is this a notable event?
   ↓
4. Generate Notifications
   ├─ "John Doe joined Coinbase"
   ├─ "3 new Solidity devs contributed to Uniswap"
   ├─ "New match for 'Senior Engineers' search"
   └─ "Person you viewed last week updated their profile"
   ↓
5. Batch Notifications
   ├─ Group by importance
   ├─ Deduplicate
   └─ Prioritize
   ↓
6. Deliver
   ├─ In-app notification center
   ├─ Email digest (if enabled)
   └─ Dashboard feed
```

### Code Example

```python
# api/services/network_intelligence_pipeline.py

class NetworkIntelligencePipeline:
    def __init__(self):
        self.db = Database()
        self.notifier = NotificationService()
        
    async def run_daily_analysis(self):
        """Run daily network intelligence"""
        
        # Get changes from last 24h
        changes = await self.detect_changes(hours=24)
        
        notifications = []
        
        # Analyze job changes
        for job_change in changes['job_changes']:
            if await self.is_significant(job_change):
                notifications.append({
                    "type": "job_change",
                    "person": job_change['person'],
                    "company": job_change['new_company'],
                    "message": f"{job_change['person_name']} just joined {job_change['new_company']}"
                })
        
        # Analyze GitHub activity
        for github_activity in changes['github_activity']:
            if await self.is_significant(github_activity):
                notifications.append({
                    "type": "github_activity",
                    "person": github_activity['person'],
                    "repo": github_activity['repo'],
                    "message": f"New contributions to {github_activity['repo']}"
                })
        
        # Check saved searches
        for search in await self.get_active_searches():
            new_matches = await self.check_for_new_matches(search)
            if new_matches:
                notifications.append({
                    "type": "new_match",
                    "search_name": search['name'],
                    "count": len(new_matches),
                    "message": f"{len(new_matches)} new matches for '{search['name']}'"
                })
        
        # Deliver notifications
        await self.notifier.batch_deliver(notifications)
```

## Workflow 3: Outreach Strategy Pipeline

**Trigger:** User clicks "How to Reach" or "Get Outreach Strategy"
**Goal:** Generate ranked contact strategies with personalized templates

### Pipeline Steps

```
1. User Requests Outreach Strategy
   ↓
2. Analyze Contact Methods
   ├─ Has email? → Direct email option
   ├─ Has mutual connections? → Intro option
   ├─ Has LinkedIn? → InMail option
   └─ Has active GitHub? → GitHub comment option
   ↓
3. Calculate Success Probability
   ├─ Email: Base 40%, +10% if verified, +15% if mutual connection mentioned
   ├─ Intro: Base 60%, +20% if close mutual, -10% per degree
   ├─ LinkedIn: Base 15%
   └─ GitHub: Base 10%
   ↓
4. Generate Personalized Templates
   ├─ Extract talking points
   │   ├─ GitHub highlights
   │   ├─ Mutual connections
   │   ├─ Recent activity
   │   └─ Shared interests
   ├─ Generate email (3 variations)
   ├─ Generate intro request
   └─ Generate LinkedIn message
   ↓
5. Optimize Timing
   ├─ Check recent job change (wait if <3 months)
   ├─ Check GitHub activity (good if recent)
   ├─ Check day/time (Tue-Thu, 9-11am best)
   └─ Generate recommendation
   ↓
6. Return Strategy
   {
     "methods": [sorted by probability],
     "templates": {email, intro, linkedin},
     "timing": {when, why},
     "talking_points": [list]
   }
```

### Code Example

```python
# api/services/outreach_strategy_pipeline.py

class OutreachStrategyPipeline:
    def __init__(self):
        self.llm = OpenAI()
        self.db = Database()
        
    async def generate_strategy(self, person_id: str, user_context: dict = None):
        """Generate complete outreach strategy"""
        
        # Get person and network data
        person = await self.db.get_person(person_id)
        network = await self.db.get_network_path(person_id, user_context['user_id'])
        
        # Analyze contact methods
        methods = []
        
        # Method 1: Email
        if person.email:
            template = await self.generate_email_template(person, user_context)
            methods.append({
                "method": "email",
                "probability": self.calculate_email_success(person, network),
                "reasoning": self.explain_email_approach(person, network),
                "template": template,
                "priority": 1
            })
        
        # Method 2: Intro via mutual connection
        if network.shortest_path_length <= 2:
            mutual = network.path[1]
            template = await self.generate_intro_request(mutual, person, user_context)
            methods.append({
                "method": "intro",
                "probability": self.calculate_intro_success(network),
                "reasoning": f"2° connection via {mutual.name}",
                "mutual_connection": mutual,
                "template": template,
                "priority": 1 if not person.email else 2
            })
        
        # Method 3: LinkedIn
        if person.linkedin_url:
            template = await self.generate_linkedin_message(person, user_context)
            methods.append({
                "method": "linkedin",
                "probability": 15,
                "reasoning": "LinkedIn InMail (typically lower response rate)",
                "template": template,
                "priority": 3
            })
        
        # Sort by priority and probability
        methods.sort(key=lambda x: (x['priority'], -x['probability']))
        
        # Generate timing recommendation
        timing = await self.optimize_timing(person)
        
        # Extract talking points
        talking_points = await self.extract_talking_points(person, network)
        
        return {
            "methods": methods,
            "timing": timing,
            "talking_points": talking_points
        }
    
    async def generate_email_template(self, person: Person, context: dict):
        """Generate personalized email template"""
        
        # Extract highlights
        github_highlights = await self.extract_github_highlights(person)
        mutual_connections = await self.get_mutual_connections(person, context['user_id'])
        
        prompt = f"""
        Write a recruiting email for {person.full_name}:
        
        About them:
        - Current: {person.headline}
        - Location: {person.location}
        - GitHub work: {github_highlights}
        - Mutual connections: {mutual_connections}
        
        About the opportunity:
        {context.get('job_description', 'Technical role at a growing company')}
        
        Requirements:
        - Reference specific work (GitHub contributions)
        - Mention mutual connection if exists
        - Be genuine and conversational
        - Explain why we're reaching out
        - Clear call to action
        - 150-200 words
        
        Generate 3 variations:
        1. Professional/Formal tone
        2. Casual/Friendly tone  
        3. Technical/Direct tone
        
        Return as JSON with keys: formal, casual, technical
        """
        
        response = await self.llm.generate(
            prompt,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.content)
```

## Workflow 4: Learning & Feedback Loop

**Trigger:** User provides feedback or completes action
**Goal:** Improve AI models over time

### Pipeline Steps

```
1. User Action/Feedback
   ├─ Thumbs up/down on AI suggestion
   ├─ Candidate added to list
   ├─ Email sent using template
   ├─ Intro request made
   └─ Hire completed
   ↓
2. Log Event
   {
     "user_id": "...",
     "action_type": "email_sent | hire | feedback",
     "context": {...},
     "outcome": "positive | negative | neutral",
     "timestamp": "..."
   }
   ↓
3. Aggregate Patterns (Weekly)
   ├─ Which filters lead to hires?
   ├─ Which email templates get responses?
   ├─ Which intro requests succeed?
   ├─ Which timing works best?
   └─ Which match scores correlate with success?
   ↓
4. Retrain Models (Monthly)
   ├─ Match scoring model
   ├─ Similar candidate recommendations
   ├─ Email template generation
   └─ Timing optimization
   ↓
5. A/B Test Improvements
   ├─ Deploy to 10% of users
   ├─ Measure performance
   ├─ Roll out if better
   └─ Revert if worse
   ↓
6. Update Production Models
```

### Code Example

```python
# api/services/learning_pipeline.py

class LearningPipeline:
    def __init__(self):
        self.feedback_db = FeedbackDatabase()
        self.model_trainer = ModelTrainer()
        
    async def log_feedback(self, feedback: dict):
        """Log user feedback"""
        await self.feedback_db.insert({
            "user_id": feedback['user_id'],
            "interaction_type": feedback['type'],
            "feedback_value": feedback['value'],  # thumbs up/down, 1-5 stars, etc.
            "context": feedback['context'],
            "timestamp": datetime.now()
        })
        
        # Check if we should trigger retraining
        recent_feedback_count = await self.feedback_db.count_recent(days=7)
        if recent_feedback_count > 1000:
            await self.trigger_retraining()
    
    async def log_outcome(self, outcome: dict):
        """Log concrete outcome (hire, response, etc.)"""
        await self.feedback_db.insert({
            "user_id": outcome['user_id'],
            "outcome_type": outcome['type'],  # hire, email_response, etc.
            "candidate_id": outcome['candidate_id'],
            "search_filters": outcome.get('search_filters'),
            "outreach_method": outcome.get('outreach_method'),
            "timestamp": datetime.now()
        })
    
    async def retrain_models(self):
        """Retrain AI models with recent data"""
        
        # Get feedback from last 30 days
        feedback = await self.feedback_db.get_recent(days=30)
        
        # Retrain match scoring
        new_match_model = await self.model_trainer.train_match_scoring(
            feedback.filter(type='hire')
        )
        
        # A/B test new model
        test_results = await self.ab_test_model(
            old_model=self.current_match_model,
            new_model=new_match_model,
            traffic_split=0.1,  # 10% to new model
            duration_days=7
        )
        
        if test_results['new_model_better']:
            await self.deploy_model(new_match_model)
```

## Workflow 5: Batch AI Operations

**Trigger:** User selects multiple candidates
**Goal:** Generate AI insights for multiple candidates efficiently

### Pipeline Steps

```
1. User Selects Multiple Candidates (e.g., 10)
   ↓
2. Queue for Batch Processing
   ├─ Add to job queue
   ├─ Estimate completion time
   └─ Show progress UI
   ↓
3. Process in Batches (5 at a time)
   ├─ Generate summaries in parallel
   ├─ Calculate match scores
   └─ Find similar candidates
   ↓
4. Update Progress
   ├─ "3/10 complete..."
   ├─ "7/10 complete..."
   └─ "10/10 complete!"
   ↓
5. Cache Results
   ↓
6. Notify User
   "✨ AI summaries ready for 10 candidates"
   ↓
7. Display Results
   ├─ Inline in search results
   ├─ Exportable report
   └─ Comparison view
```

### Code Example

```python
# api/services/batch_ai_pipeline.py

class BatchAIPipeline:
    def __init__(self):
        self.job_queue = JobQueue()
        self.profile_analyzer = ProfileAnalysisPipeline()
        
    async def process_batch(self, person_ids: list[str], user_id: str):
        """Process batch of candidates"""
        
        # Create job
        job_id = str(uuid4())
        await self.job_queue.create({
            "job_id": job_id,
            "user_id": user_id,
            "person_ids": person_ids,
            "status": "queued",
            "progress": 0,
            "total": len(person_ids)
        })
        
        # Process in background
        asyncio.create_task(self._process_batch_background(job_id, person_ids))
        
        return {"job_id": job_id, "estimated_time_seconds": len(person_ids) * 3}
    
    async def _process_batch_background(self, job_id: str, person_ids: list[str]):
        """Background batch processing"""
        
        results = []
        batch_size = 5
        
        for i in range(0, len(person_ids), batch_size):
            batch = person_ids[i:i+batch_size]
            
            # Process batch in parallel
            batch_results = await asyncio.gather(*[
                self.profile_analyzer.analyze_profile(person_id)
                for person_id in batch
            ])
            
            results.extend(batch_results)
            
            # Update progress
            await self.job_queue.update(job_id, {
                "progress": len(results),
                "status": "processing"
            })
        
        # Mark complete
        await self.job_queue.update(job_id, {
            "status": "completed",
            "results": results
        })
        
        # Notify user
        await self.notify_user(job_id)
```

## Data Ingestion for Training

### Sources

1. **User Behavior**
   - Profiles viewed
   - Candidates added to lists
   - Searches performed
   - Filters used

2. **Outcomes**
   - Emails sent
   - Responses received
   - Interviews scheduled
   - Hires completed

3. **Feedback**
   - Thumbs up/down
   - Star ratings
   - Explicit corrections
   - Feature usage

### Training Data Structure

```json
{
  "user_id": "...",
  "company_id": "...",
  "interactions": [
    {
      "type": "search",
      "filters": {...},
      "results_count": 150,
      "clicked_candidates": [...]
    },
    {
      "type": "view_profile",
      "candidate_id": "...",
      "time_spent_seconds": 45,
      "actions_taken": ["add_to_list", "copy_email"]
    },
    {
      "type": "outreach",
      "candidate_id": "...",
      "method": "email",
      "template_used": "casual",
      "outcome": "responded",
      "response_time_hours": 12
    },
    {
      "type": "hire",
      "candidate_id": "...",
      "time_to_hire_days": 25,
      "source_search": {...}
    }
  ]
}
```

## Performance Optimization

### Caching Strategy

```python
cache_strategy = {
    "profile_summary": {
        "ttl": 7 * 24 * 3600,  # 7 days
        "invalidate_on": ["profile_update", "github_activity"]
    },
    "match_score": {
        "ttl": 1 * 24 * 3600,  # 1 day
        "invalidate_on": ["search_filters_change"]
    },
    "email_template": {
        "ttl": 0,  # Always fresh (personalized)
        "invalidate_on": []
    },
    "similar_candidates": {
        "ttl": 3 * 24 * 3600,  # 3 days
        "invalidate_on": ["new_profiles_added"]
    }
}
```

### Async Processing

```python
# Long-running tasks should be async
async_tasks = [
    "profile_summary_generation",
    "batch_ai_processing",
    "similar_candidate_search",
    "email_template_generation"
]

# Immediate tasks can be sync
sync_tasks = [
    "match_score_calculation",  # Simple math
    "cache_lookup",
    "filter_validation"
]
```

## Error Handling

### Graceful Degradation

```python
try:
    ai_summary = await generate_ai_summary(person_id)
except OpenAIError as e:
    # Fall back to template-based summary
    ai_summary = generate_template_summary(person)
    log_error(e)
except TimeoutError:
    # Return partial results
    ai_summary = {"error": "Generation timed out, try again"}
```

### Rate Limiting

```python
@rate_limit(calls=100, period=3600)  # 100 calls per hour
async def generate_ai_summary(person_id: str):
    ...
```

## Monitoring & Observability

### Key Metrics

```python
metrics_to_track = {
    "ai_generation_latency": "p50, p95, p99",
    "ai_generation_success_rate": "percentage",
    "cache_hit_rate": "percentage",
    "ai_suggestion_usage_rate": "percentage",
    "user_feedback_scores": "average",
    "model_accuracy": "percentage",
    "cost_per_generation": "dollars"
}
```

### Logging

```python
logger.info("AI summary generation started", {
    "person_id": person_id,
    "user_id": user_id,
    "cache_hit": False
})

logger.info("AI summary generation completed", {
    "person_id": person_id,
    "duration_ms": 2500,
    "tokens_used": 850,
    "cost": 0.002
})
```

## Implementation Priority

1. **Week 1:** Profile Analysis Pipeline (most visible)
2. **Week 2:** Outreach Strategy Pipeline (highest value)
3. **Week 3:** Batch AI Operations (efficiency)
4. **Week 4:** Network Intelligence Pipeline (ongoing value)
5. **Week 5:** Learning & Feedback Loop (long-term improvement)

Each workflow builds on the previous, creating a comprehensive AI-powered recruiting intelligence system.

