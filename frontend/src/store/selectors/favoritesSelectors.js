import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectFavoritesState = state => state.favorites;
export const selectFavoriteItems = state => state.favorites.items;
export const selectFavoriteIds = state => state.favorites.favoriteIds;
export const selectFavoritesLoading = state => state.favorites.loading;
export const selectFavoritesError = state => state.favorites.error;
export const selectFavoritesInitialized = state => state.favorites.initialized;

// Memoized selectors
export const selectFavoriteMovieIds = createSelector(
  [selectFavoriteItems],
  items => new Set(items.map(item => item.movie_id || item.movie?.id))
);

export const selectFavoritesCount = createSelector([selectFavoriteItems], items => items.length);

export const selectIsFavorited = createSelector(
  [selectFavoriteMovieIds, (_, movieId) => movieId],
  (favoriteIds, movieId) => favoriteIds.has(movieId)
);

export const selectFavoritesSorted = createSelector([selectFavoriteItems], items =>
  [...items].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
);

export const selectRecentFavorites = createSelector([selectFavoritesSorted], sortedItems =>
  sortedItems.slice(0, 10)
);
