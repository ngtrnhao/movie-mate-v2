import React from 'react';
import { useTrendingAnalytics } from '../../../hooks/useTrendingAnalytics';
import {
  FireIcon,
  ArrowTrendingUpIcon,
  ChartBarIcon,
  StarIcon,
  EyeIcon,
  HeartIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const TrendingAnalytics = () => {
  const { data, loading, error, refetch } = useTrendingAnalytics();

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
          <div className="grid grid-cols-2 gap-4">
            <div className="h-20 bg-gray-200 rounded"></div>
            <div className="h-20 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={refetch}
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Thử lại
          </button>
        </div>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-6">
        <p className="text-gray-500 text-center">Không có dữ liệu</p>
      </div>
    );
  }

  const { trending_categories, top_performers, performance_distribution, summary } = data;

  const getCategoryIcon = category => {
    switch (category) {
      case 'viral':
        return <FireIcon className="w-5 h-5 text-red-500" />;
      case 'hot':
        return <ArrowTrendingUpIcon className="w-5 h-5 text-orange-500" />;
      case 'rising':
        return <ArrowTrendingUpIcon className="w-5 h-5 text-yellow-500" />;
      case 'stable':
        return <ArrowPathIcon className="w-5 h-5 text-green-500" />;
      default:
        return <ChartBarIcon className="w-5 h-5 text-gray-500" />;
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
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Tổng quan xu hướng</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-blue-100 rounded-full mx-auto mb-2">
              <ChartBarIcon className="w-5 h-5 text-blue-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">
              {summary.total_movies_with_metrics?.toLocaleString() || 0}
            </p>
            <p className="text-sm text-gray-500">Phim có metrics</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-green-100 rounded-full mx-auto mb-2">
              <StarIcon className="w-5 h-5 text-green-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.avg_performance_score || 0}</p>
            <p className="text-sm text-gray-500">Điểm hiệu suất TB</p>
          </div>
          <div className="text-center">
            <div className="flex items-center justify-center w-10 h-10 bg-purple-100 rounded-full mx-auto mb-2">
              <ArrowTrendingUpIcon className="w-5 h-5 text-purple-600" />
            </div>
            <p className="text-2xl font-bold text-gray-900">{summary.avg_trending_score || 0}</p>
            <p className="text-sm text-gray-500">Điểm xu hướng TB</p>
          </div>
        </div>
      </div>

      {/* Trending Categories */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Phân bố danh mục xu hướng</h3>
        <div className="space-y-4">
          {trending_categories?.map(category => (
            <div
              key={category.production_metrics__trending_category}
              className="border rounded-lg p-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  {getCategoryIcon(category.production_metrics__trending_category)}
                  <span className="ml-2 font-medium text-gray-900 capitalize">
                    {category.production_metrics__trending_category}
                  </span>
                  <span
                    className={`ml-2 px-2 py-1 rounded-full text-xs font-medium ${getCategoryColor(category.production_metrics__trending_category)}`}
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
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Viral Movies */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <FireIcon className="w-5 h-5 text-red-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Viral</h3>
          </div>
          <div className="space-y-3">
            {top_performers?.viral?.slice(0, 3).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-red-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-xs font-medium text-red-600">#{index + 1}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900 truncate">{movie.title}</span>
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
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <ArrowTrendingUpIcon className="w-5 h-5 text-orange-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Hot</h3>
          </div>
          <div className="space-y-3">
            {top_performers?.hot?.slice(0, 3).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-orange-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-xs font-medium text-orange-600">#{index + 1}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900 truncate">{movie.title}</span>
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
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center mb-4">
            <ArrowTrendingUpIcon className="w-5 h-5 text-yellow-500 mr-2" />
            <h3 className="text-lg font-medium text-gray-900">Rising</h3>
          </div>
          <div className="space-y-3">
            {top_performers?.rising?.slice(0, 3).map((movie, index) => (
              <div key={movie.id} className="flex items-center justify-between">
                <div className="flex items-center">
                  <div className="w-6 h-6 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-xs font-medium text-yellow-600">#{index + 1}</span>
                  </div>
                  <span className="text-sm font-medium text-gray-900 truncate">{movie.title}</span>
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
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Phân bố điểm hiệu suất</h3>
        <div className="space-y-3">
          {performance_distribution?.map(range => (
            <div key={range.range} className="flex items-center justify-between">
              <div className="flex items-center">
                <div className="w-4 h-4 bg-blue-500 rounded mr-3"></div>
                <span className="text-sm font-medium text-gray-900">{range.range} điểm</span>
              </div>
              <div className="flex items-center">
                <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                  <div
                    className="bg-blue-500 h-2 rounded-full"
                    style={{
                      width: `${(range.count / Math.max(...performance_distribution.map(r => r.count))) * 100}%`,
                    }}
                  ></div>
                </div>
                <span className="text-sm font-medium text-gray-900 w-10">{range.count}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default TrendingAnalytics;
