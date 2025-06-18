import { useQuery } from '@tanstack/react-query';
import {
  getFeaturedMovies,
  getTopRatedMovies,
  getTrendingMovies,
  getUpcomingMovies,
  getMovieDetails,
} from '../api/movieService';

// Query keys
export const movieKeys = {
  all: ['movies'],
  lists: () => [...movieKeys.all, 'list'],
  list: filters => [...movieKeys.lists(), { filters }],
  details: () => [...movieKeys.all, 'detail'],
  detail: id => [...movieKeys.details(), id],
};

// Custom hooks
export const useFeaturedMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'featured'],
    queryFn: getFeaturedMovies,
  });
};

export const useTrendingMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'trending'],
    queryFn: getTrendingMovies,
  });
};

export const useTopRatedMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'topRated'],
    queryFn: getTopRatedMovies,
  });
};

export const useUpcomingMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'upcoming'],
    queryFn: getUpcomingMovies,
  });
};

export const useMovieDetails = movieId => {
  return useQuery({
    queryKey: movieKeys.detail(movieId),
    queryFn: () => getMovieDetails(movieId),
    enabled: !!movieId,
  });
};
