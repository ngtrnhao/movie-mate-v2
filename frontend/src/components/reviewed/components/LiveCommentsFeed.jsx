import { motion, AnimatePresence } from 'framer-motion';
import { useState, useEffect } from 'react';
import { MessageSquare, Star, Pause, Play, RotateCcw } from 'lucide-react';

const LiveCommentsFeed = ({ comments, isLive = true }) => {
  const [isPaused, setIsPaused] = useState(false);
  const [displayComments, setDisplayComments] = useState(comments.slice(0, 5));

  // Simulate real-time updates
  useEffect(() => {
    if (!isPaused && isLive) {
      const interval = setInterval(() => {
        // Rotate comments to simulate new ones
        setDisplayComments(prev => {
          const newComments = [...prev];
          const firstComment = newComments.shift();
          newComments.push(firstComment);
          return newComments;
        });
      }, 3000);

      return () => clearInterval(interval);
    }
  }, [isPaused, isLive, comments]);

  const getCommentIcon = type => {
    switch (type) {
      case 'rating':
        return '⭐';
      case 'debate':
        return '🔥';
      case 'emotion':
        return '😭';
      default:
        return '💭';
    }
  };

  const getCommentTypeText = type => {
    switch (type) {
      case 'rating':
        return 'vừa đánh giá';
      case 'debate':
        return 'vừa tranh luận về';
      case 'emotion':
        return 'vừa cảm động với';
      default:
        return 'vừa bình luận về';
    }
  };

  return (
    <>
      <style>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
      `}</style>
      <div className="rounded-xl border border-gray-700 bg-gray-800 p-4 h-[600px] flex flex-col">
        {/* Header */}
        <div className="mb-4 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1">
              <motion.div
                animate={{ scale: [1, 1.2, 1] }}
                transition={{ duration: 1, repeat: Infinity }}
                className="h-3 w-3 rounded-full bg-red-500"
              />
              <h3 className="font-semibold text-white">Live Comments</h3>
            </div>
            <span className="rounded-full bg-red-500/20 px-2 py-1 text-xs text-red-400">
              {displayComments.length} hoạt động
            </span>
          </div>

          <div className="flex items-center gap-2">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsPaused(!isPaused)}
              className="rounded-lg bg-gray-700 p-2 text-gray-300 hover:text-white"
            >
              {isPaused ? <Play className="h-4 w-4" /> : <Pause className="h-4 w-4" />}
            </motion.button>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              className="rounded-lg bg-gray-700 p-2 text-gray-300 hover:text-white"
            >
              <RotateCcw className="h-4 w-4" />
            </motion.button>
          </div>
        </div>

        {/* Live Feed */}
        <div
          className="space-y-3 flex-1 overflow-y-auto hide-scrollbar"
          style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
        >
          <AnimatePresence mode="wait">
            {displayComments.map((comment, index) => (
              <motion.div
                key={`${comment.id}-${index}`}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: 20 }}
                transition={{ duration: 0.3, delay: index * 0.1 }}
                className="flex items-start gap-3 rounded-lg border border-gray-700/50 bg-gray-700/30 p-3 hover:bg-gray-700/50 transition-colors"
              >
                {/* Online Indicator */}
                <motion.div
                  animate={{ scale: [1, 1.2, 1] }}
                  transition={{ duration: 2, repeat: Infinity, delay: index * 0.2 }}
                  className="mt-1 h-2 w-2 rounded-full bg-green-500"
                />

                <div className="flex-1 min-w-0">
                  {/* User Action */}
                  <div className="flex items-center gap-1 text-sm">
                    <span className="font-medium text-blue-400">{comment.user}</span>
                    <span className="text-gray-400">{getCommentTypeText(comment.type)}</span>
                    <span className="font-medium text-pink-400 truncate">'{comment.movie}'</span>
                  </div>

                  {/* Comment Content */}
                  <div className="mt-1 flex items-center gap-2">
                    <span className="text-lg">{getCommentIcon(comment.type)}</span>
                    <div className="flex-1">
                      {comment.rating && (
                        <div className="flex items-center gap-1 mb-1">
                          {[...Array(comment.rating)].map((_, i) => (
                            <Star key={i} className="h-3 w-3 fill-yellow-400 text-yellow-400" />
                          ))}
                        </div>
                      )}
                      <p className="text-gray-200 text-sm line-clamp-2">"{comment.text}"</p>
                    </div>
                  </div>

                  {/* Time and Action */}
                  <div className="mt-2 flex items-center justify-between">
                    <span className="text-xs text-gray-500">📅 {comment.timeAgo} trước</span>
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      className="text-xs text-blue-400 hover:text-blue-300 flex items-center gap-1"
                    >
                      <MessageSquare className="h-3 w-3" />
                      Phản hồi
                    </motion.button>
                  </div>
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>

        {/* Status Bar */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="mt-4 flex items-center justify-between text-xs text-gray-400 border-t border-gray-700 pt-3 flex-shrink-0"
        >
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1">
              🟢 {isPaused ? 'Đã tạm dừng' : 'Đang cập nhật'}
            </span>
            <span>⚡ Tự động làm mới</span>
          </div>

          <motion.button whileHover={{ color: '#EF4444' }} className="hover:underline">
            Xem tất cả hoạt động →
          </motion.button>
        </motion.div>
      </div>
    </>
  );
};

export default LiveCommentsFeed;
