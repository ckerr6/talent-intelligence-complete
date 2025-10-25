# Frontend - React + TypeScript Application

## Structure

```
frontend/src/
├── pages/               # Top-level route components
│   ├── SearchPage.tsx         # Main search interface
│   ├── ProfilePage.tsx        # Individual profile view
│   ├── NetworkPage.tsx        # Network visualization
│   └── MarketIntelligencePage.tsx  # Analytics dashboard
│
├── components/          # Reusable UI components
│   ├── ai/             # AI-powered features
│   │   ├── AISummaryCard.tsx       # Profile summaries
│   │   ├── AskAIChat.tsx           # Interactive Q&A
│   │   └── FloatingAIAssistant.tsx # Always-available AI helper
│   │
│   ├── github/         # GitHub-specific displays
│   │   ├── GitHubProfileSection.tsx
│   │   └── GitHubContributions.tsx
│   │
│   ├── profile/        # Profile page components
│   │   ├── ProfileHeader.tsx
│   │   ├── EmploymentTimeline.tsx
│   │   └── ContactInfo.tsx
│   │
│   ├── search/         # Search interface components
│   │   ├── SmartFilters.tsx
│   │   ├── SearchResultCard.tsx
│   │   └── NaturalLanguageFilter.tsx
│   │
│   └── common/         # Shared UI components
│       ├── Button.tsx
│       ├── Card.tsx
│       └── LoadingSpinner.tsx
│
├── services/           # API client functions
│   ├── api.ts         # Main API client
│   └── notificationService.ts
│
├── store/             # Global state management (Zustand)
│   └── store.ts
│
├── types/             # TypeScript type definitions
│   └── index.ts
│
└── utils/             # Helper functions
    └── matchScoring.ts
```

## Tech Stack

- **React 18** - UI framework
- **TypeScript** - Type safety (strict mode enabled)
- **Vite** - Build tool & dev server
- **Tailwind CSS** - Styling (with custom design tokens)
- **React Query** - Server state management & caching
- **Zustand** - Client state management
- **Recharts** - Data visualization
- **vis-network** - Network graph visualization

## Adding a New Feature

### 1. Adding a New Page

**Create the page component** (`src/pages/NewPage.tsx`):
```tsx
import { useState, useEffect } from 'react';
import { Layout } from '../components/layout/Layout';

export default function NewPage() {
  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">New Feature</h1>
        {/* Your content */}
      </div>
    </Layout>
  );
}
```

**Add route** in `src/App.tsx`:
```tsx
import NewPage from './pages/NewPage';

// In the router:
<Route path="/new-feature" element={<NewPage />} />
```

### 2. Adding an API Integration

**Add to API service** (`src/services/api.ts`):
```tsx
export const api = {
  // ... existing methods
  
  async getNewData(params: NewDataParams): Promise<NewDataResponse> {
    const response = await fetch(`${API_URL}/api/new-endpoint?${new URLSearchParams(params)}`);
    if (!response.ok) throw new Error('Failed to fetch');
    return response.json();
  },
};
```

**Use with React Query** in component:
```tsx
import { useQuery } from 'react-query';
import { api } from '../services/api';

function MyComponent() {
  const { data, isLoading, error } = useQuery(
    ['newData', params],
    () => api.getNewData(params)
  );
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <div>Error loading data</div>;
  
  return <div>{/* Use data */}</div>;
}
```

### 3. Adding a Reusable Component

**Create component** (`src/components/common/NewComponent.tsx`):
```tsx
import React from 'react';

interface NewComponentProps {
  title: string;
  onAction?: () => void;
}

export const NewComponent: React.FC<NewComponentProps> = ({ title, onAction }) => {
  return (
    <div className="bg-white rounded-lg shadow p-4">
      <h3 className="text-lg font-semibold mb-2">{title}</h3>
      {onAction && (
        <button onClick={onAction} className="btn-primary">
          Action
        </button>
      )}
    </div>
  );
};
```

## Design System

### Colors (Tailwind classes)
- **Primary**: `bg-blue-600 text-white hover:bg-blue-700`
- **Secondary**: `bg-gray-100 text-gray-800 hover:bg-gray-200`
- **Success**: `bg-green-500 text-white`
- **Warning**: `bg-yellow-500 text-white`
- **Error**: `bg-red-500 text-white`

### Common Patterns

**Button:**
```tsx
<button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
  Click Me
</button>
```

**Card:**
```tsx
<div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
  {/* Content */}
</div>
```

**Loading State:**
```tsx
import { LoadingSpinner } from '../components/common/LoadingSpinner';

{isLoading && <LoadingSpinner />}
```

**Empty State:**
```tsx
import { EmptyState } from '../components/common/EmptyState';

{data.length === 0 && (
  <EmptyState
    title="No results found"
    description="Try adjusting your filters"
    action={{ label: "Clear filters", onClick: handleClear }}
  />
)}
```

## State Management

### Global State (Zustand)
Used for UI state that needs to persist across pages:

