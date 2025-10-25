import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import Layout from './components/layout/Layout';
import SearchPage from './pages/SearchPage';
import AdvancedSearchPage from './pages/AdvancedSearchPage';
import ProfilePage from './pages/ProfilePage';
import NetworkPage from './pages/NetworkPage';
import EnhancedNetworkPage from './pages/EnhancedNetworkPage';
import ListsPage from './pages/ListsPage';
import ListDetailPage from './pages/ListDetailPage';
import AnalyticsPage from './pages/AnalyticsPage';
import MarketIntelligencePage from './pages/MarketIntelligencePage';
import NotificationsPage from './pages/NotificationsPage';
import GitHubDeveloperProfile from './pages/github_native/GitHubDeveloperProfile';
import GitHubSearch from './pages/github_native/GitHubSearch';
import EnhancedGitHubProfile from './pages/github_native/EnhancedGitHubProfile';
import GraphReasoningDashboard from './pages/github_native/GraphReasoningDashboard';
import LanguageLeaderboard from './pages/market/LanguageLeaderboard';

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5 * 60 * 1000, // 5 minutes
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Navigate to="/search" replace />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="search/advanced" element={<AdvancedSearchPage />} />
            <Route path="profile/:personId" element={<ProfilePage />} />
            <Route path="network" element={<NetworkPage />} />
            <Route path="network/:personId" element={<NetworkPage />} />
            <Route path="network/enhanced" element={<EnhancedNetworkPage />} />
            <Route path="market" element={<MarketIntelligencePage />} />
            <Route path="lists" element={<ListsPage />} />
            <Route path="lists/:listId" element={<ListDetailPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="github" element={<GitHubSearch />} />
            <Route path="github/:username" element={<GitHubDeveloperProfile />} />
            <Route path="github/:username/enhanced" element={<EnhancedGitHubProfile />} />
            <Route path="graph-reasoning" element={<GraphReasoningDashboard />} />
            <Route path="market/languages" element={<LanguageLeaderboard />} />
            <Route path="*" element={<Navigate to="/search" replace />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;

