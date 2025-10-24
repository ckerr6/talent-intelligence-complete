# Component Hierarchy Specification

## Overview
Visual hierarchy is critical for data-dense applications. Our component hierarchy system creates clear information architecture through visual weight, color, elevation, and spacing.

## Hierarchy Levels

### Level 1: Hero / Primary Content
**Purpose:** Most important information, immediate focus

**Visual Characteristics:**
- Large typography (48px+)
- High contrast colors
- Significant elevation (shadow-lg to shadow-2xl)
- Generous padding (32px+)
- Prominent placement (top of page, center)

**Components:**
- Profile hero section
- Page headers with key metrics
- Primary call-to-action cards
- Match score badges (80%+)

```typescript
// Primary Card
{
  background: 'white',
  shadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  padding: '32px',
  borderRadius: '12px',
  border: '2px solid transparent',
  
  // Hover state
  hover: {
    shadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
    transform: 'translateY(-2px)',
  }
}
```

### Level 2: Secondary Content
**Purpose:** Supporting information, grouped content

**Visual Characteristics:**
- Medium typography (18-24px)
- Moderate contrast
- Subtle elevation (shadow-sm to shadow-md)
- Standard padding (16-24px)
- Section-level placement

**Components:**
- Content sections
- Feature cards
- Tab content areas
- Secondary CTAs

```typescript
// Secondary Card
{
  background: 'gray.50',
  shadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
  padding: '24px',
  borderRadius: '8px',
  border: '1px solid gray.200',
  
  // Hover state
  hover: {
    background: 'white',
    shadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  }
}
```

### Level 3: Inline / List Items
**Purpose:** Repeating elements, dense information

**Visual Characteristics:**
- Small typography (14-16px)
- Lower contrast
- Minimal elevation (borders or dividers)
- Compact padding (12-16px)
- List/grid placement

**Components:**
- Search result cards
- List items
- Table rows
- Badges and tags

```typescript
// Inline Card
{
  background: 'transparent',
  shadow: 'none',
  padding: '16px',
  borderRadius: '6px',
  borderBottom: '1px solid gray.200',
  
  // Hover state
  hover: {
    background: 'gray.50',
  }
}
```

## Visual Weight System

### Typography Weight

```typescript
hierarchy: {
  primary: {
    size: '48px',
    weight: 700,
    color: 'gray.900',
    lineHeight: 1.2,
  },
  secondary: {
    size: '24px',
    weight: 600,
    color: 'gray.800',
    lineHeight: 1.3,
  },
  tertiary: {
    size: '16px',
    weight: 500,
    color: 'gray.700',
    lineHeight: 1.5,
  },
  body: {
    size: '14px',
    weight: 400,
    color: 'gray.600',
    lineHeight: 1.5,
  },
}
```

### Color Weight

```typescript
// Information density by color intensity
emphasis: {
  high: 'gray.900',      // Primary headings
  medium: 'gray.700',    // Secondary headings
  low: 'gray.600',       // Body text
  minimal: 'gray.500',   // Meta information
  subtle: 'gray.400',    // Disabled/secondary
}
```

### Elevation Weight

```typescript
shadows: {
  none: 'none',
  xs: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  sm: '0 1px 3px 0 rgba(0, 0, 0, 0.1)',
  md: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
  lg: '0 10px 15px -3px rgba(0, 0, 0, 0.1)',
  xl: '0 20px 25px -5px rgba(0, 0, 0, 0.1)',
  '2xl': '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
}
```

## Component Patterns

### Profile Page Hierarchy

```
Level 1: Hero Section
├─ Profile name (display-lg, 700)
├─ Current role (heading-xl, 600)
├─ Match score badge (prominent)
└─ Key actions (primary buttons)

Level 2: Content Sections
├─ Section headers (heading-lg, 600)
├─ Content cards (secondary cards)
└─ Stats grids (medium prominence)

Level 3: Details
├─ List items (body-md, 400)
├─ Meta information (body-sm, 400)
└─ Timestamps (body-xs, gray.500)
```

### Search Page Hierarchy

```
Level 1: Search Controls
├─ Search input (large, prominent)
├─ Filter chips (active state)
└─ Result count (heading-xl)

Level 2: Result Cards
├─ Candidate name (heading-md, 600)
├─ Match score (colored badge)
└─ Quick stats (medium prominence)

Level 3: Result Details
├─ Headline (body-md)
├─ Location (body-sm)
└─ Tags/badges (body-xs)
```

## Interactive States

### State Hierarchy

```typescript
states: {
  default: {
    // Base state
  },
  
  hover: {
    // Increase elevation
    // Slight color shift
    // Cursor change
    shadow: '+1 level',
    transform: 'translateY(-2px)',
  },
  
  active: {
    // Pressed state
    // Decrease elevation
    shadow: '-1 level',
    transform: 'scale(0.98)',
  },
  
  focus: {
    // Keyboard focus
    // High contrast outline
    outline: '2px solid primary.600',
    outlineOffset: '2px',
  },
  
  disabled: {
    // Lowest hierarchy
    opacity: 0.5,
    cursor: 'not-allowed',
    color: 'gray.400',
  },
}
```

