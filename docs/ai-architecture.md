# AI Architecture Specification

## Vision

Transform recruiting from "search and reach out" to "AI-powered intelligence gathering and relationship building." The computer does the digging, pattern recognition, and insight generation. The recruiter focuses on high-impact conversations and relationship building.

## Core Philosophy

### AI Does The Digging
- Monitor 155K+ profiles continuously
- Track GitHub activity, job changes, network movements
- Identify patterns humans would miss
- Surface insights proactively

### Recruiter Builds Relationships
- Spend time on conversations, not searches
- Use AI-generated insights for personalized outreach
- Focus on warm introductions over cold emails
- Build long-term network value

## AI System Architecture

### Four Core AI Systems

```
┌─────────────────────────────────────────────────────────┐
│                    User Interface                        │
│         (Search, Profiles, Network, Insights)            │
└──────────────────┬──────────────────────────────────────┘
                   │
    ┌──────────────┴──────────────┐
    │                             │
    ▼                             ▼
┌─────────────┐           ┌─────────────┐
│ AI Research │           │ AI Outreach │
│  Assistant  │           │ Strategist  │
│  (Monitor)  │           │   (Guide)   │
└──────┬──────┘           └──────┬──────┘
       │                         │
       │    ┌──────────────┐     │
       └────► AI Learning  ◄─────┘
            │   System     │
            │ (Improve)    │
            └──────┬───────┘
                   │
                   ▼
            ┌──────────────┐
            │ AI Insights  │
            │    Layer     │
            │  (Suggest)   │
            └──────────────┘
```

## System 1: AI Research Assistant

**Purpose:** Continuous monitoring and pattern detection

### Capabilities

1. **Profile Monitoring**
   - Watch for job changes
   - Track GitHub activity spikes
   - Monitor new contributions
   - Detect skill additions

