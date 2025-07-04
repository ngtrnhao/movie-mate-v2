import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectFavoritesState = state => state.favorites;
export const selectFavoriteItems = state => state.favorites.items;
export const selectFavoriteIds = state => state.favorites.favoriteIds;
export const selectFavoritesLoading = state => state.favorites.loading;
export const selectFavoritesError = state => state.favorites.error;
export const selectFavoritesInitialized = state => state.favorites.initialized;
export const selectFavoriteMovieIds = state => state.favorites.favoriteIds;
export const selectFavoriteRecordIds = state => state.favorites.favoriteRecordIds;

// Derived selectors
export const selectFavoritesCount = state => state.favorites.items.length;

// Complex selectors
export const selectFavoriteMovies = state => {
  const items = state.favorites.items;
  return items.map(item => ({
    id: item.movie_id || item.movie?.id,
    title: item.movie_title || item.movie?.title,
    poster: item.movie_poster || item.movie?.poster_url,
    created_at: item.created_at,
    favorite_id: item.id,
  }));
};

// Memoized selectors
export const selectFavoritesSorted = createSelector([selectFavoriteItems], items =>
  [...items].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
);

export const selectRecentFavorites = createSelector([selectFavoritesSorted], sortedItems =>
  sortedItems.slice(0, 10)
);

export const selectIsFavorited = createSelector(
  [selectFavoriteMovieIds, (_, movieId) => movieId],
  (favoriteIds, movieId) => favoriteIds.has(movieId)
);
