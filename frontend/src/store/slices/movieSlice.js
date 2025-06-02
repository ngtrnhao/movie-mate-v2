import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';

const TMDB_BASE_URL = 'https://api.themoviedb.org/3';

// API Configuration
const options = {
  method: 'GET',
  headers: {
    accept: 'application/json',
    Authorization: `Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI0YzMzOGUzYTMzNGI4ZjgxN2M0NWNlOGIwY2JhNmRmMSIsIm5iZiI6MTc0MDYwODk5Mi40MTkwMDAxLCJzdWIiOiI2N2JmOTVlMGJjNjkzNWEwMDFhMjM2MTgiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.iOVSJPSuTWhbnD5AAQBCnQ5TYXVLCwVOgPMytmB4rHs`,
  },
};

// Cache for storing API responses
const apiCache = new Map();
const CACHE_DURATION = 5 * 60 * 1000; // 5 minutes

// Helper function to handle API calls with caching
const fetchWithCache = async (url, options) => {
  const cacheKey = url;
  const cachedData = apiCache.get(cacheKey);

  if (cachedData && Date.now() - cachedData.timestamp < CACHE_DURATION) {
    return cachedData.data;
  }

  const response = await fetch(url, options);
  if (!response.ok) {
    throw new Error(`API call failed: ${response.status} ${response.statusText}`);
  }

  const data = await response.json();
  apiCache.set(cacheKey, {
    data,
    timestamp: Date.now(),
  });

  return data;
};

//Async Thunks
export const fetchFeaturedMovies = createAsyncThunk(
  'movies/fetchFeaturedMovies',
  async (_, { rejectWithValue }) => {
    try {
      const [enData, viData] = await Promise.all([
        fetchWithCache(`${TMDB_BASE_URL}/trending/movie/week?language=en-US`, options),
        fetchWithCache(`${TMDB_BASE_URL}/trending/movie/week?language=vi-VN`, options),
      ]);

      // Fetch trailer information for each movie
      const moviesWithTrailers = await Promise.all(
        enData.results.slice(0, 3).map(async (movie) => {
          try {
            const details = await fetchWithCache(
              `${TMDB_BASE_URL}/movie/${movie.id}?append_to_response=videos`,
              options
            );
            return {
              ...movie,
              trailer:
                details.videos?.results?.find((video) => video.type === 'Trailer')?.key || null,
            };
          } catch (error) {
            console.error(`Failed to fetch trailer for movie ${movie.id}:`, error);
            return { ...movie, trailer: null };
          }
        })
      );

      return { enData: { ...enData, results: moviesWithTrailers }, viData };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const fetchMoviesByTab = createAsyncThunk(
  'movies/fetchMoviesByTab',
  async ({ tabKey, lang }, { rejectWithValue }) => {
    try {
      let url = '';
      if (tabKey === 'trending') url = `${TMDB_BASE_URL}/trending/movie/week`;
      if (tabKey === 'topRated') url = `${TMDB_BASE_URL}/movie/top_rated`;
      if (tabKey === 'upcoming') url = `${TMDB_BASE_URL}/movie/upcoming`;

      const [data, genresData] = await Promise.all([
        fetchWithCache(`${url}?language=${lang}`, options),
        fetchWithCache(`${TMDB_BASE_URL}/genre/movie/list?language=${lang}`, options),
      ]);

      // Fetch additional details for each movie
      const moviesWithDetails = await Promise.all(
        data.results.map(async (movie) => {
          try {
            const details = await fetchWithCache(
              `${TMDB_BASE_URL}/movie/${movie.id}?append_to_response=videos`,
              options
            );
            return {
              ...movie,
              trailer:
                details.videos?.results?.find((video) => video.type === 'Trailer')?.key || null,
            };
          } catch (error) {
            console.error(`Failed to fetch details for movie ${movie.id}:`, error);
            return { ...movie, trailer: null };
          }
        })
      );

      return {
        data: { ...data, results: moviesWithDetails },
        genresData,
        tabKey,
        lang,
      };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

//Initial State
const movieSlice = createSlice({
  name: 'movies',
  initialState: {
    featuredMovies: [],
    moviesByTab: {
      trending: { 'en-US': [], 'vi-VN': [] },
      topRated: { 'en-US': [], 'vi-VN': [] },
      upcoming: { 'en-US': [], 'vi-VN': [] },
    },
    loading: {
      featured: false,
      moviesByTab: false,
    },
    error: {
      featured: null,
      moviesByTab: null,
    },
    currentTab: 'trending',
  },
  reducers: {
    setCurrentTab: (state, action) => {
      state.currentTab = action.payload;
    },
    clearCache: () => {
      apiCache.clear();
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchFeaturedMovies.pending, (state) => {
        state.loading.featured = true;
        state.error.featured = null;
      })
      .addCase(fetchFeaturedMovies.fulfilled, (state, action) => {
        state.loading.featured = false;
        state.featuredMovies = transformFeaturedMovies(action.payload);
      })
      .addCase(fetchFeaturedMovies.rejected, (state, action) => {
        state.loading.featured = false;
        state.error.featured = action.payload;
      })
      .addCase(fetchMoviesByTab.pending, (state) => {
        state.loading.moviesByTab = true;
        state.error.moviesByTab = null;
      })
      .addCase(fetchMoviesByTab.fulfilled, (state, action) => {
        state.loading.moviesByTab = false;
        const { data, genresData, tabKey, lang } = action.payload;
        state.moviesByTab[tabKey][lang] = transformMovies(data.results, genresData.genres);
      })
      .addCase(fetchMoviesByTab.rejected, (state, action) => {
        state.loading.moviesByTab = false;
        state.error.moviesByTab = action.payload;
      });
  },
});

const transformFeaturedMovies = ({ enData, viData }) => {
  return enData.results.slice(0, 3).map((enMovie, index) => {
    const viMovie = viData.results[index];
    return {
      id: enMovie.id,
      title: enMovie.title,
      poster_path: enMovie.poster_path,
      adult: enMovie.adult,
      vote_average: enMovie.vote_average,
      vote_count: enMovie.vote_count,
      release_date: enMovie.release_date,
      overview: enMovie.overview,
      genre_ids: enMovie.genre_ids,
      backdrop_path: enMovie.backdrop_path,
      popularity: enMovie.popularity,
      original_language: enMovie.original_language,
      original_title: enMovie.original_title,
      title_translations: {
        en: enMovie.title,
        vi: viMovie.title,
      },
      overview_translations: {
        en: enMovie.overview,
        vi: viMovie.overview,
      },
      trailerUrl: enMovie.trailer ? `https://www.youtube.com/watch?v=${enMovie.trailer}` : null,
    };
  });
};

const transformMovies = (movies, genres) => {
  const genreMap = genres.reduce((acc, genre) => {
    acc[genre.id] = genre.name;
    return acc;
  }, {});

  return movies.map((movie) => ({
    id: movie.id,
    title: movie.title,
    poster_path: movie.poster_path,
    adult: movie.adult,
    vote_average: movie.vote_average,
    vote_count: movie.vote_count,
    release_date: movie.release_date,
    overview: movie.overview,
    genres: movie.genre_ids.map((id) => genreMap[id]),
    backdrop_path: movie.backdrop_path,
    popularity: movie.popularity,
    original_language: movie.original_language,
    original_title: movie.original_title,
    trailerUrl: movie.trailer ? `https://www.youtube.com/watch?v=${movie.trailer}` : null,
  }));
};

export const { setCurrentTab, clearCache } = movieSlice.actions;
export default movieSlice.reducer;
