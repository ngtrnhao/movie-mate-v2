export const selectFeaturedMovies = (state) => state.movies.featuredMovies;
export const selectMoviesByTab = (state) => state.movies.moviesByTab;
export const selectCurrentTab = (state) => state.movies.currentTab;
export const selectMoviesLoading = (state) => state.movies.loading;
export const selectMoviesError = (state) => state.movies.error;

// Memoized selectors
export const selectMoviesForCurrentTab = (state) => {
  const { currentTab, moviesByTab } = state.movies;
  const { language } = state.auth.userPreferences;
  return moviesByTab[currentTab][language] || [];
};

export const selectIsLoading = (state) => {
  const { loading } = state.movies;
  return loading.featured || loading.tab;
};

export const selectError = (state) => {
  const { error } = state.movies;
  return error.featured || error.tab;
};
