import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
const TMDB_BASE_URL = 'https://api.themoviedb.org/3';
const TMDB_API_KEY = process.env.TMDB_API_KEY;
// API Configuration
const options = {
  method: 'GET',
  headers: {
    accept: 'application/json',
    Authorization: `Bearer ${TMDB_API_KEY}`,
  },
};
//Async Thunks
export const fetchFeaturedMovies = createAsyncThunk(
  'movies/fetchFeaturedMovies',
  async (_, { rejectWithValue }) => {
    try {
      const [enResponse, viResponse] = await Promise.all([
        fetch(`${TMDB_BASE_URL}/trending/movie/week?language=en-US`, options),
        fetch(`${TMDB_BASE_URL}/trending/movie/week?language=vi-VN`, options),
      ]);
      if (!enResponse.ok || !viResponse.ok) {
        throw new Error('Failed to fetch movies');
      }

      const [enData, viData] = await Promise.all([enResponse.json(), viResponse.json()]);
      return { enData, viData };
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
      if (tabKey === 'top_rated') url = `${TMDB_BASE_URL}/movie/top_rated`;
      if (tabKey === 'upcoming') url = `${TMDB_BASE_URL}/movie/upcoming`;

      const [reponse, genresResponse] = await Promise.all([
        fetch(`${url}?language=${lang}`, options),
        fetch(`${TMDB_BASE_URL}/genre/movie/list?language=${lang}`, options),
      ]);

      if (!reponse.ok || !genresResponse.ok) {
        throw new Error('Failed to fetch movies');
      }
      const [data, genresData] = await Promise.all([reponse.json(), genresResponse.json()]);
      return { data, genresData, tabKey, lang };
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
      tab: false,
    },
    error: {
      featured: null,
      tab: null,
    },
    currentTab: 'trending',
  },
  reducers: {
    setCurrentTab: (state, action) => {
      state.currentTab = action.payload;
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
        //Transform and set featured movies
        state.featuredMovies = transformFeaturedMovies(action.payload);
      })
      .addCase(fetchFeaturedMovies.rejected, (state, action) => {
        state.loading.featured = false;
        state.error.featured = action.payload;
      })
      //Movies by tab
      .addCase(fetchMoviesByTab.pending, (state) => {
        state.loading.tab = true;
        state.error.tab = null;
      })
      .addCase(fetchMoviesByTab.fulfilled, (state, action) => {
        state.loading.tab = false;
        const { data, genresData, tabKey, lang } = action.payload;
        state.moviesByTab[tabKey][lang] = transformMovies(data.results, genresData.genres);
      })
      .addCase(fetchMoviesByTab.rejected, (state, action) => {
        state.loading.tab = false;
        state.error.tab = action.payload;
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
  }));
};

export const { setCurrentTab } = movieSlice.actions;
export default movieSlice.reducer;
