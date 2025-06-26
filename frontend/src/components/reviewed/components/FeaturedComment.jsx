import { motion } from 'framer-motion';
import { Heart, MessageSquare, Share2, Star, Award } from 'lucide-react';

const FeaturedComment = ({ comment }) => {
  const renderStars = rating => {
    return (
      <div className="flex items-center gap-0.5">
        {[...Array(rating)].map((_, i) => (
          <Star key={i} className="h-4 w-4 fill-yellow-400 text-yellow-400" />
        ))}
        {[...Array(5 - rating)].map((_, i) => (
          <Star key={i} className="h-4 w-4 text-gray-600" />
        ))}
      </div>
    );
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: 0.3 }}
      className="rounded-xl border border-yellow-500/30 bg-gradient-to-br from-yellow-900/20 to-orange-900/20 p-6"
    >
      {/* Header */}
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Award className="h-5 w-5 text-yellow-400" />
          <h3 className="font-semibold text-yellow-400">Bình luận nổi bật</h3>
        </div>
        <span className="text-xs text-gray-400">{comment.timeAgo}</span>
      </div>

      {/* User Info */}
      <div className="mb-4 flex items-center gap-3">
        <motion.img
          whileHover={{ scale: 1.1 }}
          src={comment.user.avatar}
          alt={comment.user.name}
          className="h-12 w-12 rounded-full border-2 border-yellow-400/50"
        />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold text-white">{comment.user.name}</h4>
            {comment.user.verified && (
              <div className="flex items-center gap-1 rounded-full bg-blue-600 px-2 py-0.5 text-xs text-white">
                ✓ {comment.user.badge}
              </div>
            )}
          </div>
          <div className="flex items-center gap-2 text-sm text-gray-400">
            <span>{comment.movie}</span>
            {renderStars(comment.rating)}
          </div>
        </div>
      </div>

      {/* Comment Text */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="mb-4 rounded-lg bg-gray-800/50 p-4"
      >
        <p className="text-gray-200 leading-relaxed">"{comment.text}"</p>
      </motion.div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 text-red-400 hover:text-red-300"
          >
            <Heart className={`h-4 w-4 ${comment.isHearted ? 'fill-current' : ''}`} />
            <span className="text-sm font-medium">{comment.likes}</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 text-blue-400 hover:text-blue-300"
          >
            <MessageSquare className="h-4 w-4" />
            <span className="text-sm font-medium">{comment.replies}</span>
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.05 }}
            whileTap={{ scale: 0.95 }}
            className="flex items-center gap-2 text-green-400 hover:text-green-300"
          >
            <Share2 className="h-4 w-4" />
            <span className="text-sm">Chia sẻ</span>
          </motion.button>
        </div>

        <motion.button
          whileHover={{
            backgroundColor: '#DC2626',
            scale: 1.02,
          }}
          whileTap={{ scale: 0.98 }}
          className="rounded-lg bg-red-600 px-4 py-2 text-sm font-medium text-white transition-colors"
        >
          Phản hồi
        </motion.button>
      </div>

      {/* Sparkle Effect */}
      <div className="absolute -right-1 -top-1 text-yellow-400">
        <motion.span
          animate={{
            rotate: [0, 360],
            scale: [1, 1.2, 1],
          }}
          transition={{
            duration: 2,
            repeat: Infinity,
            ease: 'easeInOut',
          }}
          className="text-lg"
        >
          ✨
        </motion.span>
      </div>
    </motion.div>
  );
};

export default FeaturedComment;
