import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Clock, ThumbsUp, MessageCircle, Filter, SortAsc, Grid, List } from 'lucide-react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { getUserRatings } from '../../../api/profileService';
import { useInView } from 'react-intersection-observer';
import { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { getPosterUrl } from '../../../utils/imageUtils';

const RatingCard = ({ rating, viewMode = 'list' }) => {
  const { movie_details: movie } = rating;

  if (viewMode === 'grid') {
    return (
      <div className="group relative">
        <div className="relative aspect-[2/3] rounded-xl overflow-hidden cursor-pointer transition-all duration-300 group-hover:scale-105 shadow-lg">
          <Link to={`/movies/${movie.id}`}>
            <img
              src={getPosterUrl(movie)}
              alt={movie.title}
              className="w-full h-full object-cover"
              loading="lazy"
              onError={e => {
                e.target.src = '/images/no-poster.png';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 group-hover:opacity-100 transition-all duration-300">
              <div className="absolute bottom-0 left-0 right-0 p-4">
                <h3 className="text-white font-semibold line-clamp-2 mb-2">{movie.title}</h3>
                <div className="flex items-center gap-2 text-sm">
                  <div className="flex items-center gap-1 bg-yellow-400/90 text-black font-medium px-2 py-1 rounded-lg">
                    <Star className="w-4 h-4" />
                    <span>{rating.rating}</span>
                  </div>
                  <span className="text-gray-300">
                    {new Date(movie.release_date).getFullYear()}
                  </span>
                </div>
              </div>
            </div>
          </Link>

          {/* Rating Badge */}
          <div className="absolute top-3 right-3 px-2.5 py-1.5 bg-yellow-400/90 rounded-lg shadow-lg">
            <div className="flex items-center gap-1">
              <Star className="w-4 h-4 text-black" />
              <span className="font-bold text-black">{rating.rating}</span>
            </div>
          </div>
        </div>

        <div className="mt-3 space-y-1">
          <Link to={`/movies/${movie.id}`} className="hover:text-red-400 transition-colors">
            <h3 className="text-white text-sm font-medium line-clamp-2">
              {movie.title_vi || movie.title_en || movie.title}
            </h3>
          </Link>
          <div className="flex items-center gap-1 text-gray-400 text-xs">
            <Clock className="w-3.5 h-3.5" />
            <span>{rating.time_ago}</span>
          </div>
          {rating.content && (
            <p className="text-gray-300 text-sm line-clamp-2 mt-2">{rating.content}</p>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800/50 rounded-xl overflow-hidden shadow-lg hover:bg-gray-800 transition-all">
      {/* Movie Header with Poster */}
      <div className="flex">
        <Link to={`/movies/${movie.id}`} className="w-1/4 min-w-[120px] max-w-[180px]">
          <div className="aspect-[2/3] relative group">
            <img
              src={getPosterUrl(movie)}
              alt={movie.title}
              className="w-full h-full object-cover rounded-l-xl"
              loading="lazy"
              onError={e => {
                e.target.src = '/images/no-poster.png';
              }}
            />
            <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-all duration-300 flex items-center justify-center">
              <span className="text-white text-sm font-medium">View Details</span>
            </div>
          </div>
        </Link>

        <div className="p-6 flex-1">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Link to={`/movies/${movie.id}`} className="hover:text-red-400 transition-colors">
                <h3 className="text-xl font-bold text-white mb-1">
                  {movie.title_vi || movie.title_en || movie.title}
                </h3>
                {movie.original_title && movie.original_title !== movie.title && (
                  <p className="text-gray-400 text-sm mb-2">{movie.original_title}</p>
                )}
              </Link>

              {/* Movie Meta Info */}
              <div className="flex flex-wrap gap-2 text-sm text-gray-400 mb-4">
                <span>{new Date(movie.release_date).getFullYear()}</span>
                <span>•</span>
                <span>
                  {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
                </span>
                <span>•</span>
                <span>{movie.genres.map(g => g.name).join(', ')}</span>
              </div>
            </div>

            {/* Rating Badge */}
            <div className="px-3 py-2 bg-yellow-400/90 rounded-xl shadow-lg">
              <div className="flex items-center gap-1.5">
                <Star className="w-5 h-5 text-black" />
                <span className="font-bold text-xl text-black">{rating.rating}</span>
              </div>
            </div>
          </div>

          {/* Rating Info */}
          <div className="flex items-center gap-4 mb-4 text-gray-400">
            <div className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              <span className="text-sm">{rating.time_ago}</span>
            </div>
          </div>

          {/* Movie Overview */}
          <p className="text-gray-300 line-clamp-3 mb-4">
            {movie.overview_vi || movie.overview_en || ''}
          </p>

          {/* Review Content */}
          {rating.content && (
            <>
              <p className="text-gray-300 line-clamp-3">{rating.content}</p>

              {/* Review Stats */}
              <div className="flex items-center gap-6 mt-4 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <ThumbsUp className="w-4 h-4" />
                  <span>{rating.helpful_votes} hữu ích</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageCircle className="w-4 h-4" />
                  <span>{rating.total_votes} bình luận</span>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

const RatingList = ({ userId: propUserId }) => {
  const { ref, inView } = useInView();
  const currentUser = useSelector(state => state.auth.user);
  const [viewMode, setViewMode] = useState('list'); // 'grid' or 'list'
  const [sortBy, setSortBy] = useState('date'); // 'date', 'rating', 'title'

  // Use provided userId from props, or fallback to current user's id
  const userId = propUserId || currentUser?.id;

  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ['userRatings', userId],
      queryFn: ({ pageParam = 1 }) => getUserRatings(userId, pageParam, 'vi'),
      getNextPageParam: lastPage => {
        if (lastPage.next) {
          const url = new URL(lastPage.next);
          return url.searchParams.get('page');
        }
        return undefined;
      },
      enabled: !!userId,
    });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (!userId) {
    return (
      <div className="text-center bg-yellow-500/10 border border-yellow-500/20 rounded-xl p-6 text-yellow-400">
        <p className="text-lg">Không thể tải dữ liệu. Vui lòng đăng nhập lại.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6 p-4">
        <div className="flex items-center justify-between mb-6">
          <h3 className="text-2xl font-bold text-white">My Ratings</h3>
          <div className="animate-pulse w-32 h-8 bg-gray-700 rounded-lg"></div>
        </div>

        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6'
              : 'flex flex-col gap-4'
          }
        >
          {[...Array(6)].map((_, index) => (
            <div key={index} className="animate-pulse">
              {viewMode === 'grid' ? (
                <>
                  <div className="aspect-[2/3] bg-gray-700 rounded-xl shadow-lg"></div>
                  <div className="mt-3 space-y-2">
                    <div className="h-4 bg-gray-700 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-700 rounded w-1/2"></div>
                  </div>
                </>
              ) : (
                <div className="bg-gray-800/50 rounded-xl p-6">
                  <div className="flex gap-6">
                    <div className="w-[120px] aspect-[2/3] bg-gray-700 rounded-lg"></div>
                    <div className="flex-1 space-y-4">
                      <div className="h-6 bg-gray-700 rounded w-3/4"></div>
                      <div className="h-4 bg-gray-700 rounded w-1/2"></div>
                      <div className="h-20 bg-gray-700 rounded"></div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="bg-red-500/10 border border-red-500/20 rounded-xl p-6 text-red-400">
        <p className="text-lg">
          {error?.message || 'Đã có lỗi xảy ra khi tải dữ liệu. Vui lòng thử lại sau.'}
        </p>
      </div>
    );
  }

  const ratings = data?.pages.flatMap(page => page.results) || [];

  // Sort ratings based on selected option
  const sortedRatings = [...ratings].sort((a, b) => {
    switch (sortBy) {
      case 'rating':
        return b.rating - a.rating;
      case 'title':
        return a.movie_details.title.localeCompare(b.movie_details.title);
      case 'date':
      default:
        return new Date(b.created_at) - new Date(a.created_at);
    }
  });

  if (ratings.length === 0) {
    return (
      <div className="text-center py-16 bg-gray-800/50 rounded-xl border border-gray-700">
        <div className="mb-6 text-6xl animate-pulse">⭐</div>
        <h3 className="text-xl font-semibold text-gray-200 mb-3">Chưa có đánh giá nào</h3>
        <p className="text-gray-400 text-base mb-6">
          Hãy bắt đầu đánh giá phim để theo dõi sở thích của bạn!
        </p>
        <Link
          to="/movies"
          className="inline-block px-8 py-3 bg-red-500 text-white rounded-lg hover:bg-red-600 transition-all transform hover:scale-105 active:scale-95 shadow-lg"
        >
          Khám phá phim
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <h3 className="text-2xl font-bold text-white">
          My Ratings
          <span className="ml-2 text-lg text-gray-400">({ratings.length})</span>
        </h3>

        <div className="flex items-center gap-4">
          <div className="flex items-center bg-gray-800 rounded-lg p-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'grid' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Grid size={18} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`px-3 py-1.5 rounded-md transition-all ${
                viewMode === 'list' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <List size={18} />
            </button>
          </div>

          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="bg-gray-800 text-gray-200 rounded-lg px-4 py-2 border border-gray-700 focus:outline-none focus:ring-2 focus:ring-red-500"
          >
            <option value="date">Sort by Date</option>
            <option value="rating">Sort by Rating</option>
            <option value="title">Sort by Title</option>
          </select>
        </div>
      </div>

      <div
        className={
          viewMode === 'grid'
            ? 'grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6'
            : 'flex flex-col gap-4'
        }
      >
        {sortedRatings.map(rating => (
          <RatingCard key={rating.id} rating={rating} viewMode={viewMode} />
        ))}
      </div>

      <div ref={ref} className="h-4">
        {isFetchingNextPage && (
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-red-400"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RatingList;
