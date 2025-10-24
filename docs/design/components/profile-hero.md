# Profile Hero Component Specification

## Overview

The Profile Hero is the first thing users see when viewing a candidate profile. It must immediately communicate who this person is, why they matter, and what actions can be taken.

## Visual Design

### Layout

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  ┌──────┐                                                         │
│  │      │  John Doe                                    Match: 87% │
│  │ JD   │  Senior Protocol Engineer                               │
│  │      │  San Francisco, CA • Updated 2 days ago               │
│  └──────┘                                                         │
│                                                                    │
│  [✉ Email]  [+ Add to List]  [🤖 AI Chat]  [⬇ Export]          │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

### Dimensions

- **Height:** 240px (fixed)
- **Max Width:** 1440px (contained)
- **Padding:** 48px vertical, 32px horizontal
- **Background:** White with subtle gradient
- **Shadow:** shadow-lg (0 10px 15px -3px rgba(0, 0, 0, 0.1))

## Components

### 1. Avatar

**Size:** 96px × 96px circle

**Variations:**
- **With Photo:** Display profile photo (future)
- **Initials Fallback:** Gradient background with initials

```tsx
// Gradient based on name hash
const gradients = [
  'from-indigo-400 to-indigo-600',
  'from-cyan-400 to-cyan-600',
  'from-purple-400 to-purple-600',
  'from-emerald-400 to-emerald-600',
];

const gradient = gradients[hashName(name) % gradients.length];
```

**States:**
- Default: Static
- Hover: Subtle scale (1.02x)
- Click: Opens image modal (if photo exists)

### 2. Name

**Typography:**
- Font: Inter
- Size: 48px (display-lg)
- Weight: 700 (Bold)
- Color: gray-900
- Line Height: 60px

**Responsive:**
- Mobile: 36px

**State:**
- Hover: No change (not clickable)

### 3. Current Role / Headline

**Typography:**
- Font: Inter
- Size: 24px (heading-xl)
- Weight: 600 (Semibold)
- Color: gray-700
- Line Height: 32px

**Icon:**
- Briefcase icon (20px) to the left
- Color: gray-500

**Responsive:**
- Mobile: 20px

### 4. Location & Meta Info

**Typography:**
- Font: System
- Size: 16px (body-md)
- Weight: 400 (Regular)
- Color: gray-600
- Line Height: 24px

**Format:**
```
📍 San Francisco, CA • Updated 2 days ago
```

**Elements:**
- Map pin icon (16px)
- Location text
- Separator (•)
- Last updated timestamp

### 5. Match Score Badge

**Position:** Top right corner

**Design:**
```
┌──────────────┐
│ Match  87%   │
│ ⭐⭐⭐⭐⭐   │
└──────────────┘
```

**Variations by Score:**
- **Excellent (80-100%):** 
  - Background: emerald-500
  - Text: white
  - Stars: 5/5
  - Border: 2px emerald-600

- **Good (60-79%):**
  - Background: cyan-500
  - Text: white
  - Stars: 4/5
  - Border: 2px cyan-600

- **Fair (40-59%):**
  - Background: blue-500
  - Text: white
  - Stars: 3/5
  - Border: 2px blue-600

- **Low (<40%):**
  - Background: gray-400
  - Text: white
  - Stars: 2/5
  - Border: 2px gray-500

**Size:**
- Width: 140px
- Height: 72px
- Padding: 12px
- Border Radius: 12px
- Shadow: shadow-md

**Hover:**
- Show tooltip explaining score calculation
- Slight lift effect (translateY(-2px))

### 6. Action Bar

**Layout:** Horizontal flex, gap 12px

**Buttons:** (Left to right)
1. **Email** (if available)
   - Icon: Mail (16px)
   - Text: "Email"
   - Variant: Primary (indigo-600)
   - Action: Open email compose modal

2. **Add to List**
   - Icon: Plus (16px)
   - Text: "Add to List"
   - Variant: Secondary (gray-600)
   - Action: Open list selector

3. **AI Chat**
   - Icon: Sparkles (16px) - animated
   - Text: "AI Chat"
   - Variant: AI gradient (purple-to-pink)
   - Action: Open AI chat panel

