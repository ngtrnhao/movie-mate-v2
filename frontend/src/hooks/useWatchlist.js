import { useEffect, useCallback } from 'react';
import { useSelector, useDispatch } from 'react-redux';
import {
  loadWatchlist,
  addToWatchlist as addToWatchlistAction,
  removeFromWatchlist as removeFromWatchlistAction,
  updateWatchlistStatus as updateWatchlistStatusAction,
  optimisticAddToWatchlist,
  optimisticRemoveFromWatchlist,
  optimisticUpdateStatus,
  clearError,
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

  // Load user's watchlist on mount
  useEffect(() => {
    if (isAuthenticated && user?.id && !initialized) {
      dispatch(loadWatchlist());
    }
  }, [dispatch, isAuthenticated, user?.id, initialized]);

  const loadWatchlistData = useCallback(() => {
    if (!isAuthenticated) return;
    dispatch(loadWatchlist());
  }, [dispatch, isAuthenticated]);

  const addToWatchlist = useCallback(
    async (movieId, status = 'PLANNED', movieData = null) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to add to watchlist' };
      }

      try {
        // Optimistic update
        dispatch(optimisticAddToWatchlist({ movieId, status, movieData }));

        // Dispatch async action
        const result = await dispatch(addToWatchlistAction({ movieId, status, movieData }));

        if (addToWatchlistAction.fulfilled.match(result)) {
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

  const removeFromWatchlist = useCallback(
    async movieId => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to manage watchlist' };
      }

      try {
        // Optimistic update
        dispatch(optimisticRemoveFromWatchlist({ movieId }));

        // Dispatch async action
        const result = await dispatch(removeFromWatchlistAction({ movieId }));

        if (removeFromWatchlistAction.fulfilled.match(result)) {
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

  const updateWatchlistStatus = useCallback(
    async (movieId, newStatus) => {
      if (!isAuthenticated) {
        return { success: false, error: 'Please login to update watchlist' };
      }

      try {
        // Optimistic update
        dispatch(optimisticUpdateStatus({ movieId, newStatus }));

        // Dispatch async action
        const result = await dispatch(updateWatchlistStatusAction({ movieId, newStatus }));

        if (updateWatchlistStatusAction.fulfilled.match(result)) {
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
        return await removeFromWatchlist(movieId);
      } else {
        return await addToWatchlist(movieId, 'PLANNED', movieData);
      }
    },
    [isAuthenticated, watchlistMovieIds, addToWatchlist, removeFromWatchlist]
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
    loading,
    error,
    initialized,
    watchlistCount,
    isInWatchlist,
    getWatchlistStatus,
    getWatchlistByStatus,
    addToWatchlist,
    removeFromWatchlist,
    updateWatchlistStatus,
    toggleWatchlist,
    loadWatchlist: loadWatchlistData,
    clearError: clearWatchlistError,
    isAuthenticated,
  };
};
