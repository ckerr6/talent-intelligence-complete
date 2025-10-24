# Advanced Filters Component Specification

## Overview

The Advanced Filters system transforms search from "narrow down 155K profiles manually" to "let AI suggest the perfect combination of filters based on what you're looking for."

This is filter design for the AI era: smart suggestions, natural language input, saved presets, and real-time result previews.

## Vision

### Old Way
- Manually toggle 10+ filter checkboxes
- Type exact company names
- Guess at skill combinations
- No idea how many results until you search
- Lose your filters when you navigate away

### New Way
- Type: "Senior Solidity engineers in SF with 5+ years"
- AI parses and applies filters automatically
- See result count update in real-time
- AI suggests additional filters: "Also try: has_email, merged_prs > 10"
- Save as preset: "Blockchain Senior Engineers"
- Share with team

## Components

### 1. Natural Language Filter Input

**Primary Interface:**
```
┌──────────────────────────────────────────────────────────┐
│  🔍  Describe who you're looking for...                  │
│                                                          │
│  e.g., "Senior Solidity engineers in SF with email"     │
└──────────────────────────────────────────────────────────┘
         ↓ AI parses ↓
┌──────────────────────────────────────────────────────────┐
│  ✓ Understood:                                           │
│    • Role: Senior Engineer                               │
│    • Skills: Solidity                                    │
│    • Location: San Francisco                            │
│    • Requirement: Has email                              │
│                                                          │
│  [Apply Filters]  [Refine]                               │
└──────────────────────────────────────────────────────────┘
```

**Features:**
- Real-time AI parsing
- Show what was understood
- Allow refinement
- Learning from corrections

### 2. Structured Filter Panel

**Layout:**
```
┌──────────────────────────────────────────────────────────┐
│  Filters                         [Clear All] [Save]      │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  💡 AI Suggestions                                       │
│  "Based on similar searches, also try:"                  │
│  [+ has_email] [+ merged_prs > 10] [+ companies: FAANG] │
│                                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                          │
│  Basic Filters                                           │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Company                                           │ │
│  │  [Start typing...                              ▼] │ │
│  │  Selected: Coinbase, Uniswap (×)                   │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Location                                          │ │
│  │  [San Francisco                                 ▼] │ │
│  │  Selected: San Francisco (×), Remote (×)           │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Skills / Technologies                             │ │
│  │  [Search skills...                              ▼] │ │
│  │  Selected: Solidity (×), Rust (×), TypeScript (×)  │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  Advanced Filters                                [▼]    │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Years of Experience                               │ │
│  │  [━━●━━━━━━━━━] 3 - 10 years                       │ │
│  │                                                    │ │
│  │  GitHub Activity                                   │ │
│  │  Merged PRs: [━━━●━━━━━] 10+                      │ │
│  │  Stars Earned: [━━━━●━━━] 50+                     │ │
│  │                                                    │ │
│  │  Network Distance                                  │ │
│  │  ○ Any  ● Direct (1°)  ○ 2°  ○ 3°                 │ │
│  │                                                    │ │
│  │  Requirements                                      │ │
│  │  ☑ Has Email                                       │ │
│  │  ☑ Has GitHub                                      │ │
│  │  ☐ Has LinkedIn                                    │ │
│  │  ☐ Recently Active (30 days)                      │ │
│  └────────────────────────────────────────────────────┘ │
│                                                          │
│  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━    │
│                                                          │
│  Results Preview                                         │
│  📊 ~847 candidates match these filters                 │
│  [Search →]                                              │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

## Filter Types

### 1. Multi-Select Dropdowns

**Use For:**
- Companies
- Locations
- Skills/Technologies
- Job Titles

**Features:**
- Type to search
- Infinite scroll for large lists
- Selected items shown as chips
- Click X to remove
- "Select All" / "Clear All"

**Implementation:**
```tsx
<MultiSelect
  options={companies}
  selected={selectedCompanies}
  onChange={setSelectedCompanies}
  placeholder="Select companies..."
  searchable
  async // Load more as you scroll
