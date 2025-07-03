import { useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  loadWatchlists,
  createWatchlist,
  addMovieToWatchlist,
  removeFromWatchlist,
  updateWatchlistStatus,
  clearError,
  clearWatchlist,
} from '../store/slices/watchlistSlice';
import {
  selectWatchlistItems,
  selectWatchlistLoading,
  selectWatchlistError,
  selectWatchlistInitialized,
  selectWatchlistMovieIdsSet,
  selectWatchlistByStatus,
  selectWatchlistItemByMovieId,
  selectWatchlistCount,
  selectAllWatchlists,
} from '../store/selectors/watchlistSelectors';

export const useWatchlist = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated } = useSelector(state => state.auth);

  // Redux state
  const watchlist = useSelector(selectWatchlistItems);
  const loading = useSelector(selectWatchlistLoading);
  const error = useSelector(selectWatchlistError);
  const initialized = useSelector(selectWatchlistInitialized);
  const watchlistMovieIds = useSelector(selectWatchlistMovieIdsSet);
  const watchlistCount = useSelector(selectWatchlistCount);
  const watchlists = useSelector(selectAllWatchlists);

  // Load user's watchlist on mount
  useEffect(() => {
    if (isAuthenticated && user?.id && !initialized) {
      dispatch(loadWatchlists());
    }
  }, [dispatch, isAuthenticated, user?.id, initialized]);

  const loadWatchlistData = useCallback(() => {
    if (!isAuthenticated) return;
    dispatch(loadWatchlists());
  }, [dispatch, isAuthenticated]);

  const addToWatchlist = useCallback(
    async ({ movieId, status = 'PLANNED', movieData = null, name = null }) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to add to watchlist' };
      }

      try {
        // Create a new watchlist if name is provided, otherwise use default
        const result = await dispatch(
          createWatchlist({ name: name || 'My Watchlist', movieId, status })
        );

        if (createWatchlist.fulfilled.match(result)) {
          return { success: true };
        } else {
          return { success: false, error: result.payload };
        }
      } catch (err) {
        return { success: false, error: 'Failed to add to watchlist' };
      }
    },
    [dispatch, isAuthenticated]
  );

  const addMovieToExistingWatchlist = useCallback(
    async (watchlistId, movieId) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to manage watchlist' };
      }

      try {
        const result = await dispatch(addMovieToWatchlist({ watchlistId, movieId }));

        if (addMovieToWatchlist.fulfilled.match(result)) {
          return { success: true };
        } else {
          return { success: false, error: result.payload };
        }
      } catch (err) {
        return { success: false, error: 'Failed to add movie to watchlist' };
      }
    },
    [dispatch, isAuthenticated]
  );

  const removeFromWatchlistById = useCallback(
    async (watchlistId, movieId) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to manage watchlist' };
      }

      try {
        const result = await dispatch(removeFromWatchlist({ watchlistId, movieId }));

        if (removeFromWatchlist.fulfilled.match(result)) {
          return { success: true };
        } else {
          // Revert optimistic update by reloading
          loadWatchlistData();
          return { success: false, error: result.payload };
        }
      } catch (err) {
        // Revert optimistic update by reloading
        loadWatchlistData();
        return { success: false, error: 'Failed to remove from watchlist' };
      }
    },
    [dispatch, isAuthenticated, loadWatchlistData]
  );

  const updateStatus = useCallback(
    async (watchlistId, movieId, newStatus) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to update watchlist' };
      }

      try {
        const result = await dispatch(
          updateWatchlistStatus({ watchlistId, movieId, status: newStatus })
        );

        if (updateWatchlistStatus.fulfilled.match(result)) {
          return { success: true };
        } else {
          // Revert optimistic update by reloading
          loadWatchlistData();
          return { success: false, error: result.payload };
        }
      } catch (err) {
        // Revert optimistic update by reloading
        loadWatchlistData();
        return { success: false, error: 'Failed to update watchlist status' };
      }
    },
    [dispatch, isAuthenticated, loadWatchlistData]
  );

  const toggleWatchlist = useCallback(
    async (movieId, movieData = null) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to manage watchlist' };
      }

      const isInWatchlist = watchlistMovieIds.has(movieId);

      if (isInWatchlist) {
        // Find the watchlist that contains this movie
        const watchlistItem = watchlist.find(item => (item.movie?.id || item.movie_id) === movieId);
        if (watchlistItem) {
          return await removeFromWatchlistById(watchlistItem.watchlist_id, movieId);
        }
        return { success: false, error: 'Movie not found in watchlist' };
      } else {
        return await addToWatchlist({ movieId, status: 'PLANNED', movieData });
      }
    },
    [isAuthenticated, watchlistMovieIds, watchlist, addToWatchlist, removeFromWatchlistById]
  );

  const isInWatchlist = useCallback(
    movieId => {
      return watchlistMovieIds.has(movieId);
    },
    [watchlistMovieIds]
  );

  const getWatchlistStatus = useCallback(
    movieId => {
      const item = watchlist.find(item => (item.movie?.id || item.movie_id) === movieId);
      return item?.status || null;
    },
    [watchlist]
  );

  const getWatchlistByStatus = useCallback(
    status => {
      return watchlist.filter(item => item.status === status);
    },
    [watchlist]
  );

  const clearWatchlistError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    watchlist,
    watchlists,
    loading,
    error,
    initialized,
    watchlistCount,
    addToWatchlist,
    addMovieToExistingWatchlist,
    removeFromWatchlist: removeFromWatchlistById,
    updateWatchlistStatus: updateStatus,
    toggleWatchlist,
    isInWatchlist,
    getWatchlistStatus,
    getWatchlistByStatus,
    clearWatchlistError,
    loadWatchlistData,
  };
};
