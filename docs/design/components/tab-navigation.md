# Tab Navigation Component Specification

## Overview

The Tab Navigation provides organized access to different aspects of a candidate's profile. It creates clear sections while maintaining context and allows users to quickly navigate between Employment, Code, Network, and AI Insights.

## Visual Design

### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Overview  Experience  Code (47)  Network  AI Insights           │
│ ────────                                                         │
└──────────────────────────────────────────────────────────────────┘
```

### Dimensions

- **Height:** 56px
- **Max Width:** Full width (contained by parent)
- **Border Bottom:** 2px solid gray-200
- **Background:** white (sticky)
- **Padding:** 0 (tabs manage their own padding)

## Tab Design

### Individual Tab

**Default State:**
```css
padding: 16px 24px
font-size: 16px
font-weight: 600
color: gray-600
border-bottom: 2px solid transparent
transition: all 0.2s ease
cursor: pointer
```

**Hover State:**
```css
color: gray-900
background: gray-50
```

**Active State:**
```css
color: indigo-600
border-bottom: 2px solid indigo-600
background: transparent
```

**With Badge:**
```
Code (47)
     └─ Badge showing count
```

### Badge Design

**Appearance:**
- Background: gray-200 (inactive), indigo-100 (active)
- Text Color: gray-700 (inactive), indigo-700 (active)
- Size: 20px height, auto width, min 24px
- Padding: 2px 8px
- Border Radius: 10px (pill shape)
- Font Size: 12px
- Font Weight: 600

**Position:**
- Inline with tab text
- 8px gap from text

## Tabs

### 1. Overview

**Content Preview:**
- AI-generated summary (if available)
- Key highlights
- Quick stats
- How to Reach component
- Recent activity

**Badge:**
- None

**Icon:**
- Home (optional)

### 2. Experience

**Content Preview:**
- Visual timeline
- Employment history
- Company info
- Role progression

**Badge:**
- Employment count (e.g., "Experience (5)")

**Icon:**
- Briefcase

### 3. Code

**Content Preview:**
- GitHub stats
- Repository contributions
- PR verification
- Language breakdown

**Badge:**
- Repository count (e.g., "Code (47)")
- Shows "0" if no GitHub

**Icon:**
- Github

**Special Styling:**
- If 0 repos: Muted colors, badge with gray
- If 50+ repos: Green badge, highlight

### 4. Network

**Content Preview:**
- Connection graph
- Mutual connections
- Degrees of separation
- Common companies

**Badge:**
- Connection count (e.g., "Network (23)")
- Or degrees: "2°"

**Icon:**
- Users

### 5. AI Insights

**Content Preview:**
- AI-generated summary
- Code quality analysis
- Career trajectory
- Outreach strategy
- Interactive Q&A

**Badge:**
- "New" if not viewed yet
- None if already viewed

**Icon:**
- Sparkles (animated)

**Special Styling:**
- Gradient background on hover: purple-to-pink
- Sparkle animation on icon

## Interactions

### Click Behavior

```tsx
onClick={(tabId) => {
  // Update URL
  navigate(`/profile/${personId}?tab=${tabId}`);
  
  // Smooth scroll to content
  scrollToTop('smooth');
  
  // Track analytics
  trackEvent('tab_clicked', { tab: tabId });
  
  // Load content if not cached
  if (!contentLoaded[tabId]) {
    loadTabContent(tabId);
  }
}}
```

### Keyboard Navigation

- **Arrow Left/Right:** Navigate between tabs
- **Home:** Go to first tab
- **End:** Go to last tab
- **Enter/Space:** Activate focused tab

### URL State

Tabs should sync with URL:
```
/profile/123?tab=code
/profile/123?tab=network
```

Benefits:
- Shareable links to specific tabs
- Browser back/forward works
- Bookmark specific views

## Responsive Behavior

### Desktop (>1024px)
- All tabs visible
- Full text labels
- Badges visible

### Tablet (768px - 1024px)
- All tabs visible
- Slightly reduced padding
- Badges visible

### Mobile (<768px)
- **Option A: Scrollable tabs**
  - Horizontal scroll
  - Snap to tab positions
  - Scroll indicators on edges

- **Option B: Dropdown**
  - Show current tab + dropdown icon
  - Click to open full menu
  - Selected tab highlighted

**Recommended:** Option A (scrollable)

## States

### Loading State

```tsx
<div className="flex space-x-2 animate-pulse">
  {[1, 2, 3, 4, 5].map(i => (
    <div key={i} className="h-12 w-32 bg-gray-200 rounded" />
  ))}
