import { useState } from 'react';
import { ThumbsUp, ThumbsDown, Edit, Trash2, MoreHorizontal, Flag } from 'lucide-react';
import { voteOnReview, deleteReview } from '../../api/movieService';

const ReviewActions = ({
  review,
  onVoteUpdate,
  onEdit,
  onDelete,
  showMoreActions = true,
  size = 'sm',
}) => {
  const [isVoting, setIsVoting] = useState(false);
  const [showDropdown, setShowDropdown] = useState(false);

  const handleVote = async voteType => {
    if (isVoting) return;

    setIsVoting(true);
    try {
      const result = await voteOnReview(review.id, voteType);
      if (onVoteUpdate) {
        onVoteUpdate(review.id, result);
      }
    } catch (err) {
      console.error('Error voting on review:', err);
    } finally {
      setIsVoting(false);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Bạn có chắc muốn xóa đánh giá này?')) {
      try {
        await deleteReview(review.id);
        if (onDelete) {
          onDelete(review.id);
        }
      } catch (err) {
        console.error('Error deleting review:', err);
      }
    }
  };

  const iconSize = size === 'sm' ? 14 : 16;
  const textSize = size === 'sm' ? 'text-xs' : 'text-sm';

  return (
    <div className="flex items-center gap-4">
      {/* Voting Buttons */}
      {review.can_vote !== false && (
        <>
          <button
            onClick={() => handleVote('helpful')}
            disabled={isVoting || !review.can_vote}
            className={`flex items-center gap-1 ${textSize} transition-colors ${
              review.user_vote === 'helpful'
                ? 'text-green-400'
                : 'text-gray-400 hover:text-green-300'
            } disabled:opacity-50`}
          >
            <ThumbsUp size={iconSize} />
            {review.helpful_votes || 0}
          </button>

          <button
            onClick={() => handleVote('not_helpful')}
            disabled={isVoting || !review.can_vote}
            className={`flex items-center gap-1 ${textSize} transition-colors ${
              review.user_vote === 'not_helpful'
                ? 'text-red-400'
                : 'text-gray-400 hover:text-red-300'
            } disabled:opacity-50`}
          >
            <ThumbsDown size={iconSize} />
            {(review.total_votes || 0) - (review.helpful_votes || 0)}
          </button>
        </>
      )}

      {/* Display vote counts for own reviews without voting buttons */}
      {review.can_vote === false && (
        <div className="flex items-center gap-4">
          <span className={`flex items-center gap-1 ${textSize} text-gray-500`}>
            <ThumbsUp size={iconSize} />
            {review.helpful_votes || 0}
          </span>
          <span className={`flex items-center gap-1 ${textSize} text-gray-500`}>
            <ThumbsDown size={iconSize} />
            {(review.total_votes || 0) - (review.helpful_votes || 0)}
          </span>
        </div>
      )}

      {/* Helpfulness Ratio */}
      {review.total_votes > 0 && (
        <span className={`${textSize} text-gray-400`}>
          {Math.round(((review.helpful_votes || 0) / review.total_votes) * 100)}% hữu ích
        </span>
      )}

      {/* Reply Button - Removed as it's handled by ReplySection component */}

      {/* More Actions */}
      {showMoreActions && (
        <div className="relative ml-auto">
          {/* Edit/Delete for own reviews */}
          {review.can_edit && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => onEdit && onEdit(review)}
                className="text-gray-400 hover:text-blue-400"
                title="Chỉnh sửa"
              >
                <Edit size={iconSize} />
              </button>
              <button
                onClick={handleDelete}
                className="text-gray-400 hover:text-red-400"
                title="Xóa"
              >
                <Trash2 size={iconSize} />
              </button>
            </div>
          )}

          {/* More Menu */}
          {!review.can_edit && (
            <>
              <button
                onClick={() => setShowDropdown(!showDropdown)}
                className="text-gray-400 hover:text-gray-300"
              >
                <MoreHorizontal size={iconSize} />
              </button>

              {showDropdown && (
                <div className="absolute right-0 top-full z-10 mt-1 w-32 rounded-lg bg-gray-800 py-1 shadow-lg">
                  <button
                    onClick={() => {
                      setShowDropdown(false);
                      // Handle report
                    }}
                    className="flex w-full items-center gap-2 px-3 py-2 text-sm text-gray-300 hover:bg-gray-700"
                  >
                    <Flag size={12} />
                    Báo cáo
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
};

export default ReviewActions;
