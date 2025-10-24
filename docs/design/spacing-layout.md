# Spacing & Layout System Specification

## Overview
Our spacing system is based on an 8px grid for consistency, scalability, and mathematical harmony across all components and layouts.

## Base Unit System

### Core Principle
**Base unit:** 8px (0.5rem)

All spacing values are multiples of 8px, creating visual rhythm and consistency.

### Spacing Scale

| Token | Value (px) | Value (rem) | Usage |
|-------|------------|-------------|-------|
| `xs` | 4px | 0.25rem | Tight spacing, icon gaps |
| `sm` | 8px | 0.5rem | Compact elements, badges |
| `md` | 16px | 1rem | Standard spacing, form fields |
| `lg` | 24px | 1.5rem | Section spacing, card padding |
| `xl` | 32px | 2rem | Large sections, page margins |
| `2xl` | 48px | 3rem | Major sections |
| `3xl` | 64px | 4rem | Hero sections |
| `4xl` | 96px | 6rem | Large hero sections |
| `5xl` | 128px | 8rem | Extra large sections |

### Fine-Grained Scale (Use sparingly)

| Token | Value (px) | Value (rem) | Usage |
|-------|------------|-------------|-------|
| `0.5` | 2px | 0.125rem | Hairline gaps |
| `1` | 4px | 0.25rem | Tight spacing |
| `1.5` | 6px | 0.375rem | Between xs and sm |
| `2.5` | 10px | 0.625rem | Between sm and md |
| `3.5` | 14px | 0.875rem | Between md and lg |

## Component Spacing

### Cards

```typescript
// Primary Card
padding: '24px' // lg
gap: '16px' // md

// Secondary Card
padding: '16px' // md
gap: '12px' // Between sm and md

// Compact Card
padding: '12px' // sm + md
gap: '8px' // sm
```

### Buttons

```typescript
// Large Button
paddingX: '24px' // lg
paddingY: '12px' // sm + md
gap: '8px' // sm (icon gap)

// Medium Button (default)
paddingX: '16px' // md
paddingY: '8px' // sm
gap: '8px' // sm

// Small Button
paddingX: '12px' // sm + md
paddingY: '6px' // Between xs and sm
gap: '6px' // xs + sm
```

### Form Fields

```typescript
// Input Field
paddingX: '12px' // sm + md
paddingY: '8px' // sm
marginBottom: '16px' // md

// Label
marginBottom: '8px' // sm

// Field Group
gap: '16px' // md
```

### Lists

```typescript
// List Item
paddingY: '12px' // sm + md
paddingX: '16px' // md
gap: '8px' // sm

// List Item Dense
paddingY: '8px' // sm
paddingX: '12px' // sm + md
```

## Layout Grid

### 12-Column Grid System

```typescript
container: {
  maxWidth: '1440px',
  marginX: 'auto',
  paddingX: { mobile: '16px', tablet: '24px', desktop: '32px' }
}

grid: {
  columns: 12,
  gap: { mobile: '16px', tablet: '24px', desktop: '32px' }
}
```

### Common Column Layouts

```typescript
// Two Column (50/50)
columns: 'md:grid-cols-2'
gap: '32px' // xl

// Three Column (33/33/33)
columns: 'md:grid-cols-3'
gap: '24px' // lg

// Four Column (25/25/25/25)
columns: 'lg:grid-cols-4'
gap: '24px' // lg

// Sidebar Layout (33/67)
columns: 'md:grid-cols-[1fr_2fr]'
gap: '32px' // xl

// Dashboard Layout (25/50/25)
columns: 'lg:grid-cols-[1fr_2fr_1fr]'
gap: '24px' // lg
```

## Responsive Breakpoints

### Breakpoint System

| Name | Min Width | Container Width | Usage |
|------|-----------|-----------------|-------|
| `xs` | 0px | 100% | Mobile portrait |
| `sm` | 640px | 640px | Mobile landscape |
| `md` | 768px | 768px | Tablet |
| `lg` | 1024px | 1024px | Desktop |
| `xl` | 1280px | 1280px | Large desktop |
| `2xl` | 1536px | 1440px | Extra large |

### Responsive Spacing

```typescript
// Padding scales with breakpoint
padding: {
  xs: '16px',   // Mobile
  md: '24px',   // Tablet
  lg: '32px',   // Desktop
  xl: '48px'    // Large desktop
}

// Gap scales with breakpoint
gap: {
  xs: '16px',
  md: '24px',
  lg: '32px'
}
```

## Page Layouts

### Profile Page

```typescript
layout: {
  hero: {
    paddingY: '48px', // 2xl
    paddingX: { mobile: '16px', desktop: '32px' }
  },
  
  actionBar: {
    height: '64px',
    paddingX: '24px',
    gap: '16px'
  },
  
  content: {
    maxWidth: '1440px',
    marginX: 'auto',
    paddingX: { mobile: '16px', desktop: '32px' },
    paddingY: '32px', // xl
    gap: '32px' // xl (between sections)
  },
  
  sidebar: {
    width: '320px', // Fixed on desktop
    gap: '24px' // lg
  }
}
```