</div>
```

### Empty State

If profile has no data for certain tabs:
- Overview: Always available
- Experience: Show "No employment history"
- Code: Show "No GitHub profile linked"
- Network: Show "Building network graph..."
- AI Insights: Show "Generate AI insights"

### Error State

```tsx
<div className="text-red-600 p-4">
  Failed to load tab content
  <Button onClick={retry}>Retry</Button>
</div>
```

## Tab Content Transitions

### Slide Animation

```css
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.tab-content {
  animation: slideIn 0.3s ease-out;
}
```

### Fade Animation (Alternative)

```css
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.tab-content {
  animation: fadeIn 0.2s ease-out;
}
```

## Sticky Behavior

### Desktop

```css
.tab-navigation {
  position: sticky;
  top: 64px; /* Below header */
  z-index: 40;
  background: white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

### Mobile

```css
.tab-navigation {
  position: sticky;
  top: 56px; /* Below mobile header */
  z-index: 40;
}
```

## Badge Logic

### Code Tab Badge

```typescript
function getCodeBadgeValue(githubProfile?: GitHubProfile): string | number {
  if (!githubProfile) return 0;
  
  const repoCount = githubProfile.public_repos || 0;
  
  if (repoCount === 0) return 0;
  if (repoCount >= 100) return '99+';
  return repoCount;
}

function getCodeBadgeColor(githubProfile?: GitHubProfile): string {
  if (!githubProfile) return 'gray';
  
  const repoCount = githubProfile.public_repos || 0;
  
  if (repoCount === 0) return 'gray';
  if (repoCount >= 50) return 'emerald';
  if (repoCount >= 10) return 'cyan';
  return 'blue';
}
```

### Network Tab Badge

```typescript
function getNetworkBadge(networkStats?: NetworkStats): string {
  if (!networkStats) return '';
  
  const degree = networkStats.shortest_path_length;
  
  if (degree === 1) return '1°'; // Direct connection
  if (degree === 2) return '2°'; // 2 degrees
  if (degree === 3) return '3°'; // 3 degrees
  
  return String(networkStats.total_connections);
}
```

### AI Insights Badge

```typescript
function getAIInsightsBadge(viewed: boolean, available: boolean): string | null {
  if (!available) return null;
  if (!viewed) return 'New';
  return null;
}
```

## Accessibility

### ARIA Attributes

```html
<div role="tablist" aria-label="Profile sections">
  <button
    role="tab"
    aria-selected="true"
    aria-controls="overview-panel"
    id="overview-tab"
    tabindex="0"
  >
    Overview
  </button>
  
  <button
    role="tab"
    aria-selected="false"
    aria-controls="code-panel"
    id="code-tab"
    tabindex="-1"
  >
    Code
    <span aria-label="47 repositories">47</span>
  </button>
  
  <!-- More tabs -->
</div>

<div
  role="tabpanel"
  aria-labelledby="overview-tab"
  id="overview-panel"
  tabindex="0"
>
  <!-- Tab content -->
</div>
```

### Focus Management

```typescript
function handleTabChange(newTab: string) {
  // Update selected tab
  setActiveTab(newTab);
  
  // Focus the tab panel
  const panel = document.getElementById(`${newTab}-panel`);
  panel?.focus();
  
  // Announce to screen readers
  announceToScreenReader(`Switched to ${newTab} section`);
}
```

## Implementation

```tsx
// frontend/src/components/profile/TabNavigation.tsx

interface Tab {
  id: string;
  label: string;
  badge?: string | number;
  icon?: React.ReactNode;
  color?: string;
}

interface TabNavigationProps {
  activeTab: string;
  onTabChange: (tabId: string) => void;
  tabs: Tab[];
}

export default function TabNavigation({
  activeTab,
  onTabChange,
  tabs
}: TabNavigationProps) {
  const tabListRef = useRef<HTMLDivElement>(null);
  
  const handleKeyDown = (e: KeyboardEvent, currentIndex: number) => {
    let newIndex = currentIndex;
    
    if (e.key === 'ArrowLeft') {
      newIndex = Math.max(0, currentIndex - 1);
    } else if (e.key === 'ArrowRight') {
      newIndex = Math.min(tabs.length - 1, currentIndex + 1);
    } else if (e.key === 'Home') {
      newIndex = 0;
    } else if (e.key === 'End') {
      newIndex = tabs.length - 1;
    } else {
      return;
    }
    
    e.preventDefault();
    onTabChange(tabs[newIndex].id);
  };
  
  return (
    <div
      ref={tabListRef}
      role="tablist"
      className="sticky top-16 z-40 bg-white border-b-2 border-gray-200 shadow-sm"
    >
      <div className="max-w-7xl mx-auto">
        <div className="flex space-x-1 overflow-x-auto scrollbar-hide">
          {tabs.map((tab, index) => {
            const isActive = tab.id === activeTab;
            
            return (
              <button
                key={tab.id}
                role="tab"
                aria-selected={isActive}
                aria-controls={`${tab.id}-panel`}
                id={`${tab.id}-tab`}
                tabIndex={isActive ? 0 : -1}
                onClick={() => onTabChange(tab.id)}
                onKeyDown={(e) => handleKeyDown(e, index)}
                className={cn(
                  'flex items-center gap-2 px-6 py-4 font-semibold text-base',
                  'border-b-2 transition-all duration-200 whitespace-nowrap',
                  isActive ? [
                    'text-indigo-600 border-indigo-600'
                  ] : [
                    'text-gray-600 border-transparent',
                    'hover:text-gray-900 hover:bg-gray-50'
                  ]
                )}
              >
                {tab.icon && (
                  <span className={cn(
                    tab.id === 'ai-insights' && 'animate-pulse'
                  )}>
                    {tab.icon}
                  </span>
                )}
                
                <span>{tab.label}</span>
                
                {tab.badge !== undefined && tab.badge !== null && (
                  <span className={cn(
                    'inline-flex items-center justify-center',
                    'min-w-[24px] h-5 px-2 rounded-full',
                    'text-xs font-semibold',
                    isActive ? [
                      'bg-indigo-100 text-indigo-700'
                    ] : [
                      'bg-gray-200 text-gray-700'
                    ],
                    tab.color === 'emerald' && isActive && 'bg-emerald-100 text-emerald-700'
                  )}>
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      </div>
    </div>
  );
}
```

## Usage Example

```tsx
// In ProfilePage component

const tabs = [
  {
    id: 'overview',
    label: 'Overview',
    icon: <Home className="w-4 h-4" />
  },
  {
    id: 'experience',
    label: 'Experience',
    icon: <Briefcase className="w-4 h-4" />,
    badge: profile.employment?.length || 0
  },
  {
    id: 'code',
    label: 'Code',
    icon: <Github className="w-4 h-4" />,
    badge: profile.github_profile?.public_repos || 0,
    color: profile.github_profile?.public_repos >= 50 ? 'emerald' : undefined
  },
  {
    id: 'network',
    label: 'Network',
    icon: <Users className="w-4 h-4" />,
    badge: networkStats?.total_connections || ''
  },
  {
    id: 'ai-insights',
    label: 'AI Insights',
    icon: <Sparkles className="w-4 h-4" />,
    badge: !aiInsightsViewed ? 'New' : undefined
  }
];

<TabNavigation
  activeTab={activeTab}
  onTabChange={(tabId) => {
    setActiveTab(tabId);
    navigate(`?tab=${tabId}`);
  }}
  tabs={tabs}
/>
```

## Testing Checklist

- [ ] All tabs render correctly
- [ ] Active tab is highlighted
- [ ] Badges show correct values
- [ ] Click navigation works
- [ ] Keyboard navigation works (arrow keys)
- [ ] URL updates on tab change
- [ ] Direct URL navigation works
- [ ] Responsive behavior correct
- [ ] Sticky positioning works
- [ ] Screen reader announces tab changes
- [ ] Focus management correct
- [ ] Animations smooth
- [ ] Content loads correctly for each tab

## Future Enhancements

1. **Tab Reordering**
   - Drag and drop to reorder
   - Persist user preferences

2. **Tab Customization**
   - Hide/show tabs
   - Rename tabs

3. **Tab Groups**
   - Group related tabs
   - Collapsible groups

4. **Quick Actions in Tabs**
   - Right-click menu
   - Quick export
   - Quick share

