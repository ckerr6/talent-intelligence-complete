# Talent Intelligence Platform - Frontend

Modern React + TypeScript frontend for the Talent Intelligence MVP.

## 🎯 Current Status

**Phase 1 Foundation: COMPLETE** ✅

### What's Built

- ✅ React 18 + TypeScript + Vite setup
- ✅ Tailwind CSS for styling
- ✅ React Router for navigation
- ✅ React Query for API state management
- ✅ Zustand for global state
- ✅ Full type definitions for all API entities
- ✅ Complete API service layer with axios
- ✅ Layout components (Header, Sidebar, Layout)
- ✅ Search page with filters and pagination
- ✅ Placeholder pages for Profile, Network, Lists, Analytics

### File Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── layout/
│   │       ├── Header.tsx          ✅ Top navigation bar
│   │       ├── Sidebar.tsx         ✅ Collapsible sidebar with nav
│   │       └── Layout.tsx          ✅ Main layout wrapper
│   ├── pages/
│   │   ├── SearchPage.tsx          ✅ Candidate search with filters
│   │   ├── ProfilePage.tsx         🚧 Placeholder
│   │   ├── NetworkPage.tsx         🚧 Placeholder
│   │   ├── ListsPage.tsx           🚧 Placeholder
│   │   └── AnalyticsPage.tsx       🚧 Placeholder
│   ├── services/
│   │   └── api.ts                  ✅ Complete API client
│   ├── store/
│   │   └── store.ts                ✅ Zustand global state
│   ├── types/
│   │   └── index.ts                ✅ All TypeScript types
│   ├── App.tsx                     ✅ Router setup
│   ├── main.tsx                    ✅ Entry point
│   └── index.css                   ✅ Tailwind + custom styles
├── package.json                    ✅ Dependencies
├── vite.config.ts                  ✅ Vite configuration
├── tsconfig.json                   ✅ TypeScript config
├── tailwind.config.js              ✅ Tailwind config
└── postcss.config.js               ✅ PostCSS config
```

## 🚀 Getting Started

### Prerequisites

- Node.js 18+
- Backend API running on `http://localhost:8000`

### Installation

```bash
cd frontend
npm install
```

### Development

```bash
npm run dev
```

Frontend will run on `http://localhost:3000` with API proxy to port 8000.

### Build

```bash
npm run build
```

Production build output in `dist/` directory.

## 📦 Features

### Current (Phase 1)

**Search & Discovery:**
- Full-text search across people
- Filter by company, location, headline
- Filter by has_email, has_github
- Pagination (50 results per page)
- Responsive design

**Navigation:**
- Collapsible sidebar
- Clean routing between pages
- Breadcrumb-style navigation

**State Management:**
- API response caching with React Query
- Global UI state with Zustand
- Optimistic updates ready

### Coming Next (Phase 2)

**Profile Page:**
- LinkedIn + GitHub unified view
- Full employment timeline
- Contact information display
- GitHub activity and contributions
- "How to Reach" intro pathfinding
- Match scoring display
- Quick actions (add to list, add note, add tag)

**Network Page:**
- Interactive force-directed graph (vis.js)
- 1st/2nd/3rd degree connection visualization
- Company and repo filtering
- Click nodes to navigate
- Path highlighting

**Lists Management:**
- Create/edit/delete lists
- Add/remove candidates
- Bulk operations
- Notes per candidate
- Drag and drop
- Export to CSV

**Analytics Dashboard:**
- Hiring patterns charts
- Talent flow Sankey diagrams
- Technology distribution
- Market intelligence metrics

## 🎨 Design System

### Colors

**Primary (Blue):**
- Used for main actions, links, active states
- `primary-50` to `primary-900`

**Secondary (Purple):**
- Used for secondary actions, badges
- `secondary-50` to `secondary-900`

### Typography

- **Font:** Inter (sans-serif)
- **Sizes:** Tailwind default scale
- **Weights:** 300 (light), 400 (regular), 500 (medium), 600 (semibold), 700 (bold)

### Components

- Cards: White background, shadow, rounded corners
- Buttons: Primary (blue), Secondary (gray outline)
- Inputs: Border on focus, ring effect
- Loading: Spinner animation
- Skeleton: Shimmer effect for loading states

## 🔌 API Integration

All API calls go through `src/services/api.ts`:

```typescript
import api from './services/api';

// Search people
const results = await api.searchPeople(filters, offset, limit);

// Get full profile
const profile = await api.getPersonProfile(personId);

// Network operations
const path = await api.findPath(sourceId, targetId);
const connections = await api.getConnections(personId);

// Lists
const lists = await api.getLists();
await api.addToList(listId, personId, notes);

// Notes & Tags
await api.createNote(personId, noteText);
await api.addTag(personId, tag);
```

## 📊 State Management

### React Query (API State)

Used for all API calls with automatic:
- Caching (5 minute stale time)
- Background refetching
- Error handling
- Loading states

### Zustand (Global UI State)

```typescript
import { useAppStore } from './store/store';

const { lists, selectedListId, sidebarCollapsed } = useAppStore();
const { setLists, toggleSidebar } = useAppStore();
```

Manages:
- Lists cache
- Saved searches
- UI preferences (sidebar collapsed)
- Current user

## 🧪 Testing (TODO)

```bash
# Unit tests
npm run test

# E2E tests
npm run test:e2e
```

## 📝 Code Style

- TypeScript strict mode
- ESLint + Prettier (configured)
- Functional components with hooks
- No prop drilling (use React Query + Zustand)
- Consistent file naming (PascalCase for components)

## 🔜 Next Steps

**Immediate (This Week):**
1. Complete ProfilePage with all sections
2. Implement network graph visualization
3. Build lists management UI
4. Add match scoring display

**Phase 2 (Weeks 2-3):**
5. Analytics dashboard with charts
6. AI match scoring integration
7. Market intelligence visualizations
8. Advanced search filters

**Phase 3 (Week 4):**
9. Polish animations and transitions
10. Mobile responsiveness improvements
11. Keyboard shortcuts
12. Accessibility audit

## 🐛 Known Issues

- None yet (fresh build!)

## 📚 Resources

- [React Query Docs](https://tanstack.com/query/latest)
- [Zustand Docs](https://docs.pmnd.rs/zustand/getting-started/introduction)
- [Tailwind CSS Docs](https://tailwindcss.com/docs)
- [Vite Docs](https://vitejs.dev/)
- [vis-network Docs](https://visjs.github.io/vis-network/docs/network/)

## 🤝 Contributing

1. Create feature branch
2. Build component with TypeScript
3. Add to appropriate page
4. Test with API running
5. Commit with clear message

---

**Last Updated:** October 22, 2025  
**Status:** Phase 1 Complete, Phase 2 Ready to Start

