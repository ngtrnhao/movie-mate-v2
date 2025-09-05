import { useState } from 'react';
import { Users, Settings, Image, Film } from 'lucide-react';
import { useTranslation } from '../../../i18n/hooks/useTranslation';
import { Link } from 'react-router-dom';

// Import existing components to reuse
import CastSection from '../../../components/movies/movie-details/CastSection';
import MovieReviewSection from './MovieReviewSection';
import ProductionCompanies from '../../../components/movies/ProductionCompanies';

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
    { id: 'similar', label: t('details.tabs.similar'), icon: Film },
  ];

  if (!movie) return null;

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Tab Navigation - Responsive */}
      <div className="border-b border-gray-700">
        <nav className="flex space-x-4 overflow-x-auto sm:space-x-8">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1 border-b-2 px-2 py-3 text-xs font-medium transition-colors sm:gap-2 sm:px-2 sm:py-4 sm:text-sm ${
                  activeTab === tab.id
                    ? 'border-red-500 text-red-500'
                    : 'border-transparent text-gray-400 hover:border-gray-300 hover:text-gray-300'
                }`}
              >
                <Icon size={16} className="sm:size-18" />
                <span className="hidden sm:inline">{tab.label}</span>
                <span className="sm:hidden">{tab.label.split(' ')[0]}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Tab Content - Responsive min-height */}
      <div className="min-h-[300px] sm:min-h-[400px]">
        {activeTab === 'cast' && (
          <CastTabSection cast={cast} isLoading={isLoadingCast} error={castError} />
        )}
        {activeTab === 'technical' && <TechnicalSection movie={movie} />}
        {activeTab === 'media' && <MediaSection movie={movie} />}
        {activeTab === 'similar' && <SimilarMoviesSection similarMovies={similarMovies} />}
      </div>

      {/* Movie Reviews Section - Below Tabs - Responsive spacing */}
      <div className="border-t border-gray-700 pt-4 sm:pt-6">
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

// Technical Details Section - Responsive
const TechnicalSection = ({ movie }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="space-y-4 text-white sm:space-y-6">
      <h3 className="mb-3 text-xl font-bold sm:mb-4 sm:text-2xl">{t('details.technicalInfo')}</h3>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {movie.runtime && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.duration')}
            </h4>
            <p className="text-sm text-gray-200 sm:text-base">{movie.runtime} phút</p>
          </div>
        )}

        {movie.release_date && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.releaseDate')}
            </h4>
            <p className="text-sm text-gray-200 sm:text-base">
              {new Date(movie.release_date).toLocaleDateString('vi-VN', {
                day: '2-digit',
                month: '2-digit',
                year: 'numeric',
              })}
            </p>
          </div>
        )}

        {movie.adult !== undefined && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.ageRating')}
            </h4>
            <p className="text-sm text-gray-200 sm:text-base">
              {movie.is_adult ? t('details.age18') : t('details.suitableForAll')}
            </p>
          </div>
        )}

        {movie.imdb_id && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">IMDB ID</h4>
            <a
              href={`https://www.imdb.com/title/${movie.imdb_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-yellow-400 hover:text-yellow-300 sm:text-base"
            >
              {movie.imdb_id}
            </a>
          </div>
        )}

        {movie.tmdb_id && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">TMDB ID</h4>
            <a
              href={`https://www.themoviedb.org/movie/${movie.tmdb_id}`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-400 hover:text-blue-300 sm:text-base"
            >
              {movie.tmdb_id}
            </a>
          </div>
        )}

        {movie.status && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.status')}
            </h4>
            <p className="text-sm text-gray-200 sm:text-base">{movie.status}</p>
          </div>
        )}

        {/* Budget - New addition */}
        {movie.production_info?.budget && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.budget')}
            </h4>
            <p className="text-sm text-gray-200 sm:text-base">
              ${(movie.production_info.budget / 1000000).toFixed(1)}M
            </p>
          </div>
        )}

        {/* Revenue - New addition */}
        {movie.production_info?.revenue && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.revenue')}
            </h4>
            <p className="text-sm text-gray-200 sm:text-base">
              ${(movie.production_info.revenue / 1000000).toFixed(1)}M
            </p>
          </div>
        )}

        {/* Homepage - New addition */}
        {movie.production_info?.homepage && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.homepage')}
            </h4>
            <a
              href={movie.production_info.homepage}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-400 hover:text-blue-300 sm:text-base"
            >
              {t('details.visitHomepage')}
            </a>
          </div>
        )}

        {/* Production Countries - Enhanced display */}
        {movie.production_info?.production_countries?.length > 0 && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.country')}
            </h4>
            <div className="flex flex-wrap gap-1">
              {movie.production_info.production_countries.map((country, index) => (
                <span
                  key={index}
                  className="rounded bg-white/20 px-2 py-1 text-xs font-medium backdrop-blur-sm"
                >
                  {country.name || country}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Spoken Languages - Enhanced display */}
        {movie.production_info?.spoken_languages?.length > 0 && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-semibold text-gray-300 sm:text-base">
              {t('details.language')}
            </h4>
            <div className="flex flex-wrap gap-1">
              {movie.production_info.spoken_languages.map((language, index) => (
                <span
                  key={index}
                  className="rounded bg-white/20 px-2 py-1 text-xs font-medium backdrop-blur-sm uppercase"
                >
                  {language.name || language}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Production Companies - Enhanced display */}
        {movie.production_info?.production_companies?.length > 0 && (
          <div className="rounded-lg bg-gray-800/50 p-3 sm:p-4">
            <ProductionCompanies
              companies={movie.production_info.production_companies}
              maxDisplay={4}
              showDetails={false}
            />
          </div>
        )}
      </div>

      {/* Rating Details - Responsive */}
      {(movie.cached_imdb_rating || movie.cached_tmdb_rating) && (
        <div>
          <h4 className="mb-3 text-lg font-semibold sm:mb-4 sm:text-xl">
            {t('details.ratingFromSources')}
          </h4>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4">
            {movie.cached_imdb_rating && (
              <div className="rounded-lg border border-yellow-600/30 bg-yellow-600/20 p-3 sm:p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold sm:text-base">IMDB</span>
                  <span className="text-lg font-bold sm:text-xl">
                    {movie.cached_imdb_rating}/10
                  </span>
                </div>
                {movie.cached_imdb_votes && (
                  <p className="mt-1 text-xs text-gray-400 sm:text-sm">
                    {movie.cached_imdb_votes.toLocaleString()} {t('details.votes')}
                  </p>
                )}
              </div>
            )}

            {movie.cached_tmdb_rating && (
              <div className="rounded-lg border border-blue-600/30 bg-blue-600/20 p-3 sm:p-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-semibold sm:text-base">TMDB</span>
                  <span className="text-lg font-bold sm:text-xl">
                    {movie.cached_tmdb_rating}/10
                  </span>
                </div>
                {movie.cached_tmdb_votes && (
                  <p className="mt-1 text-xs text-gray-400 sm:text-sm">
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

// Media Section - Enhanced with MovieImage gallery - Responsive
const MediaSection = ({ movie }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="space-y-4 text-white sm:space-y-6">
      <h3 className="mb-3 text-xl font-bold sm:mb-4 sm:text-2xl">Hình ảnh</h3>

      {movie.images ? (
        <div className="space-y-6 sm:space-y-8">
          {/* Posters Gallery - Responsive grid */}
          {movie.images.posters && movie.images.posters.length > 0 && (
            <div>
              <h4 className="mb-3 text-lg font-semibold text-gray-300 sm:mb-4 sm:text-xl">
                Poster ({movie.images.posters.length})
              </h4>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
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
                      <span className="text-xs text-white sm:text-sm">
                        {poster.width}x{poster.height}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Backdrops Gallery - Responsive grid */}
          {movie.images.backdrops && movie.images.backdrops.length > 0 && (
            <div>
              <h4 className="mb-3 text-lg font-semibold text-gray-300 sm:mb-4 sm:text-xl">
                Backdrop ({movie.images.backdrops.length})
              </h4>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 sm:gap-4">
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
                      <span className="text-xs text-white sm:text-sm">
                        {backdrop.width}x{backdrop.height}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Screenshots Gallery - Responsive grid */}
          {movie.images.screenshots && movie.images.screenshots.length > 0 && (
            <div>
              <h4 className="mb-3 text-lg font-semibold text-gray-300 sm:mb-4 sm:text-xl">
                Screenshot ({movie.images.screenshots.length})
              </h4>
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 lg:grid-cols-4">
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
                      <span className="text-xs text-white sm:text-sm">
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
              <div className="py-8 text-center sm:py-12">
                <h4 className="mb-2 text-lg font-semibold text-gray-400 sm:text-xl">
                  {t('details.noImages')}
                </h4>
                <p className="text-sm text-gray-500 sm:text-base">{t('details.noImagesDesc')}</p>
              </div>
            )}
        </div>
      ) : (
        <div className="py-8 text-center sm:py-12">
          <h4 className="mb-2 text-lg font-semibold text-gray-400 sm:text-xl">
            {t('details.loadingImages')}
          </h4>
          <p className="text-sm text-gray-500 sm:text-base">{t('details.loadingImagesDesc')}</p>
        </div>
      )}
    </div>
  );
};

// Similar Movies Section - renamed from RecommendTabSection - Responsive
const SimilarMoviesSection = ({ similarMovies }) => {
  const { t } = useTranslation('movies');

  return (
    <div className="space-y-4 text-white sm:space-y-6">
      {similarMovies && similarMovies.length > 0 ? (
        <div>
          <h3 className="mb-3 text-xl font-bold sm:mb-4 sm:text-2xl">
            {t('details.similarMovies')}
          </h3>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 sm:gap-4 md:grid-cols-4 lg:grid-cols-6">
            {similarMovies.map(movie => (
              <div
                key={movie.id}
                className="group relative overflow-hidden rounded-lg bg-gray-800 transition-transform hover:scale-105"
              >
                <Link to={`/movies/${movie.id}`}>
                  <div className="aspect-[1/2] w-full overflow-hidden">
                    <img
                      src={movie.poster_url || movie.poster_path}
                      alt={movie.title}
                      className="size-full object-cover transition-transform duration-300 group-hover:scale-110"
                      onError={e => {
                        e.target.src = 'https://via.placeholder.com/500x750?text=No+Image';
                      }}
                    />
                  </div>
                  <div className="absolute inset-x-0 bottom-0 bg-gradient-to-t from-black/90 to-transparent p-2 sm:p-4">
                    <h4 className="line-clamp-1 text-xs font-semibold text-white sm:text-sm">
                      {movie.title}
                    </h4>
                    <div className="mt-1 flex items-center gap-1 sm:gap-2">
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
        <div className="flex min-h-[150px] items-center justify-center rounded-lg border border-dashed border-gray-600 p-6 text-center sm:min-h-[200px] sm:p-8">
          <div>
            <p className="text-base font-medium text-white sm:text-lg">{t('details.comingSoon')}</p>
            <p className="text-xs text-gray-400 sm:text-sm">{t('details.similarMovies')}</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default MainContent;
