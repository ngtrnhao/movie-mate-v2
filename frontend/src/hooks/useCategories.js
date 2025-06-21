import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useTranslation } from '../i18n/hooks/useTranslation';
import axiosInstance from '../api/axios';
import { useCallback } from 'react';

// Tối ưu query options để tránh re-render và cải thiện performance
const defaultQueryOptions = {
  staleTime: 15 * 60 * 1000, // 15 phút - tăng thời gian cache
  gcTime: 60 * 60 * 1000, // 60 phút - garbage collection time
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchOnReconnect: false,
  retry: 2,
  retryDelay: attemptIndex => Math.min(1000 * 2 ** attemptIndex, 30000),
  placeholderData: [], // Cung cấp placeholder data để tránh loading flash
};

// Prefetch categories khi cần thiết
export const prefetchCategories = async (queryClient, language = 'en') => {
  await queryClient.prefetchQuery({
    queryKey: ['categories', language],
    queryFn: async () => {
      const res = await axiosInstance.get(`/api/metadata/categories/?language=${language}`);
      if (res.data.status !== 'success') {
        throw new Error(res.data.message || 'Failed to fetch categories');
      }
      return res.data.data;
    },
    ...defaultQueryOptions,
  });
};

export const useCategories = (options = {}) => {
  const { i18n } = useTranslation();
  const queryClient = useQueryClient();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return useQuery({
    queryKey: ['categories', app_language],
    queryFn: async () => {
      try {
        const res = await axiosInstance.get(`/api/metadata/categories/?language=${app_language}`);
        if (res.data.status !== 'success') {
          throw new Error(res.data.message || 'Failed to fetch categories');
        }
        return res.data.data;
      } catch (error) {
        console.error('Error fetching categories:', error);
        throw error;
      }
    },
    ...defaultQueryOptions,
    ...options,
  });
};

export const useCategoryMovies = (categoryId, options = {}) => {
  const { i18n } = useTranslation();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return useQuery({
    queryKey: ['category-movies', categoryId, app_language],
    queryFn: async () => {
      try {
        const res = await axiosInstance.get(
          `/api/metadata/categories/${categoryId}/movies/?language=${app_language}`
        );
        if (res.data.status !== 'success') {
          throw new Error(res.data.message || 'Failed to fetch category movies');
        }
        return res.data.data;
      } catch (error) {
        console.error('Error fetching category movies:', error);
        throw error;
      }
    },
    enabled: !!categoryId,
    ...defaultQueryOptions,
    ...options,
  });
};

// Hook để prefetch categories khi cần thiết
export const usePrefetchCategories = () => {
  const queryClient = useQueryClient();
  const { i18n } = useTranslation();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return useCallback(async () => {
    await prefetchCategories(queryClient, app_language);
  }, [queryClient, app_language]);
};

// Hook để invalidate categories cache khi cần
export const useInvalidateCategories = () => {
  const queryClient = useQueryClient();
  const { i18n } = useTranslation();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return () => {
    queryClient.invalidateQueries({ queryKey: ['categories', app_language] });
  };
};
