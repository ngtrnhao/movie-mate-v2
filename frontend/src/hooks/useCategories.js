import { useQuery } from '@tanstack/react-query';
import { useTranslation } from '../i18n/hooks/useTranslation';
import axiosInstance from '../api/axios';

// Tối ưu query options để tránh re-render
const defaultQueryOptions = {
  staleTime: 10 * 60 * 1000, // 10 phút
  cacheTime: 30 * 60 * 1000, // 30 phút
  refetchOnWindowFocus: false,
  refetchOnMount: false,
  refetchOnReconnect: false,
  retry: 1,
  retryDelay: 1000,
};

export const useCategories = () => {
  const { i18n } = useTranslation();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return useQuery({
    queryKey: ['categories', app_language],
    queryFn: async () => {
      const res = await axiosInstance.get(`/api/metadata/categories/?language=${app_language}`);
      if (res.data.status !== 'success') {
        throw new Error(res.data.message || 'Failed to fetch categories');
      }
      return res.data.data;
    },
    ...defaultQueryOptions,
  });
};

export const useCategoryMovies = categoryId => {
  const { i18n } = useTranslation();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return useQuery({
    queryKey: ['category-movies', categoryId, app_language],
    queryFn: async () => {
      const res = await axiosInstance.get(
        `/api/metadata/categories/${categoryId}/movies/?language=${app_language}`
      );
      if (res.data.status !== 'success') {
        throw new Error(res.data.message || 'Failed to fetch category movies');
      }
      return res.data.data;
    },
    enabled: !!categoryId,
    ...defaultQueryOptions,
  });
};
