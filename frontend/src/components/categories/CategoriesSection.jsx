import { memo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from '../../i18n/hooks/useTranslation';
import { useCategories } from '../../hooks/useCategories';
import CategoryGrid from './CategoryGrid';
import { LazyLoader, GridSkeleton } from '../common/LazyLoader';

const CategoriesSection = memo(() => {
  const { t } = useTranslation('landing');
  const navigate = useNavigate();

  // Sử dụng hook với options tối ưu cho section này
  const {
    data: categories,
    isLoading: catLoading,
    error: catError,
    refetch: refetchCategories,
  } = useCategories({
    staleTime: 20 * 60 * 1000, // 20 phút
    placeholderData: [],
  });

  // Memoize handlers
  const handleViewAllCategories = useCallback(() => {
    navigate('/categories');
  }, [navigate]);

  const handleCategoryClick = useCallback(
    category => {
      // Navigate to movies page with genre filter
      navigate(`/movies?genres=${category.id}&sort_by=popularity&order=desc`);
    },
    [navigate]
  );

  return (
    <section className="relative bg-gradient-to-b from-gray-900 via-gray-900 to-black py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center"
        >
          <h2 className="text-center text-3xl font-bold text-white sm:text-4xl">
            {t('exploreCategories.title')}
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-gray-400">
            {t('exploreCategories.subtitle')}
          </p>

          {/* Categories Grid */}
          <LazyLoader fallback={<GridSkeleton count={8} />}>
            <CategoryGrid
              categories={categories}
              onCategoryClick={handleCategoryClick}
              loading={catLoading}
              error={catError}
              retry={refetchCategories}
            />
          </LazyLoader>

          {/* View All Button */}
          <div className="mt-8 flex justify-center">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handleViewAllCategories}
              className="flex items-center rounded-sm bg-red-600 px-8 py-3 text-sm font-semibold text-white transition-colors duration-300 hover:bg-red-700"
            >
              {t('exploreCategories.viewAllCategories')}
              <motion.span
                animate={{ x: [0, 5, 0] }}
                transition={{ duration: 1.5, repeat: Infinity }}
                className="ml-2 flex items-center"
              >
                <svg
                  className="size-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  xmlns="http://www.w3.org/2000/svg"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M14 5l7 7m0 0l-7 7m7-7H3"
                  />
                </svg>
              </motion.span>
            </motion.button>
          </div>
        </motion.div>
      </div>
    </section>
  );
});

CategoriesSection.displayName = 'CategoriesSection';

export default CategoriesSection;
