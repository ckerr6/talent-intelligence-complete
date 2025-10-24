# How to Reach Component Specification

## Overview

The "How to Reach" component is **the most important feature for recruiters**. It transforms the recruiting workflow from "figure out how to contact this person" to "here's the best way to reach them, ranked by success probability, with AI-generated templates ready to go."

This component embodies the AI-first philosophy: the computer does the strategic thinking, the recruiter does the relationship building.

## Vision

### Old Way (Manual)
1. Check if they have email
2. If not, check LinkedIn
3. Try to remember if we have mutual connections
4. Manually search network graph
5. Google for other contact methods
6. Write email from scratch
7. Hope for the best

###New Way (AI-Powered)
1. Click "How to Reach"
2. See ranked strategies with success probabilities
3. Click "Use Email Template"
4. AI-generated, personalized message ready
5. Send with confidence

## Visual Design

### Layout

```
┌────────────────────────────────────────────────────────────────┐
│  How to Reach John Doe                                         │
├────────────────────────────────────────────────────────────────┤
│                                                                │
│  🎯 Recommended Strategy                                       │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  1. Direct Email                            Success: 75%  │ │
│  │     charlie@example.com                                   │ │
│  │                                                            │ │
│  │     💡 AI Insight: Email verified. Recent GitHub          │ │
│  │        activity suggests they're engaged and responsive.  │ │
│  │                                                            │ │
│  │     [📧 Use Email Template]  [📋 Copy Email]             │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  2. Mutual Connection Intro                 Success: 65%  │ │
│  │     Via Sarah Chen (worked at Uniswap)                   │ │
│  │                                                            │ │
│  │     💡 AI Insight: Sarah and John worked together for     │ │
│  │        2 years. Strong connection likely.                 │ │
│  │                                                            │ │
│  │     [🤝 Request Intro]  [👁 View Sarah's Profile]        │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  ┌──────────────────────────────────────────────────────────┐ │
│  │  3. LinkedIn InMail                         Success: 15%  │ │
│  │                                                            │ │
│  │     💡 AI Insight: Use as fallback. Response rates       │ │
│  │        typically low for cold InMails.                    │ │
│  │                                                            │ │
│  │     [in Open LinkedIn]                                    │ │
│  └──────────────────────────────────────────────────────────┘ │
│                                                                │
│  📅 Best Time to Reach                                         │
│  Tuesday-Thursday, 9-11am PST                                 │
│  💡 Based on typical response patterns                        │
│                                                                │
└────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Header

**Typography:**
- "How to Reach [Name]"
- Font: Inter, 24px, weight 600
- Color: gray-900

### 2. Strategy Cards

Each strategy is a card with:

**Structure:**
- Rank number (1, 2, 3)
- Method name
- Success probability (right-aligned)
- Contact details
- AI Insight (with lightbulb icon)
- Action buttons

**Hierarchy by Success Probability:**
- **High (>60%):** Green border-left (4px), emerald-50 background
- **Medium (40-60%):** Blue border-left (4px), blue-50 background
- **Low (<40%):** Gray border-left (4px), gray-50 background

### 3. AI Insights

**Format:**
```
💡 AI Insight: [Reasoning for this strategy]
```

**Examples:**
- "Email verified. Recent GitHub activity suggests engagement."
- "Sarah and John worked together for 2 years at Uniswap."
- "This person recently changed jobs. May be open to conversations."
- "High GitHub activity in relevant technologies."

### 4. Action Buttons

**Primary Actions:**
- Use Email Template
- Request Intro
- Open LinkedIn
- Copy Email

**Button Design:**
- Size: medium
- Icon + text
- Full width on mobile
- Inline on desktop

## Strategy Types

### Strategy 1: Direct Email

**When Available:**
- Person has verified email

**Success Probability Factors:**
- Base: 40%
- +15% if email verified
- +10% if mutual connection mentioned
- +10% if recent GitHub activity
- -20% if recently changed jobs (<3 months)

**Actions:**
1. **Use Email Template**
   - Opens modal with 3 AI-generated variations
   - Personalized with GitHub work, mutual connections
   - Tone options: formal, casual, technical
   
2. **Copy Email**
   - Copies email to clipboard
   - Shows toast: "Email copied!"

**Example AI Insight:**
```
"Email verified. Recent contributions to [repo] show engagement 
in [technology]. Mention this in your outreach."
```

### Strategy 2: Mutual Connection Intro

**When Available:**
- Network distance ≤ 2 degrees
- At least one mutual connection

**Success Probability Factors:**
- Base: 50%
- +20% if worked together at same company
- +15% if contributed to same GitHub repos
- -10% for each degree of separation

**Display:**
```
Via [Mutual Name] ([Connection Context])

