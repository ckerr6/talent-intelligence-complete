# Quick Integration Guide - New Design System Components

## 🎯 Goal

Replace the current ProfilePage with the new polished design system components in under 30 minutes.

---

## Step 1: Backup Current ProfilePage (1 minute)

```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/frontend/src/pages
cp ProfilePage.tsx ProfilePage.backup.tsx
```

---

## Step 2: Copy Example Implementation (1 minute)

```bash
cp ProfilePage.example.tsx ProfilePage.tsx
```

That's it! The example implementation is production-ready.

---

## Step 3: Start the Frontend (1 minute)

```bash
cd /Users/charlie.kerr/TI_Complete_Clone/talent-intelligence-complete/frontend
npm run dev
```

Visit: http://localhost:3000

---

## Step 4: Test the New Components (5 minutes)

### Test ProfileHero
1. Navigate to any profile page
2. See the large hero section with avatar, name, match score
3. Test action buttons (Email, Add to List, AI Chat, Export)
4. Verify responsive behavior (resize browser)

### Test TabNavigation
1. Click on different tabs (Overview, Experience, Code, Network, AI Insights)
2. Verify URL updates (`?tab=code`)
3. Test keyboard navigation (Tab, Arrow keys)
4. See badge counts on tabs

### Test StickyActionBar
1. Scroll down the page
2. See the sticky action bar appear at the top
3. See scroll progress indicator
4. Test actions from sticky bar

### Test Toast Notifications
1. Click any action button
2. See toast notification appear
3. Watch auto-dismiss with progress bar
4. Test action buttons in toasts

---

## Step 5: Customize (Optional)

### Update Match Score Algorithm

Edit `ProfilePage.tsx`:

```typescript
const calculateMatchScore = () => {
  if (!profile) return 50;
  
  let score = 0;
  
  // Your custom logic here
  if (profile.emails?.length > 0) score += 30;
  if (profile.github_profile) score += 20;
  // ... add more factors
  
  return Math.min(100, score);
};
```

### Add Custom Actions

```typescript
const handleCustomAction = () => {
  toast.success('Custom action completed!');
  // Your logic here
};

<Button
  onClick={handleCustomAction}
  icon={<YourIcon className="w-4 h-4" />}
  variant="primary"
>
  Custom Action
</Button>
```

### Modify Tabs

```typescript
// Add custom tab
const customTabs = [
  ...tabs,
  {
    id: 'custom',
    label: 'Custom Tab',
    icon: <CustomIcon className="w-4 h-4" />,
    badge: 5,
  },
];

// Add tab content
{activeTab === 'custom' && (
  <div>
    <h2>Custom Tab Content</h2>
  </div>
)}
```

---

## Common Customizations

### Change Colors

Edit `frontend/src/styles/tokens.ts`:

```typescript
primary: {
  // Change from indigo to your brand color
  600: '#YOUR_COLOR_HERE',
  700: '#YOUR_DARKER_COLOR',
}
```

### Change Avatar Gradients

Edit `ProfileHero.tsx`:

```typescript
const gradients = [
  'bg-gradient-to-br from-YOUR-400 to-YOUR-600',
  // Add more gradient options
];
```

### Change Match Score Thresholds

Edit `ProfileHero.tsx`:

```typescript
function getMatchScoreConfig(score?: number) {
  if (score >= 90) return { bgColor: 'bg-emerald-500', stars: 5 }; // Changed from 80
  // ... adjust other thresholds
}
```

### Change Toast Position

Edit your component:

```tsx
<ToastContainer 
  toasts={toast.toasts} 
  position="bottom-right" // Changed from top-right
/>
```

---

## Component Reference

### Button
```tsx
<Button
  variant="primary"           // primary, secondary, outline, ghost, danger, success
  size="md"                   // xs, sm, md, lg, xl
  icon={<Icon />}             // Optional icon
  iconPosition="left"         // left or right
  loading={false}             // Show spinner
  fullWidth={false}           // Full width button
  onClick={handler}
>
  Button Text
</Button>
```

### Badge
```tsx
<Badge
  variant="success"           // default, primary, secondary, success, warning, danger, info
  size="md"                   // xs, sm, md, lg
  icon={<Icon />}             // Optional icon
  rounded={true}              // Pill shape
  onRemove={() => {}}         // Show X button
  onClick={() => {}}          // Make clickable
  pulse={false}               // Pulse animation
>
  Badge Text
</Badge>
```

### Card
```tsx
<Card
  hierarchy="primary"         // primary, secondary, inline
  padding="md"                // none, sm, md, lg
  hover={true}                // Hover lift effect
  loading={false}             // Show loading overlay
  error={null}                // Show error state
  onClick={() => {}}          // Make clickable
>
  Card Content
</Card>
```

### Toast
```tsx
const toast = useToast();

toast.success('Success message');
toast.error('Error message');
toast.warning('Warning message');
toast.info('Info message', {
  duration: 3000,
  action: {
    label: 'Undo',
    onClick: () => console.log('undone'),
  },
});
```

---

## Troubleshooting

### Issue: Imports not found

**Solution:** Make sure you're using the correct paths:
```typescript
import Button from '../components/common/Button';
import { useToast } from '../components/common/Toast';
import ProfileHero from '../components/profile/ProfileHero';
```

### Issue: TypeScript errors

**Solution:** Install missing types:
```bash
npm install --save-dev @types/react @types/react-dom
```

### Issue: Styles not applying

**Solution:** Make sure Tailwind is configured correctly in `tailwind.config.js`:
```javascript
content: [
  "./src/**/*.{js,jsx,ts,tsx}",
],
```

### Issue: Avatar gradients all the same

**Solution:** Check that the `getAvatarGradient` function is using the person's name as the hash seed.

---

## Next Features to Implement

1. **HowToReach Component** - Already spec'd, ready to build
2. **Advanced Filters** - Natural language + AI suggestions
3. **Email Templates** - AI-generated personalized emails
4. **Intro Requests** - Mutual connection workflow
5. **Bulk Actions** - Multi-select and batch operations

---

## Need Help?

1. **See full implementation:** `ProfilePage.example.tsx`
2. **Read design specs:** `docs/design/` directory
3. **Check design tokens:** `frontend/src/styles/tokens.ts`
4. **Review components:** `frontend/src/components/` directory

---

## Success Checklist

- [ ] ProfileHero displays correctly with match score
- [ ] TabNavigation switches between tabs
- [ ] StickyActionBar appears on scroll
- [ ] Toast notifications work
- [ ] Buttons have smooth animations
- [ ] Badges show correct colors
- [ ] Cards have proper hierarchy
- [ ] Responsive design works on mobile
- [ ] Keyboard navigation works
- [ ] All actions trigger toasts

If all checked, you're done! 🎉

---

**Time to complete:** ~30 minutes
**Difficulty:** Easy (copy & paste)
**Impact:** 10x visual polish

