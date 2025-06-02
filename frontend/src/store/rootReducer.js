import { combineReducers } from '@reduxjs/toolkit';
import authReducer from './slices/authSlice';
import movieReducer from './slices/movieSlice';
import profileReducer from './slices/profileSlice';

const rootReducer = combineReducers({
  auth: authReducer,
  movies: movieReducer,
  profile: profileReducer,
});

export default rootReducer;
