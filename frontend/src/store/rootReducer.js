import { combineReducers } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import movieReducer from './slices/movieSlice';
import profileReducer from './slices/profileSlice';
import favoritesReducer from './slices/favoritesSlice';
import watchlistReducer from './slices/watchlistSlice';
import dashboardReducer from './slices/dashboardSlice';
import recommendationReducer from './slices/recommendationSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  movies: movieReducer,
  profile: profileReducer,
  favorites: favoritesReducer,
  watchlist: watchlistReducer,
  dashboard: dashboardReducer,
  recommendations: recommendationReducer,
});

export default rootReducer;