Examples:
- "Via Sarah Chen (worked at Uniswap)"
- "Via Mike Johnson (both contributed to Hardhat)"
- "Via 2 mutual connections"
```

**Actions:**
1. **Request Intro**
   - Opens intro request modal
   - AI-generated intro message
   - Fields: To (mutual), About (candidate), Message
   - Preview before sending
   
2. **View Connection Profile**
   - Opens mutual connection's profile
   - Shows relationship strength

**Example AI Insight:**
```
"Sarah and John worked together for 2 years. They both 
contributed to the same codebase. Strong connection likely."
```

### Strategy 3: LinkedIn InMail

**When Available:**
- Person has LinkedIn URL
- (Always available as fallback)

**Success Probability:**
- Base: 15%
- Lower for cold outreach
- Use only as last resort

**Actions:**
1. **Open LinkedIn**
   - Opens LinkedIn profile in new tab
   - Tracks click for learning

**Example AI Insight:**
```
"Use as fallback. InMail response rates typically low 
for cold outreach. Consider waiting for mutual connection."
```

### Strategy 4: GitHub Comment (Bonus)

**When Available:**
- Person has active GitHub
- Recently active on public repos

**Success Probability:**
- Base: 10%
- Technical/niche approach
- Best for open-source focused roles

**Actions:**
1. **View Recent Activity**
   - Shows recent PRs/issues
   - Suggests specific repo to engage with

**Example AI Insight:**
```
"Recently contributed to [repo]. Commenting on their work 
could be a technical ice-breaker."
```

## Timing Recommendations

### Best Time to Reach

**Display:**
```
📅 Best Time to Reach
Tuesday-Thursday, 9-11am PST
💡 Based on typical response patterns
```

**Factors:**
- Day of week (Tue-Thu best)
- Time of day (9-11am, 2-4pm)
- Timezone consideration
- Recent job change (wait 3-6 months)
- GitHub activity patterns

**Examples:**
- "Now is a good time - active GitHub suggests engagement"
- "Wait 2 months - recently changed jobs"
- "Avoid December - holiday season"

## Interactions

### Email Template Modal

**Trigger:** Click "Use Email Template"

**Modal Content:**
```
┌─────────────────────────────────────────────────────┐
│  Email to John Doe                            [✕]   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  [Formal] [Casual] [Technical] ← Tone Selector      │
│                                                     │
│  Subject: [AI-generated subject line]              │
│  ┌─────────────────────────────────────────────┐   │
│  │ Hi John,                                    │   │
│  │                                             │   │
│  │ I came across your work on [specific repo] │   │
│  │ and was impressed by [specific detail].    │   │
│  │                                             │   │
│  │ We're building a team focused on [area]    │   │
│  │ and your experience with [tech] would be   │   │
│  │ valuable.                                   │   │
│  │                                             │   │
│  │ [Mutual connection mention if exists]      │   │
│  │                                             │   │
│  │ Would you be open to a brief conversation? │   │
│  │                                             │   │
│  │ Best,                                       │   │
│  │ [Your name]                                 │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  💡 This email references John's contribution to   │
│     [repo] and mentions your mutual connection.    │
│                                                     │
│  [Edit Before Sending]  [Copy to Clipboard]  [Send]│
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Features:**
- 3 tone variations (tabs)
- Editable text area
- AI explains personalization
- Preview before sending
- Copy to clipboard option
- Direct send (future)

### Intro Request Modal

**Trigger:** Click "Request Intro"

