import { createAsyncThunk, createSlice } from '@reduxjs/toolkit';
import {
  getFeaturedMovies,
  getTopRatedMovies,
  getTrendingMovies,
  getUpcomingMovies,
} from '../../api/movieService';

// Cache for storing API responses
const apiCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Helper function to handle API calls with caching
export const fetchWithCache = async url => {
  const cacheKey = url;
  const cachedData = apiCache.get(cacheKey);

  if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
    return cachedData.data;
  }

  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  apiCache.set(cacheKey, {
    data,
    timestamp: Date.now(),
  });

  return data;
};

//Async Thunks
export const fetchFeaturedMovies = createAsyncThunk(
  'movies/fetchFeaturedMovies',
  async (_, { rejectWithValue }) => {
    try {
      console.log('Fetching featured movies...');
      const data = await getFeaturedMovies();
      console.log('Featured movies data:', data);
      return data;
    } catch (error) {
      console.error('Error fetching featured movies:', error);
      return rejectWithValue(error.message);
    }
  }
);

export const fetchMoviesByTab = createAsyncThunk(
  'movies/fetchMoviesByTab',
  async ({ tabKey, lang }, { rejectWithValue }) => {
    try {
      let data;
      switch (tabKey) {
        case 'trending':
          data = await getTrendingMovies();
          break;
        case 'topRated':
          data = await getTopRatedMovies();
          break;
        case 'upcoming':
          data = await getUpcomingMovies();
          break;
        default:
          throw new Error(`Invalid tab key: ${tabKey}`);
      }
      return {
        data,
        tabKey,
        lang,
      };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

//Initial State
const initialState = {
  featuredMovies: [],
  moviesByTab: {
    trending: { 'en-US': [], 'vi-VN': [] },
    topRated: { 'en-US': [], 'vi-VN': [] },
    upcoming: { 'en-US': [], 'vi-VN': [] },
  },
  currentTab: 'trending',
  loading: {
    featured: false,
    moviesByTab: false,
  },
  error: {
    featured: null,
    moviesByTab: null,
  },
};

const movieSlice = createSlice({
  name: 'movies',
  initialState,
  reducers: {
    setFeaturedMovies: (state, action) => {
      state.featuredMovies = action.payload;
      state.loading.featured = false;
      state.error.featured = null;
    },
    setMoviesByTab: (state, action) => {
      const { tab, movies } = action.payload;
      state.moviesByTab[tab] = {
        'en-US': movies,
        'vi-VN': movies,
      };
      state.loading.moviesByTab = false;
      state.error.moviesByTab = null;
    },
    setCurrentTab: (state, action) => {
      state.currentTab = action.payload;
    },
    clearCache: () => {
      apiCache.clear();
    },
  },
  extraReducers: builder => {
    builder
      // Featured Movies
      .addCase(fetchFeaturedMovies.pending, state => {
        state.loading.featured = true;
        state.error.featured = null;
      })
      .addCase(fetchFeaturedMovies.fulfilled, (state, action) => {
        state.loading.featured = false;
        state.featuredMovies = action.payload;
      })
      .addCase(fetchFeaturedMovies.rejected, (state, action) => {
        state.loading.featured = false;
        state.error.featured = action.payload;
      })
      // Movies by Tab
      .addCase(fetchMoviesByTab.pending, state => {
        state.loading.moviesByTab = true;
        state.error.moviesByTab = null;
      })
      .addCase(fetchMoviesByTab.fulfilled, (state, action) => {
        state.loading.moviesByTab = false;
        const { data, tabKey, lang } = action.payload;
        state.moviesByTab[tabKey][lang] = data;
      })
      .addCase(fetchMoviesByTab.rejected, (state, action) => {
        state.loading.moviesByTab = false;
        state.error.moviesByTab = action.payload;
      });
  },
});

export const { setFeaturedMovies, setMoviesByTab, setCurrentTab, clearCache } = movieSlice.actions;
export default movieSlice.reducer;