```tsx
// In store.ts
export const useStore = create<Store>((set) => ({
  user: null,
  setUser: (user) => set({ user }),
}));

// In component
import { useStore } from '../store/store';

function MyComponent() {
  const user = useStore((state) => state.user);
  const setUser = useStore((state) => state.setUser);
  
  // Use user...
}
```

### Server State (React Query)
Used for data from the API:

```tsx
import { useQuery, useMutation, useQueryClient } from 'react-query';

function MyComponent() {
  const queryClient = useQueryClient();
  
  // Fetch data
  const { data } = useQuery('people', api.getPeople);
  
  // Mutate data
  const mutation = useMutation(api.updatePerson, {
    onSuccess: () => {
      queryClient.invalidateQueries('people');
    },
  });
  
  return <div>{/* Use data and mutation */}</div>;
}
```

## Common Tasks

### Fetch and Display Data
```tsx
import { useQuery } from 'react-query';
import { api } from '../services/api';

function PeopleList() {
  const { data, isLoading } = useQuery('people', () => api.getPeople({ limit: 20 }));
  
  if (isLoading) return <LoadingSpinner />;
  
  return (
    <div className="space-y-4">
      {data?.data.map(person => (
        <div key={person.person_id} className="bg-white p-4 rounded-lg shadow">
          <h3>{person.full_name}</h3>
          <p>{person.headline}</p>
        </div>
      ))}
    </div>
  );
}
```

### Handle Form Submission
```tsx
import { useState } from 'react';
import { useMutation } from 'react-query';

function CreatePersonForm() {
  const [formData, setFormData] = useState({ name: '', email: '' });
  
  const mutation = useMutation(api.createPerson, {
    onSuccess: () => {
      alert('Person created!');
      setFormData({ name: '', email: '' });
    },
  });
  
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    mutation.mutate(formData);
  };
  
  return (
    <form onSubmit={handleSubmit}>
      <input
        value={formData.name}
        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
        placeholder="Name"
      />
      <button type="submit" disabled={mutation.isLoading}>
        {mutation.isLoading ? 'Creating...' : 'Create'}
      </button>
    </form>
  );
}
```

### Navigate Between Pages
```tsx
import { useNavigate } from 'react-router-dom';

function MyComponent() {
  const navigate = useNavigate();
  
  return (
    <button onClick={() => navigate('/profile/123')}>
      View Profile
    </button>
  );
}
```

## Development

### Running the Dev Server
```bash
cd frontend
npm install    # First time only
npm run dev    # Start dev server (port 3000)
```

### Building for Production
```bash
npm run build   # Creates dist/ folder
npm run preview # Preview production build
```

### Type Checking
```bash
npm run type-check  # Run TypeScript compiler
```

## API Integration

The frontend talks to the FastAPI backend at `http://localhost:8000`.

**API base URL:** Set in `src/services/api.ts`:
```typescript
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
```

**Making requests:**
```typescript
// GET request
const response = await fetch(`${API_URL}/api/people`);
const data = await response.json();

// POST request
const response = await fetch(`${API_URL}/api/people`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ full_name: 'John Doe' }),
});
```

## TypeScript Types

### Defining Types
```typescript
// In src/types/index.ts
export interface Person {
  person_id: string;
  full_name: string;
  headline?: string;
  location?: string;
  github_username?: string;
}

export interface SearchFilters {
  company?: string;
  location?: string;
  has_github?: boolean;
}
```

### Using Types
```typescript
import { Person, SearchFilters } from '../types';

function MyComponent() {
  const [filters, setFilters] = useState<SearchFilters>({});
  const [people, setPeople] = useState<Person[]>([]);
  
  // ...
}
```

## Styling Best Practices

### Use Tailwind Utilities
```tsx
// Good
<div className="flex items-center gap-4 p-4 bg-white rounded-lg shadow">

// Avoid custom CSS when Tailwind has it
<div style={{ display: 'flex', padding: '16px' }}> // ❌
```

### Responsive Design
```tsx
// Mobile-first approach
<div className="w-full md:w-1/2 lg:w-1/3">
  {/* Full width on mobile, half on tablet, third on desktop */}
</div>
```

### Hover & Focus States
```tsx
<button className="bg-blue-600 hover:bg-blue-700 focus:ring-2 focus:ring-blue-500">
  Button
</button>
```

## Testing

```bash
npm test              # Run tests
npm test -- --watch   # Watch mode
```

Example test:
```typescript
import { render, screen } from '@testing-library/react';
import { ProfileHeader } from './ProfileHeader';

test('renders person name', () => {
  render(<ProfileHeader person={{ full_name: 'John Doe' }} />);
  expect(screen.getByText('John Doe')).toBeInTheDocument();
});
```

## Questions?

- Check existing components for patterns
- Look at `src/services/api.ts` for API methods
- Review `src/types/index.ts` for data structures
- See `.cursorrules` in project root for overall architecture