**Modal Content:**
```
┌─────────────────────────────────────────────────────┐
│  Request Introduction                         [✕]   │
├─────────────────────────────────────────────────────┤
│                                                     │
│  To: Sarah Chen                                     │
│  About: John Doe (Senior Engineer)                 │
│                                                     │
│  Message to Sarah:                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ Hey Sarah,                                  │   │
│  │                                             │   │
│  │ I'm looking to connect with John Doe about │   │
│  │ a senior engineering opportunity.           │   │
│  │                                             │   │
│  │ I saw you both worked together at Uniswap  │   │
│  │ - would you be comfortable making an intro?│   │
│  │                                             │   │
│  │ Happy to provide more context if helpful.   │   │
│  │                                             │   │
│  │ Thanks!                                     │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  💡 AI suggests mentioning your Uniswap connection │
│     and John's blockchain experience.              │
│                                                     │
│  [Edit]  [Preview]  [Send Request]                 │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Success Probability Algorithm

```typescript
function calculateSuccessProbability(
  person: Person,
  method: 'email' | 'intro' | 'linkedin' | 'github',
  context: OutreachContext
): number {
  let probability = 0;
  
  switch (method) {
    case 'email':
      probability = 40; // Base
      if (person.email_verified) probability += 15;
      if (context.mutual_connection) probability += 10;
      if (person.recent_github_activity) probability += 10;
      if (person.recently_changed_jobs) probability -= 20;
      break;
      
    case 'intro':
      probability = 50; // Base
      if (context.worked_together) probability += 20;
      if (context.github_collaboration) probability += 15;
      probability -= (context.degrees_of_separation * 10);
      break;
      
    case 'linkedin':
      probability = 15; // Base (low)
      break;
      
    case 'github':
      probability = 10; // Base (very niche)
      if (person.very_active_github) probability += 15;
      break;
  }
  
  return Math.max(0, Math.min(100, probability));
}
```

## Implementation

```tsx
// frontend/src/components/profile/HowToReach.tsx

interface OutreachStrategy {
  rank: number;
  method: 'email' | 'intro' | 'linkedin' | 'github';
  label: string;
  successProbability: number;
  details: string;
  aiInsight: string;
  actions: ActionButton[];
}

interface HowToReachProps {
  personId: string;
  person: Person;
  networkPath?: NetworkPath;
}

export default function HowToReach({
  personId,
  person,
  networkPath
}: HowToReachProps) {
  const [strategies, setStrategies] = useState<OutreachStrategy[]>([]);
  const [loading, setLoading] = useState(true);
  const [emailModalOpen, setEmailModalOpen] = useState(false);
  const [introModalOpen, setIntroModalOpen] = useState(false);
  
  useEffect(() => {
    loadOutreachStrategies();
  }, [personId]);
  
  async function loadOutreachStrategies() {
    setLoading(true);
    try {
      const response = await api.getOutreachStrategy(personId);
      setStrategies(response.strategies);
    } catch (error) {
      toast.error("Failed to load outreach strategies");
    } finally {
      setLoading(false);
    }
  }
  
  if (loading) {
    return <SkeletonStrategies />;
  }
  
  return (
    <Card className="p-6">
      <h3 className="text-2xl font-semibold text-gray-900 mb-6">
        How to Reach {person.full_name}
      </h3>
      
      <div className="space-y-4">
        {strategies.map((strategy) => (
          <StrategyCard
            key={strategy.rank}
            strategy={strategy}
            onUseEmailTemplate={() => setEmailModalOpen(true)}
            onRequestIntro={() => setIntroModalOpen(true)}
          />
        ))}
      </div>
      
      <TimingRecommendation personId={personId} />
      
      <EmailTemplateModal
        isOpen={emailModalOpen}
        onClose={() => setEmailModalOpen(false)}
        person={person}
      />
      
      <IntroRequestModal
        isOpen={introModalOpen}
        onClose={() => setIntroModalOpen(false)}
        person={person}
        mutualConnection={networkPath?.path[1]}
      />
    </Card>
  );
}
```

## Testing Checklist

- [ ] All strategies display correctly
- [ ] Success probabilities calculate accurately
- [ ] AI insights are relevant and helpful
- [ ] Email template modal opens
- [ ] Intro request modal opens
- [ ] Copy email works
- [ ] LinkedIn link opens correctly
- [ ] Timing recommendations make sense
- [ ] Responsive on all devices
- [ ] Loading states show
- [ ] Error handling works
- [ ] Analytics tracking works

## Future Enhancements

1. **Email Tracking**
   - Track if email was opened
   - Track if links were clicked
   - Update success probabilities

2. **Intro Request Tracking**
   - Track intro request status
   - Notify when intro is made
   - Thank mutual connection

3. **Response Rate Learning**
   - Track actual response rates
   - Update probability algorithm
   - Personalize per user/company

4. **Automated Follow-ups**
   - Schedule follow-up reminders
   - AI-generated follow-up templates
   - Smart cadence recommendations

5. **Multi-Channel Sequences**
   - Try email, wait 3 days
   - Then try intro
   - Then try LinkedIn
   - Automated sequences

This component alone can 10x recruiter productivity by eliminating the "how do I reach this person?" problem entirely.

