import React, { memo } from 'react';

const LoadingGrid = memo(({ count = 12 }) => {
  return (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6">
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="animate-pulse rounded-lg bg-gray-800 shadow-lg"
          style={{
            // GPU optimization
            transform: 'translateZ(0)',
            backfaceVisibility: 'hidden',
            // Stagger animation delays để prevent simultaneous start
            animationDelay: `${(index % 6) * 50}ms`,
          }}
        >
          {/* Poster skeleton */}
          <div className="aspect-[2/3] w-full rounded-t-lg bg-gray-700" />

          {/* Content skeleton */}
          <div className="p-3">
            {/* Title skeleton */}
            <div className="mb-2 h-4 rounded bg-gray-700" />
            <div className="h-3 w-3/4 rounded bg-gray-700" />
          </div>
        </div>
      ))}
    </div>
  );
});

LoadingGrid.displayName = 'LoadingGrid';

export default LoadingGrid;
