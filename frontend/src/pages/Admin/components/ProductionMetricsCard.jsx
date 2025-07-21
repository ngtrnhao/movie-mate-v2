import {
  ChartBarIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  UserGroupIcon,
  PlayIcon,
  StarIcon,
} from '@heroicons/react/24/outline';
import {
  ArrowTrendingUpIcon as TrendingUpIconSolid,
  FireIcon as FireIconSolid,
  ChartBarIcon as ChartBarIconSolid,
} from '@heroicons/react/24/solid';

const ProductionMetricsCard = ({ movie }) => {
  if (!movie) return null;

  const {
    production_metrics: metrics = {},
    quality_metrics: quality = {},
    admin_control: adminControl = {},
  } = movie;

  // Calculate performance indicators
  const engagementRate = (metrics.engagement_rate || 0) * 100;
  const performanceScore = metrics.performance_score || 0;
  const trendingCategory = metrics.trending_category || 'stable';
  const homepageViews = metrics.homepage_views || 0;
  const detailViews = metrics.detail_page_views || 0;
  const trailerPlays = metrics.trailer_plays || 0;
  const clickThroughRate = (metrics.click_through_rate || 0) * 100;
  const trailerCompletionRate = (metrics.trailer_completion_rate || 0) * 100;

  // Trending category styling
  const getTrendingBadge = category => {
    const configs = {
      trending: {
        icon: FireIconSolid,
        bgColor: 'bg-red-100',
        textColor: 'text-red-800',
        borderColor: 'border-red-200',
        label: 'Thịnh hành',
      },
      rising: {
        icon: TrendingUpIconSolid,
        bgColor: 'bg-blue-100',
        textColor: 'text-blue-800',
        borderColor: 'border-blue-200',
        label: 'Đang tăng',
      },
      hot: {
        icon: FireIconSolid,
        bgColor: 'bg-orange-100',
        textColor: 'text-orange-800',
        borderColor: 'border-orange-200',
        label: 'Hot',
      },
      stable: {
        icon: ChartBarIconSolid,
        bgColor: 'bg-gray-100',
        textColor: 'text-gray-800',
        borderColor: 'border-gray-200',
        label: 'Ổn định',
      },
      declining: {
        icon: ArrowTrendingDownIcon,
        bgColor: 'bg-yellow-100',
        textColor: 'text-yellow-800',
        borderColor: 'border-yellow-200',
        label: 'Giảm',
      },
    };

    const config = configs[category] || configs.stable;
    const IconComponent = config.icon;

    return (
      <span
        className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-medium ${config.bgColor} ${config.textColor} ${config.borderColor}`}
      >
        <IconComponent className="mr-1.5 size-4" />
        {config.label}
      </span>
    );
  };

  // Performance score color
  const getPerformanceScoreColor = score => {
    if (score >= 8) return 'text-green-600';
    if (score >= 6) return 'text-blue-600';
    if (score >= 4) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Engagement rate color
  const getEngagementColor = rate => {
    if (rate >= 10) return 'text-green-600';
    if (rate >= 5) return 'text-blue-600';
    if (rate >= 2) return 'text-yellow-600';
    return 'text-red-600';
  };

  // Metric item component
  const MetricItem = ({
    icon: Icon,
    label,
    value,
    color = 'text-gray-600',
    description = null,
  }) => (
    <div className="flex items-center justify-between py-2">
      <div className="flex items-center">
        <Icon className="mr-2 size-5 text-gray-400" />
        <span className="text-sm text-gray-600">{label}</span>
      </div>
      <div className="text-right">
        <div className={`text-sm font-semibold ${color}`}>{value}</div>
        {description && <div className="text-xs text-gray-500">{description}</div>}
      </div>
    </div>
  );

  return (
    <div className="space-y-4">
      {/* Header with trending badge */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">Production Metrics</h3>
        {getTrendingBadge(trendingCategory)}
      </div>

      {/* Performance Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {/* Performance Score */}
        <div className="rounded-lg bg-gray-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ChartBarIcon className="mr-2 size-6 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Performance</span>
            </div>
            <div className={`text-2xl font-bold ${getPerformanceScoreColor(performanceScore)}`}>
              {performanceScore.toFixed(1)}
            </div>
          </div>
          <div className="mt-2">
            <div className="h-2 rounded-full bg-gray-200">
              <div
                className={`h-2 rounded-full ${
                  performanceScore >= 8
                    ? 'bg-green-500'
                    : performanceScore >= 6
                      ? 'bg-blue-500'
                      : performanceScore >= 4
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, (performanceScore / 10) * 100)}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Engagement Rate */}
        <div className="rounded-lg bg-gray-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <UserGroupIcon className="mr-2 size-6 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Engagement</span>
            </div>
            <div className={`text-2xl font-bold ${getEngagementColor(engagementRate)}`}>
              {engagementRate.toFixed(1)}%
            </div>
          </div>
          <div className="mt-2">
            <div className="h-2 rounded-full bg-gray-200">
              <div
                className={`h-2 rounded-full ${
                  engagementRate >= 10
                    ? 'bg-green-500'
                    : engagementRate >= 5
                      ? 'bg-blue-500'
                      : engagementRate >= 2
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                }`}
                style={{ width: `${Math.min(100, engagementRate * 10)}%` }}
              ></div>
            </div>
          </div>
        </div>

        {/* Trending Score */}
        <div className="rounded-lg bg-gray-50 p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <ArrowTrendingUpIcon className="mr-2 size-6 text-gray-400" />
              <span className="text-sm font-medium text-gray-700">Trending</span>
            </div>
            <div className="text-2xl font-bold text-purple-600">
              {(metrics.trending_score || 0).toFixed(1)}
            </div>
          </div>
          <div className="mt-2 text-xs text-gray-500">
            {metrics.trending_score > 5 ? 'Đang hot' : 'Bình thường'}
          </div>
        </div>
      </div>

      {/* Detailed Metrics */}
      <div className="rounded-lg border border-gray-200 bg-white p-4">
        <h4 className="text-md mb-3 font-medium text-gray-900">Chi tiết metrics</h4>

        <div className="space-y-1">
          <MetricItem
            icon={EyeIcon}
            label="Lượt xem trang chủ"
            value={homepageViews.toLocaleString()}
            description={homepageViews > 1000 ? 'Cao' : homepageViews > 100 ? 'Trung bình' : 'Thấp'}
          />

          <MetricItem
            icon={MagnifyingGlassIcon}
            label="Lượt xem chi tiết"
            value={detailViews.toLocaleString()}
            description={`${((detailViews / (homepageViews || 1)) * 100).toFixed(1)}% từ homepage`}
          />

          {trailerPlays > 0 && (
            <MetricItem
              icon={PlayIcon}
              label="Lượt xem trailer"
              value={trailerPlays.toLocaleString()}
              description={`${trailerCompletionRate.toFixed(1)}% hoàn thành`}
            />
          )}

          <MetricItem
            icon={UserGroupIcon}
            label="Click-through rate"
            value={`${clickThroughRate.toFixed(2)}%`}
            color={
              clickThroughRate > 5
                ? 'text-green-600'
                : clickThroughRate > 2
                  ? 'text-blue-600'
                  : 'text-gray-600'
            }
          />

          {metrics.last_featured_date && (
            <MetricItem
              icon={StarIcon}
              label="Featured lần cuối"
              value={new Date(metrics.last_featured_date).toLocaleDateString('vi-VN')}
              description={`${metrics.total_featured_days || 0} ngày tổng`}
            />
          )}
        </div>
      </div>

      {/* Quality & Admin Status */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div className="rounded-lg border border-blue-200 bg-blue-50 p-4">
          <h4 className="mb-2 text-sm font-medium text-blue-900">Chất lượng content</h4>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-blue-700">Completeness:</span>
              <span className="font-medium text-blue-900">
                {parseFloat(quality.content_completeness || 0).toFixed(1)}%
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-blue-700">Quality Score:</span>
              <span className="font-medium text-blue-900">
                {quality.quality_score
                  ? `${parseFloat(quality.quality_score).toFixed(1)}/10`
                  : 'N/A'}
              </span>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <h4 className="mb-2 text-sm font-medium text-green-900">Admin Status</h4>
          <div className="space-y-1">
            <div className="flex justify-between text-sm">
              <span className="text-green-700">Featured:</span>
              <span className="font-medium text-green-900">
                {adminControl.admin_featured ? 'Có' : 'Không'}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-green-700">Priority:</span>
              <span className="font-medium text-green-900">
                {adminControl.admin_priority || 0}/10
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ProductionMetricsCard;
