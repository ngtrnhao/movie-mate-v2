import { motion } from 'framer-motion';
import { useState } from 'react';
import { Search, Filter, Settings, Flame, TrendingUp, Trophy } from 'lucide-react';

// Import components
import HotMovieCard from './components/HotMovieCard';
import FeaturedCommentsSlider from './components/FeaturedCommentsSlider';
import LiveCommentsFeed from './components/LiveCommentsFeed';
import MovieBuzzSidebar from './components/MovieBuzzSidebar';

// Import data
import movieBuzzData from './movieBuzzData';

const MovieBuzzSection = () => {
  const [activeFilter, setActiveFilter] = useState('all');
  const [isLivePaused, setIsLivePaused] = useState(false);

  const filters = [
    { id: 'all', label: 'Tất cả', icon: '🔥' },
    { id: 'hot', label: 'Đang hot', icon: '🚀' },
    { id: 'new', label: 'Mới nhất', icon: '✨' },
    { id: 'trending', label: 'Thịnh hành', icon: '📈' },
  ];

  return (
    <>
      <style>{`
        .hide-scrollbar::-webkit-scrollbar {
          display: none;
        }
      `}</style>
      <section className="bg-gray-900 py-8 pl-14">
        {/* Horizontal Rectangle Container */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="mx-auto w-full max-w-[95vw] min-h-[600px] rounded-3xl border border-gray-700 bg-gray-800/50 p-6 shadow-2xl backdrop-blur-sm"
        >
          {/* Compact Header Row */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="mb-4 flex items-center justify-between"
          >
            {/* Left: Title & Live Badge */}
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2">
                <motion.div
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 2, repeat: Infinity }}
                  className="text-2xl"
                >
                  🎬
                </motion.div>
                <h2 className="text-2xl font-bold text-white">Góc Điện Ảnh Sôi Động</h2>
                <motion.div
                  animate={{ scale: [1, 1.1, 1] }}
                  transition={{ duration: 1.5, repeat: Infinity }}
                  className="rounded-full bg-red-500 px-2 py-1 text-xs font-medium text-white"
                >
                  LIVE
                </motion.div>
              </div>

              {/* Filter Tabs - Inline with header */}
              <div className="flex gap-2 ml-8">
                {filters.map(filter => (
                  <motion.button
                    key={filter.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={() => setActiveFilter(filter.id)}
                    className={`flex items-center gap-1 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                      activeFilter === filter.id
                        ? 'bg-pink-600 text-white'
                        : 'bg-gray-700 text-gray-400 hover:bg-gray-600 hover:text-white'
                    }`}
                  >
                    <span className="text-sm">{filter.icon}</span>
                    {filter.label}
                  </motion.button>
                ))}
              </div>
            </div>

            {/* Right: Search & Controls */}
            <div className="flex items-center gap-3">
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                className="relative"
              >
                <Search className="absolute left-3 top-1/2 h-3 w-3 -translate-y-1/2 text-gray-400" />
                <input
                  type="text"
                  placeholder="Tìm kiếm..."
                  className="w-40 rounded-lg border border-gray-600 bg-gray-800 py-1.5 pl-8 pr-3 text-xs text-white placeholder-gray-400 focus:border-pink-500 focus:outline-none"
                />
              </motion.div>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-lg border border-gray-600 bg-gray-800 p-1.5 text-gray-300 hover:text-white"
              >
                <Filter className="h-3 w-3" />
              </motion.button>

              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="rounded-lg border border-gray-600 bg-gray-800 p-1.5 text-gray-300 hover:text-white"
              >
                <Settings className="h-3 w-3" />
              </motion.button>
            </div>
          </motion.div>

          {/* Featured Comments Slider - Top Horizontal */}
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="mb-4"
          >
            <FeaturedCommentsSlider comments={movieBuzzData.featuredComments} />
          </motion.div>

          {/* Main Horizontal Layout */}
          <div className="flex min-h-[400px] gap-6">
            {/* Left Section - Hot Movies (Vertical Stack) */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
              className="w-[420px] flex-shrink-0"
            >
              <div className="h-[600px] rounded-xl border border-gray-600 bg-gray-700/30 p-4 flex flex-col">
                <div className="mb-4 flex items-center gap-2 flex-shrink-0">
                  <Flame className="h-4 w-4 text-red-500" />
                  <h3 className="text-sm font-semibold text-white">Phim Hot</h3>
                  <div className="rounded-full bg-red-500/20 px-2 py-0.5 text-xs text-red-400">
                    {movieBuzzData.hotMovies.length}
                  </div>
                </div>

                <div className="flex-1 min-h-0">
                  <div
                    className="h-full overflow-y-auto hide-scrollbar"
                    style={{ scrollbarWidth: 'none', msOverflowStyle: 'none' }}
                  >
                    <div className="space-y-3 p-1">
                      {movieBuzzData.hotMovies.map(movie => (
                        <HotMovieCard key={movie.id} movie={movie} />
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* Center Section - Live Feed */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
              className="flex-1 flex flex-col h-[600px] "
            >
              <div className="flex-1">
                <LiveCommentsFeed comments={movieBuzzData.liveComments} isLive={!isLivePaused} />
              </div>
            </motion.div>

            {/* Right Section - Enhanced Stats & Community */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              className="w-[380px] flex-shrink-0 flex flex-col gap-4"
            >
              {/* Enhanced Stats Section */}
              <div className="rounded-xl border border-gray-600 bg-gray-700/30 p-5 ">
                <div className="mb-4 flex items-center gap-2">
                  <TrendingUp className="h-5 w-5 text-blue-400" />
                  <h3 className="text-lg font-semibold text-white">Thống Kê Hôm Nay</h3>
                  <motion.div
                    animate={{ scale: [1, 1.2, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-blue-400"
                  >
                    📊
                  </motion.div>
                </div>

                <div className="space-y-4">
                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.4 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-800/50"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">💬</span>
                      <span className="text-sm text-gray-400">Bình luận mới</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-white">
                        {movieBuzzData.stats.todayComments.toLocaleString()}
                      </div>
                      <div className="text-xs text-green-400">+127 hôm qua</div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.5 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-800/50"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">👥</span>
                      <span className="text-sm text-gray-400">Users hoạt động</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-white">
                        {movieBuzzData.stats.activeUsers}
                      </div>
                      <div className="text-xs text-green-400">+23 đang online</div>
                    </div>
                  </motion.div>

                  <motion.div
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: 0.6 }}
                    className="flex items-center justify-between p-3 rounded-lg bg-gray-800/50"
                  >
                    <div className="flex items-center gap-2">
                      <span className="text-lg">⭐</span>
                      <span className="text-sm text-gray-400">Reviews mới</span>
                    </div>
                    <div className="text-right">
                      <div className="text-xl font-bold text-white">
                        {movieBuzzData.stats.newReviews}
                      </div>
                      <div className="text-xs text-green-400">+8 hôm nay</div>
                    </div>
                  </motion.div>
                </div>
              </div>

              {/* Top Contributors */}
              <div className="rounded-xl border border-gray-600 bg-gray-700/30 p-5">
                <div className="mb-4 flex items-center gap-2">
                  <Trophy className="h-5 w-5 text-yellow-400" />
                  <h3 className="text-lg font-semibold text-white">Top Contributors</h3>
                  <motion.div
                    animate={{ rotate: [0, 10, -10, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-yellow-400"
                  >
                    🏆
                  </motion.div>
                </div>

                <div className="space-y-3">
                  {movieBuzzData.leaderboard.slice(0, 4).map((user, index) => (
                    <motion.div
                      key={user.rank}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: 0.4 + index * 0.1 }}
                      className="flex items-center gap-3 p-2 rounded-lg bg-gray-800/30 hover:bg-gray-800/50 transition-all"
                    >
                      <span className="text-2xl">{user.badge}</span>
                      <div className="flex-1">
                        <div className="text-sm font-medium text-white">{user.user}</div>
                        <div className="text-xs text-gray-400">Rank #{user.rank}</div>
                      </div>
                      <div className="text-right">
                        <div className="text-sm font-bold text-yellow-400">{user.points}</div>
                        <div className="text-xs text-gray-500">điểm</div>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            </motion.div>
          </div>

          {/* Bottom Section - Modern Layout */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
            className="mt-6 grid grid-cols-12 gap-6"
          >
            {/* Left - Thể Loại Đang Hot - Enhanced */}
            <div className="col-span-8 rounded-xl border border-gray-600 bg-gradient-to-r from-gray-700/40 to-gray-600/30 p-6">
              <div className="mb-4 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <TrendingUp className="h-5 w-5 text-green-400" />
                  <h3 className="text-lg font-semibold text-white">Thể Loại Đang Hot</h3>
                  <motion.div
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-green-400"
                  >
                    🔥
                  </motion.div>
                </div>
                <motion.button
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  className="text-xs text-green-400 hover:text-green-300 flex items-center gap-1"
                >
                  Xem tất cả →
                </motion.button>
              </div>

              {/* Grid layout 3x3 for better space usage */}
              <div className="grid grid-cols-3 gap-3 mb-4">
                {movieBuzzData.genreTrending.map((genre, index) => (
                  <motion.div
                    key={genre.genre}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: 0.1 * index }}
                    whileHover={{ scale: 1.05, y: -2 }}
                    className="group relative overflow-hidden rounded-xl bg-gradient-to-br from-gray-800/60 to-gray-900/60 p-4 cursor-pointer transition-all hover:shadow-lg"
                    style={{
                      boxShadow: `0 0 20px ${genre.color}20`,
                    }}
                  >
                    {/* Background gradient effect */}
                    <div
                      className="absolute inset-0 opacity-10 transition-opacity group-hover:opacity-20"
                      style={{
                        background: `linear-gradient(135deg, ${genre.color}40, transparent)`,
                      }}
                    />

                    {/* Content */}
                    <div className="relative z-10">
                      <div className="mb-3 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-lg">{genre.icon}</span>
                          <h4 className="text-sm font-bold text-white group-hover:text-white transition-colors">
                            {genre.genre}
                          </h4>
                        </div>
                        <motion.div
                          whileHover={{ scale: 1.2 }}
                          className="text-xs font-bold px-2 py-1 rounded-full"
                          style={{
                            backgroundColor: `${genre.color}20`,
                            color: genre.color,
                          }}
                        >
                          {genre.percentage}%
                        </motion.div>
                      </div>

                      {/* Enhanced progress bar */}
                      <div className="mb-2">
                        <div className="relative h-2 rounded-full bg-gray-700 overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${genre.percentage}%` }}
                            transition={{ duration: 1.5, delay: 0.2 * index, ease: 'easeOut' }}
                            className="h-full rounded-full relative"
                            style={{ backgroundColor: genre.color }}
                          >
                            {/* Shimmer effect */}
                            <motion.div
                              animate={{ x: ['-100%', '100%'] }}
                              transition={{ duration: 2, repeat: Infinity, repeatDelay: 1 }}
                              className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent"
                            />
                          </motion.div>
                        </div>
                      </div>

                      {/* Stats */}
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-gray-400">{genre.movies} phim</span>
                        <div className="flex items-center gap-1 text-gray-400">
                          <span>📈</span>
                          <span
                            className={genre.trend === 'up' ? 'text-green-400' : 'text-red-400'}
                          >
                            {genre.change}
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>

              {/* Trending insight */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 1 }}
                className="rounded-lg bg-gradient-to-r from-blue-900/30 to-purple-900/30 border border-blue-500/30 p-3"
              >
                <div className="flex items-center gap-2 text-xs">
                  <span className="text-blue-400">💡</span>
                  <span className="text-gray-300">
                    <strong className="text-blue-400">Action</strong> đang dẫn đầu với
                    <strong className="text-yellow-400 ml-1">89% popularity</strong> - tăng{' '}
                    <strong className="text-green-400">+12%</strong> so với tuần trước
                  </span>
                </div>
              </motion.div>
            </div>

            {/* Right - Community Highlights */}
            <div className="col-span-4 space-y-4">
              <div className="mb-4 flex items-center gap-2">
                <motion.span
                  animate={{ rotate: [0, 10, -10, 0] }}
                  transition={{ duration: 3, repeat: Infinity }}
                  className="text-xl"
                >
                  🏆
                </motion.span>
                <h3 className="text-lg font-semibold text-white">Community Highlights</h3>
              </div>

              {/* Top Reviewer of the Week */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 }}
                whileHover={{ scale: 1.03, backgroundColor: 'rgba(34, 197, 94, 0.1)' }}
                className="group rounded-xl border border-gray-600 bg-gradient-to-br from-green-900/20 to-gray-700/50 p-4 cursor-pointer transition-all hover:border-green-500/50"
              >
                <div className="flex items-center gap-3">
                  <motion.div whileHover={{ scale: 1.2 }} className="text-2xl">
                    👑
                  </motion.div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white group-hover:text-green-400 transition-colors">
                      Reviewer của tuần
                    </h4>
                    <p className="text-xs text-gray-400 mt-1">CinePhile_VN - 47 reviews</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="text-sm font-bold text-green-400">+156 điểm</div>
                      <span className="text-xs text-gray-500">tuần này</span>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Most Liked Comment */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.7 }}
                whileHover={{ scale: 1.03, backgroundColor: 'rgba(239, 68, 68, 0.1)' }}
                className="group rounded-xl border border-gray-600 bg-gradient-to-br from-red-900/20 to-gray-700/50 p-4 cursor-pointer transition-all hover:border-red-500/50"
              >
                <div className="flex items-center gap-3">
                  <motion.div
                    whileHover={{ scale: 1.2 }}
                    animate={{ scale: [1, 1.1, 1] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-2xl"
                  >
                    ❤️
                  </motion.div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white group-hover:text-red-400 transition-colors">
                      Bình luận được yêu thích
                    </h4>
                    <p className="text-xs text-gray-400 mt-1 line-clamp-2">
                      "Avatar 2 thật sự là masterpiece..."
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="text-sm font-bold text-red-400">1,234 likes</div>
                      <span className="text-xs text-gray-500">hôm nay</span>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Rising Star */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.8 }}
                whileHover={{ scale: 1.03, backgroundColor: 'rgba(168, 85, 247, 0.1)' }}
                className="group rounded-xl border border-gray-600 bg-gradient-to-br from-purple-900/20 to-gray-700/50 p-4 cursor-pointer transition-all hover:border-purple-500/50"
              >
                <div className="flex items-center gap-3">
                  <motion.div
                    whileHover={{ rotate: 180 }}
                    transition={{ duration: 0.5 }}
                    className="text-2xl"
                  >
                    ⭐
                  </motion.div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white group-hover:text-purple-400 transition-colors">
                      Rising Star
                    </h4>
                    <p className="text-xs text-gray-400 mt-1">MovieLover88 - New member</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="text-sm font-bold text-purple-400">+89 likes</div>
                      <span className="text-xs text-gray-500">3 ngày</span>
                    </div>
                  </div>
                </div>
              </motion.div>

              {/* Hot Discussion */}
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.9 }}
                whileHover={{ scale: 1.03, backgroundColor: 'rgba(249, 115, 22, 0.1)' }}
                className="group rounded-xl border border-gray-600 bg-gradient-to-br from-orange-900/20 to-gray-700/50 p-4 cursor-pointer transition-all hover:border-orange-500/50"
              >
                <div className="flex items-center gap-3">
                  <motion.div
                    whileHover={{ scale: 1.2 }}
                    animate={{ rotate: [0, 5, -5, 0] }}
                    transition={{ duration: 2, repeat: Infinity }}
                    className="text-2xl"
                  >
                    🔥
                  </motion.div>
                  <div className="flex-1">
                    <h4 className="font-semibold text-white group-hover:text-orange-400 transition-colors">
                      Cuộc thảo luận hot
                    </h4>
                    <p className="text-xs text-gray-400 mt-1">MCU Phase 5: Có còn hấp dẫn?</p>
                    <div className="mt-2 flex items-center gap-2">
                      <div className="text-sm font-bold text-orange-400">78 replies</div>
                      <span className="text-xs text-gray-500">đang diễn ra</span>
                    </div>
                  </div>
                </div>
              </motion.div>
            </div>
          </motion.div>
        </motion.div>

        {/* Floating Action Button */}
        <motion.div
          initial={{ opacity: 0, scale: 0 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 1 }}
          className="fixed bottom-8 right-8 z-10"
        >
          <motion.button
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.9 }}
            animate={{ y: [0, -8, 0] }}
            transition={{ duration: 2, repeat: Infinity }}
            className="rounded-full bg-pink-600 p-3 text-white shadow-lg hover:bg-pink-500"
          >
            💬
          </motion.button>
        </motion.div>
      </section>
    </>
  );
};

export default MovieBuzzSection;
