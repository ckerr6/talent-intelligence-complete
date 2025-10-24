# Typography System Specification

## Overview
Our typography system balances professionalism with readability, using modern font families optimized for technical content and data-dense interfaces.

## Font Families

### Display & Headings: Inter
**Purpose:** Headlines, hero sections, navigation
- **Weight:** 400 (Regular), 500 (Medium), 600 (Semibold), 700 (Bold), 800 (Extrabold)
- **Features:** Variable font, optimized for digital, excellent readability
- **CDN:** Google Fonts or self-hosted

```css
font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

### Body Text: System Font Stack
**Purpose:** Body copy, descriptions, form inputs
- **Rationale:** Performance, native feel, excellent rendering
- **Fallback:** Platform-specific system fonts

```css
font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
```

### Code & Data: JetBrains Mono
**Purpose:** Code snippets, GitHub repos, technical data, IDs
- **Weight:** 400 (Regular), 500 (Medium), 600 (Semibold)
- **Features:** Monospace, optimized for code, ligatures

```css
font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
```

## Type Scale

### Desktop Scale (Base: 16px)

| Token | Size | Line Height | Letter Spacing | Weight | Use Case |
|-------|------|-------------|----------------|--------|----------|
| `display-2xl` | 72px | 90px (1.25) | -0.02em | 800 | Marketing hero |
| `display-xl` | 60px | 72px (1.2) | -0.02em | 800 | Page hero |
| `display-lg` | 48px | 60px (1.25) | -0.01em | 700 | Profile name |
| `display-md` | 36px | 44px (1.22) | -0.01em | 700 | Section headers |
| `display-sm` | 30px | 38px (1.27) | 0 | 600 | Card headers |
| `heading-xl` | 24px | 32px (1.33) | 0 | 600 | Current role, subheadings |
| `heading-lg` | 20px | 28px (1.4) | 0 | 600 | Component headers |
| `heading-md` | 18px | 26px (1.44) | 0 | 600 | Small headers |
| `heading-sm` | 16px | 24px (1.5) | 0 | 600 | Tiny headers |
| `body-xl` | 20px | 30px (1.5) | 0 | 400 | Large body |
| `body-lg` | 18px | 28px (1.56) | 0 | 400 | Intro paragraphs |
| `body-md` | 16px | 24px (1.5) | 0 | 400 | Body text (default) |
| `body-sm` | 14px | 20px (1.43) | 0 | 400 | Secondary text |
| `body-xs` | 12px | 16px (1.33) | 0 | 400 | Labels, captions |
| `code-lg` | 16px | 24px (1.5) | 0 | 400 | Code blocks |
| `code-md` | 14px | 20px (1.43) | 0 | 400 | Inline code |
| `code-sm` | 12px | 16px (1.33) | 0 | 400 | Small code |

### Mobile Scale (Base: 16px)

Reduce display sizes by 20-30% for mobile:

| Token | Desktop | Mobile | Use Case |
|-------|---------|--------|----------|
| `display-lg` | 48px | 36px | Profile name |
| `display-md` | 36px | 28px | Section headers |
| `display-sm` | 30px | 24px | Card headers |
| `heading-xl` | 24px | 20px | Current role |

## Font Weights

| Weight | Value | Usage |
|--------|-------|-------|
| Regular | 400 | Body text, descriptions |
| Medium | 500 | Emphasis, labels |
| Semibold | 600 | Headings, buttons, strong emphasis |
| Bold | 700 | Major headings, hero text |
| Extrabold | 800 | Display text, marketing |

## Semantic Typography

### Profile Page

```typescript
// Profile Name
fontSize: '48px'
lineHeight: '60px'
fontWeight: 700
fontFamily: 'Inter'
color: colors.text.primary

// Current Role
fontSize: '24px'
lineHeight: '32px'
fontWeight: 600
fontFamily: 'Inter'
color: colors.text.secondary

// Body Text
fontSize: '16px'
lineHeight: '24px'
fontWeight: 400
fontFamily: 'System'
color: colors.text.body
```

### Search Results

```typescript
// Candidate Name
fontSize: '18px'
lineHeight: '26px'
fontWeight: 600
fontFamily: 'Inter'
color: colors.text.primary

// Headline
fontSize: '14px'
lineHeight: '20px'
fontWeight: 400
fontFamily: 'System'
color: colors.text.secondary
```

### Buttons

```typescript
// Large Button
fontSize: '16px'
lineHeight: '24px'
fontWeight: 600
fontFamily: 'Inter'

// Medium Button (default)
fontSize: '14px'
lineHeight: '20px'
fontWeight: 600
fontFamily: 'Inter'

