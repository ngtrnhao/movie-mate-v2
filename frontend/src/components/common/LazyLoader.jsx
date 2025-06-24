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
    <div className="mb-2 h-4 rounded bg-gray-700"></div>
    <div className="mb-2 h-4 w-3/4 rounded bg-gray-700"></div>
    <div className="h-4 w-1/2 rounded bg-gray-700"></div>
  </div>
);

// Grid skeleton cho movie grid
const GridSkeleton = ({ count = 6, className = '' }) => (
  <div
    className={`grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 ${className}`}
  >
    {Array.from({ length: count }).map((_, index) => (
      <div key={index} className="animate-pulse">
        <div className="mb-2 aspect-[2/3] rounded-lg bg-gray-700"></div>
        <div className="mb-1 h-3 rounded bg-gray-700"></div>
        <div className="h-3 w-2/3 rounded bg-gray-700"></div>
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
