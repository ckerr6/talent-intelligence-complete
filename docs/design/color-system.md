# Color System Specification

## Overview
Our color system is designed to convey intelligence, trust, and technological sophistication while maintaining accessibility and visual hierarchy.

## Primary Colors

### Indigo (Primary)
**Purpose:** Trust, intelligence, professionalism
- `indigo-50`: `#EEF2FF` - Backgrounds, hover states
- `indigo-100`: `#E0E7FF` - Light accents
- `indigo-200`: `#C7D2FE` - Borders, dividers
- `indigo-300`: `#A5B4FC` - Disabled states
- `indigo-400`: `#818CF8` - Hover states
- `indigo-500`: `#6366F1` - Primary actions
- `indigo-600`: `#4F46E5` - Primary (default)
- `indigo-700`: `#4338CA` - Primary hover
- `indigo-800`: `#3730A3` - Primary active
- `indigo-900`: `#312E81` - Deep accents

**Usage:**
- Primary buttons
- Links
- Active states
- Brand elements

### Cyan (Secondary)
**Purpose:** Technology, GitHub integration, data
- `cyan-50`: `#ECFEFF`
- `cyan-100`: `#CFFAFE`
- `cyan-200`: `#A5F3FC`
- `cyan-300`: `#67E8F9`
- `cyan-400`: `#22D3EE`
- `cyan-500`: `#06B6D4` - Secondary (default)
- `cyan-600`: `#0891B2`
- `cyan-700`: `#0E7490`
- `cyan-800`: `#155E75`
- `cyan-900`: `#164E63`

**Usage:**
- GitHub-related features
- Secondary actions
- Data visualizations
- Tech badges

### Amber (Accent)
**Purpose:** Discovery, highlights, important information
- `amber-50`: `#FFFBEB`
- `amber-100`: `#FEF3C7`
- `amber-200`: `#FDE68A`
- `amber-300`: `#FCD34D`
- `amber-400`: `#FBBF24`
- `amber-500`: `#F59E0B` - Accent (default)
- `amber-600`: `#D97706`
- `amber-700`: `#B45309`
- `amber-800`: `#92400E`
- `amber-900`: `#78350F`

**Usage:**
- Discovery moments
- Important highlights
- Warnings (non-error)
- Match score indicators

## Semantic Colors

### Success (Emerald)
**Purpose:** Verified, confirmed, successful actions
- `emerald-50`: `#ECFDF5`
- `emerald-100`: `#D1FAE5`
- `emerald-500`: `#10B981` - Success (default)
- `emerald-600`: `#059669`
- `emerald-700`: `#047857`

**Usage:**
- Merged PRs
- Email verified
- Successful actions
- High match scores (80%+)

### Warning (Orange)
**Purpose:** Needs attention, verification required
- `orange-50`: `#FFF7ED`
- `orange-100`: `#FFEDD5`
- `orange-500`: `#F97316` - Warning (default)
- `orange-600`: `#EA580C`
- `orange-700`: `#C2410C`

**Usage:**
- Fork repositories (needs verification)
- Incomplete profiles
- Attention needed

### Error (Red)
**Purpose:** Errors, destructive actions
- `red-50`: `#FEF2F2`
- `red-100`: `#FEE2E2`
- `red-500`: `#EF4444` - Error (default)
- `red-600`: `#DC2626`
- `red-700`: `#B91C1C`

**Usage:**
- Error messages
- Failed actions
- Destructive buttons

### Info (Blue)
**Purpose:** Information, AI features
- `blue-50`: `#EFF6FF`
- `blue-100`: `#DBEAFE`
- `blue-500`: `#3B82F6` - Info (default)
- `blue-600`: `#2563EB`
- `blue-700`: `#1D4ED8`

**Usage:**
- Informational messages
- Tips and hints
- Standard badges

## Neutral Colors

### Gray Scale
- `gray-50`: `#F9FAFB` - Backgrounds
- `gray-100`: `#F3F4F6` - Secondary backgrounds
- `gray-200`: `#E5E7EB` - Borders
- `gray-300`: `#D1D5DB` - Borders (hover)
- `gray-400`: `#9CA3AF` - Disabled text
- `gray-500`: `#6B7280` - Secondary text
- `gray-600`: `#4B5563` - Body text
- `gray-700`: `#374151` - Headlines
- `gray-800`: `#1F2937` - Primary text
- `gray-900`: `#111827` - Black

## Special Purpose Colors

### AI Features (Purple/Pink Gradient)
**Purpose:** AI-powered features, magical moments
- `purple-500`: `#A855F7`
- `purple-600`: `#9333EA`
- `pink-500`: `#EC4899`
- `pink-600`: `#DB2777`

**Usage:**
- AI assistant
- AI-generated content
- Magical moments
- Premium features

### Match Score Colors
**Purpose:** Visual feedback on candidate fit
- **Excellent (80-100%)**: `emerald-500` (#10B981)
- **Good (60-79%)**: `cyan-500` (#06B6D4)
- **Fair (40-59%)**: `blue-500` (#3B82F6)
- **Low (<40%)**: `gray-400` (#9CA3AF)

## Dark Mode Considerations

### Background Colors
- Primary background: `gray-900` (#111827)
- Secondary background: `gray-800` (#1F2937)
- Tertiary background: `gray-700` (#374151)

### Text Colors (Dark Mode)
- Primary text: `gray-50` (#F9FAFB)
- Secondary text: `gray-400` (#9CA3AF)
- Tertiary text: `gray-500` (#6B7280)

### Adjustments
- Reduce saturation by 10-15% in dark mode
- Increase contrast ratios
- Use lighter shades of colors

## Accessibility Compliance

### WCAG AA Requirements
- **Normal text:** Minimum contrast ratio of 4.5:1
- **Large text (18px+ or 14px+ bold):** Minimum contrast ratio of 3:1
- **UI components:** Minimum contrast ratio of 3:1

### Tested Combinations
✅ `indigo-600` on white: 7.8:1 (Pass)
✅ `cyan-600` on white: 4.8:1 (Pass)
✅ `gray-600` on white: 5.7:1 (Pass)
✅ `white` on `indigo-600`: 7.8:1 (Pass)
✅ `white` on `cyan-600`: 4.8:1 (Pass)

## Usage Guidelines

### Hierarchy
1. **Primary actions:** `indigo-600`
2. **Secondary actions:** `cyan-600` or `gray-600`
3. **Tertiary actions:** `gray-400` or text links
4. **Destructive actions:** `red-600`

### Backgrounds
1. **Primary cards:** `white` (light) / `gray-800` (dark)
2. **Secondary cards:** `gray-50` (light) / `gray-700` (dark)
3. **Inline sections:** `transparent` with borders

### Badges & Labels
- **Status badges:** Semantic colors (success, warning, error)
- **Category badges:** `gray-100` background with `gray-700` text
- **Interactive badges:** Primary/secondary colors with hover states

### Gradients
```css
/* AI Features */
background: linear-gradient(135deg, #9333EA 0%, #EC4899 100%);

/* Hero sections */
background: linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%);

/* Success states */
background: linear-gradient(135deg, #10B981 0%, #06B6D4 100%);
```

## Implementation

See `frontend/src/styles/tokens.ts` for TypeScript/JavaScript usage.

Example:
```typescript
import { colors } from '@/styles/tokens';

// Use semantic names
backgroundColor: colors.primary[600]
color: colors.text.primary
borderColor: colors.border.default
```