4. **Export**
   - Icon: Download (16px)
   - Text: "Export"
   - Variant: Outline
   - Action: Download profile PDF

**Responsive:**
- Mobile: Stack vertically or show only icons with tooltips

## States

### Loading State

```tsx
<div className="animate-pulse">
  <div className="h-24 w-24 rounded-full bg-gray-300" />
  <div className="h-12 w-64 bg-gray-300 rounded" />
  <div className="h-6 w-48 bg-gray-300 rounded" />
</div>
```

### Empty State

If profile data is incomplete:
```tsx
<div className="text-center py-12">
  <p className="text-gray-500">Profile information unavailable</p>
  <Button variant="outline">Refresh Profile</Button>
</div>
```

### Error State

```tsx
<div className="bg-red-50 border border-red-200 rounded-lg p-6">
  <p className="text-red-700">Failed to load profile</p>
  <Button onClick={retry}>Try Again</Button>
</div>
```

## Interactions

### Hover Effects

**Name:**
- No hover effect (not clickable)

**Avatar:**
- Scale: 1.02x
- Shadow: shadow-xl
- Cursor: pointer (if photo exists)

**Match Score Badge:**
- translateY: -2px
- Shadow: shadow-lg
- Show tooltip

**Action Buttons:**
- Standard button hover states
- Slight scale (0.98x) on press

### Click Actions

**Email Button:**
```tsx
onClick={() => {
  if (person.email) {
    openEmailModal({
      to: person.email,
      name: person.full_name,
      templateSuggestions: await getAITemplates(person.person_id)
    });
  } else {
    toast.warning("Email not available. Try mutual connection intro.");
  }
}}
```

**Add to List Button:**
```tsx
onClick={() => {
  openListSelector({
    personId: person.person_id,
    onSuccess: (listName) => {
      toast.success(`Added to ${listName}`);
    }
  });
}}
```

**AI Chat Button:**
```tsx
onClick={() => {
  openAIChatPanel({
    personId: person.person_id,
    context: "profile_view"
  });
}}
```

**Export Button:**
```tsx
onClick={async () => {
  toast.info("Generating PDF...");
  const pdf = await generateProfilePDF(person.person_id);
  downloadFile(pdf, `${person.full_name}_profile.pdf`);
  toast.success("PDF downloaded!");
}}
```

## Responsive Behavior

### Desktop (>1024px)
- Full layout as shown
- All buttons with text
- Large avatar (96px)
- Large typography

### Tablet (768px - 1024px)
- Slightly reduced spacing
- Avatar: 80px
- Name: 40px
- Buttons: Icon + text

### Mobile (<768px)
- Avatar: 72px
- Name: 32px
- Role: 18px
- Stack action buttons vertically
- Or: Show only icons with tooltips
- Match badge moves below name

## Accessibility

### Semantic HTML

```html
<header aria-label="Profile header">
  <div role="img" aria-label="Profile avatar">
    <!-- Avatar -->
  </div>
  <h1>John Doe</h1>
  <h2>Senior Protocol Engineer</h2>
  <div role="status" aria-label="Profile metadata">
    <span>San Francisco, CA</span>
    <span>Updated 2 days ago</span>
  </div>
  <div role="complementary" aria-label="Match score">
    <span>Match score: 87%</span>
  </div>
  <nav aria-label="Profile actions">
    <button aria-label="Send email">Email</button>
    <button aria-label="Add to list">Add to List</button>
    <button aria-label="Chat with AI about this candidate">AI Chat</button>
    <button aria-label="Export profile as PDF">Export</button>
  </nav>
</header>
```

### Keyboard Navigation

- Tab order: Avatar → Buttons (left to right)
- Enter/Space: Activate button
- Escape: Close any opened modals
- Focus visible: 2px outline, 2px offset

### Screen Reader

- Announce name and role immediately
- Announce match score with context
- Announce button purposes clearly
- Announce state changes (added to list, etc.)

## Animation

### Initial Load

```css
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.profile-hero {
  animation: fadeInUp 0.4s ease-out;
}
```

### Match Score Badge

```css
@keyframes pulse {
  0%, 100% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
}

.match-badge {
  animation: pulse 2s ease-in-out infinite;
}
```

## Implementation

