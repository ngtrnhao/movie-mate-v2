import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Clock, ThumbsUp, MessageCircle, Grid, List } from 'lucide-react';
import SpoilerBadge from '../../../components/common/SpoilerBadge';
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
        <div className="relative aspect-[2/3] cursor-pointer overflow-hidden rounded-xl shadow-lg transition-all duration-300 group-hover:scale-105">
          <Link to={`/movies/${movie.id}`}>
            <img
              src={getPosterUrl(movie)}
              alt={movie.title}
              className="size-full object-cover"
              loading="lazy"
              onError={e => {
                e.target.src = 'https://placehold.co/600x400';
              }}
            />
            <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 transition-all duration-300 group-hover:opacity-100">
              <div className="absolute inset-x-0 bottom-0 p-4">
                <h3 className="mb-2 line-clamp-2 font-semibold text-white">{movie.title}</h3>
                <div className="flex items-center gap-2 text-sm">
                  <div className="flex items-center gap-1 rounded-lg bg-yellow-400/90 px-2 py-1 font-medium text-black">
                    <Star className="size-4" />
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
          <div className="absolute right-3 top-3 rounded-lg bg-yellow-400/90 px-2.5 py-1.5 shadow-lg">
            <div className="flex items-center gap-1">
              <Star className="size-4 text-black" />
              <span className="font-bold text-black">{rating.rating}</span>
            </div>
          </div>
        </div>

        <div className="mt-3 space-y-1">
          <Link to={`/movies/${movie.id}`} className="transition-colors hover:text-red-400">
            <h3 className="line-clamp-2 text-sm font-medium text-white">
              {movie.title_vi || movie.title_en || movie.title}
            </h3>
          </Link>
          <div className="flex items-center gap-1 text-xs text-gray-400">
            <Clock className="size-3.5" />
            <span>{rating.time_ago}</span>
          </div>
          {rating.content && (
            <p className="mt-2 line-clamp-2 text-sm text-gray-300">{rating.content}</p>
          )}
          <SpoilerBadge isSpoiler={rating.is_spoiler} size="xs" />
        </div>
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-xl bg-gray-800/50 shadow-lg transition-all hover:bg-gray-800">
      {/* Movie Header with Poster */}
      <div className="flex">
        <Link to={`/movies/${movie.id}`} className="w-1/4 min-w-[120px] max-w-[180px]">
          <div className="group relative aspect-[2/3]">
            <img
              src={getPosterUrl(movie)}
              alt={movie.title}
              className="size-full rounded-l-xl object-cover"
              loading="lazy"
              onError={e => {
                e.target.src = 'https://placehold.co/600x400';
              }}
            />
            <div className="absolute inset-0 flex items-center justify-center bg-black/60 opacity-0 transition-all duration-300 group-hover:opacity-100">
              <span className="text-sm font-medium text-white">View Details</span>
            </div>
          </div>
        </Link>

        <div className="flex-1 p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <Link to={`/movies/${movie.id}`} className="transition-colors hover:text-red-400">
                <h3 className="mb-1 text-xl font-bold text-white">
                  {movie.title_vi || movie.title_en || movie.title}
                </h3>
                {movie.original_title && movie.original_title !== movie.title && (
                  <p className="mb-2 text-sm text-gray-400">{movie.original_title}</p>
                )}
              </Link>

              {/* Movie Meta Info */}
              <div className="mb-4 flex flex-wrap gap-2 text-sm text-gray-400">
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
            <div className="rounded-xl bg-yellow-400/90 px-3 py-2 shadow-lg">
              <div className="flex items-center gap-1.5">
                <Star className="size-5 text-black" />
                <span className="text-xl font-bold text-black">{rating.rating}</span>
              </div>
            </div>
          </div>

          {/* Rating Info */}
          <div className="mb-4 flex items-center gap-4 text-gray-400">
            <div className="flex items-center gap-1">
              <Clock className="size-4" />
              <span className="text-sm">{rating.time_ago}</span>
            </div>
          </div>

          {/* Movie Overview */}
          <p className="mb-4 line-clamp-3 text-gray-300">
            {movie.overview_vi || movie.overview_en || ''}
          </p>

          {/* Review Content */}
          {rating.content && (
            <>
              <p className="line-clamp-3 text-gray-300">{rating.content}</p>

              {/* Spoiler Badge */}
              <div className="mt-3">
                <SpoilerBadge isSpoiler={rating.is_spoiler} size="sm" />
              </div>

              {/* Review Stats */}
              <div className="mt-4 flex items-center gap-6 text-sm text-gray-400">
                <div className="flex items-center gap-2">
                  <ThumbsUp className="size-4" />
                  <span>{rating.helpful_votes} hữu ích</span>
                </div>
                <div className="flex items-center gap-2">
                  <MessageCircle className="size-4" />
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
      <div className="rounded-xl border border-yellow-500/20 bg-yellow-500/10 p-6 text-center text-yellow-400">
        <p className="text-lg">Không thể tải dữ liệu. Vui lòng đăng nhập lại.</p>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="space-y-6 p-4">
        <div className="mb-6 flex items-center justify-between">
          <h3 className="text-2xl font-bold text-white">My Ratings</h3>
          <div className="h-8 w-32 animate-pulse rounded-lg bg-gray-700"></div>
        </div>

        <div
          className={
            viewMode === 'grid'
              ? 'grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
              : 'flex flex-col gap-4'
          }
        >
          {[...Array(6)].map((_, index) => (
            <div key={index} className="animate-pulse">
              {viewMode === 'grid' ? (
                <>
                  <div className="aspect-[2/3] rounded-xl bg-gray-700 shadow-lg"></div>
                  <div className="mt-3 space-y-2">
                    <div className="h-4 w-3/4 rounded bg-gray-700"></div>
                    <div className="h-3 w-1/2 rounded bg-gray-700"></div>
                  </div>
                </>
              ) : (
                <div className="rounded-xl bg-gray-800/50 p-6">
                  <div className="flex gap-6">
                    <div className="aspect-[2/3] w-[120px] rounded-lg bg-gray-700"></div>
                    <div className="flex-1 space-y-4">
                      <div className="h-6 w-3/4 rounded bg-gray-700"></div>
                      <div className="h-4 w-1/2 rounded bg-gray-700"></div>
                      <div className="h-20 rounded bg-gray-700"></div>
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
      <div className="rounded-xl border border-red-500/20 bg-red-500/10 p-6 text-red-400">
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
      <div className="rounded-xl border border-gray-700 bg-gray-800/50 py-16 text-center">
        <div className="mb-6 animate-pulse text-6xl">⭐</div>
        <h3 className="mb-3 text-xl font-semibold text-gray-200">Chưa có đánh giá nào</h3>
        <p className="mb-6 text-base text-gray-400">
          Hãy bắt đầu đánh giá phim để theo dõi sở thích của bạn!
        </p>
        <Link
          to="/movies"
          className="inline-block rounded-lg bg-red-500 px-8 py-3 text-white shadow-lg transition-all hover:scale-105 hover:bg-red-600 active:scale-95"
        >
          Khám phá phim
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-6 p-4">
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <h3 className="text-2xl font-bold text-white">
          My Ratings
          <span className="ml-2 text-lg text-gray-400">({ratings.length})</span>
        </h3>

        <div className="flex items-center gap-4">
          <div className="flex items-center rounded-lg bg-gray-800 p-2">
            <button
              onClick={() => setViewMode('grid')}
              className={`rounded-md px-3 py-1.5 transition-all ${
                viewMode === 'grid' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <Grid size={18} />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`rounded-md px-3 py-1.5 transition-all ${
                viewMode === 'list' ? 'bg-red-500 text-white' : 'text-gray-400 hover:text-white'
              }`}
            >
              <List size={18} />
            </button>
          </div>

          <select
            value={sortBy}
            onChange={e => setSortBy(e.target.value)}
            className="rounded-lg border border-gray-700 bg-gray-800 px-4 py-2 text-gray-200 focus:outline-none focus:ring-2 focus:ring-red-500"
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
            ? 'grid grid-cols-2 gap-6 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5'
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
            <div className="size-8 animate-spin rounded-full border-b-2 border-red-400"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RatingList;
