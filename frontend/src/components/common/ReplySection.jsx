import { useState, useEffect } from 'react';
import { Send, MessageSquare, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { useSelector } from 'react-redux';
import { replyToReview, getReviewReplies } from '../../api/movieService';
import ReviewActions from './ReviewActions';
import { useSpoilerDetection } from '../../hooks/useSpoilerDetection';
import SpoilerDetectionAlert from './SpoilerDetectionAlert';

const ReplySection = ({ review, onReplySuccess }) => {
  const [showReplies, setShowReplies] = useState(false);
  const [showReplyForm, setShowReplyForm] = useState(false);
  const [replies, setReplies] = useState([]);
  const [replyText, setReplyText] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [isSpoiler, setIsSpoiler] = useState(false);

  const isAuthenticated = useSelector(state => state.auth.isAuthenticated);
  const user = useSelector(state => state.auth.user);

  // Spoiler detection hook
  const {
    isAnalyzing,
    detectionResult,
    error: spoilerError,
    analyzeContentDebounced,
    clearAnalysis,
    shouldAutoMark,
    shouldShowWarning,
  } = useSpoilerDetection('vi', '');

  const fetchReplies = async () => {
    if (loading) return;

    setLoading(true);
    setError(null);

    try {
      const response = await getReviewReplies(review.id);
      // Get replies from the results array in paginated response
      setReplies(response.results || []);
    } catch (err) {
      console.error('Error fetching replies:', err);
      setError('Không thể tải phản hồi');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (showReplies && replies.length === 0) {
      fetchReplies();
    }
  }, [showReplies]);

  const handleToggleReplies = () => {
    setShowReplies(!showReplies);
  };

  const handleToggleReplyForm = () => {
    if (!isAuthenticated) {
      // Show login prompt or redirect to login
      alert('Bạn cần đăng nhập để trả lời');
      return;
    }
    setShowReplyForm(!showReplyForm);
    setReplyText('');
    setError(null);
  };

  const handleSubmitReply = async () => {
    if (!replyText.trim() || replyText.length < 5) {
      setError('Phản hồi phải có ít nhất 5 ký tự');
      return;
    }

    setSubmitting(true);
    setError(null);

    try {
      const replyData = {
        content: replyText.trim(),
        language: 'vi',
        is_public: true,
        is_spoiler: isSpoiler || shouldAutoMark,
      };

      const response = await replyToReview(review.id, replyData);

      if (response.status === 'success') {
        // Add new reply to the list
        setReplies(prev => [...prev, response.data]);
        setReplyText('');
        setShowReplyForm(false);
        setShowReplies(true);

        // Update reply count in parent review
        if (onReplySuccess) {
          onReplySuccess(review.id, response.data);
        }

        // Fetch latest replies to ensure correct order
        fetchReplies();
      }
    } catch (err) {
      console.error('Error submitting reply:', err);
      setError(err.response?.data?.message || 'Không thể gửi phản hồi');
    } finally {
      setSubmitting(false);
    }
  };

  const handleVoteUpdate = (replyId, voteResult) => {
    setReplies(prev =>
      prev.map(reply =>
        reply.id === replyId
          ? {
              ...reply,
              helpful_votes: voteResult.helpful_votes,
              total_votes: voteResult.total_votes,
              user_vote: voteResult.user_vote,
            }
          : reply
      )
    );
  };

  const canReply = review.can_reply !== false && isAuthenticated && user?.id !== review.user?.id;
  const isExternal = review.review_type === 'EXTERNAL';

  return (
    <div className="mt-4 border-l-2 border-gray-700 pl-4">
      {/* Reply count and toggle */}
      <div className="mb-3 flex items-center gap-4">
        {review.reply_count > 0 && (
          <button
            onClick={handleToggleReplies}
            className="flex items-center gap-2 text-sm text-blue-400 transition-colors hover:text-blue-300"
          >
            <MessageSquare size={14} />
            <span>{review.reply_count} phản hồi</span>
            {showReplies ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
          </button>
        )}

        {canReply && !isExternal && (
          <button
            onClick={handleToggleReplyForm}
            className="flex items-center gap-2 text-sm text-gray-400 transition-colors hover:text-gray-300"
          >
            <Send size={14} />
            Trả lời
          </button>
        )}
        {/* Show log if cannot reply to external review */}
        {isExternal && (
          <span className="flex items-center gap-1 text-xs text-orange-400">
            <AlertTriangle size={14} className="inline-block" />
            Không thể trả lời review từ nguồn ngoài (external review)
          </span>
        )}
      </div>

      {/* Reply form */}
      {showReplyForm && (
        <div className="mb-4 rounded-lg bg-gray-800/30 p-4">
          <div className="mb-3">
            <textarea
              value={replyText}
              onChange={e => {
                const newContent = e.target.value;
                setReplyText(newContent);

                // Trigger spoiler detection on content change
                if (newContent.trim().length >= 5) {
                  analyzeContentDebounced(newContent);
                } else {
                  clearAnalysis();
                }
              }}
              placeholder="Viết phản hồi của bạn (ít nhất 5 ký tự)..."
              className="w-full resize-none rounded-lg bg-gray-700 p-3 text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="3"
              maxLength={500}
            />

            {/* Spoiler Detection Alert */}
            <SpoilerDetectionAlert
              detectionResult={detectionResult}
              isAnalyzing={isAnalyzing}
              onMarkAsSpoiler={() => setIsSpoiler(true)}
              onDismiss={clearAnalysis}
              onReviewContent={() => {
                // Focus back to textarea for review
                const textarea = document.querySelector('textarea');
                if (textarea) textarea.focus();
              }}
            />

            <div className="mt-2 flex items-center justify-between">
              <span className="text-xs text-gray-400">{replyText.length}/500</span>
              {error && <span className="text-xs text-red-400">{error}</span>}
            </div>
          </div>

          <div className="flex items-center justify-end gap-2">
            {/* Spoiler Checkbox */}
            <div className="mr-auto flex items-center space-x-2">
              <input
                type="checkbox"
                id="spoiler-checkbox-reply"
                checked={isSpoiler}
                onChange={e => setIsSpoiler(e.target.checked)}
                className="size-4 rounded border-gray-600 bg-gray-700 text-orange-500 focus:ring-orange-500 focus:ring-offset-gray-800"
              />
              <label htmlFor="spoiler-checkbox-reply" className="text-sm text-gray-300">
                Chứa spoiler
              </label>
            </div>

            <button
              onClick={handleToggleReplyForm}
              disabled={submitting}
              className="px-4 py-2 text-sm text-gray-400 hover:text-gray-300 disabled:opacity-50"
            >
              Hủy
            </button>
            <button
              onClick={handleSubmitReply}
              disabled={submitting || !replyText.trim() || replyText.length < 5}
              className="flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {submitting ? (
                <>
                  <div className="size-4 animate-spin rounded-full border-2 border-white/30 border-t-white" />
                  Đang gửi...
                </>
              ) : (
                <>
                  <Send size={14} />
                  Gửi phản hồi
                </>
              )}
            </button>
          </div>
        </div>
      )}

      {/* Replies list */}
      {showReplies && (
        <div className="space-y-4">
          {loading ? (
            <div className="py-4 text-center text-gray-400">
              <div className="mx-auto mb-2 size-6 animate-spin rounded-full border-2 border-gray-400/30 border-t-gray-400" />
              Đang tải phản hồi...
            </div>
          ) : error ? (
            <div className="py-4 text-center text-red-400">{error}</div>
          ) : replies.length > 0 ? (
            <div className="space-y-4 pl-4">
              {replies.map(reply => (
                <div key={reply.id} className="rounded-lg bg-gray-800/20 p-4">
                  <div className="flex items-start gap-3">
                    <img
                      src={reply.reviewer_avatar || '/api/placeholder/32/32'}
                      alt={reply.reviewer_name || 'User'}
                      className="size-8 rounded-full object-cover"
                      onError={e => {
                        e.target.src = `https://ui-avatars.com/api/?name=${reply.reviewer_name || 'User'}&background=random&color=fff&size=32`;
                      }}
                    />
                    <div className="flex-1">
                      <div className="mb-1 flex items-center gap-2">
                        <h4 className="text-sm font-medium text-white">{reply.reviewer_name}</h4>
                        {reply.is_verified_reviewer && (
                          <span className="text-xs text-blue-400">✓</span>
                        )}
                        <span className="text-xs text-gray-500">
                          {new Date(reply.created_at).toLocaleDateString('vi-VN')}
                        </span>
                      </div>
                      <p className="mb-3 text-sm leading-relaxed text-gray-300">{reply.content}</p>
                      <ReviewActions
                        review={reply}
                        onVoteUpdate={handleVoteUpdate}
                        showMoreActions={false}
                        size="sm"
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="py-4 text-center text-gray-500">Chưa có phản hồi nào</div>
          )}
        </div>
      )}
    </div>
  );
};

export default ReplySection;