/>
```

### 2. Range Sliders

**Use For:**
- Years of experience
- GitHub stats (PRs, stars, repos)
- Company size
- Salary range (future)

**Features:**
- Dual handles (min/max)
- Show current values
- Snap to reasonable increments
- Keyboard accessible

**Implementation:**
```tsx
<RangeSlider
  min={0}
  max={20}
  value={experienceRange}
  onChange={setExperienceRange}
  label="Years of Experience"
  suffix="years"
/>
```

### 3. Checkboxes

**Use For:**
- Boolean filters (has email, has GitHub)
- Multiple optional selections

**Features:**
- Clear labels
- Help tooltips
- Group related checkboxes

### 4. Radio Buttons

**Use For:**
- Mutually exclusive options
- Network distance (Any, 1°, 2°, 3°)

## AI Features

### 1. AI Filter Suggestions

**Trigger:** Based on current filters + viewing patterns

**Display:**
```
💡 AI Suggestions
"Based on similar searches, also try:"
[+ has_email] [+ merged_prs > 10] [+ companies: FAANG]
```

**Logic:**
```typescript
async function generateFilterSuggestions(
  currentFilters: Filters,
  userHistory: SearchHistory
): Promise<FilterSuggestion[]> {
  // Find similar successful searches
  const similar = await findSimilarSearches(currentFilters);
  
  // Extract common filters they used
  const commonFilters = extractCommonFilters(similar);
  
  // Remove already applied filters
  const suggestions = commonFilters.filter(
    f => !isApplied(f, currentFilters)
  );
  
  // Rank by success rate
  return rankBySuccessRate(suggestions);
}
```

**Examples:**
- If filtering for Solidity → Suggest "also try: TypeScript, Rust"
- If filtering for Coinbase → Suggest "also try: Uniswap, Compound"
- If filtering for SF → Suggest "also try: Remote"
- If no email filter → Suggest "has_email for better reachability"

### 2. Natural Language Parsing

**Input:**
```
"Senior Solidity engineers in SF with 5+ years and email"
```

**Parsing Logic:**
```typescript
async function parseNaturalLanguage(input: string): Promise<ParsedFilters> {
  const prompt = `
    Parse this recruiting search into structured filters:
    "${input}"
    
    Extract:
    - seniority_level (junior, mid, senior, staff, principal)
    - skills (programming languages, frameworks)
    - location
    - years_of_experience (range)
    - requirements (has_email, has_github, etc.)
    - companies
    
    Return as JSON.
  `;
  
  const result = await openai.generate(prompt);
  return JSON.parse(result);
}
```

**Output:**
```json
{
  "seniority_level": "senior",
  "skills": ["Solidity"],
  "location": ["San Francisco"],
  "years_of_experience": { "min": 5 },
  "requirements": {
    "has_email": true
  }
}
```

**Show Parsed Result:**
```
✓ Understood:
  • Seniority: Senior
  • Skills: Solidity
  • Location: San Francisco
  • Experience: 5+ years
  • Requirement: Has email

[Apply Filters]  [Refine]
```

### 3. Smart Defaults

**Based on Context:**
- First-time users → Suggest "has_email" by default
- Looking at blockchain profiles → Suggest blockchain companies
- Previously hired from X → Suggest similar to X

### 4. Filter Learning

**Track:**
- Which filters lead to hires
- Which combinations are common
- Which filters rarely help
- User-specific patterns

**Use:**
- Improve AI suggestions
- Reorder filters by usefulness
- Hide rarely-used filters
- Personalize defaults

## Filter Presets

### Saved Searches

**Features:**
- Save current filter combination
- Name and describe preset
- Quick-load presets
- Edit/delete presets
- Share with team

**UI:**
```
┌────────────────────────────────────────────────┐
│  Saved Searches                          [+]   │
├────────────────────────────────────────────────┤
│  ┌──────────────────────────────────────────┐ │
│  │  Senior Blockchain Engineers            │ │
│  │  📊 847 matches • Updated 2 hours ago   │ │
│  │  [Load] [Edit] [Share] [Delete]         │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  Frontend Engineers - FAANG              │ │
│  │  📊 1,243 matches • Updated 1 day ago    │ │
│  │  [Load] [Edit] [Share] [Delete]         │ │
│  └──────────────────────────────────────────┘ │
│                                                │
│  ┌──────────────────────────────────────────┐ │
│  │  ML Engineers with Papers                │ │
│  │  📊 156 matches • Updated 3 days ago     │ │
│  │  [Load] [Edit] [Share] [Delete]         │ │
│  └──────────────────────────────────────────┘ │
└────────────────────────────────────────────────┘
```

### Template Presets

**Pre-built searches:**
- "Blockchain Engineers"
- "Frontend React Developers"
- "Data Scientists with PhDs"
- "Engineering Managers"
- "Product Designers"

## Real-Time Result Preview

### As Filters Change

**Display:**
```
📊 ~847 candidates match these filters
```

**Update:**
- Debounced (300ms after last change)
- Show loading spinner
- Animate count change

**Implementation:**
```typescript
const [resultCount, setResultCount] = useState<number | null>(null);
const [loading, setLoading] = useState(false);

