import { useCallback } from 'react';
import { useSelector } from 'react-redux';
import {
  selectFavoriteItems,
  selectFavoritesLoading,
  selectFavoritesError,
  selectFavoritesInitialized,
  selectFavoriteMovieIds,
  selectFavoritesCount,
  selectFavoriteRecordIds,
} from '../store/selectors/favoritesSelectors';

/**
 * Hook chỉ để lấy favorites state mà không load API
 * Sử dụng cho các component chỉ cần đọc state
 */
export const useFavoritesState = () => {
  // Redux state
  const favorites = useSelector(selectFavoriteItems);
  const loading = useSelector(selectFavoritesLoading);
  const error = useSelector(selectFavoritesError);
  const initialized = useSelector(selectFavoritesInitialized);
  const favoritesCount = useSelector(selectFavoritesCount);
  const favoriteMovieIds = useSelector(selectFavoriteMovieIds);
  const favoriteRecordIds = useSelector(selectFavoriteRecordIds);

  const isFavorited = useCallback(
    movieId => {
      return favoriteMovieIds.has(movieId);
    },
    [favoriteMovieIds]
  );

  return {
    favorites,
    loading,
    error,
    initialized,
    favoritesCount,
    favoriteMovieIds,
    favoriteRecordIds,
    isFavorited,
  };
};
