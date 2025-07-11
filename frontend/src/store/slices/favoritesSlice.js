import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getFavoriteMoviesAPI,
  addToFavoritesAPI,
  removeFromFavoritesAPI,
} from '../../api/profileService';

// Async thunks
export const loadFavorites = createAsyncThunk(
  'favorites/loadFavorites',
  async (userId, { rejectWithValue }) => {
    try {
      console.log('🔍 Loading favorites for user:', userId);
      const response = await getFavoriteMoviesAPI(userId);
      console.log('✅ Favorites loaded successfully:', response);
      return response.results || response;
    } catch (error) {
      console.error('❌ Failed to load favorites:', error);
      return rejectWithValue(error.error || 'Failed to load favorites');
    }
  }
);

export const addToFavorites = createAsyncThunk(
  'favorites/addToFavorites',
  async ({ movieId, movieData }, { rejectWithValue }) => {
    try {
      console.log('🔍 Adding to favorites:', { movieId, movieData });
      const response = await addToFavoritesAPI(movieId);
      console.log('✅ Added to favorites successfully:', response);
      return {
        ...response,
        movie_id: movieId,
        movie_title: movieData?.title,
        movie_poster: movieData?.poster_url,
        created_at: new Date().toISOString(),
      };
    } catch (error) {
      console.error('❌ Failed to add to favorites:', error);
      return rejectWithValue(error.error || 'Failed to add to favorites');
    }
  }
);

export const removeFromFavorites = createAsyncThunk(
  'favorites/removeFromFavorites',
  async ({ movieId, favoriteId }, { getState, rejectWithValue }) => {
    try {
      console.log('🔍 Removing from favorites:', { movieId, favoriteId });

      // If favoriteId is not provided, find it from state
      if (!favoriteId) {
        const state = getState().favorites;
        const favoriteRecord = state.items.find(fav => (fav.movie_id || fav.movie?.id) === movieId);
        favoriteId = favoriteRecord?.id;
        console.log('🔍 Found favoriteId from state:', favoriteId, 'for movieId:', movieId);
        console.log('Current state items:', state.items);
      }

      if (!favoriteId) {
        console.error('❌ Favorite record not found for movieId:', movieId);
        return rejectWithValue('Favorite record not found');
      }

      await removeFromFavoritesAPI(favoriteId);
      console.log('✅ Removed from favorites successfully');
      return { movieId, favoriteId };
    } catch (error) {
      console.error('❌ Failed to remove from favorites:', error);
      return rejectWithValue(error.error || 'Failed to remove from favorites');
    }
  }
);

const initialState = {
  items: [],
  favoriteIds: new Set(),
  favoriteRecordIds: new Map(), // Map of movieId -> favoriteId
  loading: false,
  loadingMovies: new Set(), // Track loading state for individual movies
  error: null,
  initialized: false,
};

