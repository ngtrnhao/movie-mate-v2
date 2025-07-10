import {
  Star,
  Favorite,
  RateReview,
  ThumbUp,
  TrendingUp,
  TrendingDown,
  BarChart,
} from '@mui/icons-material';
import { useSelector } from 'react-redux';
import { selectUser } from '../../../store/selectors/authSelectors';
import { getUserType, getUserLimit, USER_TYPES } from '../../../utils/userPermissions';
import LimitCounter from '../../../components/common/LimitCounter';
import UpgradePrompt from '../../../components/common/UpgradePrompt';

// Cải tiến UI cho Rating Distribution
const RatingDistribution = ({ distribution }) => {
  if (!distribution) return null;
  const stars = [5, 4, 3, 2, 1];

  // Find the maximum count for percentage calculation
  const maxCount = Math.max(...stars.map(star => distribution[`${star}_star`] || 0));
  const totalRatings = stars.reduce((sum, star) => sum + (distribution[`${star}_star`] || 0), 0);

  return (
    <div className="mt-4 rounded-lg bg-gray-800 p-4">
      <div className="mb-4 flex items-center gap-2">
        <BarChart className="size-5 text-blue-400" />
        <h3 className="font-medium text-gray-200">Rating Distribution</h3>
        <span className="ml-auto text-sm text-gray-400">{totalRatings} total</span>
      </div>

      <div className="space-y-3">
        {stars.map(star => {
          const count = distribution[`${star}_star`] || 0;
          const percentage = totalRatings > 0 ? (count / totalRatings) * 100 : 0;

          return (
            <div key={star} className="grid grid-cols-12 items-center gap-2">
              {/* Star Rating */}
              <div className="col-span-2 flex items-center text-sm">
                <span className="text-yellow-400">{star}</span>
                <Star className="ml-1 size-4 text-yellow-400" />
              </div>

              {/* Progress Bar */}
              <div className="col-span-8 h-4 overflow-hidden rounded-full bg-gray-700">
                <div
                  className="h-full rounded-full bg-yellow-400/80 transition-all duration-300"
                  style={{ width: `${percentage}%` }}
                />
              </div>

              {/* Count & Percentage */}
              <div className="col-span-2 text-right">
                <span className="text-sm text-gray-300">{count}</span>
                <span className="ml-1 text-xs text-gray-500">({percentage.toFixed(0)}%)</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

const StatsCard = ({ stats }) => {
  const user = useSelector(selectUser);
  const userType = getUserType(user);

  const favoritesLimit = getUserLimit(user, 'favorites');
  const listsLimit = getUserLimit(user, 'lists');
  const reviewsLimit = getUserLimit(user, 'reviews_per_day');

  const statItems = [
    // {
    //   label: 'Movies Watched',
    //   value: stats?.movies_watched || 0,
    //   icon: <Movie className="text-red-600" />,
    //   color: 'text-blue-400',
    //   showLimit: false,
    // },
    {
      label: 'Reviews Written',
      value: stats?.reviews_count || 0,
      icon: <RateReview className="text-red-600" />,
      color: 'text-green-400',
      limit: reviewsLimit,
      showLimit: userType !== USER_TYPES.GUEST,
    },
    {
      label: 'Average Rating',
      value: stats?.average_rating ? `${stats.average_rating.toFixed(1)}★` : 'N/A',
      icon: <Star className="text-red-600" />,
      color: 'text-yellow-400',
      showLimit: false,
    },
    {
      label: 'Favorites',
      value: stats?.favorites_count || 0,
      icon: <Favorite className="text-red-600" />,
      color: 'text-red-400',
      limit: favoritesLimit,
      showLimit: userType !== USER_TYPES.GUEST,
    },
    {
      label: 'Total Ratings',
      value: stats?.total_ratings || 0,
      icon: <ThumbUp className="text-red-600" />,
      color: 'text-purple-400',
      showLimit: false,
    },
    {
      label: 'Highest Rating',
      value: stats?.highest_rating ? `${stats.highest_rating.toFixed(1)}★` : 'N/A',
      icon: <TrendingUp className="text-green-400" />,
      color: 'text-green-400',
      showLimit: false,
    },
    {
      label: 'Lowest Rating',
      value: stats?.lowest_rating ? `${stats.lowest_rating.toFixed(1)}★` : 'N/A',
      icon: <TrendingDown className="text-red-400" />,
      color: 'text-red-400',
      showLimit: false,
    },
    {
      label: 'Helpful Votes',
      value: stats?.helpful_votes_received || 0,
      icon: <ThumbUp className="text-blue-400" />,
      color: 'text-blue-400',
      showLimit: false,
    },
    {
      label: 'Helpfulness Ratio',
      value: stats?.helpfulness_ratio ? `${(stats.helpfulness_ratio * 100).toFixed(0)}%` : '0%',
      icon: <ThumbUp className="text-blue-400" />,
      color: 'text-blue-400',
      showLimit: false,
    },
    {
      label: 'Total Watch Time',
      value: stats?.total_watch_time ? `${Math.round(stats.total_watch_time / 60)}h` : '0h',
      icon: <Star className="text-indigo-400" />,
      color: 'text-indigo-400',
      showLimit: false,
    },
    {
      label: 'Reviews This Week',
      value: stats?.reviews_this_week || 0,
      icon: <RateReview className="text-green-400" />,
      color: 'text-green-400',
      showLimit: false,
    },
    {
      label: 'Reviews This Month',
      value: stats?.reviews_this_month || 0,
      icon: <RateReview className="text-green-400" />,
      color: 'text-green-400',
      showLimit: false,
    },
    {
      label: 'Ratings This Week',
      value: stats?.ratings_this_week || 0,
      icon: <ThumbUp className="text-purple-400" />,
      color: 'text-purple-400',
      showLimit: false,
    },
    {
      label: 'Ratings This Month',
      value: stats?.ratings_this_month || 0,
      icon: <ThumbUp className="text-purple-400" />,
      color: 'text-purple-400',
      showLimit: false,
    },
  ];

  return (
    <div className="rounded-2xl border border-gray-700 bg-gray-800/95 p-6 shadow-xl backdrop-blur-sm">
      <h3 className="mb-6 text-xl font-bold text-white">Profile Stats</h3>

      {userType === USER_TYPES.GUEST && (
        <div className="mb-6">
          <UpgradePrompt user={user} feature="detailed statistics" type="inline" size="sm" />
        </div>
      )}

      <div className="space-y-4">
        {statItems.map((item, index) => (
          <div key={index} className="rounded-lg bg-gray-900/50 p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                {item.icon}
                <span className="text-gray-300">{item.label}</span>
              </div>
              <span className={`font-bold ${item.color}`}>{item.value}</span>
            </div>

            {/* Show limits for authenticated users */}
            {item.showLimit && item.limit !== undefined && (
              <div className="mt-2 flex justify-end">
                <LimitCounter current={item.value} max={item.limit} type="badge" size="xs" />
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Rating Distribution */}
      {stats?.rating_distribution && (
        <RatingDistribution distribution={stats.rating_distribution} />
      )}

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
