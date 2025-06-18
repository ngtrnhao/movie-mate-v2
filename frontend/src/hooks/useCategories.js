import { useQuery } from '@tanstack/react-query';
import axiosInstance from '../api/axios';
import { useTranslation } from 'react-i18next';

const fetchCategories = async language => {
  const res = await axiosInstance.get(`/api/metadata/categories/?language=${language}`);
  if (res.data.status !== 'success') {
    throw new Error(res.data.message || 'Failed to fetch categories');
  }
  return res.data.data;
};

export const useCategories = () => {
  const { i18n } = useTranslation();
  const app_language = i18n.language === 'vi' ? 'vi' : 'en';

  return useQuery({
    queryKey: ['categories', app_language],
    queryFn: () => fetchCategories(app_language),
    staleTime: Infinity, // cache vĩnh viễn
    cacheTime: Infinity, // cache vĩnh viễn
    refetchOnWindowFocus: false,
    refetchOnMount: false,
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
    staleTime: Infinity, // cache vĩnh viễn
    cacheTime: Infinity, // cache vĩnh viễn
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};
