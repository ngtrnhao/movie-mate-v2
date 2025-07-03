import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getWatchlistAPI,
  addToWatchlistAPI,
  updateWatchlistStatusAPI,
  removeFromWatchlistAPI,
} from '../../api/profileService';

// Async thunks
export const loadWatchlist = createAsyncThunk(
  'watchlist/loadWatchlist',
  async (_, { rejectWithValue }) => {
    try {
      const response = await getWatchlistAPI();
      return response.results || response;
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to load watchlist');
    }
  }
);

export const addToWatchlist = createAsyncThunk(
  'watchlist/addToWatchlist',
  async ({ movieId, status = 'PLANNED', movieData }, { rejectWithValue }) => {
    try {
      const response = await addToWatchlistAPI(movieId, status);
      return {
        ...response,
        movie: movieData || { id: movieId },
        status,
        created_at: new Date().toISOString(),
      };
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to add to watchlist');
    }
  }
);

export const updateWatchlistStatus = createAsyncThunk(
  'watchlist/updateStatus',
  async ({ movieId, newStatus }, { getState, rejectWithValue }) => {
    try {
      const { watchlist } = getState().watchlist;
      const watchlistRecord = watchlist.items.find(
        item => (item.movie?.id || item.movie_id) === movieId
      );

      if (!watchlistRecord) {
        return rejectWithValue('Movie not found in watchlist');
      }

      await updateWatchlistStatusAPI(watchlistRecord.id, newStatus);
      return { movieId, newStatus, watchlistId: watchlistRecord.id };
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to update watchlist status');
    }
  }
);

export const removeFromWatchlist = createAsyncThunk(
  'watchlist/removeFromWatchlist',
  async ({ movieId, watchlistId }, { getState, rejectWithValue }) => {
    try {
      // If watchlistId is not provided, find it from state
      if (!watchlistId) {
        const { watchlist } = getState().watchlist;
        const watchlistRecord = watchlist.items.find(
          item => (item.movie?.id || item.movie_id) === movieId
        );
        watchlistId = watchlistRecord?.id;
      }

      if (!watchlistId) {
        return rejectWithValue('Watchlist record not found');
      }

      await removeFromWatchlistAPI(watchlistId);
      return { movieId, watchlistId };
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to remove from watchlist');
    }
  }
);

const initialState = {
  lists: [],
  loading: false,
  error: null,
  initialized: false,
};

const watchlistSlice = createSlice({
  name: 'watchlist',
  initialState,
  reducers: {
    clearError: state => {
      state.error = null;
    },
    clearWatchlist: state => {
      state.items = [];
      state.movieIds = new Set();
      state.initialized = false;
    },
    // Optimistic updates
    optimisticAddToWatchlist: (state, action) => {
      const { movieId, status, movieData } = action.payload;
      if (!state.movieIds.has(movieId)) {
        state.movieIds.add(movieId);
        state.items.push({
          id: `temp-${movieId}`,
          movie: movieData || { id: movieId },
          movie_id: movieId,
          status,
          created_at: new Date().toISOString(),
          _isOptimistic: true,
        });
      }
    },
    optimisticRemoveFromWatchlist: (state, action) => {
      const { movieId } = action.payload;
      state.movieIds.delete(movieId);
      state.items = state.items.filter(item => (item.movie?.id || item.movie_id) !== movieId);
    },
    optimisticUpdateStatus: (state, action) => {
      const { movieId, newStatus } = action.payload;
      const item = state.items.find(item => (item.movie?.id || item.movie_id) === movieId);
      if (item) {
        item.status = newStatus;
        item._statusUpdating = true;
      }
    },
    // Manual add/remove/update for external updates
    addWatchlistItem: (state, action) => {
      const item = action.payload;
      const movieId = item.movie?.id || item.movie_id;
      if (movieId && !state.movieIds.has(movieId)) {
        state.movieIds.add(movieId);
        state.items.push(item);
      }
    },
    removeWatchlistItem: (state, action) => {
      const { movieId } = action.payload;
      state.movieIds.delete(movieId);
      state.items = state.items.filter(item => (item.movie?.id || item.movie_id) !== movieId);
    },
    updateWatchlistItemStatus: (state, action) => {
      const { movieId, status } = action.payload;
      const item = state.items.find(item => (item.movie?.id || item.movie_id) === movieId);
      if (item) {
        item.status = status;
      }
    },
  },
  extraReducers: builder => {
    builder
      // Load watchlist
      .addCase(loadWatchlist.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadWatchlist.fulfilled, (state, action) => {
        state.loading = false;
        state.items = action.payload;
        state.movieIds = new Set(action.payload.map(item => item.movie?.id || item.movie_id));
        state.initialized = true;
      })
      .addCase(loadWatchlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Add to watchlist
      .addCase(addToWatchlist.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addToWatchlist.fulfilled, (state, action) => {
        state.loading = false;
        const item = action.payload;
        const movieId = item.movie?.id || item.movie_id;

        // Remove optimistic entry if exists
        state.items = state.items.filter(
          item => !item._isOptimistic || (item.movie?.id || item.movie_id) !== movieId
        );

        // Add real entry
        if (!state.movieIds.has(movieId)) {
          state.movieIds.add(movieId);
          state.items.push(item);
        }
      })
      .addCase(addToWatchlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;

        // Revert optimistic update
        const movieId = action.meta.arg.movieId;
        state.movieIds.delete(movieId);
        state.items = state.items.filter(
          item => !item._isOptimistic || (item.movie?.id || item.movie_id) !== movieId
        );
      })

      // Update status
      .addCase(updateWatchlistStatus.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateWatchlistStatus.fulfilled, (state, action) => {
        state.loading = false;
        const { movieId, newStatus } = action.payload;
        const item = state.items.find(item => (item.movie?.id || item.movie_id) === movieId);
        if (item) {
          item.status = newStatus;
          delete item._statusUpdating;
        }
      })
      .addCase(updateWatchlistStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;

        // Revert optimistic update - you might want to reload here
        const movieId = action.meta.arg.movieId;
        const item = state.items.find(item => (item.movie?.id || item.movie_id) === movieId);
        if (item) {
          delete item._statusUpdating;
        }
      })

      // Remove from watchlist
      .addCase(removeFromWatchlist.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeFromWatchlist.fulfilled, (state, action) => {
        state.loading = false;
        const { movieId } = action.payload;
        state.movieIds.delete(movieId);
        state.items = state.items.filter(item => (item.movie?.id || item.movie_id) !== movieId);
      })
      .addCase(removeFromWatchlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const {
  clearError,
  clearWatchlist,
  optimisticAddToWatchlist,
  optimisticRemoveFromWatchlist,
  optimisticUpdateStatus,
  addWatchlistItem,
  removeWatchlistItem,
  updateWatchlistItemStatus,
} = watchlistSlice.actions;

export default watchlistSlice.reducer;