## Information Density

### Density Levels

**Compact (Dense Lists)**
```typescript
{
  padding: '8px 12px',
  gap: '4px',
  fontSize: '14px',
  lineHeight: 1.4,
}
```

**Standard (Default)**
```typescript
{
  padding: '16px',
  gap: '16px',
  fontSize: '16px',
  lineHeight: 1.5,
}
```

**Comfortable (Reading)**
```typescript
{
  padding: '24px',
  gap: '24px',
  fontSize: '16px',
  lineHeight: 1.6,
}
```

**Spacious (Marketing)**
```typescript
{
  padding: '48px',
  gap: '32px',
  fontSize: '18px',
  lineHeight: 1.7,
}
```

## Content Organization

### Card Anatomy

```
┌─────────────────────────────────────┐
│ [Icon] Header             [Action]  │ ← Primary (Level 1)
├─────────────────────────────────────┤
│                                     │
│ Primary content text goes here      │ ← Body (Level 2)
│ with important information          │
│                                     │
│ ┌─────────┐ ┌─────────┐           │
│ │ Metric  │ │ Metric  │           │ ← Stats (Level 2)
│ └─────────┘ └─────────┘           │
│                                     │
├─────────────────────────────────────┤
│ Meta • Information • Tags           │ ← Meta (Level 3)
└─────────────────────────────────────┘
```

### Section Anatomy

```
┌─────────────────────────────────────┐
│                                     │
│  Section Title                      │ ← Level 1 (heading-lg)
│  Brief description if needed        │ ← Level 2 (body-md)
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Content Card 1              │   │ ← Level 2 (cards)
│  └─────────────────────────────┘   │
│                                     │
│  ┌─────────────────────────────┐   │
│  │ Content Card 2              │   │
│  └─────────────────────────────┘   │
│                                     │
└─────────────────────────────────────┘
```

## Responsive Hierarchy

### Mobile Adjustments

**Simplify Hierarchy:**
- Reduce from 3 levels to 2
- Collapse secondary information
- Stack instead of side-by-side
- Increase tap target sizes

```typescript
mobile: {
  hero: {
    fontSize: '36px',  // Reduced from 48px
    padding: '24px',   // Reduced from 32px
  },
  
  card: {
    padding: '16px',   // Reduced from 24px
    gap: '12px',       // Reduced from 16px
  },
  
  tapTarget: {
    minHeight: '44px', // Minimum
    minWidth: '44px',
  },
}
```

## Accessibility

### Focus Hierarchy

```typescript
// Keyboard navigation order matches visual hierarchy
tabIndex: {
  primary: 0,    // Hero actions, main CTAs
  secondary: 0,  // Section actions
  tertiary: 0,   // Inline actions
  skip: -1,      // Hidden but focusable
  excluded: -1,  // Decorative only
}
```

### Screen Reader Hierarchy

```html
<!-- Proper heading hierarchy -->
<h1>Profile Name</h1>          <!-- Level 1 -->
  <h2>Employment History</h2>  <!-- Level 2 -->
    <h3>Company Name</h3>      <!-- Level 3 -->
```

## Usage Guidelines

### DO
✅ Use consistent hierarchy throughout app
✅ Make primary actions obvious
✅ Group related information
✅ Use elevation purposefully
✅ Maintain clear visual rhythm
✅ Test with real content

### DON'T
❌ Create more than 3 hierarchy levels on one page
❌ Make everything "important"
❌ Use color alone for hierarchy
❌ Forget mobile simplification
❌ Ignore semantic HTML structure
❌ Skip accessibility testing

## Examples

### High Hierarchy (Primary Card)

```tsx
<div className="bg-white rounded-xl shadow-xl p-8 border-2 border-transparent hover:border-primary-500 transition-all">
  <h2 className="text-4xl font-bold text-gray-900 mb-2">
    Primary Heading
  </h2>
  <p className="text-xl text-gray-700">
    Important supporting text
  </p>
</div>
```

### Medium Hierarchy (Secondary Card)

```tsx
<div className="bg-gray-50 rounded-lg shadow-sm p-6 border border-gray-200 hover:bg-white hover:shadow-md transition-all">
  <h3 className="text-2xl font-semibold text-gray-800 mb-2">
    Secondary Heading
  </h3>
  <p className="text-base text-gray-600">
    Supporting content
  </p>
</div>
```

### Low Hierarchy (Inline Item)

```tsx
<div className="py-3 px-4 border-b border-gray-200 hover:bg-gray-50 transition-colors">
  <h4 className="text-base font-medium text-gray-700">
    Item Title
  </h4>
  <p className="text-sm text-gray-500">
    Meta information
  </p>
</div>
```

## Implementation

See `frontend/src/components/common/Card.tsx` for hierarchy variants:

```typescript
interface CardProps {
  hierarchy?: 'primary' | 'secondary' | 'inline';
  // ... other props
}
```

