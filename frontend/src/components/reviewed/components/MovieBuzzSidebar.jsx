import { motion } from 'framer-motion';
import { TrendingUp, Users, MessageSquare, Star, Trophy, Zap } from 'lucide-react';

const MovieBuzzSidebar = ({ stats, leaderboard, trendingTags }) => {
  return (
    <div className="space-y-6">
      {/* Stats Widget */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        className="rounded-xl border border-gray-700 bg-gray-800 p-4"
      >
        <div className="mb-4 flex items-center gap-2">
          <TrendingUp className="h-5 w-5 text-blue-400" />
          <h3 className="font-semibold text-white">Thống kê hôm nay</h3>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4 text-pink-400" />
              <span className="text-sm text-gray-300">Bình luận</span>
            </div>
            <div className="text-right">
              <div className="font-semibold text-white">{stats.todayComments.toLocaleString()}</div>
              <div className="text-xs text-green-400">+{stats.growthPercent}% hôm qua</div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Users className="h-4 w-4 text-blue-400" />
              <span className="text-sm text-gray-300">User active</span>
            </div>
            <div className="text-right">
              <div className="font-semibold text-white">{stats.activeUsers}</div>
              <div className="text-xs text-blue-400">🟢 Online: 123</div>
            </div>
          </div>

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-400" />
              <span className="text-sm text-gray-300">Đánh giá mới</span>
            </div>
            <div className="text-right">
              <div className="font-semibold text-white">{stats.newReviews}</div>
              <div className="text-xs text-gray-400">Trong 24h</div>
            </div>
          </div>
        </div>

        <motion.button
          whileHover={{
            backgroundColor: '#1F2937',
            scale: 1.02,
          }}
          whileTap={{ scale: 0.98 }}
          className="mt-4 w-full rounded-lg border border-gray-600 py-2 text-sm text-gray-300 transition-colors hover:text-white"
        >
          📈 Xem chi tiết
        </motion.button>
      </motion.div>

      {/* Leaderboard */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.1 }}
        className="rounded-xl border border-gray-700 bg-gray-800 p-4"
      >
        <div className="mb-4 flex items-center gap-2">
          <Trophy className="h-5 w-5 text-yellow-400" />
          <h3 className="font-semibold text-white">Top Reviewer</h3>
        </div>

        <div className="space-y-3">
          {leaderboard.map((user, index) => (
            <motion.div
              key={user.rank}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 + index * 0.1 }}
              className="flex items-center gap-3 rounded-lg bg-gray-700/30 p-3 hover:bg-gray-700/50 transition-colors"
            >
              <div className="text-lg">{user.badge}</div>
              <div className="flex-1 min-w-0">
                <div className="font-medium text-white truncate">{user.user}</div>
                <div className="text-xs text-gray-400">{user.achievement}</div>
              </div>
              <div className="text-right">
                <div className="text-sm font-semibold text-yellow-400">
                  {user.points.toLocaleString()}
                </div>
                <div className="text-xs text-gray-500">điểm</div>
              </div>
            </motion.div>
          ))}
        </div>

        <motion.button
          whileHover={{
            backgroundColor: '#FCD34D',
            color: '#1F2937',
          }}
          whileTap={{ scale: 0.98 }}
          className="mt-4 w-full rounded-lg bg-yellow-400/20 py-2 text-sm text-yellow-400 transition-all hover:font-medium"
        >
          🏆 Xem bảng xếp hạng
        </motion.button>
      </motion.div>

      {/* Trending Tags */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.2 }}
        className="rounded-xl border border-gray-700 bg-gray-800 p-4"
      >
        <div className="mb-4 flex items-center gap-2">
          <Zap className="h-5 w-5 text-purple-400" />
          <h3 className="font-semibold text-white">Trending Tags</h3>
        </div>

        <div className="space-y-2">
          {trendingTags.map((tag, index) => (
            <motion.div
              key={tag.tag}
              initial={{ opacity: 0, x: 10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 + index * 0.05 }}
              whileHover={{ scale: 1.02 }}
              className="flex items-center justify-between rounded-lg bg-gray-700/30 p-2 hover:bg-gray-700/50 transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-2">
                <span className="text-sm font-medium text-purple-400">#{tag.tag}</span>
                <span className="text-xs text-gray-400">({tag.count})</span>
              </div>
              <div
                className={`text-xs font-medium ${
                  tag.growth > 0 ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {tag.growth > 0 ? '+' : ''}
                {tag.growth}%
              </div>
            </motion.div>
          ))}
        </div>

        <motion.button
          whileHover={{
            backgroundColor: '#8B5CF6',
            scale: 1.02,
          }}
          whileTap={{ scale: 0.98 }}
          className="mt-4 w-full rounded-lg bg-purple-600/20 py-2 text-sm text-purple-400 transition-all hover:text-white"
        >
          🔥 Khám phá thêm tags
        </motion.button>
      </motion.div>

      {/* Quick Actions */}
      <motion.div
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        transition={{ delay: 0.3 }}
        className="rounded-xl border border-gray-700 bg-gradient-to-br from-pink-900/20 to-purple-900/20 p-4"
      >
        <h3 className="mb-3 font-semibold text-white">Tham gia ngay</h3>

        <div className="space-y-2">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full rounded-lg bg-pink-600 py-2 text-sm font-medium text-white hover:bg-pink-500 transition-colors"
          >
            ✍️ Viết bình luận
          </motion.button>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            className="w-full rounded-lg border border-purple-600 py-2 text-sm font-medium text-purple-400 hover:bg-purple-600/20 transition-colors"
          >
            🎯 Tạo cuộc thảo luận
          </motion.button>
        </div>
      </motion.div>
    </div>
  );
};

export default MovieBuzzSidebar;
