// import React from 'react';

const CategoryGrid = ({ categories, onCategoryClick }) => (
  <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
    {categories.map((cat) => (
      <div
        key={cat.id}
        className="group relative cursor-pointer rounded-lg bg-gradient-to-b from-gray-200 to-gray-700 p-6 shadow-lg transition-all duration-300 hover:-translate-y-2 hover:ring-2 hover:ring-red-500"
        onClick={() => onCategoryClick?.(cat)}
      >
        {/* Placeholder image or icon */}
        <div className="absolute inset-0 flex items-center justify-center opacity-10">
          <svg width="64" height="64" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="32" cy="32" r="30" />
            <rect x="20" y="20" width="24" height="24" rx="4" />
          </svg>
        </div>
        <div className="relative z-10 mt-24">
          <h3 className="mb-1 text-lg font-bold text-white">{cat.name}</h3>
          <p className="text-sm text-gray-200">{cat.count} movies</p>
        </div>
      </div>
    ))}
  </div>
);

export default CategoryGrid;
