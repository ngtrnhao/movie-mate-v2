import { useSelector } from 'react-redux';
import { Heart, Clock, Eye, CheckCircle } from 'lucide-react';
import {
  selectFavoritesCount,
  selectFavoritesInitialized,
} from '../../store/selectors/favoritesSelectors';
import {
  selectWatchlistCounts,
  selectWatchlistInitialized,
} from '../../store/selectors/watchlistSelectors';

const UserStatsCard = ({ className = '' }) => {
  const { isAuthenticated } = useSelector(state => state.auth);

  const favoritesCount = useSelector(selectFavoritesCount);
  const favoritesInitialized = useSelector(selectFavoritesInitialized);

  const watchlistCounts = useSelector(selectWatchlistCounts);
  const watchlistInitialized = useSelector(selectWatchlistInitialized);

  if (!isAuthenticated) {
    return null;
  }

  const stats = [
    {
      label: 'Favorites',
      count: favoritesInitialized ? favoritesCount : '...',
      icon: Heart,
      color: 'text-pink-500',
      bgColor: 'bg-pink-500/10',
    },
    {
      label: 'Plan to Watch',
      count: watchlistInitialized ? watchlistCounts.planned : '...',
      icon: Clock,
      color: 'text-blue-500',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: 'Watching',
      count: watchlistInitialized ? watchlistCounts.watching : '...',
      icon: Eye,
      color: 'text-yellow-500',
      bgColor: 'bg-yellow-500/10',
    },
    {
      label: 'Watched',
      count: watchlistInitialized ? watchlistCounts.watched : '...',
      icon: CheckCircle,
      color: 'text-green-500',
      bgColor: 'bg-green-500/10',
    },
  ];

  return (
    <div className={`grid grid-cols-2 gap-4 md:grid-cols-4 ${className}`}>
      {stats.map(stat => {
        const IconComponent = stat.icon;

        return (
          <div
            key={stat.label}
            className={`rounded-lg ${stat.bgColor} p-4 transition-all duration-200 hover:scale-105`}
          >
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-400">{stat.label}</p>
                <p className="mt-1 text-2xl font-bold text-white">{stat.count}</p>
              </div>
              <div className={`${stat.color}`}>
                <IconComponent size={24} />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default UserStatsCard;
