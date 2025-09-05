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

// Tối ưu query options để tránh re-render
const defaultQueryOptions = {
  staleTime: 5 * 60 * 1000, // 5 phút
  cacheTime: 10 * 60 * 1000, // 10 phút
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchOnReconnect: false,
  retry: 1,
  retryDelay: 1000,
};

// Custom hooks
export const useFeaturedMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'featured'],
    queryFn: getFeaturedMovies,
    ...defaultQueryOptions,
  });
};

export const useTrendingMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'trending'],
    queryFn: getTrendingMovies,
    ...defaultQueryOptions,
  });
};

export const useTopRatedMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'topRated'],
    queryFn: getTopRatedMovies,
    ...defaultQueryOptions,
  });
};

export const useUpcomingMovies = () => {
  return useQuery({
    queryKey: [...movieKeys.lists(), 'upcoming'],
    queryFn: getUpcomingMovies,
    ...defaultQueryOptions,
  });
};

export const useMovieDetails = movieId => {
  return useQuery({
    queryKey: movieKeys.detail(movieId),
    queryFn: () => getMovieDetails(movieId),
    enabled: !!movieId,
    ...defaultQueryOptions,
  });
};
