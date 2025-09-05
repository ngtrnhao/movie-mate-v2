import { useQuery } from '@tanstack/react-query';
import { useTranslation } from '../i18n/hooks/useTranslation';
import {
  getGenresForAdmin,
  getMovieStatusOptions,
  getApprovalStatusOptions,
  getVisibilityStatusOptions,
} from '../api/adminMovieService';

// Query options cho admin form data
const defaultQueryOptions = {
  staleTime: 30 * 60 * 1000, // 30 phút
  gcTime: 60 * 60 * 1000, // 60 phút
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchOnReconnect: false,
  retry: 2,
  retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
};

// Hook để fetch genres cho admin form - lấy tất cả ngôn ngữ
export const useAdminGenres = (options = {}) => {
  return useQuery({
    queryKey: ['admin-genres-all'],
    queryFn: () => getGenresForAdmin(),
    ...defaultQueryOptions,
    ...options,
  });
};

// Hook để fetch movie status options
export const useMovieStatusOptions = (options = {}) => {
  return useQuery({
    queryKey: ['movie-status-options'],
    queryFn: getMovieStatusOptions,
    ...defaultQueryOptions,
    ...options,
  });
};

// Hook để fetch approval status options
export const useApprovalStatusOptions = (options = {}) => {
  return useQuery({
    queryKey: ['approval-status-options'],
    queryFn: getApprovalStatusOptions,
    ...defaultQueryOptions,
    ...options,
  });
};

// Hook để fetch visibility status options
export const useVisibilityStatusOptions = (options = {}) => {
  return useQuery({
    queryKey: ['visibility-status-options'],
    queryFn: getVisibilityStatusOptions,
    ...defaultQueryOptions,
    ...options,
  });
};

// Hook tổng hợp để fetch tất cả options cần thiết cho admin movie form
export const useAdminMovieFormData = (options = {}) => {
  const genres = useAdminGenres(options);
  const movieStatusOptions = useMovieStatusOptions(options);
  const approvalStatusOptions = useApprovalStatusOptions(options);
  const visibilityStatusOptions = useVisibilityStatusOptions(options);

  // Tính toán loading và error states
  const isLoading =
    genres.isLoading ||
    movieStatusOptions.isLoading ||
    approvalStatusOptions.isLoading ||
    visibilityStatusOptions.isLoading;

  const error =
    genres.error ||
    movieStatusOptions.error ||
    approvalStatusOptions.error ||
    visibilityStatusOptions.error;

  return {
    genres: genres.data || [],
    movieStatusOptions: movieStatusOptions.data || [],
    approvalStatusOptions: approvalStatusOptions.data || [],
    visibilityStatusOptions: visibilityStatusOptions.data || [],
    isLoading,
    error,
    refetch: () => {
      genres.refetch();
      movieStatusOptions.refetch();
      approvalStatusOptions.refetch();
      visibilityStatusOptions.refetch();
    },
  };
};