2. **Network Intelligence**
   - Identify new connections
   - Map company movements (who's hiring)
   - Detect talent clusters
   - Find rising stars

3. **Pattern Recognition**
   - Successful hire patterns
   - Effective search combinations
   - Optimal outreach timing
   - Career trajectory patterns

4. **Proactive Notifications**
   - "New match for your search"
   - "John joined Coinbase (company you're watching)"
   - "3 Solidity devs just contributed to Uniswap"
   - "This candidate updated their GitHub"

### Technical Architecture

```python
# Background worker pattern
class AIResearchAssistant:
    def __init__(self):
        self.profile_monitor = ProfileMonitor()
        self.network_analyzer = NetworkAnalyzer()
        self.pattern_detector = PatternDetector()
        
    def run_continuous(self):
        """Run monitoring loop"""
        while True:
            # Monitor profiles (every 6 hours)
            self.profile_monitor.check_updates()
            
            # Analyze network changes (every 12 hours)
            self.network_analyzer.detect_movements()
            
            # Identify patterns (daily)
            self.pattern_detector.find_patterns()
            
            # Sleep until next cycle
            sleep(6 * 3600)
```

### Data Pipeline

```
1. Data Collection
   ├─ GitHub API polling
   ├─ Profile change detection
   └─ Network graph updates

2. Analysis
   ├─ NLP on profile changes
   ├─ Graph analysis on connections
   └─ Time-series on activity

3. Insight Generation
   ├─ Match candidate patterns
   ├─ Identify anomalies
   └─ Generate notifications

4. Delivery
   ├─ In-app notifications
   ├─ Email digests
   └─ Dashboard updates
```

## System 2: AI Insights Layer

**Purpose:** Context-aware suggestions and intelligence

### Capabilities

1. **Profile Intelligence**
   - Auto-generate career summaries
   - Assess technical depth
   - Identify unique strengths
   - Compare to similar candidates

2. **Match Scoring**
   - Multi-factor relevance scoring
   - Explain why candidates match
   - Predict success probability
   - Rank by fit

3. **Similar Candidates**
   - Vector embeddings of profiles
   - "People also viewed"
   - "Similar to this candidate"
   - Expand search intelligently

4. **Interactive Q&A**
   - "Is this person a senior engineer?"
   - "What's their blockchain experience?"
   - "Would they fit our culture?"
   - Context-aware answers

### Technical Architecture

```python
class AIInsightsLayer:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4o-mini")
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = VectorStore()
        
    async def generate_summary(self, person_id: str):
        """Generate AI profile summary"""
        profile = await self.get_full_profile(person_id)
        
        prompt = f"""
        Analyze this candidate for a technical role:
        - Employment: {profile.employment}
        - GitHub: {profile.github}
        - Network: {profile.network}
        
        Provide: summary, key strengths, ideal roles, concerns
        """
        
        return await self.llm.generate(prompt)
    
    async def calculate_match_score(self, person_id: str, filters: dict):
        """Calculate multi-factor match score"""
        score = 0
        explanations = []
        
        # Email availability (30 points)
        if person.has_email:
            score += 30
            explanations.append("Has verified email")
        
        # GitHub activity (20 points)
        if person.has_github:
            score += 20
            if person.merged_prs > 10:
                score += 10
                explanations.append(f"{person.merged_prs} merged PRs")
        
        # Network distance (-10 per degree)
        distance = await self.get_network_distance(person_id)
        score -= (distance * 10)
        if distance <= 2:
            explanations.append(f"{distance}° connection")
        
        # Experience match
        exp_match = self.match_experience(person, filters)
        score += exp_match * 5
        
        return {
            "score": min(100, max(0, score)),
            "explanations": explanations
        }
    
    async def find_similar(self, person_id: str, limit: int = 10):
        """Find similar candidates using embeddings"""
        # Generate embedding for target person
        embedding = await self.generate_embedding(person_id)
        
        # Search vector store
        similar = await self.vector_store.similarity_search(
            embedding,
            limit=limit
        )
        
        return similar
```

### Vector Embeddings

```python
def generate_profile_embedding(profile):
    """Create vector embedding of profile"""
    
    # Combine key attributes
    text = f"""
    Role: {profile.current_role}
    Skills: {', '.join(profile.skills)}
    Experience: {profile.years_of_experience} years
    Companies: {', '.join(profile.companies)}
    GitHub: {profile.github_languages}
    Projects: {', '.join(profile.notable_repos)}
    """
    
    # Generate embedding
    embedding = openai.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    
    return embedding.data[0].embedding
```

## System 3: AI Outreach Strategist

**Purpose:** Optimize relationship building and introductions

### Capabilities

1. **Outreach Strategy**
   - Ranked contact methods (Email > Intro > LinkedIn)
   - Success probability for each
   - Reasoning for recommendations
   - Timing optimization

2. **Email Personalization**
   - Extract key talking points
   - Reference specific GitHub work
   - Mention mutual connections
   - Adjust tone (formal/casual)

3. **Intro Request Generation**
   - Analyze mutual connection strength
   - Generate personalized intro requests
   - Suggest talking points
   - Track success rates

4. **Timing Optimization**
   - Best time to reach out
   - Factor in recent activity
   - Company hiring cycles
   - Response probability

### Technical Architecture

```python
class AIOutreachStrategist:
    def __init__(self):
        self.llm = OpenAI(model="gpt-4o-mini")
        self.timing_model = TimingOptimizer()
        
    async def generate_strategy(self, person_id: str):
        """Generate ranked outreach strategy"""
        person = await self.get_person(person_id)
        network = await self.get_network_path(person_id)
        
        strategies = []
        
        # Strategy 1: Direct Email
        if person.email:
            success_prob = self.estimate_email_success(person)
            strategies.append({
                "method": "email",
                "probability": success_prob,
                "reasoning": f"Has verified email. {success_prob}% response rate typical.",
                "template": await self.generate_email_template(person)
            })
        
        # Strategy 2: Mutual Connection Intro
        if network.shortest_path_length <= 2:
            mutual = network.path[1]  # Person in between
            success_prob = self.estimate_intro_success(mutual, person)
            strategies.append({
                "method": "intro",
                "probability": success_prob,
                "reasoning": f"2° connection via {mutual.name} (worked together at {mutual.company})",
                "template": await self.generate_intro_request(mutual, person)
            })
        
        # Strategy 3: LinkedIn InMail
        if person.linkedin_url:
            strategies.append({
                "method": "linkedin",
                "probability": 15,  # Typically low
                "reasoning": "LinkedIn InMail as fallback (lower response rate)",
                "url": person.linkedin_url
            })
        
        # Sort by probability
        strategies.sort(key=lambda x: x["probability"], reverse=True)
        
        return strategies
    
    async def generate_email_template(self, person: Person):
        """Generate personalized email"""
        
        # Extract key points
        github_highlights = self.extract_github_highlights(person)
        mutual_connections = await self.get_mutual_connections(person)
        
        prompt = f"""
        Write a personalized recruiting email for {person.name}:
        
        Context:
        - Current role: {person.current_role}
        - Notable GitHub work: {github_highlights}
        - Mutual connections: {mutual_connections}
        - Location: {person.location}
        
        Requirements:
        - Reference specific GitHub contributions
        - Mention mutual connection if exists
        - Be genuine and specific
        - Professional but warm tone
        - 150 words max
        
        Generate 3 variations:
        1. Formal
        2. Casual
        3. Technical
        """
        
        return await self.llm.generate(prompt)
    
    async def optimize_timing(self, person_id: str):
        """Suggest optimal contact timing"""
        person = await self.get_person(person_id)
        
        factors = {
            "recent_job_change": self.check_job_change(person),
            "github_activity": self.check_github_activity(person),
            "company_hiring_cycle": self.check_company_cycle(person),
            "day_of_week": self.optimal_day(),
        }
        
        if factors["recent_job_change"]:
            return {
                "timing": "3-6 months",
                "reason": "Recently changed jobs. Wait for settling period."
            }
        
        if factors["github_activity"] == "high":
            return {
                "timing": "now",
                "reason": "High GitHub activity suggests engagement and visibility."
            }
        
        return {
            "timing": "Tuesday-Thursday, 9-11am",
            "reason": "Optimal response times based on historical data."
        }
```

### Email Template System

```
Template Structure:
1. Hook (personalized)
2. Context (why reaching out)
3. Value prop (opportunity)
4. Call to action (clear next step)
5. Signature

AI Personalization:
- Extract from GitHub: "Saw your work on [repo]"
- Extract from profile: "Your experience with [tech]"
- Reference mutual: "Our mutual connection [name]"
- Location-specific: "We're also based in [city]"
```

## System 4: AI Learning System

**Purpose:** Continuous improvement through feedback

### Capabilities

1. **Feedback Collection**
   - Thumbs up/down on suggestions
   - "This was helpful/not helpful"
   - Correction interface
   - Explicit preferences

2. **Pattern Learning**
   - Which filters lead to hires
   - Which outreach templates work
   - Which timing is optimal
   - Which candidates get added to lists

3. **Model Improvement**
   - Retrain match scoring
   - Update recommendation algorithms
   - Refine email templates
   - Adjust timing models

4. **A/B Testing**
   - Test different approaches
   - Measure outcomes
   - Roll out winners
   - Continuous optimization

### Technical Architecture

```python
class AILearningSystem:
    def __init__(self):
        self.feedback_store = FeedbackStore()
        self.model_trainer = ModelTrainer()
        
    async def collect_feedback(self, interaction: dict):
        """Collect user feedback"""
        feedback = {
            "interaction_id": interaction.id,
            "type": interaction.type,  # search, email, intro, etc.
            "feedback": interaction.feedback,  # thumbs up/down
            "outcome": interaction.outcome,  # hired, responded, etc.
            "context": interaction.context,
            "timestamp": datetime.now()
        }
        
        await self.feedback_store.save(feedback)
        
        # Trigger retraining if enough data
        if await self.should_retrain():
            await self.retrain_models()
    
    async def learn_from_success(self, hire_event: dict):
        """Learn from successful hires"""
        
        # What led to this hire?
        search_filters = await self.get_search_that_found_candidate(hire_event.candidate_id)
        outreach_method = await self.get_outreach_method(hire_event.candidate_id)
        
        # Update models
        await self.model_trainer.positive_example({
            "filters": search_filters,
            "outreach": outreach_method,
            "candidate_profile": hire_event.candidate_profile,
            "company": hire_event.company
        })
    
    async def retrain_models(self):
        """Retrain AI models with new data"""
        
        # Get feedback data
        feedback = await self.feedback_store.get_recent(days=30)
        
        # Retrain match scoring
        await self.retrain_match_scoring(feedback)
        
        # Update email templates
        await self.update_email_templates(feedback)
        
        # Adjust timing models
        await self.adjust_timing_models(feedback)
        
        # A/B test new models
        await self.deploy_with_ab_test()
```

### Company-Specific Training

```python
async def train_company_model(company_id: str):
    """Build company-specific hiring model"""
    
    # Get successful hires
    hires = await db.get_successful_hires(company_id)
    
    # Extract patterns
    patterns = {
        "common_skills": extract_common_skills(hires),
        "typical_experience": calculate_avg_experience(hires),
        "source_companies": find_common_companies(hires),
        "github_patterns": analyze_github_patterns(hires),
        "successful_outreach": analyze_outreach_methods(hires)
    }
    
    # Train custom model
    model = train_custom_match_model(patterns)
    
    # Store for this company
    await model_store.save(company_id, model)
    
    return model
```

## Integration Points

### Real-Time AI

**When:** User actions trigger AI
- View profile → Generate summary
- Search → Calculate match scores
- Add to list → Suggest similar candidates
- Click email → Generate template

### Background AI

**When:** Scheduled jobs, continuous monitoring
- Hourly: Monitor GitHub activity
- Daily: Analyze network changes
- Weekly: Retrain models
- Monthly: Generate insights reports

### On-Demand AI

**When:** User explicitly requests
- "Generate AI summary"
- "Compare candidates"
- "Ask AI a question"
- "Suggest outreach strategy"

## Performance Considerations

### Caching Strategy

```python
# Cache AI results aggressively
cache_ttl = {
    "profile_summary": 7 * 24 * 3600,  # 7 days
    "match_score": 1 * 24 * 3600,      # 1 day
    "email_template": 0,                # No cache (personalized)
    "similar_candidates": 3 * 24 * 3600  # 3 days
}
```

### Cost Optimization

```python
# Token usage optimization
strategies = {
    "use_gpt4o_mini": "Cost effective for most tasks",
    "batch_processing": "Process multiple at once",
    "cache_aggressively": "Avoid duplicate API calls",
    "smart_triggering": "Only generate when needed",
    "user_pays_for_premium": "AI features in paid tier"
}
```

### Rate Limiting

```python
rate_limits = {
    "free_tier": {
        "ai_summaries_per_month": 10,
        "ai_questions_per_day": 5,
        "email_templates_per_week": 3
    },
    "pro_tier": {
        "ai_summaries_per_month": 100,
        "ai_questions_per_day": 50,
        "email_templates_per_week": "unlimited"
    },
    "enterprise": {
        "unlimited": True,
        "custom_training": True
    }
}
```

## Success Metrics

### AI Effectiveness
- AI suggestions used: >40% of searches
- AI outreach templates used: >50%
- AI-suggested candidates added to lists: >30%
- Match score accuracy: >80%

### User Productivity
- Time saved per candidate: 5+ minutes
- Outreach response rate: +25%
- Time to first hire: -30%
- Network growth rate: +50% MoM

### Model Performance
- Match score correlation with hires: >0.7
- Email template response rate: >40%
- Intro request success rate: >60%
- Timing optimization improvement: +20%

## Implementation Roadmap

See `ai-workflows.md` for detailed implementation workflows and data pipelines.