const favoritesSlice = createSlice({
  name: 'favorites',
  initialState,
  reducers: {
    clearError: state => {
      state.error = null;
    },
    clearFavorites: state => {
      state.items = [];
      state.favoriteIds = new Set();
      state.favoriteRecordIds = new Map();
      state.loadingMovies = new Set();
      state.initialized = false;
    },
    // Optimistic updates
    optimisticAddFavorite: (state, action) => {
      const { movieId, movieData } = action.payload;
      console.log('🔄 Optimistic add favorite:', { movieId, movieData });
      if (!state.favoriteIds.has(movieId)) {
        state.favoriteIds.add(movieId);
        state.loadingMovies.add(movieId); // Add to loading set
        const tempId = `temp-${movieId}`;
        state.favoriteRecordIds.set(movieId, tempId);
        state.items.push({
          id: tempId,
          movie_id: movieId,
          movie_title: movieData?.title,
          movie_poster: movieData?.poster_url,
          created_at: new Date().toISOString(),
          _isOptimistic: true,
        });
      }
    },
    optimisticRemoveFavorite: (state, action) => {
      const { movieId } = action.payload;
      console.log('🔄 Optimistic remove favorite:', { movieId });
      state.favoriteIds.delete(movieId);
      state.favoriteRecordIds.delete(movieId);
      state.loadingMovies.add(movieId); // Add to loading set
      state.items = state.items.filter(item => (item.movie_id || item.movie?.id) !== movieId);
    },
  },
  extraReducers: builder => {
    builder
      // Load favorites
      .addCase(loadFavorites.pending, state => {
        console.log('🔄 Loading favorites...');
        state.loading = true;
        state.error = null;
      })
      .addCase(loadFavorites.fulfilled, (state, action) => {
        console.log('✅ Favorites loaded:', action.payload);
        state.loading = false;
        state.items = action.payload;
        state.favoriteIds = new Set(action.payload.map(fav => fav.movie_id || fav.movie?.id));
        state.favoriteRecordIds = new Map(
          action.payload.map(fav => [fav.movie_id || fav.movie?.id, fav.id])
        );
        state.initialized = true;
      })
      .addCase(loadFavorites.rejected, (state, action) => {
        console.error('❌ Load favorites failed:', action.payload);
        state.loading = false;
        state.error = action.payload;
      })

      // Add to favorites
      .addCase(addToFavorites.pending, state => {
        console.log('🔄 Adding to favorites...');
        state.loading = true;
        state.error = null;
      })
      .addCase(addToFavorites.fulfilled, (state, action) => {
        console.log('✅ Add to favorites fulfilled:', action.payload);
        state.loading = false;
        const favorite = action.payload;
        const movieId = favorite.movie_id;

        // Remove optimistic entry if exists
        state.items = state.items.filter(item => !item._isOptimistic || item.movie_id !== movieId);

        // Add real entry
        if (!state.favoriteIds.has(movieId)) {
          state.favoriteIds.add(movieId);
          state.favoriteRecordIds.set(movieId, favorite.id);
          state.items.push(favorite);
        }
      })
      .addCase(addToFavorites.rejected, (state, action) => {
        console.error('❌ Add to favorites failed:', action.payload);
        state.loading = false;
        state.error = action.payload;

        // Revert optimistic update
        const movieId = action.meta.arg.movieId;
        state.favoriteIds.delete(movieId);
        state.favoriteRecordIds.delete(movieId);
        state.items = state.items.filter(item => !item._isOptimistic || item.movie_id !== movieId);
      })

      // Remove from favorites
      .addCase(removeFromFavorites.pending, state => {
        console.log('🔄 Removing from favorites...');
        state.loading = true;
        state.error = null;
      })
      .addCase(removeFromFavorites.fulfilled, (state, action) => {
        console.log('✅ Remove from favorites fulfilled:', action.payload);
        state.loading = false;
        const { movieId } = action.payload;
        state.favoriteIds.delete(movieId);
        state.favoriteRecordIds.delete(movieId);
        state.items = state.items.filter(item => (item.movie_id || item.movie?.id) !== movieId);
      })
      .addCase(removeFromFavorites.rejected, (state, action) => {
        console.error('❌ Remove from favorites failed:', action.payload);
        state.loading = false;
        state.error = action.payload;

        // Get the movieId from the action meta
        const movieId = action.meta.arg.movieId;

        // If the movie was optimistically removed, add it back
        if (!state.favoriteIds.has(movieId)) {
          // Find the movie in the original items array (before optimistic update)
          const originalItem = state.items.find(
            item => (item.movie_id || item.movie?.id) === movieId
          );

          if (originalItem) {
            state.favoriteIds.add(movieId);
            state.favoriteRecordIds.set(movieId, originalItem.id);
            state.items.push(originalItem);
          }
        }
      });
  },
});

export const { clearError, clearFavorites, optimisticAddFavorite, optimisticRemoveFavorite } =
  favoritesSlice.actions;

export default favoritesSlice.reducer;