### Search Page

```typescript
layout: {
  filters: {
    paddingY: '24px',
    paddingX: '24px',
    gap: '16px'
  },
  
  results: {
    gap: '16px', // md (between cards)
    paddingY: '24px'
  },
  
  resultCard: {
    padding: '24px', // lg
    gap: '16px' // md
  }
}
```

### Dashboard Page

```typescript
layout: {
  header: {
    paddingY: '24px',
    paddingX: '32px',
    marginBottom: '32px'
  },
  
  grid: {
    columns: 'lg:grid-cols-3',
    gap: '24px'
  },
  
  card: {
    padding: '24px',
    gap: '16px'
  }
}
```

## Stack Spacing

### Vertical Stacks

```typescript
// Tight stack (form fields, list items)
gap: '8px' // sm

// Standard stack (content sections)
gap: '16px' // md

// Loose stack (major sections)
gap: '32px' // xl

// Extra loose (page sections)
gap: '48px' // 2xl
```

### Horizontal Stacks

```typescript
// Tight (badges, tags)
gap: '8px' // sm

// Standard (buttons, actions)
gap: '12px' // sm + md

// Loose (navigation items)
gap: '24px' // lg
```

## Z-Index Layers

### Layer System

| Layer | Value | Usage |
|-------|-------|-------|
| `base` | 0 | Default layer |
| `dropdown` | 1000 | Dropdown menus |
| `sticky` | 1100 | Sticky headers |
| `fixed` | 1200 | Fixed elements |
| `modal-backdrop` | 1300 | Modal overlays |
| `modal` | 1400 | Modal content |
| `popover` | 1500 | Popovers, tooltips |
| `toast` | 1600 | Toast notifications |

## White Space Usage

### Content Density Levels

```typescript
// Compact (data tables, dense lists)
padding: '8px',
gap: '4px'

// Standard (default for most components)
padding: '16px',
gap: '16px'

// Comfortable (reading content, forms)
padding: '24px',
gap: '24px'

// Spacious (hero sections, marketing)
padding: '48px',
gap: '32px'
```

## Margins vs Padding

### Guidelines

**Use Padding for:**
- Internal spacing within components
- Clickable area extension
- Visual rhythm within bounded areas

**Use Margin for:**
- Spacing between components
- Layout gaps
- Section separation

**Prefer Gap over Margin:**
- Flexbox and Grid layouts
- More predictable spacing
- Better collapsing behavior

## Accessibility

### Touch Target Sizes

```typescript
// Minimum touch target
minHeight: '44px' // WCAG 2.1 Level AAA
minWidth: '44px'

// Recommended touch target
minHeight: '48px'
minWidth: '48px'

// Comfortable touch target
minHeight: '56px'
minWidth: '56px'
```

### Focus Spacing

```typescript
// Outline offset
outlineOffset: '2px' // Breathing room around focus

// Focus padding
padding: '8px' // Ensure focus ring doesn't clip
```

## Implementation

### Tailwind Config

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    spacing: {
      'xs': '4px',
      'sm': '8px',
      'md': '16px',
      'lg': '24px',
      'xl': '32px',
      '2xl': '48px',
      '3xl': '64px',
      '4xl': '96px',
      '5xl': '128px',
    },
  },
};
```

### TypeScript Tokens

```typescript
// frontend/src/styles/tokens.ts
export const spacing = {
  xs: '4px',
  sm: '8px',
  md: '16px',
  lg: '24px',
  xl: '32px',
  '2xl': '48px',
  '3xl': '64px',
  '4xl': '96px',
  '5xl': '128px',
};

export const layout = {
  maxWidth: {
    content: '65ch',
    page: '1440px',
    modal: '600px',
  },
  breakpoints: {
    sm: '640px',
    md: '768px',
    lg: '1024px',
    xl: '1280px',
    '2xl': '1536px',
  },
};
```

## Usage Guidelines

### DO
✅ Use 8px increments for all spacing
✅ Use gap for flex/grid layouts
✅ Use semantic tokens (xs, sm, md, etc.)
✅ Scale spacing responsively
✅ Maintain consistent touch targets
✅ Follow the grid system

### DON'T
❌ Use arbitrary pixel values
❌ Mix spacing systems
❌ Forget mobile touch targets
❌ Over-complicate layouts
❌ Ignore responsive breakpoints
❌ Use negative margins excessively

## Visual Examples

```
┌─────────────────────────────────────┐
│ Card (padding: 24px)                │
│ ┌─────────────────────────────────┐ │
│ │ Header (marginBottom: 16px)     │ │
│ └─────────────────────────────────┘ │
│                                      │ gap: 16px
│ ┌─────────────────────────────────┐ │
│ │ Content                         │ │
│ └─────────────────────────────────┘ │
│                                      │ gap: 16px
│ ┌─────────────────────────────────┐ │
│ │ Footer                          │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

