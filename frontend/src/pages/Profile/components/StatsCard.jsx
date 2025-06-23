import { Movie, Star, Visibility, Favorite, RateReview, ThumbUp } from '@mui/icons-material';

const StatsCard = ({ stats }) => {
  const statItems = [
    {
      label: 'Movies Watched',
      value: stats?.movies_watched || 0,
      icon: <Movie className="text-red-600" />,
      color: 'text-blue-400',
    },
    {
      label: 'Reviews Written',
      value: stats?.reviews_count || 0,
      icon: <RateReview className="text-red-600" />,
      color: 'text-green-400',
    },
    {
      label: 'Average Rating',
      value: stats?.average_rating ? `${stats.average_rating.toFixed(1)}★` : 'N/A',
      icon: <Star className="text-red-600" />,
      color: 'text-yellow-400',
    },
    {
      label: 'Favorites',
      value: stats?.favorites_count || 0,
      icon: <Favorite className="text-red-600" />,
      color: 'text-red-400',
    },
    {
      label: 'Total Ratings',
      value: stats?.total_ratings || 0,
      icon: <ThumbUp className="text-red-600" />,
      color: 'text-purple-400',
    },
    {
      label: 'Watch Time',
      value: stats?.total_watch_time ? `${Math.round(stats.total_watch_time / 60)}h` : '0h',
      icon: <Visibility className="text-red-600" />,
      color: 'text-indigo-400',
    },
  ];

  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800/95 p-6 shadow-xl backdrop-blur-sm">
      <h3 className="mb-6 text-xl font-bold text-white">Profile Stats</h3>

      <div className="space-y-4">
        {statItems.map((item, index) => (
          <div
            key={index}
            className="flex items-center justify-between rounded-lg bg-gray-900/50 p-4"
          >
            <div className="flex items-center gap-3">
              {item.icon}
              <span className="text-gray-300">{item.label}</span>
            </div>
            <span className={`font-bold ${item.color}`}>{item.value}</span>
          </div>
        ))}
      </div>

      {stats?.streak_days && stats.streak_days > 0 && (
        <div className="mt-6 rounded-lg border border-red-600/30 bg-red-600/10 p-4">
          <div className="flex items-center gap-2">
            <span className="text-red-600">🔥</span>
            <span className="font-semibold text-red-600">{stats.streak_days} day streak!</span>
          </div>
          <p className="mt-1 text-sm text-gray-400">Keep watching movies to maintain your streak</p>
        </div>
      )}
    </div>
  );
};

export default StatsCard;
