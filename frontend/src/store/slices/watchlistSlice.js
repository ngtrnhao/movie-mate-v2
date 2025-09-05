import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  getWatchlistsAPI,
  addToWatchlistAPI,
  addMovieToWatchlistAPI,
  removeFromWatchlistAPI,
  updateWatchlistStatusAPI,
} from '../../api/profileService';

// Async thunks
export const loadWatchlists = createAsyncThunk(
  'watchlist/loadWatchlists',
  async (_, { rejectWithValue }) => {
    try {
      const response = await getWatchlistsAPI();
      return response.results || response;
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to load watchlists');
    }
  }
);

export const createWatchlist = createAsyncThunk(
  'watchlist/createWatchlist',
  async ({ name, movieId = null, status = 'PLANNED' }, { rejectWithValue }) => {
    try {
      // Create the watchlist with the movie if provided
      const watchlist = await addToWatchlistAPI(movieId, status, name);
      return watchlist;
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to create watchlist');
    }
  }
);

export const addMovieToWatchlist = createAsyncThunk(
  'watchlist/addMovieToWatchlist',
  async ({ watchlistId, movieId, status = 'PLANNED' }, { rejectWithValue }) => {
    try {
      const response = await addMovieToWatchlistAPI(watchlistId, movieId, status);
      return response;
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to add movie to watchlist');
    }
  }
);

export const removeFromWatchlist = createAsyncThunk(
  'watchlist/removeFromWatchlist',
  async ({ watchlistId, movieId }, { rejectWithValue }) => {
    try {
      await removeFromWatchlistAPI(watchlistId, movieId);
      return { watchlistId, movieId };
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to remove from watchlist');
    }
  }
);

export const updateWatchlistStatus = createAsyncThunk(
  'watchlist/updateStatus',
  async ({ watchlistId, movieId, status }, { rejectWithValue }) => {
    try {
      const response = await updateWatchlistStatusAPI(watchlistId, movieId, status);
      return response;
    } catch (error) {
      return rejectWithValue(error.error || 'Failed to update status');
    }
  }
);

const initialState = {
  watchlists: [],
  items: [],
  movieIds: new Set(),
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
      state.watchlists = [];
      state.items = [];
      state.movieIds = new Set();
      state.initialized = false;
    },
  },
  extraReducers: builder => {
    builder
      // Load watchlists
      .addCase(loadWatchlists.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(loadWatchlists.fulfilled, (state, action) => {
        state.loading = false;
        state.watchlists = action.payload;
        state.initialized = true;

        // Update items and movieIds
        state.items = action.payload.flatMap(list =>
          list.items.map(item => ({
            ...item,
            watchlist_id: list.id,
          }))
        );
        state.movieIds = new Set(state.items.map(item => item.movie?.id || item.movie_id));
      })
      .addCase(loadWatchlists.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Create watchlist
      .addCase(createWatchlist.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(createWatchlist.fulfilled, (state, action) => {
        state.loading = false;
        state.watchlists.push(action.payload);
      })
      .addCase(createWatchlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Add movie to watchlist
      .addCase(addMovieToWatchlist.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(addMovieToWatchlist.fulfilled, (state, action) => {
        state.loading = false;
        const { watchlist_id, movie_id, status } = action.payload;

        // Add to items if not already present
        if (
          !state.items.some(
            item =>
              item.watchlist_id === watchlist_id &&
              (item.movie?.id === movie_id || item.movie_id === movie_id)
          )
        ) {
          state.items.push({
            watchlist_id,
            movie_id,
            status,
            created_at: new Date().toISOString(),
          });
          state.movieIds.add(movie_id);
        }

        // Update movie count in watchlist
        const watchlist = state.watchlists.find(w => w.id === watchlist_id);
        if (watchlist) {
          watchlist.movie_count = (watchlist.movie_count || 0) + 1;
        }
      })
      .addCase(addMovieToWatchlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Remove from watchlist
      .addCase(removeFromWatchlist.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(removeFromWatchlist.fulfilled, (state, action) => {
        state.loading = false;
        const { watchlistId, movieId } = action.payload;

        // Remove from items
        state.items = state.items.filter(
          item =>
            !(
              item.watchlist_id === watchlistId &&
              (item.movie?.id === movieId || item.movie_id === movieId)
            )
        );

        // Update movieIds
        if (!state.items.some(item => item.movie?.id === movieId || item.movie_id === movieId)) {
          state.movieIds.delete(movieId);
        }

        // Update movie count in watchlist
        const watchlist = state.watchlists.find(w => w.id === watchlistId);
        if (watchlist) {
          watchlist.movie_count = Math.max(0, (watchlist.movie_count || 1) - 1);
        }
      })
      .addCase(removeFromWatchlist.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      })

      // Update status
      .addCase(updateWatchlistStatus.pending, state => {
        state.loading = true;
        state.error = null;
      })
      .addCase(updateWatchlistStatus.fulfilled, (state, action) => {
        state.loading = false;
        const { watchlist_id, movie_id, status } = action.payload;

        // Update status in items
        const item = state.items.find(
          item =>
            item.watchlist_id === watchlist_id &&
            (item.movie?.id === movie_id || item.movie_id === movie_id)
        );
        if (item) {
          item.status = status;
        }
      })
      .addCase(updateWatchlistStatus.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload;
      });
  },
});

export const { clearError, clearWatchlist } = watchlistSlice.actions;

export default watchlistSlice.reducer;