// Small Button
fontSize: '12px'
lineHeight: '16px'
fontWeight: 600
fontFamily: 'Inter'
```

## Responsive Typography

### Breakpoints
- **Mobile:** < 640px
- **Tablet:** 640px - 1024px
- **Desktop:** > 1024px
- **Large Desktop:** > 1440px

### Fluid Typography

Use `clamp()` for smooth scaling:

```css
/* Display Large: 36px (mobile) to 48px (desktop) */
font-size: clamp(2.25rem, 1.5rem + 2vw, 3rem);

/* Heading XL: 20px (mobile) to 24px (desktop) */
font-size: clamp(1.25rem, 1rem + 0.5vw, 1.5rem);

/* Body: 14px (mobile) to 16px (desktop) */
font-size: clamp(0.875rem, 0.8125rem + 0.25vw, 1rem);
```

## Text Styles

### Emphasis

```css
/* Strong Emphasis */
font-weight: 600;
color: colors.text.primary;

/* Subtle Emphasis */
font-weight: 500;
color: colors.text.secondary;

/* De-emphasis */
font-weight: 400;
color: colors.text.tertiary;
```

### Special Text

```css
/* Link */
color: colors.primary[600];
text-decoration: none;
font-weight: 500;

/* Link Hover */
text-decoration: underline;
color: colors.primary[700];

/* Code Inline */
font-family: 'JetBrains Mono', monospace;
font-size: 0.875em;
background: colors.gray[100];
padding: 0.125rem 0.375rem;
border-radius: 0.25rem;

/* Label */
font-size: 0.875rem;
font-weight: 600;
letter-spacing: 0.025em;
text-transform: uppercase;
color: colors.text.tertiary;
```

## Line Length

### Optimal Reading Width
- **Body text:** 60-75 characters per line (ch)
- **Wide content:** 75-100 characters
- **Narrow content:** 45-60 characters

```css
/* Content container */
max-width: 65ch; /* ~520-650px depending on font */
```

## Vertical Rhythm

### Spacing Between Elements

Based on 8px grid:

```css
/* Heading to body */
margin-bottom: 1rem; /* 16px */

/* Paragraph spacing */
margin-bottom: 1.5rem; /* 24px */

/* Section spacing */
margin-bottom: 3rem; /* 48px */

/* Component spacing */
margin-bottom: 2rem; /* 32px */
```

## Accessibility

### Minimum Sizes
- **Body text:** Minimum 14px (16px recommended)
- **Buttons:** Minimum 14px
- **Form labels:** Minimum 14px
- **Small text:** Minimum 12px (use sparingly)

### Contrast Requirements
- Body text (16px): 4.5:1 contrast ratio
- Large text (18px+): 3:1 contrast ratio
- Follow color system guidelines

### Focus States
```css
/* Keyboard focus */
outline: 2px solid colors.primary[600];
outline-offset: 2px;
```

## Implementation

See `frontend/src/styles/tokens.ts`:

```typescript
export const typography = {
  display: {
    '2xl': { size: '72px', lineHeight: '90px', weight: 800 },
    xl: { size: '60px', lineHeight: '72px', weight: 800 },
    lg: { size: '48px', lineHeight: '60px', weight: 700 },
    md: { size: '36px', lineHeight: '44px', weight: 700 },
    sm: { size: '30px', lineHeight: '38px', weight: 600 },
  },
  heading: {
    xl: { size: '24px', lineHeight: '32px', weight: 600 },
    lg: { size: '20px', lineHeight: '28px', weight: 600 },
    md: { size: '18px', lineHeight: '26px', weight: 600 },
    sm: { size: '16px', lineHeight: '24px', weight: 600 },
  },
  body: {
    xl: { size: '20px', lineHeight: '30px', weight: 400 },
    lg: { size: '18px', lineHeight: '28px', weight: 400 },
    md: { size: '16px', lineHeight: '24px', weight: 400 },
    sm: { size: '14px', lineHeight: '20px', weight: 400 },
    xs: { size: '12px', lineHeight: '16px', weight: 400 },
  },
};
```

## Usage Guidelines

### DO
✅ Use Inter for headings and important UI elements
✅ Use system fonts for body text (performance)
✅ Use JetBrains Mono for code and technical data
✅ Maintain consistent line heights
✅ Scale typography responsively
✅ Ensure adequate contrast

### DON'T
❌ Mix too many font weights (stick to 400, 600, 700)
❌ Use text smaller than 12px
❌ Ignore line length (keep under 75ch)
❌ Forget mobile scaling
❌ Use color alone to convey meaning
❌ Skip accessibility testing