const debouncedFetchCount = useDeferr(async (filters: Filters) => {
  setLoading(true);
  try {
    const count = await api.getFilterCount(filters);
    setResultCount(count);
  } finally {
    setLoading(false);
  }
}, 300);

useEffect(() => {
  debouncedFetchCount(filters);
}, [filters]);
```

**Visual:**
```
Loading: [spinner] Counting matches...
Result:  📊 ~847 candidates match these filters
Empty:   ⚠️  No candidates match. Try removing filters.
```

## Performance

### Filter Count Queries

**Optimize:**
```sql
-- Use COUNT(*) with same filters as main query
-- Add EXPLAIN ANALYZE to check performance
-- Ensure indexes on all filter columns

SELECT COUNT(*) FROM person p
LEFT JOIN github_profile gp ON p.person_id = gp.person_id
WHERE
  (p.location ILIKE ANY($1) OR $1 IS NULL)
  AND (EXISTS (
    SELECT 1 FROM employment e
    WHERE e.person_id = p.person_id
    AND e.company_name = ANY($2)
  ) OR $2 IS NULL)
  AND (gp.total_merged_prs >= $3 OR $3 IS NULL)
  AND (p.email IS NOT NULL OR $4 = FALSE);
```

### Caching

**Cache filter counts:**
```typescript
// Cache for 5 minutes
const cacheKey = `filter_count:${hashFilters(filters)}`;
const cached = await redis.get(cacheKey);

if (cached) return parseInt(cached);

const count = await db.countWithFilters(filters);
await redis.set(cacheKey, count, 'EX', 300);

return count;
```

## Responsive Design

### Desktop
- Full panel with all filters visible
- Side-by-side multi-select dropdowns
- Range sliders with labels

### Tablet
- Collapsible sections
- Single-column layout
- Full-width dropdowns

### Mobile
- Bottom sheet for filters
- One filter at a time
- Large touch targets
- Floating "Show Results" button

## Accessibility

### Keyboard Navigation
- Tab through all inputs
- Arrow keys in dropdowns
- Enter to apply
- Escape to close

### Screen Reader
- Announce filter changes
- Announce result count updates
- Label all inputs clearly

### Focus Management
- Visible focus indicators
- Logical tab order
- Focus trap in modals

## Implementation

```tsx
// frontend/src/components/search/AdvancedFilters.tsx

interface AdvancedFiltersProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
  onSearch: () => void;
}

