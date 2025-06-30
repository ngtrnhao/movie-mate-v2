import React from 'react';
import { Link } from 'react-router-dom';
import { Star, Clock, ThumbsUp, MessageCircle } from 'lucide-react';
import { useInfiniteQuery } from '@tanstack/react-query';
import { getUserRatings } from '../../../api/profileService';
import { useInView } from 'react-intersection-observer';
import { useEffect } from 'react';
import { useSelector } from 'react-redux';
import { getPosterUrl } from '../../../utils/imageUtils';

const RatingCard = ({ rating }) => {
  const { movie_details: movie } = rating;

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-shadow">
      {/* Movie Header with Poster */}
      <div className="flex">
        <Link to={`/movies/${movie.id}`} className="w-1/3 min-w-[120px] max-w-[200px]">
          <img
            src={getPosterUrl(movie)}
            alt={movie.title}
            className="w-full h-full object-cover"
            loading="lazy"
            onError={e => {
              e.target.src = '/images/no-poster.png';
            }}
          />
        </Link>

        <div className="p-4 flex-1">
          <Link to={`/movies/${movie.id}`} className="hover:text-blue-400 transition-colors">
            <h3 className="text-xl font-semibold text-white mb-1">{movie.title}</h3>
            {movie.original_title && movie.original_title !== movie.title && (
              <p className="text-gray-400 text-sm mb-2">{movie.original_title}</p>
            )}
          </Link>

          {/* Movie Meta Info */}
          <div className="flex flex-wrap gap-2 text-sm text-gray-400 mb-3">
            <span>{new Date(movie.release_date).getFullYear()}</span>
            <span>•</span>
            <span>
              {Math.floor(movie.runtime / 60)}h {movie.runtime % 60}m
            </span>
            <span>•</span>
            <span>{movie.genres.map(g => g.name).join(', ')}</span>
          </div>

          {/* Rating Info */}
          <div className="flex items-center gap-4 mb-3">
            <div className="flex items-center gap-1">
              <Star className="w-5 h-5 text-yellow-400 fill-current" />
              <span className="text-lg font-semibold text-white">{rating.rating}</span>
            </div>
            <div className="flex items-center gap-1 text-gray-400">
              <Clock className="w-4 h-4" />
              <span className="text-sm">{rating.time_ago}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Review Content */}
      {rating.content && (
        <div className="p-4 pt-0">
          <p className="text-gray-300">{rating.content}</p>

          {/* Review Stats */}
          <div className="flex items-center gap-4 mt-3 text-sm text-gray-400">
            <div className="flex items-center gap-1">
              <ThumbsUp className="w-4 h-4" />
              <span>{rating.helpful_votes} hữu ích</span>
            </div>
            <div className="flex items-center gap-1">
              <MessageCircle className="w-4 h-4" />
              <span>{rating.total_votes} bình luận</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const RatingList = ({ userId: propUserId }) => {
  const { ref, inView } = useInView();
  const currentUser = useSelector(state => state.auth.user);

  // Use provided userId from props, or fallback to current user's id
  const userId = propUserId || currentUser?.id;

  const { data, isLoading, isError, error, fetchNextPage, hasNextPage, isFetchingNextPage } =
    useInfiniteQuery({
      queryKey: ['userRatings', userId],
      queryFn: ({ pageParam = 1 }) => getUserRatings(userId, pageParam),
      getNextPageParam: lastPage => {
        if (lastPage.next) {
          const url = new URL(lastPage.next);
          return url.searchParams.get('page');
        }
        return undefined;
      },
      // Only enable the query if we have a valid userId
      enabled: !!userId,
    });

  useEffect(() => {
    if (inView && hasNextPage && !isFetchingNextPage) {
      fetchNextPage();
    }
  }, [inView, hasNextPage, isFetchingNextPage, fetchNextPage]);

  if (!userId) {
    return (
      <div className="text-center text-yellow-400 py-8">
        Không thể tải dữ liệu. Vui lòng đăng nhập lại.
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="flex justify-center items-center h-48">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-400"></div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="text-center text-red-400 py-8">
        {error?.message || 'Đã có lỗi xảy ra khi tải dữ liệu. Vui lòng thử lại sau.'}
      </div>
    );
  }

  const ratings = data?.pages.flatMap(page => page.results) || [];

  if (ratings.length === 0) {
    return (
      <div className="text-center text-gray-400 py-8">
        <div className="mb-4 text-6xl">⭐</div>
        <h3 className="text-xl font-semibold mb-2">Chưa có đánh giá nào</h3>
        <p>Hãy bắt đầu đánh giá phim để theo dõi sở thích của bạn!</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {ratings.map(rating => (
        <RatingCard key={rating.id} rating={rating} />
      ))}

      <div ref={ref} className="h-4">
        {isFetchingNextPage && (
          <div className="flex justify-center">
            <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-400"></div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RatingList;
