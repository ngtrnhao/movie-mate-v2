import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { X, AlertTriangle, Flag } from 'lucide-react';
import { reportReview } from '../../api/movieService';

const ReportModal = ({ isOpen, onClose, review, onReportSuccess }) => {
  const [reason, setReason] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  const reportReasons = [
    {
      value: 'offensive',
      label: 'Ngôn ngữ xúc phạm',
      description: 'Review chứa từ ngữ xúc phạm, thô tục hoặc không phù hợp',
      icon: '🚫',
    },
    {
      value: 'spam',
      label: 'Spam hoặc quảng cáo',
      description: 'Review chứa nội dung spam, quảng cáo hoặc không liên quan',
      icon: '📢',
    },
    {
      value: 'abuse',
      label: 'Quấy rối hoặc lạm dụng',
      description: 'Review chứa nội dung quấy rối, đe dọa hoặc lạm dụng',
      icon: '⚠️',
    },
    {
      value: 'irrelevant',
      label: 'Nội dung không liên quan',
      description: 'Review không liên quan đến phim hoặc chủ đề',
      icon: '❌',
    },
    {
      value: 'spoiler',
      label: 'Chứa spoiler',
      description: 'Review tiết lộ nội dung quan trọng của phim',
      icon: '🤐',
    },
    {
      value: 'other',
      label: 'Lý do khác',
      description: 'Lý do khác không được liệt kê ở trên',
      icon: '📝',
    },
  ];

  const handleSubmit = async e => {
    e.preventDefault();
    if (!reason) {
      setError('Vui lòng chọn lý do báo cáo');
      return;
    }

    setIsSubmitting(true);
    setError('');

    try {
      await reportReview(review.id, reason, description);
      onReportSuccess && onReportSuccess();
      onClose();
    } catch (err) {
      setError(err.error || 'Có lỗi xảy ra khi báo cáo. Vui lòng thử lại.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    setReason('');
    setDescription('');
    setError('');
    onClose();
  };

  // Handle escape key
  useEffect(() => {
    const handleEscape = e => {
      if (e.key === 'Escape' && isOpen) {
        handleClose();
      }
    };

    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  if (!isOpen || !mounted) return null;

  const modalContent = (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/50 backdrop-blur-sm">
      <div className="w-full max-w-md rounded-lg bg-gray-800 p-6 shadow-xl mx-4">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Flag className="h-5 w-5 text-red-400" />
            <h3 className="text-lg font-semibold text-white">Báo cáo review</h3>
          </div>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-white transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Review Preview */}
        <div className="mb-4 rounded-lg bg-gray-700/50 p-3">
          <p className="text-sm text-gray-300">
            <strong>Review của {review.reviewer_name}:</strong>
          </p>
          <p className="mt-1 text-sm text-gray-400 line-clamp-2">{review.content}</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Reason Selection */}
          <div>
            <label className="mb-2 block text-sm font-medium text-white">Lý do báo cáo *</label>
            <div className="space-y-2 max-h-60 overflow-y-auto scrollbar-hide">
              {reportReasons.map(reportReason => (
                <label
                  key={reportReason.value}
                  className={`flex cursor-pointer items-start gap-3 rounded-lg border p-3 transition-colors ${
                    reason === reportReason.value
                      ? 'border-red-500 bg-red-500/10'
                      : 'border-gray-600 bg-gray-700/50 hover:border-gray-500'
                  }`}
                >
                  <input
                    type="radio"
                    name="reason"
                    value={reportReason.value}
                    checked={reason === reportReason.value}
                    onChange={e => setReason(e.target.value)}
                    className="mt-1 h-4 w-4 text-red-500 focus:ring-red-500"
                  />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{reportReason.icon}</span>
                      <span className="font-medium text-white">{reportReason.label}</span>
                    </div>
                    <p className="mt-1 text-xs text-gray-400">{reportReason.description}</p>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="mb-2 block text-sm font-medium text-white">
              Mô tả chi tiết (tùy chọn)
            </label>
            <textarea
              value={description}
              onChange={e => setDescription(e.target.value)}
              placeholder="Cung cấp thêm chi tiết về lý do báo cáo..."
              className="w-full rounded-lg bg-gray-700 p-3 text-sm text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-red-500"
              rows="3"
              maxLength="500"
            />
            <p className="mt-1 text-xs text-gray-400">{description.length}/500 ký tự</p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="flex items-center gap-2 rounded-lg bg-red-500/20 border border-red-500/30 p-3">
              <AlertTriangle className="h-4 w-4 text-red-400" />
              <p className="text-sm text-red-300">{error}</p>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleClose}
              className="flex-1 rounded-lg bg-gray-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-gray-500"
            >
              Hủy
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !reason}
              className="flex-1 rounded-lg bg-red-500 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-red-600 disabled:cursor-not-allowed disabled:bg-gray-600"
            >
              {isSubmitting ? 'Đang gửi...' : 'Gửi báo cáo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );

  // Use Portal to render at the top level of DOM
  return createPortal(modalContent, document.body);
};

export default ReportModal;
