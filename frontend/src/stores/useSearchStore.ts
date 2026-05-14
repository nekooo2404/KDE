import { create } from 'zustand';

interface SearchState {
  query: string;
  isSearching: boolean;
  prediction: any | null;
  history: any[];
  setQuery: (q: string) => void;
  setIsSearching: (val: boolean) => void;
  setPrediction: (data: any) => void;
  clearSearch: () => void;
}

export const useSearchStore = create<SearchState>((set) => ({
  query: '',
  isSearching: false,
  prediction: null,
  history: [],
  setQuery: (query) => set({ query }),
  setIsSearching: (isSearching) => set({ isSearching }),
  setPrediction: (data) => set((state) => ({ 
    prediction: data,
    history: data ? [data, ...state.history.slice(0, 9)] : state.history
  })),
  clearSearch: () => set({ query: '', prediction: null, isSearching: false }),
}));
