import { createSelector } from '@reduxjs/toolkit';

// Basic selectors
export const selectWatchlistState = state => state.watchlist;
export const selectWatchlistItems = state => state.watchlist.items;
export const selectWatchlistMovieIds = state => state.watchlist.movieIds;
export const selectWatchlistLoading = state => state.watchlist.loading;
export const selectWatchlistError = state => state.watchlist.error;
export const selectWatchlistInitialized = state => state.watchlist.initialized;
export const selectAllWatchlists = state => state.watchlist.watchlists;

// Memoized selectors
export const selectWatchlistMovieIdsSet = createSelector(
  [selectWatchlistItems],
  items => new Set(items.map(item => item.movie?.id || item.movie_id))
);

export const selectWatchlistCount = createSelector([selectWatchlistItems], items => items.length);

export const selectIsInWatchlist = createSelector(
  [selectWatchlistMovieIdsSet, (_, movieId) => movieId],
  (movieIds, movieId) => movieIds.has(movieId)
);

export const selectWatchlistByStatus = createSelector(
  [selectWatchlistItems, (_, status) => status],
  (items, status) => items.filter(item => item.status === status)
);

export const selectWatchlistItemByMovieId = createSelector(
  [selectWatchlistItems, (_, movieId) => movieId],
  (items, movieId) => items.find(item => (item.movie?.id || item.movie_id) === movieId)
);

export const selectWatchlistStatus = createSelector(
  [selectWatchlistItemByMovieId],
  item => item?.status || null
);

// Watchlist-specific selectors
export const selectWatchlistById = createSelector(
  [selectAllWatchlists, (_, id) => id],
  (watchlists, id) => watchlists.find(list => list.id === id)
);

export const selectWatchlistsByMovieId = createSelector(
  [selectAllWatchlists, selectWatchlistItems, (_, movieId) => movieId],
  (watchlists, items, movieId) => {
    const watchlistIds = new Set(
      items
        .filter(item => (item.movie?.id || item.movie_id) === movieId)
        .map(item => item.watchlist_id)
    );
    return watchlists.filter(list => watchlistIds.has(list.id));
  }
);

// Status-specific selectors
export const selectPlannedMovies = createSelector([selectWatchlistItems], items =>
  items.filter(item => item.status === 'PLANNED')
);

export const selectWatchingMovies = createSelector([selectWatchlistItems], items =>
  items.filter(item => item.status === 'WATCHING')
);

export const selectWatchedMovies = createSelector([selectWatchlistItems], items =>
  items.filter(item => item.status === 'WATCHED')
);

// Count selectors
export const selectWatchlistCounts = createSelector([selectWatchlistItems], items => ({
  total: items.length,
  planned: items.filter(item => item.status === 'PLANNED').length,
  watching: items.filter(item => item.status === 'WATCHING').length,
  watched: items.filter(item => item.status === 'WATCHED').length,
}));

export const selectRecentWatchlistItems = createSelector([selectWatchlistItems], items =>
  [...items].sort((a, b) => new Date(b.created_at) - new Date(a.created_at)).slice(0, 10)
);
