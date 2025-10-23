import { create } from 'zustand';
import type { SavedSearch, CandidateList } from '../types';

interface AppState {
  // User preferences
  currentUserId: string | null;
  
  // Lists cache
  lists: CandidateList[];
  selectedListId: string | null;
  
  // Saved searches cache
  savedSearches: SavedSearch[];
  
  // UI state
  sidebarCollapsed: boolean;
  
  // Actions
  setCurrentUser: (userId: string | null) => void;
  setLists: (lists: CandidateList[]) => void;
  setSelectedList: (listId: string | null) => void;
  setSavedSearches: (searches: SavedSearch[]) => void;
  toggleSidebar: () => void;
  
  // List operations
  addList: (list: CandidateList) => void;
  updateList: (listId: string, updates: Partial<CandidateList>) => void;
  removeList: (listId: string) => void;
  
  // Search operations
  addSavedSearch: (search: SavedSearch) => void;
  removeSavedSearch: (searchId: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // Initial state
  currentUserId: null,
  lists: [],
  selectedListId: null,
  savedSearches: [],
  sidebarCollapsed: false,
  
  // Actions
  setCurrentUser: (userId) => set({ currentUserId: userId }),
  
  setLists: (lists) => set({ lists }),
  
  setSelectedList: (listId) => set({ selectedListId: listId }),
  
  setSavedSearches: (searches) => set({ savedSearches: searches }),
  
  toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
  
  // List operations
  addList: (list) => set((state) => ({ lists: [...state.lists, list] })),
  
  updateList: (listId, updates) =>
    set((state) => ({
      lists: state.lists.map((list) =>
        list.list_id === listId ? { ...list, ...updates } : list
      ),
    })),
  
  removeList: (listId) =>
    set((state) => ({
      lists: state.lists.filter((list) => list.list_id !== listId),
      selectedListId: state.selectedListId === listId ? null : state.selectedListId,
    })),
  
  // Search operations
  addSavedSearch: (search) =>
    set((state) => ({ savedSearches: [...state.savedSearches, search] })),
  
  removeSavedSearch: (searchId) =>
    set((state) => ({
      savedSearches: state.savedSearches.filter((search) => search.search_id !== searchId),
    })),
}));

