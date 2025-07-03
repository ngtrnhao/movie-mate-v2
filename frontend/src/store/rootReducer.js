import { combineReducers } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import movieReducer from './slices/movieSlice';
import profileReducer from './slices/profileSlice';
import favoritesReducer from './slices/favoritesSlice';
import watchlistReducer from './slices/watchlistSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  movies: movieReducer,
  profile: profileReducer,
  favorites: favoritesReducer,
  watchlist: watchlistReducer,
});

export default rootReducer;
