import { useState } from 'react';
import {
  ChartBarIcon,
  CalendarDaysIcon,
  ClockIcon,
  SparklesIcon,
  AdjustmentsHorizontalIcon,
  ArrowTrendingUpIcon,
  BoltIcon,
  EyeIcon,
  HeartIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';

const AdvancedAdminFilters = ({
  filters,
  onFilterChange,
  onResetFilters,
  showAdvanced,
  onToggleAdvanced,
}) => {
  const [activeTab, setActiveTab] = useState('quality');

  const qualityRatingOptions = [
    { value: 'Excellent', label: 'Excellent (8-10)', color: 'bg-green-100 text-green-800' },
    { value: 'Good', label: 'Good (6-8)', color: 'bg-blue-100 text-blue-800' },
    { value: 'Fair', label: 'Fair (4-6)', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'Poor', label: 'Poor (0-4)', color: 'bg-red-100 text-red-800' },
    { value: 'Not Assessed', label: 'Not Assessed', color: 'bg-gray-100 text-gray-800' },
  ];

  const completionStatusOptions = [
    { value: 'Complete', label: 'Complete (90-100%)', color: 'bg-green-100 text-green-800' },
    {
      value: 'Nearly Complete',
      label: 'Nearly Complete (70-90%)',
      color: 'bg-blue-100 text-blue-800',
    },
    { value: 'Partial', label: 'Partial (50-70%)', color: 'bg-yellow-100 text-yellow-800' },
    { value: 'Incomplete', label: 'Incomplete (<50%)', color: 'bg-red-100 text-red-800' },
  ];

  const campaignTypeOptions = [
    { value: 'marketing', label: 'Marketing Campaign' },
    { value: 'seasonal', label: 'Seasonal Campaign' },
    { value: 'special', label: 'Special Event' },
    { value: 'promotion', label: 'Promotion' },
    { value: 'launch', label: 'Movie Launch' },
  ];

  const trendingCategories = [
    { value: 'trending', label: 'Trending', color: 'bg-red-100 text-red-800' },
    { value: 'hot', label: 'Hot', color: 'bg-orange-100 text-orange-800' },
    { value: 'rising', label: 'Rising', color: 'bg-green-100 text-green-800' },
    { value: 'stable', label: 'Stable', color: 'bg-blue-100 text-blue-800' },
    { value: 'declining', label: 'Declining', color: 'bg-yellow-100 text-yellow-800' },
  ];

  const adminPriorityOptions = [
    { value: '0', label: 'No Priority (0)' },
    { value: '1', label: 'Low Priority (1-3)', range: [1, 3] },
    { value: '4', label: 'Medium Priority (4-6)', range: [4, 6] },
    { value: '7', label: 'High Priority (7-8)', range: [7, 8] },
    { value: '9', label: 'Critical Priority (9-10)', range: [9, 10] },
  ];

  const tabs = [
    { id: 'quality', label: 'Quality Control', icon: ChartBarIcon, color: 'text-blue-600' },
    { id: 'scheduling', label: 'Scheduling', icon: CalendarDaysIcon, color: 'text-green-600' },
    {
      id: 'performance',
      label: 'Performance',
      icon: ArrowTrendingUpIcon,
      color: 'text-purple-600',
    },
    {
      id: 'admin',
      label: 'Admin Controls',
      icon: AdjustmentsHorizontalIcon,
      color: 'text-orange-600',
    },
  ];

  const handleFilterChange = (key, value) => {
    onFilterChange(key, value === '' ? null : value);
  };

  const handleToggleFilter = key => {
    const currentValue = filters[key];
    onFilterChange(key, currentValue ? false : true);
  };

  const hasActiveFilters = () => {
    const advancedFilterKeys = [
      'quality_score_min',
      'quality_score_max',
      'content_completeness_min',
      'overall_quality_rating',
      'completion_status',
      'minimum_quality_met',
      'campaign_type',
      'campaign_priority_min',
      'admin_priority_min',
      'is_published_now',
      'is_featured_now',
      'has_quality_issues',
      'performance_score_min',
      'trending_score_min',
      'trending_category',
      'engagement_rate_min',
      'homepage_views_min',
      'detail_page_views_min',
      'trailer_plays_min',
      'click_through_rate_min',
      'user_favorites_min',
    ];
    return advancedFilterKeys.some(
      key => filters[key] !== null && filters[key] !== undefined && filters[key] !== ''
    );
  };

  if (!showAdvanced) {
    return (
      <div className="border-t border-gray-200 bg-gray-50 px-6 py-4">
        <button
          onClick={onToggleAdvanced}
          className="flex items-center space-x-2 text-sm text-gray-600 hover:text-gray-900"
        >
          <AdjustmentsHorizontalIcon className="h-4 w-4" />
          <span>Show Advanced Filters</span>
          {hasActiveFilters() && (
            <span className="ml-2 inline-flex h-2 w-2 rounded-full bg-blue-500"></span>
          )}
        </button>
      </div>
    );
  }

  const renderQualityFilters = () => (
    <div className="space-y-6">
      {/* Quality Score Range */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Quality Score
          </label>
          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            value={filters.quality_score_min || ''}
            onChange={e => handleFilterChange('quality_score_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="0.0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Quality Score
          </label>
          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            value={filters.quality_score_max || ''}
            onChange={e => handleFilterChange('quality_score_max', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="10.0"
          />
        </div>
      </div>

      {/* Content Completeness */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Content Completeness (%)
        </label>
        <input
          type="number"
          min="0"
          max="100"
          value={filters.content_completeness_min || ''}
          onChange={e => handleFilterChange('content_completeness_min', e.target.value)}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          placeholder="0"
        />
      </div>

      {/* Quality Rating */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Overall Quality Rating
        </label>
        <select
          value={filters.overall_quality_rating || ''}
          onChange={e => handleFilterChange('overall_quality_rating', e.target.value)}
          className="block w-full rounded-md text-gray-700 border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option value="">All Ratings</option>
          {qualityRatingOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Completion Status */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Completion Status</label>
        <select
          value={filters.completion_status || ''}
          onChange={e => handleFilterChange('completion_status', e.target.value)}
          className="block w-full rounded-md text-gray-700 border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option value="">All Status</option>
          {completionStatusOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Quality Flags */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Quality Requirements</label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.minimum_quality_met === true}
              onChange={() => handleToggleFilter('minimum_quality_met')}
              className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
            />
            <span className="ml-2 text-sm text-gray-700">Meets minimum quality standards</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.has_quality_issues === true}
              onChange={() => handleToggleFilter('has_quality_issues')}
              className="rounded  border-gray-300 text-red-600 focus:ring-red-500"
            />
            <span className="ml-2 text-sm text-gray-700">
              Has quality issues requiring attention
            </span>
          </label>
        </div>
      </div>

      {/* Admin Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Admin Priority
        </label>
        <select
          value={filters.admin_priority_min || ''}
          onChange={e => handleFilterChange('admin_priority_min', e.target.value)}
          className="block w-full rounded-md text-gray-700 border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option value="">All Priorities</option>
          {adminPriorityOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  );

  const renderSchedulingFilters = () => (
    <div className="space-y-6">
      {/* Campaign Type */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Campaign Type</label>
        <select
          value={filters.campaign_type || ''}
          onChange={e => handleFilterChange('campaign_type', e.target.value)}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
        >
          <option value="">All Campaigns</option>
          {campaignTypeOptions.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Campaign Priority */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum Campaign Priority
        </label>
        <input
          type="number"
          min="0"
          max="10"
          value={filters.campaign_priority_min || ''}
          onChange={e => handleFilterChange('campaign_priority_min', e.target.value)}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-green-500 focus:ring-green-500"
          placeholder="0"
        />
      </div>

      {/* Publishing Status */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Current Status</label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.is_published_now === true}
              onChange={() => handleToggleFilter('is_published_now')}
              className="rounded border-gray-300 text-green-600 focus:ring-green-500"
            />
            <span className="ml-2 text-sm text-gray-700">Currently Published</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.is_featured_now === true}
              onChange={() => handleToggleFilter('is_featured_now')}
              className="rounded border-gray-300 text-green-600 focus:ring-green-500"
            />
            <span className="ml-2 text-sm text-gray-700">Currently Featured</span>
          </label>
        </div>
      </div>
    </div>
  );

  const renderPerformanceFilters = () => (
    <div className="space-y-6">
      {/* Performance Scores */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Performance Score
          </label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.1"
            value={filters.performance_score_min || ''}
            onChange={e => handleFilterChange('performance_score_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0.0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Trending Score
          </label>
          <input
            type="number"
            min="0"
            max="10"
            step="0.1"
            value={filters.trending_score_min || ''}
            onChange={e => handleFilterChange('trending_score_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0.0"
          />
        </div>
      </div>

      {/* Trending Category */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Trending Category</label>
        <select
          value={filters.trending_category || ''}
          onChange={e => handleFilterChange('trending_category', e.target.value)}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
        >
          <option value="">All Categories</option>
          {trendingCategories.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      </div>

      {/* Engagement Metrics */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Engagement Rate (%)
          </label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={filters.engagement_rate_min || ''}
            onChange={e => handleFilterChange('engagement_rate_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0.00"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Homepage Views
          </label>
          <input
            type="number"
            min="0"
            value={filters.homepage_views_min || ''}
            onChange={e => handleFilterChange('homepage_views_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Detail Views
          </label>
          <input
            type="number"
            min="0"
            value={filters.detail_page_views_min || ''}
            onChange={e => handleFilterChange('detail_page_views_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0"
          />
        </div>
      </div>

      {/* Trailer & Click Metrics */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Trailer Plays
          </label>
          <input
            type="number"
            min="0"
            value={filters.trailer_plays_min || ''}
            onChange={e => handleFilterChange('trailer_plays_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Click-Through Rate (%)
          </label>
          <input
            type="number"
            min="0"
            max="100"
            step="0.01"
            value={filters.click_through_rate_min || ''}
            onChange={e => handleFilterChange('click_through_rate_min', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
            placeholder="0.00"
          />
        </div>
      </div>

      {/* User Favorites */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          Minimum User Favorites
        </label>
        <input
          type="number"
          min="0"
          value={filters.user_favorites_min || ''}
          onChange={e => handleFilterChange('user_favorites_min', e.target.value)}
          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500"
          placeholder="0"
        />
      </div>
    </div>
  );

  const renderAdminFilters = () => (
    <div className="space-y-6">
      {/* Publication Status */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Publication Status</label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.is_published_now === true}
              onChange={() => handleToggleFilter('is_published_now')}
              className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
            />
            <span className="ml-2 text-sm text-gray-700">Currently published</span>
          </label>
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.is_featured_now === true}
              onChange={() => handleToggleFilter('is_featured_now')}
              className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
            />
            <span className="ml-2 text-sm text-gray-700">Currently featured</span>
          </label>
        </div>
      </div>

      {/* Approval Status Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Approval Status</label>
        <select
          value={filters.approval_status || ''}
          onChange={e => handleFilterChange('approval_status', e.target.value)}
          className="block w-full rounded-md text-gray-700 border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500"
        >
          <option value="">All Statuses</option>
          <option value="NEEDS_REVIEW">Needs Review</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
          <option value="PENDING">Pending</option>
        </select>
      </div>

      {/* Visibility Status Filter */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">Visibility Status</label>
        <select
          value={filters.visibility_status || ''}
          onChange={e => handleFilterChange('visibility_status', e.target.value)}
          className="block w-full rounded-md text-gray-700 border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500"
        >
          <option value="">All Visibility</option>
          <option value="PUBLISHED">Published</option>
          <option value="DRAFT">Draft</option>
          <option value="SCHEDULED">Scheduled</option>
          <option value="ARCHIVED">Archived</option>
          <option value="RESTRICTED">Restricted</option>
        </select>
      </div>

      {/* Admin Priority Range */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Minimum Admin Priority
          </label>
          <input
            type="number"
            min="0"
            max="10"
            value={filters.admin_priority_min || ''}
            onChange={e => handleFilterChange('admin_priority_min', e.target.value)}
            className="block w-full rounded-md text-gray-700 border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500"
            placeholder="0"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Maximum Admin Priority
          </label>
          <input
            type="number"
            min="0"
            max="10"
            value={filters.admin_priority_max || ''}
            onChange={e => handleFilterChange('admin_priority_max', e.target.value)}
            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-orange-500 focus:ring-orange-500"
            placeholder="10"
          />
        </div>
      </div>

      {/* Featured Status */}
      <div className="space-y-3">
        <label className="block text-sm font-medium text-gray-700">Featured Options</label>
        <div className="space-y-2">
          <label className="flex items-center">
            <input
              type="checkbox"
              checked={filters.admin_featured === true}
              onChange={() => handleToggleFilter('admin_featured')}
              className="rounded border-gray-300 text-orange-600 focus:ring-orange-500"
            />
            <span className="ml-2 text-sm text-gray-700">Admin featured movies only</span>
          </label>
        </div>
      </div>
    </div>
  );

  return (
    <div className="border-t border-gray-200 bg-white">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
        <div className="flex items-center space-x-2">
          <AdjustmentsHorizontalIcon className="h-5 w-5 text-gray-400" />
          <h3 className="text-lg font-medium text-gray-900">Advanced Filters</h3>
          {hasActiveFilters() && (
            <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
              Active
            </span>
          )}
        </div>
        <div className="flex items-center space-x-2">
          {hasActiveFilters() && (
            <button onClick={onResetFilters} className="text-sm text-gray-500 hover:text-gray-700">
              Reset Filters
            </button>
          )}
          <button
            onClick={onToggleAdvanced}
            className="rounded-md p-1 text-gray-400 hover:text-gray-500"
          >
            <XMarkIcon className="h-5 w-5" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 px-6" aria-label="Tabs">
          {tabs.map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center space-x-2 border-b-2 py-4 px-1 text-sm font-medium ${
                  activeTab === tab.id
                    ? `border-blue-500 ${tab.color}`
                    : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                }`}
              >
                <Icon className="h-4 w-4" />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>

      {/* Filter Content */}
      <div className="px-6 py-6">
        {activeTab === 'quality' && renderQualityFilters()}
        {activeTab === 'scheduling' && renderSchedulingFilters()}
        {activeTab === 'performance' && renderPerformanceFilters()}
        {activeTab === 'admin' && renderAdminFilters()}
      </div>
    </div>
  );
};

export default AdvancedAdminFilters;
