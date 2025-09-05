import { useTrendingAnalytics } from '../../../hooks/useTrendingAnalytics';
import {
  FireIcon,
  ArrowTrendingUpIcon,
  ChartBarIcon,
  StarIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const TrendingAnalytics = () => {
  const { data, loading, error, refetch } = useTrendingAnalytics();

  if (loading) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="animate-pulse">
          <div className="mb-4 h-4 w-1/4 rounded bg-gray-200"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 rounded bg-gray-200"></div>
            <div className="h-20 rounded bg-gray-200"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <div className="text-center">
          <p className="mb-4 text-red-600">{error}</p>
          <button
            onClick={refetch}
            className="rounded bg-blue-500 px-4 py-2 text-white hover:bg-blue-600"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <p className="text-center text-gray-500">Không có dữ liệu</p>
      </div>
    );
  }

  const { trending_categories, top_performers, performance_distribution, summary } = data;

  const getCategoryIcon = category => {
    switch (category) {
      case 'viral':
        return <FireIcon className="size-5 text-red-500" />;
      case 'hot':
        return <ArrowTrendingUpIcon className="size-5 text-orange-500" />;
      case 'rising':
        return <ArrowTrendingUpIcon className="size-5 text-yellow-500" />;
      case 'stable':
        return <ArrowPathIcon className="size-5 text-green-500" />;
      default:
        return <ChartBarIcon className="size-5 text-gray-500" />;
    }
  };

  const getCategoryColor = category => {
    switch (category) {
      case 'viral':
        return 'bg-red-100 text-red-800';
      case 'hot':
        return 'bg-orange-100 text-orange-800';
      case 'rising':
        return 'bg-yellow-100 text-yellow-800';
      case 'stable':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary Stats */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Tổng quan xu hướng</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-blue-100">
              <ChartBarIcon className="size-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {summary.total_movies_with_metrics?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Phim có metrics</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-green-100">
              <StarIcon className="size-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.avg_performance_score || 0}</p>
            <p className="text-sm text-gray-500">Điểm hiệu suất TB</p>
          </div>
          <div className="text-center">
            <div className="mx-auto mb-2 flex size-10 items-center justify-center rounded-full bg-purple-100">
              <ArrowTrendingUpIcon className="size-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.avg_trending_score || 0}</p>
            <p className="text-sm text-gray-500">Điểm xu hướng TB</p>
          </div>
        </div>
      </div>

      {/* Trending Categories */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Phân bố danh mục xu hướng</h3>
        <div className="space-y-4">
          {trending_categories?.map(category => (
            <div
              key={category.production_metrics__trending_category}
              className="rounded-lg border p-4"
            >
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center">
                  {getCategoryIcon(category.production_metrics__trending_category)}
                  <span className="ml-2 font-medium capitalize text-gray-900">
                    {category.production_metrics__trending_category}
                  </span>
                  <span
                    className={`ml-2 rounded-full px-2 py-1 text-xs font-medium ${getCategoryColor(category.production_metrics__trending_category)}`}
                  >
                    {category.count} phim
                  </span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    Score: {Math.round(category.avg_trending_score || 0)}
                  </p>
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm text-gray-500">
                <div>
                  <p>Hiệu suất TB: {Math.round(category.avg_performance_score || 0)}</p>
                </div>
                <div>
                  <p>Tương tác: {category.total_engagement?.toLocaleString() || 0}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Top Performers */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        {/* Viral Movies */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center">
            <FireIcon className="mr-2 size-5 text-red-500" />
            <h3 className="text-lg font-medium text-gray-900">Viral</h3>
          </div>
          <div className="space-y-3">
            {top_performers?.viral?.slice(0, 3).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="mr-3 flex size-6 items-center justify-center rounded-full bg-red-100">
                    <span className="text-xs font-medium text-red-600">#{index + 1}</span>
                  </div>
                  <span className="truncate text-sm font-medium text-gray-900">{movie.title}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {movie.production_metrics__trending_score}
                  </p>
                  <p className="text-xs text-gray-500">Score</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Hot Movies */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center">
            <ArrowTrendingUpIcon className="mr-2 size-5 text-orange-500" />
            <h3 className="text-lg font-medium text-gray-900">Hot</h3>
          </div>
          <div className="space-y-3">
            {top_performers?.hot?.slice(0, 3).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="mr-3 flex size-6 items-center justify-center rounded-full bg-orange-100">
                    <span className="text-xs font-medium text-orange-600">#{index + 1}</span>
                  </div>
                  <span className="truncate text-sm font-medium text-gray-900">{movie.title}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {movie.production_metrics__trending_score}
                  </p>
                  <p className="text-xs text-gray-500">Score</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Rising Movies */}
        <div className="rounded-lg bg-white p-6 shadow-sm">
          <div className="mb-4 flex items-center">
            <ArrowTrendingUpIcon className="mr-2 size-5 text-yellow-500" />
            <h3 className="text-lg font-medium text-gray-900">Rising</h3>
          </div>
          <div className="space-y-3">
            {top_performers?.rising?.slice(0, 3).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="mr-3 flex size-6 items-center justify-center rounded-full bg-yellow-100">
                    <span className="text-xs font-medium text-yellow-600">#{index + 1}</span>
                  </div>
                  <span className="truncate text-sm font-medium text-gray-900">{movie.title}</span>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-gray-900">
                    {movie.production_metrics__trending_score}
                  </p>
                  <p className="text-xs text-gray-500">Score</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Performance Distribution */}
      <div className="rounded-lg bg-white p-6 shadow-sm">
        <h3 className="mb-4 text-lg font-medium text-gray-900">Phân bố điểm hiệu suất</h3>
        <div className="space-y-3">
          {performance_distribution?.map(range => (
            <div key={range.range} className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="mr-3 size-4 rounded bg-blue-500"></div>
                <span className="text-sm font-medium text-gray-900">{range.range} điểm</span>
              </div>
              <div className="flex items-center">
                <div className="mr-3 h-2 w-32 rounded-full bg-gray-200">
                  <div
                    className="h-2 rounded-full bg-blue-500"
                    style={{
                      width: `${(range.count / Math.max(...performance_distribution.map(r => r.count))) * 100}%`,
                    }}
                  ></div>
                </div>
                <span className="w-10 text-sm font-medium text-gray-900">{range.count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TrendingAnalytics;
