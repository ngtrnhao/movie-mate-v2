import { useNavigate } from 'react-router-dom';
import LoadingSpinner from '../common/LoadingSpinner';
import './CategoryGrid.css';

// const genreImages = {
//   'Phim Hành Động':
//     'https://images.unsplash.com/photo-1467987506553-8f3916508521?auto=format&fit=crop&w=400&q=80',
// };

const defaultImage =
  'https://images.unsplash.com/photo-1517602302552-471fe67acf66?auto=format&fit=crop&w=400&q=80';

const CategoryGrid = ({ categories, onCategoryClick, loading }) => {
  const navigate = useNavigate();

  const handleCategoryClick = category => {
    if (onCategoryClick) {
      onCategoryClick(category);
    } else {
      navigate(`/categories/${category.slug}`);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-10">
        <LoadingSpinner />
      </div>
    );
  }

  if (!categories || categories.length === 0) {
    return <div className="py-10 text-center text-gray-400">No categories found.</div>;
  }

  return (
    <div className="mt-10 grid grid-cols-1 gap-8 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
      {categories.map(cat => {
        // Ưu tiên poster của latest_movie, fallback sang genreImages hoặc defaultImage
        const posterUrl = cat.latest_movie?.poster_url || defaultImage; //|| genreImages[cat.name]

        return (
          <div
            key={cat.id}
            className="glow-hover group relative cursor-pointer overflow-hidden rounded-xl border-2 border-transparent transition-all duration-300 hover:-translate-y-2 hover:ring-2 hover:ring-red-500"
            style={{
              minHeight: 220,
              backgroundImage: `url(${posterUrl})`,
              backgroundSize: 'cover',
              backgroundPosition: 'center',
            }}
            onClick={() => handleCategoryClick(cat)}
          >
            {/* Overlay */}
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent opacity-80 transition-all duration-300 group-hover:opacity-90"></div>

            {/* Nút CTA ở giữa card */}
            <div className="absolute inset-0 z-20 flex items-center justify-center opacity-0 transition-opacity duration-300 group-hover:opacity-100">
              <button
                className="flex items-center gap-2 rounded-full bg-red-600 px-5 py-2 text-sm font-semibold text-white shadow-lg transition-all duration-300 hover:scale-105 hover:bg-red-700"
                onClick={e => {
                  e.stopPropagation();
                  handleCategoryClick(cat);
                }}
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
              <h3 className="text-xl font-bold text-white drop-shadow">{cat.name}</h3>
              <p className="text-sm text-gray-200">{cat.count} movies</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CategoryGrid;
