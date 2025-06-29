import { useState } from 'react';
import { Users, Settings, Image, Heart } from 'lucide-react';
import { getPrimaryRating, getRatingBadgeColors } from '../../../utils/ratingUtils';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link } from 'react-router-dom';

// Import existing components to reuse
import CastSection from '../../../components/movies/movie-details/CastSection';
import MovieReviewSection from './MovieReviewSection';

const MainContent = ({
  movie,
  cast,
  similarMovies = [],
  isLoadingCast = false,
  castError = null,
}) => {
  const { t } = useTranslation('movies');
  const [activeTab, setActiveTab] = useState('cast');

  const tabs = [
    { id: 'cast', label: t('details.tabs.cast'), icon: Users },
    { id: 'technical', label: t('details.tabs.technical'), icon: Settings },
    { id: 'media', label: t('details.tabs.media'), icon: Image },
    { id: 'recommend', label: t('details.tabs.recommend'), icon: Heart },
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
                className={`flex items-center gap-2 border-b-2 px-2 py-4 text-sm font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-500'
                    : 'border-transparent text-gray-400 hover:border-gray-300 hover:text-gray-300'
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
const TechnicalSection = ({ movie }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="space-y-6 text-white">
      <h3 className="mb-4 text-2xl font-bold">{t('details.technicalInfo')}</h3>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
        {movie.runtime && (
          <div className="rounded-lg bg-gray-800/50 p-4">
            <h4 className="mb-2 font-semibold text-gray-300">{t('details.duration')}</h4>
            <p className="text-gray-200">{movie.runtime} phút</p>
          </div>
        )}

        {movie.release_date && (
          <div className="rounded-lg bg-gray-800/50 p-4">
            <h4 className="mb-2 font-semibold text-gray-300">{t('details.releaseDate')}</h4>
            <p className="text-gray-200">
              {new Date(movie.release_date).toLocaleDateString('vi-VN')}
            </p>
          </div>
        )}

        {movie.adult !== undefined && (
          <div className="rounded-lg bg-gray-800/50 p-4">
            <h4 className="mb-2 font-semibold text-gray-300">{t('details.ageRating')}</h4>
            <p className="text-gray-200">
              {movie.is_adult ? t('details.age18') : t('details.suitableForAll')}
            </p>
          </div>
        )}

        {movie.imdb_id && (
          <div className="rounded-lg bg-gray-800/50 p-4">
            <h4 className="mb-2 font-semibold text-gray-300">IMDB ID</h4>
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
          <div className="rounded-lg bg-gray-800/50 p-4">
            <h4 className="mb-2 font-semibold text-gray-300">TMDB ID</h4>
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
          <div className="rounded-lg bg-gray-800/50 p-4">
            <h4 className="mb-2 font-semibold text-gray-300">{t('details.status')}</h4>
            <p className="text-gray-200">{movie.status}</p>
          </div>
        )}
      </div>

      {/* Rating Details */}
      {(movie.cached_imdb_rating || movie.cached_tmdb_rating) && (
        <div>
          <h4 className="mb-4 text-xl font-semibold">{t('details.ratingFromSources')}</h4>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {movie.cached_imdb_rating && (
              <div className="rounded-lg border border-yellow-600/30 bg-yellow-600/20 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">IMDB</span>
                  <span className="text-xl font-bold">{movie.cached_imdb_rating}/10</span>
                </div>
                {movie.cached_imdb_votes && (
                  <p className="mt-1 text-sm text-gray-400">
                    {movie.cached_imdb_votes.toLocaleString()} {t('details.votes')}
                  </p>
                )}
              </div>
            )}

            {movie.cached_tmdb_rating && (
              <div className="rounded-lg border border-blue-600/30 bg-blue-600/20 p-4">
                <div className="flex items-center justify-between">
                  <span className="font-semibold">TMDB</span>
                  <span className="text-xl font-bold">{movie.cached_tmdb_rating}/10</span>
                </div>
                {movie.cached_tmdb_votes && (
                  <p className="mt-1 text-sm text-gray-400">
                    {movie.cached_tmdb_votes.toLocaleString()} {t('details.votes')}
                  </p>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

// Media Section - Enhanced with MovieImage gallery
const MediaSection = ({ movie }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="space-y-6 text-white">
      <h3 className="mb-4 text-2xl font-bold">Hình ảnh</h3>

      {movie.images ? (
        <div className="space-y-8">
          {/* Posters Gallery */}
          {movie.images.posters && movie.images.posters.length > 0 && (
            <div>
              <h4 className="mb-4 text-xl font-semibold text-gray-300">
                Poster ({movie.images.posters.length})
              </h4>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {movie.images.posters.map(poster => (
                  <div
                    key={poster.id}
                    className="group relative overflow-hidden rounded-lg bg-gray-800"
                  >
                    <img
                      src={poster.image_url}
                      alt="Movie Poster"
                      className="h-auto w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      onError={e => {
                        e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                      <span className="text-sm text-white">
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
              <h4 className="mb-4 text-xl font-semibold text-gray-300">
                Backdrop ({movie.images.backdrops.length})
              </h4>
              <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                {movie.images.backdrops.map(backdrop => (
                  <div
                    key={backdrop.id}
                    className="group relative overflow-hidden rounded-lg bg-gray-800"
                  >
                    <img
                      src={backdrop.image_url}
                      alt="Movie Backdrop"
                      className="h-auto w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      onError={e => {
                        e.target.src = 'https://via.placeholder.com/1920x1080?text=No+Image';
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                      <span className="text-sm text-white">
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
              <h4 className="mb-4 text-xl font-semibold text-gray-300">
                Screenshot ({movie.images.screenshots.length})
              </h4>
              <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-4">
                {movie.images.screenshots.map(screenshot => (
                  <div
                    key={screenshot.id}
                    className="group relative overflow-hidden rounded-lg bg-gray-800"
                  >
                    <img
                      src={screenshot.image_url}
                      alt="Movie Screenshot"
                      className="h-auto w-full object-cover transition-transform duration-300 group-hover:scale-105"
                      onError={e => {
                        e.target.src = 'https://via.placeholder.com/1920x1080?text=No+Image';
                      }}
                    />
                    <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition-opacity duration-300 group-hover:opacity-100">
                      <span className="text-sm text-white">
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
              <div className="py-12 text-center">
                <h4 className="mb-2 text-xl font-semibold text-gray-400">
                  {t('details.noImages')}
                </h4>
                <p className="text-gray-500">{t('details.noImagesDesc')}</p>
              </div>
            )}
        </div>
      ) : (
        <div className="py-12 text-center">
          <h4 className="mb-2 text-xl font-semibold text-gray-400">{t('details.loadingImages')}</h4>
          <p className="text-gray-500">{t('details.loadingImagesDesc')}</p>
        </div>
      )}
    </div>
  );
};

// Recommend Tab Section
const RecommendTabSection = ({ similarMovies }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="space-y-6 text-white">
      {similarMovies && similarMovies.length > 0 ? (
        <div>
          <h3 className="mb-4 text-2xl font-bold">{t('details.similarMovies')}</h3>
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6">
            {similarMovies.map(movie => (
              <div
                key={movie.id}
                className="group relative overflow-hidden rounded-lg bg-gray-800 transition-transform hover:scale-105"
              >
                <Link to={`/movies/${movie.id}`}>
                  <div className="aspect-[2/3] w-full overflow-hidden">
                    <img
                      src={movie.poster_url || movie.poster_path}
                      alt={movie.title}
                      className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                      onError={e => {
                        e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                      }}
                    />
                  </div>
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-4">
                    <h4 className="line-clamp-1 text-sm font-semibold text-white">{movie.title}</h4>
                    <div className="mt-1 flex items-center gap-2">
                      {movie.rating && (
                        <span className="text-xs text-yellow-500">★ {movie.rating.toFixed(1)}</span>
                      )}
                      {movie.release_date && (
                        <span className="text-xs text-gray-400">
                          {new Date(movie.release_date).getFullYear()}
                        </span>
                      )}
                    </div>
                  </div>
                </Link>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-dashed border-gray-600 p-8 text-center">
          <div>
            <p className="text-lg font-medium text-white">{t('details.comingSoon')}</p>
            <p className="text-sm text-gray-400">{t('details.similarMovies')}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainContent;
