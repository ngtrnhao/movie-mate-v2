import { Suspense } from 'react';

// Loading component cho lazy loading
const LoadingSpinner = ({ size = 'md', className = '' }) => {
  const sizeClasses = {
    sm: 'size-4',
    md: 'size-8',
    lg: 'size-12',
    xl: 'size-16',
  };

  return (
    <div className={`flex items-center justify-center ${className}`}>
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-2 border-red-600 border-t-transparent`}
      ></div>
    </div>
  );
};

// Skeleton loader cho content
const ContentSkeleton = ({ className = '' }) => (
  <div className={`animate-pulse ${className}`}>
    <div className="h-4 bg-gray-700 rounded mb-2"></div>
    <div className="h-4 bg-gray-700 rounded mb-2 w-3/4"></div>
    <div className="h-4 bg-gray-700 rounded w-1/2"></div>
  </div>
);

// Grid skeleton cho movie grid
const GridSkeleton = ({ count = 6, className = '' }) => (
  <div
    className={`grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4 ${className}`}
  >
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="animate-pulse">
        <div className="aspect-[2/3] bg-gray-700 rounded-lg mb-2"></div>
        <div className="h-3 bg-gray-700 rounded mb-1"></div>
        <div className="h-3 bg-gray-700 rounded w-2/3"></div>
      </div>
    ))}
  </div>
);

// LazyLoader component chính
const LazyLoader = ({
  children,
  fallback = <LoadingSpinner />,
  className = '',
  minHeight = 'min-h-[200px]',
}) => {
  return (
    <Suspense
      fallback={
        <div className={`flex items-center justify-center ${minHeight} ${className}`}>
          {fallback}
        </div>
      }
    >
      {children}
    </Suspense>
  );
};

export { LazyLoader, LoadingSpinner, ContentSkeleton, GridSkeleton };
