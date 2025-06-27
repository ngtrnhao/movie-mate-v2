import { useState } from 'react';
import { Users, Settings, Image, Heart } from 'lucide-react';

// Import existing components to reuse
import CastSection from '../../../components/movies/movie-details/CastSection';
import MovieReviewSection from './MovieReviewSection';
import SimilarMovies from '../../../components/movies/movie-details/SimilarMovies';

const MainContent = ({
  movie,
  cast,
  similarMovies = [],
  isLoadingCast = false,
  castError = null,
}) => {
  const [activeTab, setActiveTab] = useState('cast');

  const tabs = [
    { id: 'cast', label: 'Diễn viên', icon: Users },
    { id: 'technical', label: 'Thông tin kỹ thuật', icon: Settings },
    { id: 'media', label: 'Hình ảnh', icon: Image },
    { id: 'recommend', label: 'Đề xuất', icon: Heart },
  ];

  if (!movie) return null;

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 py-4 px-2 border-b-2 font-medium text-sm transition-colors ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-500'
                    : 'border-transparent text-gray-400 hover:text-gray-300 hover:border-gray-300'
                }`}
              >
                <Icon size={18} />
                {tab.label}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="min-h-[400px]">
        {activeTab === 'cast' && (
          <CastTabSection cast={cast} isLoading={isLoadingCast} error={castError} />
        )}
        {activeTab === 'technical' && <TechnicalSection movie={movie} />}
        {activeTab === 'media' && <MediaSection movie={movie} />}
        {activeTab === 'recommend' && <RecommendTabSection similarMovies={similarMovies} />}
      </div>

      {/* Movie Reviews Section - Below Tabs */}
      <div className="border-t border-gray-700 pt-6">
        <MovieReviewSection movieId={movie?.id} />
      </div>
    </div>
  );
};

// Cast Tab Section - reuse existing CastSection component with loading states
const CastTabSection = ({ cast, isLoading, error }) => (
  <div className="text-white">
    <CastSection cast={cast} isLoading={isLoading} error={error} />
  </div>
);

// Technical Details Section
const TechnicalSection = ({ movie }) => (
  <div className="space-y-6 text-white">
    <h3 className="text-2xl font-bold mb-4">Thông tin kỹ thuật</h3>

    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {movie.runtime && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-300 mb-2">Thời lượng</h4>
          <p className="text-gray-200">{movie.runtime} phút</p>
        </div>
      )}

      {movie.release_date && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-300 mb-2">Ngày phát hành</h4>
          <p className="text-gray-200">
            {new Date(movie.release_date).toLocaleDateString('vi-VN')}
          </p>
        </div>
      )}

      {movie.adult !== undefined && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-300 mb-2">Giới hạn tuổi</h4>
          <p className="text-gray-200">{movie.is_adult ? '18+' : 'Phù hợp mọi lứa tuổi'}</p>
        </div>
      )}

      {movie.imdb_id && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-300 mb-2">IMDB ID</h4>
          <a
            href={`https://www.imdb.com/title/${movie.imdb_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-yellow-400 hover:text-yellow-300"
          >
            {movie.imdb_id}
          </a>
        </div>
      )}

      {movie.tmdb_id && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-300 mb-2">TMDB ID</h4>
          <a
            href={`https://www.themoviedb.org/movie/${movie.tmdb_id}`}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300"
          >
            {movie.tmdb_id}
          </a>
        </div>
      )}

      {movie.status && (
        <div className="bg-gray-800/50 p-4 rounded-lg">
          <h4 className="font-semibold text-gray-300 mb-2">Trạng thái sản xuất</h4>
          <p className="text-gray-200">{movie.status}</p>
        </div>
      )}
    </div>

    {/* Rating Details */}
    {(movie.cached_imdb_rating || movie.cached_tmdb_rating) && (
      <div>
        <h4 className="text-xl font-semibold mb-4">Đánh giá từ các nguồn</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {movie.cached_imdb_rating && (
            <div className="bg-yellow-600/20 p-4 rounded-lg border border-yellow-600/30">
              <div className="flex items-center justify-between">
                <span className="font-semibold">IMDB</span>
                <span className="text-xl font-bold">{movie.cached_imdb_rating}/10</span>
              </div>
              {movie.cached_imdb_votes && (
                <p className="text-sm text-gray-400 mt-1">
                  {movie.cached_imdb_votes.toLocaleString()} lượt đánh giá
                </p>
              )}
            </div>
          )}

          {movie.cached_tmdb_rating && (
            <div className="bg-blue-600/20 p-4 rounded-lg border border-blue-600/30">
              <div className="flex items-center justify-between">
                <span className="font-semibold">TMDB</span>
                <span className="text-xl font-bold">{movie.cached_tmdb_rating}/10</span>
              </div>
              {movie.cached_tmdb_votes && (
                <p className="text-sm text-gray-400 mt-1">
                  {movie.cached_tmdb_votes.toLocaleString()} lượt đánh giá
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    )}
  </div>
);

// Media Section - Enhanced with MovieImage gallery
const MediaSection = ({ movie }) => (
  <div className="space-y-6 text-white">
    <h3 className="text-2xl font-bold mb-4">Hình ảnh</h3>

    {movie.images ? (
      <div className="space-y-8">
        {/* Posters Gallery */}
        {movie.images.posters && movie.images.posters.length > 0 && (
          <div>
            <h4 className="text-xl font-semibold text-gray-300 mb-4">
              Poster ({movie.images.posters.length})
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {movie.images.posters.map(poster => (
                <div
                  key={poster.id}
                  className="group relative overflow-hidden rounded-lg bg-gray-800"
                >
                  <img
                    src={poster.image_url}
                    alt="Movie Poster"
                    className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={e => {
                      e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                    }}
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                    <span className="text-white text-sm">
                      {poster.width}x{poster.height}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Backdrops Gallery */}
        {movie.images.backdrops && movie.images.backdrops.length > 0 && (
          <div>
            <h4 className="text-xl font-semibold text-gray-300 mb-4">
              Backdrop ({movie.images.backdrops.length})
            </h4>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {movie.images.backdrops.map(backdrop => (
                <div
                  key={backdrop.id}
                  className="group relative overflow-hidden rounded-lg bg-gray-800"
                >
                  <img
                    src={backdrop.image_url}
                    alt="Movie Backdrop"
                    className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={e => {
                      e.target.src = 'https://via.placeholder.com/1920x1080?text=No+Image';
                    }}
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                    <span className="text-white text-sm">
                      {backdrop.width}x{backdrop.height}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Screenshots Gallery */}
        {movie.images.screenshots && movie.images.screenshots.length > 0 && (
          <div>
            <h4 className="text-xl font-semibold text-gray-300 mb-4">
              Screenshot ({movie.images.screenshots.length})
            </h4>
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {movie.images.screenshots.map(screenshot => (
                <div
                  key={screenshot.id}
                  className="group relative overflow-hidden rounded-lg bg-gray-800"
                >
                  <img
                    src={screenshot.image_url}
                    alt="Movie Screenshot"
                    className="w-full h-auto object-cover transition-transform duration-300 group-hover:scale-105"
                    onError={e => {
                      e.target.src = 'https://via.placeholder.com/1920x1080?text=No+Image';
                    }}
                  />
                  <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-center justify-center">
                    <span className="text-white text-sm">
                      {screenshot.width}x{screenshot.height}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* No Images Found */}
        {(!movie.images.posters || movie.images.posters.length === 0) &&
          (!movie.images.backdrops || movie.images.backdrops.length === 0) &&
          (!movie.images.screenshots || movie.images.screenshots.length === 0) && (
            <div className="text-center py-12">
              <h4 className="text-xl font-semibold text-gray-400 mb-2">Không có hình ảnh</h4>
              <p className="text-gray-500">Chưa có hình ảnh nào được thêm cho phim này.</p>
            </div>
          )}
      </div>
    ) : (
      <div className="text-center py-12">
        <h4 className="text-xl font-semibold text-gray-400 mb-2">Đang tải hình ảnh...</h4>
        <p className="text-gray-500">Vui lòng đợi trong giây lát.</p>
      </div>
    )}
  </div>
);

// Recommend Tab Section
const RecommendTabSection = ({ similarMovies }) => (
  <div className="space-y-6 text-white">
    {similarMovies && similarMovies.length > 0 ? (
      <div>
        <h3 className="text-2xl font-bold mb-4">Phim tương tự</h3>
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
          {similarMovies.map(movie => (
            <div
              key={movie.id}
              className="group relative overflow-hidden rounded-lg bg-gray-800 transition-transform hover:scale-105"
            >
              <div className="aspect-[2/3] w-full overflow-hidden">
                <img
                  src={
                    movie.poster_url ||
                    movie.poster_path ||
                    'https://via.placeholder.com/500x750?text=No+Image'
                  }
                  alt={movie.title || movie.title_en || 'Movie'}
                  className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                  onError={e => {
                    e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                  }}
                />
              </div>

              {/* Movie Info */}
              <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-3">
                <h4 className="line-clamp-2 text-sm font-semibold text-white">
                  {movie.title_vi || movie.title_en || movie.title || 'No Title'}
                </h4>
                <div className="mt-1 flex items-center gap-2">
                  {(() => {
                    // Handle different rating formats
                    let ratingValue = null;

                    if (typeof movie.rating === 'number') {
                      ratingValue = movie.rating;
                    } else if (movie.rating && typeof movie.rating === 'object') {
                      ratingValue =
                        movie.rating.imdb || movie.rating.tmdb || movie.rating.combined_score;
                    } else if (movie.cached_imdb_rating) {
                      ratingValue = parseFloat(movie.cached_imdb_rating);
                    } else if (movie.vote_average) {
                      ratingValue = parseFloat(movie.vote_average);
                    }

                    return ratingValue && ratingValue > 0 ? (
                      <div className="flex items-center gap-1">
                        <span className="text-yellow-400">★</span>
                        <span className="text-xs text-gray-300">{ratingValue.toFixed(1)}</span>
                      </div>
                    ) : null;
                  })()}
                  {movie.release_date && (
                    <span className="text-xs text-gray-400">
                      {new Date(movie.release_date).getFullYear()}
                    </span>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    ) : (
      <div className="text-center py-12">
        <h3 className="text-xl font-semibold text-gray-400 mb-2">Không có phim tương tự</h3>
        <p className="text-gray-500">Chúng tôi đang cập nhật thêm phim tương tự cho bạn.</p>
      </div>
    )}
  </div>
);

export default MainContent;
