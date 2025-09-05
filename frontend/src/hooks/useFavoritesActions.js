import { useCallback } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import toast from 'react-hot-toast';
import {
  loadFavorites,
  addToFavorites as addToFavoritesAction,
  removeFromFavorites as removeFromFavoritesAction,
  optimisticAddFavorite,
  optimisticRemoveFavorite,
  clearError,
} from '../store/slices/favoritesSlice';
import { selectFavoriteRecordIds } from '../store/selectors/favoritesSelectors';

/**
 * Hook cho favorites actions
 * Sử dụng cho các component cần thực hiện actions
 */
export const useFavoritesActions = () => {
  const dispatch = useDispatch();
  const { user, isAuthenticated } = useSelector(state => state.auth);
  const favoriteRecordIds = useSelector(selectFavoriteRecordIds);

  const loadFavoritesList = useCallback(() => {
    if (!isAuthenticated || !user?.id) return;
    dispatch(loadFavorites(user.id));
  }, [dispatch, isAuthenticated, user?.id]);

  const addToFavorites = useCallback(
    async (movieId, movieData = null) => {
      console.log('🎬 addToFavorites called:', { movieId, movieData, isAuthenticated, user });

      if (!isAuthenticated) {
        toast.error('Please login to add favorites');
        console.warn('❌ Not authenticated - cannot add to favorites');
        return { success: false, error: 'Please login to add favorites' };
      }

      try {
        console.log('🔄 Starting add to favorites process...');
        // Optimistic update
        dispatch(optimisticAddFavorite({ movieId, movieData }));
        console.log('✅ Optimistic update dispatched');
        toast.loading('Adding to favorites...', { id: `favorite-${movieId}` });

        // Dispatch async action
        console.log('🚀 Dispatching addToFavoritesAction...');
        const result = await dispatch(addToFavoritesAction({ movieId, movieData }));
        console.log('📝 Dispatch result:', result);
        if (result.error) {
          toast.error('Failed to add to favorites', { id: `favorite-${movieId}` });
          console.error('❌ Thunk error:', result.error, result);
        }
        // Check if the action was fulfilled
        if (result.type === addToFavoritesAction.fulfilled.type) {
          toast.success('Added to favorites!', { id: `favorite-${movieId}` });
          console.log('✅ Add to favorites successful');
          return { success: true };
        } else if (result.type === addToFavoritesAction.rejected.type) {
          toast.error('Failed to add to favorites', { id: `favorite-${movieId}` });
          console.error('❌ Add to favorites failed:', result.payload, result);
          return { success: false, error: result.payload };
        } else {
          toast.error('Something went wrong', { id: `favorite-${movieId}` });
          console.error('❌ Unexpected result type:', result.type, result);
          return { success: false, error: 'Unexpected response' };
        }
      } catch (err) {
        toast.error('Failed to add to favorites', { id: `favorite-${movieId}` });
        console.error('❌ Exception in addToFavorites:', err);
        if (err && err.response) {
          console.error('❌ API error response:', err.response);
        }
        return { success: false, error: err?.message || 'Failed to add to favorites' };
      }
    },
    [dispatch, isAuthenticated, user]
  );

  const removeFromFavorites = useCallback(
    async movieId => {
      console.log('🗑️ removeFromFavorites called:', { movieId, isAuthenticated, user });

      if (!isAuthenticated) {
        toast.error('Please login to manage favorites');
        console.warn('❌ Not authenticated - cannot remove from favorites');
        return { success: false, error: 'Please login to manage favorites' };
      }

      try {
        console.log('🔄 Starting remove from favorites process...');
        const favoriteId = favoriteRecordIds.get(movieId);
        console.log('🔍 Found favoriteId:', favoriteId, 'for movieId:', movieId);

        if (!favoriteId) {
          console.error('❌ No favorite record ID found for movie:', movieId);
          toast.error('Unable to remove from favorites', { id: `favorite-${movieId}` });
          return { success: false, error: 'Favorite record not found' };
        }

        // Optimistic update
        dispatch(optimisticRemoveFavorite({ movieId }));
        console.log('✅ Optimistic remove dispatched');
        toast.loading('Removing from favorites...', { id: `favorite-${movieId}` });

        // Dispatch async action
        console.log('🚀 Dispatching removeFromFavoritesAction...');
        const result = await dispatch(removeFromFavoritesAction({ movieId, favoriteId }));
        console.log('📝 Remove result:', result);

        // Check if the action was fulfilled
        if (result.type === removeFromFavoritesAction.fulfilled.type) {
          toast.success('Removed from favorites!', { id: `favorite-${movieId}` });
          console.log('✅ Remove from favorites successful');
          return { success: true };
        } else if (result.type === removeFromFavoritesAction.rejected.type) {
          toast.error('Failed to remove from favorites', { id: `favorite-${movieId}` });
          console.error('❌ Remove from favorites failed:', result.payload);
          // Revert optimistic update by reloading
          loadFavoritesList();
          return { success: false, error: result.payload };
        } else {
          toast.error('Something went wrong', { id: `favorite-${movieId}` });
          console.error('❌ Unexpected remove result type:', result.type);
          // Revert optimistic update by reloading
          loadFavoritesList();
          return { success: false, error: 'Unexpected response' };
        }
      } catch (err) {
        toast.error('Failed to remove from favorites', { id: `favorite-${movieId}` });
        console.error('❌ Exception in removeFromFavorites:', err);
        // Revert optimistic update by reloading
        loadFavoritesList();
        return { success: false, error: 'Failed to remove from favorites' };
      }
    },
    [dispatch, isAuthenticated, user, loadFavoritesList, favoriteRecordIds]
  );

  const clearFavoritesError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  return {
    addToFavorites,
    removeFromFavorites,
    loadFavorites: loadFavoritesList,
    clearError: clearFavoritesError,
  };
};