export default function AdvancedFilters({
  filters,
  onChange,
  onSearch
}: AdvancedFiltersProps) {
  const [naturalLanguageInput, setNaturalLanguageInput] = useState('');
  const [parsing, setParsing] = useState(false);
  const [aiSuggestions, setAISuggestions] = useState<FilterSuggestion[]>([]);
  const [resultCount, setResultCount] = useState<number | null>(null);
  
  // Parse natural language
  async function handleNaturalLanguageParse() {
    setParsing(true);
    try {
      const parsed = await api.parseNaturalLanguage(naturalLanguageInput);
      onChange(parsed);
      toast.success("Filters applied from description");
    } catch (error) {
      toast.error("Couldn't parse input. Try structured filters.");
    } finally {
      setParsing(false);
    }
  }
  
  // Load AI suggestions
  useEffect(() => {
    loadAISuggestions();
  }, [filters]);
  
  async function loadAISuggestions() {
    const suggestions = await api.getFilterSuggestions(filters);
    setAISuggestions(suggestions);
  }
  
  // Count matches
  const debouncedCount = useDebouncedCallback(
    async (f: SearchFilters) => {
      const count = await api.countMatches(f);
      setResultCount(count);
    },
    300
  );
  
  useEffect(() => {
    debouncedCount(filters);
  }, [filters]);
  
  return (
    <Card className="p-6">
      {/* Natural Language Input */}
      <div className="mb-6">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Describe who you're looking for
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="e.g., Senior Solidity engineers in SF with email"
            className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
            value={naturalLanguageInput}
            onChange={(e) => setNaturalLanguageInput(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter') handleNaturalLanguageParse();
            }}
          />
          <Button
            onClick={handleNaturalLanguageParse}
            loading={parsing}
            icon={<Sparkles className="w-4 h-4" />}
          >
            Parse
          </Button>
        </div>
      </div>
      
      {/* AI Suggestions */}
      {aiSuggestions.length > 0 && (
        <AIFilterSuggestions
          suggestions={aiSuggestions}
          onApply={(suggestion) => {
            onChange({ ...filters, ...suggestion.filters });
          }}
        />
      )}
      
      {/* Structured Filters */}
      <div className="space-y-4">
        <MultiSelectFilter
          label="Company"
          options={companies}
          selected={filters.companies}
          onChange={(companies) => onChange({ ...filters, companies })}
        />
        
        <MultiSelectFilter
          label="Location"
          options={locations}
          selected={filters.locations}
          onChange={(locations) => onChange({ ...filters, locations })}
        />
        
        <MultiSelectFilter
          label="Skills"
          options={skills}
          selected={filters.skills}
          onChange={(skills) => onChange({ ...filters, skills })}
        />
        
        <RangeSlider
          label="Years of Experience"
          min={0}
          max={20}
          value={filters.experience_range}
          onChange={(experience_range) => onChange({ ...filters, experience_range })}
        />
        
        <CheckboxGroup
          label="Requirements"
          options={[
            { value: 'has_email', label: 'Has Email' },
            { value: 'has_github', label: 'Has GitHub' },
            { value: 'recently_active', label: 'Recently Active' }
          ]}
          selected={filters.requirements}
          onChange={(requirements) => onChange({ ...filters, requirements })}
        />
      </div>
      
      {/* Result Preview */}
      <div className="mt-6 p-4 bg-blue-50 rounded-lg">
        {resultCount !== null ? (
          <p className="text-blue-900 font-medium">
            📊 ~{resultCount.toLocaleString()} candidates match these filters
          </p>
        ) : (
          <p className="text-blue-700">Counting matches...</p>
        )}
      </div>
      
      {/* Actions */}
      <div className="mt-6 flex gap-3">
        <Button onClick={onSearch} variant="primary" className="flex-1">
          Search
        </Button>
        <Button
          onClick={() => onChange({})}
          variant="outline"
        >
          Clear All
        </Button>
      </div>
    </Card>
  );
}
```

## Testing Checklist

- [ ] Natural language parsing works
- [ ] All filter types work correctly
- [ ] AI suggestions are relevant
- [ ] Result count updates correctly
- [ ] Saved searches work
- [ ] Clear all works
- [ ] Responsive on all devices
- [ ] Keyboard navigation works
- [ ] Screen reader accessible
- [ ] Performance is good (< 300ms)

## Future Enhancements

1. **Visual Query Builder**
   - Drag-and-drop filter construction
   - Visual AND/OR logic
   - Save complex queries

2. **Filter Analytics**
   - Most used filters
   - Most successful combinations
   - Unused filters (hide them)

3. **Collaborative Filters**
   - Share filters with team
   - Team-wide saved searches
   - Comment on search strategies

4. **Smart Alerts**
   - "New match for your search"
   - Daily/weekly digest
   - Push notifications

This filter system transforms search from tedious to intelligent, making recruiters 10x more effective at finding the right candidates.

