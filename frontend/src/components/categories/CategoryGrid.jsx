import { useNavigate } from 'react-router-dom';
import { useCallback, useMemo, memo } from 'react';
import RetryImage from '../common/RetryImage';
import './CategoryGrid.css';

// Fallback images cho từng category
const categoryFallbackImages = {
  Action:
    'https://images.unsplash.com/photo-1467987506553-8f3916508521?auto=format&fit=crop&w=400&q=80',
  Drama:
    'https://images.unsplash.com/photo-1517604931442-7e0c8ed2963c?auto=format&fit=crop&w=400&q=80',
  Comedy:
    'https://images.unsplash.com/photo-1512070679279-8988d32161be?auto=format&fit=crop&w=400&q=80',
  Horror:
    'https://images.unsplash.com/photo-1509347528160-9a9e33742cdb?auto=format&fit=crop&w=400&q=80',
  Romance:
    'https://images.unsplash.com/photo-1517602302552-471fe67acf66?auto=format&fit=crop&w=400&q=80',
  'Sci-Fi':
    'https://images.unsplash.com/photo-1518709268805-4e9042af2176?auto=format&fit=crop&w=400&q=80',
  Thriller:
    'https://images.unsplash.com/photo-1512070679279-8988d32161be?auto=format&fit=crop&w=400&q=80',
};

const defaultImage =
  'https://images.unsplash.com/photo-1517602302552-471fe67acf66?auto=format&fit=crop&w=400&q=80';

// Component tối ưu cho Category Card với memo
const CategoryCard = memo(({ category, onClick }) => {
  // Memoize poster URL để tránh re-render
  const posterUrl = useMemo(
    () =>
      category.latest_movie?.poster_url || categoryFallbackImages[category.name] || defaultImage,
    [category.latest_movie?.poster_url, category.name]
  );

  // Memoize fallback URL
  const fallbackUrl = useMemo(
    () => categoryFallbackImages[category.name] || defaultImage,
    [category.name]
  );

  // Memoize click handler
  const handleClick = useCallback(() => {
    onClick(category);
  }, [onClick, category]);

  const handleButtonClick = useCallback(
    e => {
      e.stopPropagation();
      onClick(category);
    },
    [onClick, category]
  );

  return (
    <div
      className="glow-hover group relative cursor-pointer overflow-hidden rounded-xl border-2 border-transparent transition-all duration-300 hover:-translate-y-2 hover:ring-2 hover:ring-red-500"
      style={{ minHeight: 220 }}
      onClick={handleClick}
    >
      {/* Background Image với RetryImage */}
      <RetryImage
        src={posterUrl}
        alt={category.name}
        fallbackSrc={fallbackUrl}
        maxRetries={3}
        retryDelay={1000}
        className="absolute inset-0 size-full object-cover"
        loading="lazy"
      />

      {/* Overlay */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent opacity-80 transition-all duration-300 group-hover:opacity-90"></div>

      {/* Nút CTA ở giữa card */}
      <div className="absolute inset-0 z-20 flex items-center justify-center opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <button
          className="flex items-center gap-2 rounded-full bg-red-600 px-5 py-2 text-sm font-semibold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:bg-red-700"
          onClick={handleButtonClick}
        >
          Khám phá
          <svg
            className="size-4"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M14 5l7 7m0 0l-7 7m7-7H3" />
          </svg>
        </button>
      </div>

      {/* Nội dung */}
      <div className="absolute inset-x-0 bottom-0 z-10 p-4">
        <h3 className="text-xl font-bold text-white drop-shadow">{category.name}</h3>
        <p className="text-sm text-gray-200">{category.count} movies</p>
      </div>
    </div>
  );
});

CategoryCard.displayName = 'CategoryCard';

// Error boundary component cho categories
const CategoryErrorFallback = ({ error, retry }) => (
  <div className="flex flex-col items-center justify-center py-10 text-center">
    <div className="mb-4 text-red-500">
      <svg className="mx-auto size-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
        />
      </svg>
    </div>
    <h3 className="mb-2 text-lg font-semibold text-white">Failed to load categories</h3>
    <p className="mb-4 text-sm text-gray-400">{error?.message || 'Something went wrong'}</p>
    <button
      onClick={retry}
      className="rounded-md bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-700"
    >
      Try Again
    </button>
  </div>
);

// Loading skeleton component
const CategorySkeleton = () => (
  <div className="grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
    {Array.from({ length: 8 }).map((_, index) => (
      <div
        key={index}
        className="relative h-56 animate-pulse overflow-hidden rounded-xl bg-gray-800"
      >
        <div className="absolute inset-0 bg-gradient-to-t from-gray-800 to-gray-700"></div>
        <div className="absolute inset-x-4 bottom-4">
          <div className="mb-2 h-6 w-3/4 rounded bg-gray-600"></div>
          <div className="h-4 w-1/2 rounded bg-gray-600"></div>
        </div>
      </div>
    ))}
  </div>
);

const CategoryGrid = memo(({ categories, onCategoryClick, loading, error, retry }) => {
  const navigate = useNavigate();

  const handleCategoryClick = useCallback(
    category => {
      if (onCategoryClick) {
        onCategoryClick(category);
      } else {
        // Navigate to movies page with genre filter
        navigate(`/movies?genres=${category.id}&sort_by=popularity&order=desc`);
      }
    },
    [onCategoryClick, navigate]
  );

  // Memoize grid className
  const gridClassName = useMemo(() => {
    return 'mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4';
  }, []);

  // Memoize sorted categories để tránh re-render
  const sortedCategories = useMemo(() => {
    if (!categories) return [];
    return [...categories].sort((a, b) => b.count - a.count);
  }, [categories]);

  // Error state
  if (error) {
    return <CategoryErrorFallback error={error} retry={retry} />;
  }

  // Loading state
  if (loading) {
    return <CategorySkeleton />;
  }

  // Empty state
  if (!categories || categories.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-10 text-center">
        <div className="mb-4 text-gray-400">
          <svg className="mx-auto size-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"
            />
          </svg>
        </div>
        <h3 className="mb-2 text-lg font-semibold text-white">No categories found</h3>
        <p className="text-sm text-gray-400">Try refreshing the page or check back later.</p>
      </div>
    );
  }

  return (
    <div className={gridClassName}>
      {sortedCategories.map(category => (
        <CategoryCard key={category.id} category={category} onClick={handleCategoryClick} />
      ))}
    </div>
  );
});

CategoryGrid.displayName = 'CategoryGrid';

export default CategoryGrid;