```tsx
// frontend/src/components/profile/ProfileHero.tsx

interface ProfileHeroProps {
  person: Person;
  matchScore?: number;
  onEmailClick?: () => void;
  onAddToListClick?: () => void;
  onAIChatClick?: () => void;
  onExportClick?: () => void;
}

export default function ProfileHero({
  person,
  matchScore,
  onEmailClick,
  onAddToListClick,
  onAIChatClick,
  onExportClick
}: ProfileHeroProps) {
  const initials = person.full_name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);
    
  const gradient = getGradientForName(person.full_name);
  
  const scoreColor = matchScore >= 80 ? 'emerald' :
                     matchScore >= 60 ? 'cyan' :
                     matchScore >= 40 ? 'blue' : 'gray';
  
  return (
    <header className="bg-white rounded-xl shadow-lg p-12 mb-6 relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-r from-gray-50 to-white opacity-50" />
      
      {/* Content */}
      <div className="relative flex items-start justify-between">
        <div className="flex items-center space-x-6">
          {/* Avatar */}
          <div className={`w-24 h-24 rounded-full bg-gradient-to-br ${gradient} 
                         flex items-center justify-center text-white text-3xl font-bold
                         hover:scale-105 transition-transform cursor-pointer shadow-lg`}>
            {initials}
          </div>
          
          {/* Info */}
          <div>
            <h1 className="text-5xl font-bold text-gray-900 mb-2">
              {person.full_name}
            </h1>
            {person.headline && (
              <h2 className="text-2xl font-semibold text-gray-700 flex items-center gap-2">
                <Briefcase className="w-5 h-5 text-gray-500" />
                {person.headline}
              </h2>
            )}
            <div className="mt-2 text-gray-600 flex items-center gap-2 text-base">
              {person.location && (
                <>
                  <MapPin className="w-4 h-4" />
                  <span>{person.location}</span>
                </>
              )}
              {person.refreshed_at && (
                <>
                  <span className="text-gray-400">•</span>
                  <span>Updated {formatRelativeTime(person.refreshed_at)}</span>
                </>
              )}
            </div>
          </div>
        </div>
        
        {/* Match Score Badge */}
        {matchScore !== undefined && (
          <MatchScoreBadge score={matchScore} color={scoreColor} />
        )}
      </div>
      
      {/* Action Bar */}
      <div className="mt-8 flex items-center gap-3 relative">
        {person.has_email && (
          <Button
            onClick={onEmailClick}
            icon={<Mail className="w-4 h-4" />}
            variant="primary"
          >
            Email
          </Button>
        )}
        
        <Button
          onClick={onAddToListClick}
          icon={<Plus className="w-4 h-4" />}
          variant="secondary"
        >
          Add to List
        </Button>
        
        <Button
          onClick={onAIChatClick}
          icon={<Sparkles className="w-4 h-4 animate-pulse" />}
          className="bg-gradient-to-r from-purple-600 to-pink-600 text-white hover:from-purple-700 hover:to-pink-700"
        >
          AI Chat
        </Button>
        
        <Button
          onClick={onExportClick}
          icon={<Download className="w-4 h-4" />}
          variant="outline"
        >
          Export
        </Button>
      </div>
    </header>
  );
}
```

## Testing Checklist

- [ ] Displays all profile information correctly
- [ ] Avatar gradient is consistent for same name
- [ ] Match score colors correctly based on value
- [ ] All buttons trigger correct actions
- [ ] Responsive behavior works on all screen sizes
- [ ] Loading state shows while data fetches
- [ ] Error state shows with retry option
- [ ] Keyboard navigation works properly
- [ ] Screen reader announces all content
- [ ] Animations are smooth and non-jarring
- [ ] Hover effects work on all interactive elements
- [ ] Tooltips show helpful information

## Future Enhancements

1. **Profile Photo Support**
   - Upload profile photos
   - Fetch from LinkedIn/GitHub
   - Crop/resize UI

2. **Quick Edit**
   - Inline edit of headline
   - Update location
   - Add tags/notes

3. **Verification Badges**
   - "Email verified"
   - "GitHub verified"
   - "Responded previously"

4. **Social Proof**
   - "Viewed 47 times this month"
   - "Added to 12 lists"
   - "Similar to 3 successful hires"

