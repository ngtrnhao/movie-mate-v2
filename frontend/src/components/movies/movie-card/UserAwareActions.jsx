import { useState } from 'react';
import { useSelector } from 'react-redux';
import { Heart, Plus, Star, MessageSquare, Tag, BookOpen } from 'lucide-react';
import { selectUser } from '../../../store/selectors/authSelectors';
import {
  getUserType,
  getUserLimit,
  canUserPerform,
  USER_TYPES,
} from '../../../utils/userPermissions';
import LimitCounter from '../../common/LimitCounter';
import UpgradePrompt from '../../common/UpgradePrompt';

const UserAwareActions = ({
  movie,
  onFavorite,
  onAddToList,
  onRate,
  onReview,
  onAddTag,
  isFavorited = false,
  currentRating = 0,
  userFavoritesCount = 0,
  userReviewsToday = 0,
}) => {
  const user = useSelector(selectUser);
  const userType = getUserType(user);
  const [showUpgradeModal, setShowUpgradeModal] = useState(null);

  // Get user limits
  const favoritesLimit = getUserLimit(user, 'favorites');
  const listsLimit = getUserLimit(user, 'lists');
  const reviewsLimit = getUserLimit(user, 'reviews_per_day');

  // Check permissions
  const canFavorite =
    userType !== USER_TYPES.GUEST && (favoritesLimit === -1 || userFavoritesCount < favoritesLimit);
  const canAddToList = userType !== USER_TYPES.GUEST && listsLimit > 0;
  const canRate =
    userType !== USER_TYPES.GUEST && (reviewsLimit === -1 || userReviewsToday < reviewsLimit);
  const canReview =
    userType !== USER_TYPES.GUEST && (reviewsLimit === -1 || userReviewsToday < reviewsLimit);
  const canEditReview = canUserPerform(user, 'can_edit_reviews');
  const canAddTags = canUserPerform(user, 'can_add_tags');

  const handleAction = (action, callback) => {
    if (userType === USER_TYPES.GUEST) {
      setShowUpgradeModal(action);
      return;
    }

    // Check specific limits
    if (action === 'favorite' && !canFavorite) {
      setShowUpgradeModal('favorites');
      return;
    }

    if ((action === 'rate' || action === 'review') && !canRate) {
      setShowUpgradeModal('reviews');
      return;
    }

    if (action === 'addTag' && !canAddTags) {
      setShowUpgradeModal('tags');
      return;
    }

    callback && callback();
  };

  return (
    <div className="space-y-3">
      {/* Action Buttons */}
      <div className="flex flex-wrap gap-2">
        {/* Favorite Button */}
        <button
          onClick={() => handleAction('favorite', onFavorite)}
          disabled={userType !== USER_TYPES.GUEST && !canFavorite && isFavorited}
          className={`flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
            isFavorited
              ? 'bg-red-600 text-white hover:bg-red-700'
              : userType === USER_TYPES.GUEST || !canFavorite
                ? 'cursor-not-allowed bg-gray-700 text-gray-400'
                : 'bg-gray-700 text-white hover:bg-gray-600'
          }`}
        >
          <Heart className={`size-4 ${isFavorited ? 'fill-current' : ''}`} />
          <span>
            {userType === USER_TYPES.GUEST ? 'Sign In' : isFavorited ? 'Favorited' : 'Favorite'}
          </span>
        </button>

        {/* Add to List Button */}
        <button
          onClick={() => handleAction('addToList', onAddToList)}
          disabled={userType !== USER_TYPES.GUEST && !canAddToList}
          className={`flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
            userType === USER_TYPES.GUEST || !canAddToList
              ? 'cursor-not-allowed bg-gray-700 text-gray-400'
              : 'bg-gray-700 text-white hover:bg-gray-600'
          }`}
        >
          <Plus className="size-4" />
          <span>{userType === USER_TYPES.GUEST ? 'Sign In' : 'Add to List'}</span>
        </button>

        {/* Rating Button */}
        <button
          onClick={() => handleAction('rate', onRate)}
          disabled={userType !== USER_TYPES.GUEST && !canRate}
          className={`flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
            currentRating > 0
              ? 'bg-yellow-600 text-white hover:bg-yellow-700'
              : userType === USER_TYPES.GUEST || !canRate
                ? 'cursor-not-allowed bg-gray-700 text-gray-400'
                : 'bg-gray-700 text-white hover:bg-gray-600'
          }`}
        >
          <Star className={`size-4 ${currentRating > 0 ? 'fill-current' : ''}`} />
          <span>
            {userType === USER_TYPES.GUEST
              ? 'Sign In'
              : currentRating > 0
                ? `${currentRating}/5`
                : 'Rate'}
          </span>
        </button>

        {/* Review Button */}
        <button
          onClick={() => handleAction('review', onReview)}
          disabled={userType !== USER_TYPES.GUEST && !canReview}
          className={`flex items-center gap-1 rounded-lg px-3 py-2 text-sm font-medium transition-all ${
            userType === USER_TYPES.GUEST || !canReview
              ? 'cursor-not-allowed bg-gray-700 text-gray-400'
              : 'bg-gray-700 text-white hover:bg-gray-600'
          }`}
        >
          <MessageSquare className="size-4" />
          <span>{userType === USER_TYPES.GUEST ? 'Sign In' : 'Review'}</span>
        </button>

        {/* Add Tags Button - Premium Feature */}
        {canAddTags && (
          <button
            onClick={() => handleAction('addTag', onAddTag)}
            className="flex items-center gap-1 rounded-lg bg-amber-600 px-3 py-2 text-sm font-medium text-white transition-all hover:bg-amber-700"
          >
            <Tag className="size-4" />
            <span>Add Tags</span>
          </button>
        )}

        {/* Watch Later - Member+ Feature */}
        {userType !== USER_TYPES.GUEST && (
          <button
            onClick={() => handleAction('watchLater', () => {})}
            className="flex items-center gap-1 rounded-lg bg-blue-600 px-3 py-2 text-sm font-medium text-white transition-all hover:bg-blue-700"
          >
            <BookOpen className="size-4" />
            <span>Watch Later</span>
          </button>
        )}
      </div>

      {/* Usage Limits Display */}
      {userType !== USER_TYPES.GUEST && (
        <div className="flex flex-wrap gap-4 text-xs">
          <LimitCounter
            current={userFavoritesCount}
            max={favoritesLimit}
            label="Favorites"
            type="badge"
            size="xs"
          />
          <LimitCounter
            current={userReviewsToday}
            max={reviewsLimit}
            label="Reviews today"
            type="badge"
            size="xs"
          />
        </div>
      )}

      {/* Upgrade Prompts */}
      {showUpgradeModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="relative max-w-md">
            <button
              onClick={() => setShowUpgradeModal(null)}
              className="absolute -right-2 -top-2 rounded-full bg-gray-800 p-1 text-white"
            >
              <svg className="size-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>
            <UpgradePrompt user={user} feature={showUpgradeModal} type="inline" size="md" />
          </div>
        </div>
      )}
    </div>
  );
};

export default UserAwareActions;
