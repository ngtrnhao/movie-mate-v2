import { useState, useEffect, useCallback } from 'react';
import { moderateReview, getUnifiedModerationQueue } from '../../../api/movieService';
import moderationCacheService from '../../../services/moderationCacheService';

const QueueList = ({
  selectedItems,
  onSelectItem,
  onSelectAll,
  onClearSelection,
  isAdmin,
  // Add props for external data
  items: externalItems = [],
  totalPages: externalTotalPages = 1,
  stats: externalStats = {},
  disableInternalFetch = false,
  onDataFetch = null,
}) => {
  // Local state for search, filter, sort
  const [items, setItems] = useState(externalItems);
  const [filteredItems, setFilteredItems] = useState(externalItems);
  const [searchTerm, setSearchTerm] = useState('');
  const [filters, setFilters] = useState({
    type: 'all',
    priority: 'all',
    status: 'all',
  });
  const [sortBy, setSortBy] = useState('createdAt');
  const [sortOrder, setSortOrder] = useState('desc');
  const [loading, setLoading] = useState(!disableInternalFetch);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(externalTotalPages);
  const [stats, setStats] = useState(externalStats);
  const [lastFetchTime, setLastFetchTime] = useState(0);

  // Update items when external data changes
  useEffect(() => {
    if (externalItems && disableInternalFetch) {
      setItems(externalItems);
      setTotalPages(externalTotalPages);
      setStats(externalStats);
      setLoading(false);
      // Filter/sort on new data
      setSearchTerm('');
      setFilters({ type: 'all', priority: 'all', status: 'all' });
      setSortBy('createdAt');
      setSortOrder('desc');
    }
  }, [externalItems, externalTotalPages, externalStats, disableInternalFetch]);

  // Filter, search, and sort items
  useEffect(() => {
    let result = [...items];
    // Filter
    if (filters.type !== 'all') {
      result = result.filter(item => item.type === filters.type);
    }
    if (filters.priority !== 'all') {
      result = result.filter(item => item.priority === filters.priority);
    }
    if (filters.status !== 'all') {
      result = result.filter(item => item.status === filters.status);
    }
    // Search
    if (searchTerm) {
      result = result.filter(
        item =>
          (item.title || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
          (item.description || '').toLowerCase().includes(searchTerm.toLowerCase())
      );
    }
    // Sort
    result.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];
      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });
    setFilteredItems(result);
  }, [items, filters, searchTerm, sortBy, sortOrder]);

  // Fetch moderation data from API with caching (only if not disabled)
  const fetchModerationData = useCallback(async () => {
    if (disableInternalFetch) {
      console.log('🚫 QueueList internal fetch disabled - using external data');
      return;
    }

    // Skip if data is fresh (less than 30 seconds old)
    const now = Date.now();
    if (now - lastFetchTime < 30000 && items.length > 0) {
      console.log('🚫 Skipping API call for Queue - data is fresh');
      return;
    }

    try {
      setLoading(true);
      console.log('🔄 Fetching unified moderation queue for QueueList...');

      const data = await getUnifiedModerationQueue(currentPage, 100);

      setItems(data.tasks || []);
      setTotalPages(data.total_pages || 1);
      setStats(data.stats?.priority_stats || {});
      setLastFetchTime(now);

      // Notify parent component about data fetch
      if (onDataFetch) {
        onDataFetch({
          items: data.tasks || [],
          totalPages: data.total_pages || 1,
          stats: data.stats?.priority_stats || {},
          timestamp: now,
        });
      }

      console.log('✅ Queue data loaded:', {
        totalItems: data.tasks?.length || 0,
        totalPages: data.total_pages || 1,
        fromCache: false,
      });
    } catch (error) {
      console.error('Error fetching moderation data:', error);
    } finally {
      setLoading(false);
    }
  }, [currentPage, lastFetchTime, items.length, onDataFetch, disableInternalFetch]);

  // Only fetch if internal fetch is not disabled
  useEffect(() => {
    if (!disableInternalFetch) {
      fetchModerationData();
    } else {
      console.log('✅ QueueList using external data - no internal fetch needed');
      setLoading(false);
    }
  }, [fetchModerationData, disableInternalFetch]);

  const getTypeColor = type => {
    switch (type) {
      case 'review':
        return 'bg-purple-100 text-purple-700';
      case 'comment':
        return 'bg-amber-100 text-amber-700';
      case 'rating':
        return 'bg-pink-100 text-pink-700';
      case 'report':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700';
      case 'low':
        return 'bg-green-100 text-green-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusColor = status => {
    switch (status) {
      case 'backlog':
        return 'bg-yellow-100 text-yellow-700';
      case 'in_progress':
        return 'bg-blue-100 text-blue-700';
      case 'review':
        return 'bg-purple-100 text-purple-700';
      case 'completed':
        return 'bg-green-100 text-green-700';
      case 'pending':
        return 'bg-yellow-100 text-yellow-700';
      case 'approved':
        return 'bg-green-100 text-green-700';
      case 'rejected':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleModerate = async (taskId, action) => {
    try {
      // Extract review ID from task ID
      const reviewId = taskId.split('_')[1];
      const reason = action === 'approve' ? 'Approved by moderator' : 'Rejected due to violations';
      await moderateReview(reviewId, action, reason);

      // Invalidate cache and refresh queue
      moderationCacheService.invalidateCache('unified_moderation_queue');
      fetchModerationData(); // Re-fetch to update stats and items
    } catch (error) {
      console.error('Error moderating review:', error);
    }
  };

  const formatDate = dateString => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const getModerationReasons = task => {
    const reasons = [];

    if (task.moderation_reasons) {
      task.moderation_reasons.forEach(reason => {
        switch (reason) {
          case 'user_reported':
            reasons.push({ text: 'Báo cáo từ người dùng', color: 'bg-red-100 text-red-700' });
            break;
          case 'marked_spoiler':
            reasons.push({ text: 'Đánh dấu spoiler', color: 'bg-purple-100 text-purple-700' });
            break;
          case 'auto_detected_spoiler':
            reasons.push({
              text: 'Tự động phát hiện spoiler',
              color: 'bg-orange-100 text-orange-700',
            });
            break;
          case 'potential_spoiler':
            reasons.push({ text: 'Có thể chứa spoiler', color: 'bg-yellow-100 text-yellow-700' });
            break;
        }
      });
    }

    if (task.report_count > 0) {
      reasons.push({
        text: `${task.report_count} báo cáo`,
        color: 'bg-red-100 text-red-700',
      });
    }

    return reasons;
  };

  const handleFilterChange = (filterType, value) => {
    setFilters(prev => ({
      ...prev,
      [filterType]: value,
    }));
  };

  const handleSort = field => {
    if (sortBy === field) {
      setSortOrder(prev => (prev === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const isAllSelected =
    filteredItems.length > 0 && filteredItems.every(item => selectedItems.includes(item.id));

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="size-12 animate-spin rounded-full border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-lg border-l-4 border-red-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="mr-3 size-6 text-red-600">🚨</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên cao</p>
              <p className="text-2xl font-bold text-gray-900">{stats.high || 0}</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border-l-4 border-yellow-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="mr-3 size-6 text-yellow-600">⚠️</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên trung bình</p>
              <p className="text-2xl font-bold text-gray-900">{stats.medium || 0}</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border-l-4 border-green-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="mr-3 size-6 text-green-600">✅</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên thấp</p>
              <p className="text-2xl font-bold text-gray-900">{stats.low || 0}</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border-l-4 border-blue-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <div className="mr-3 size-6 text-blue-600">📊</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng cộng</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg bg-white p-4 shadow">
        <div className="grid grid-cols-12 gap-4">
          {/* Search */}
          <div className="col-span-6">
            <label className="mb-2 block text-sm font-medium text-gray-700">Tìm kiếm</label>
            <input
              type="text"
              placeholder="Tìm kiếm theo tiêu đề, nội dung, tác giả..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full rounded border-gray-300 text-gray-900 focus:ring-indigo-500"
            />
          </div>

          {/* Type Filter */}
          <div className="col-span-2">
            <label className="mb-2 block text-sm font-medium text-gray-700">Loại</label>
            <select
              value={filters.type}
              onChange={e => handleFilterChange('type', e.target.value)}
              className="w-full rounded border-gray-300 text-gray-900 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="reported">Báo cáo</option>
              <option value="spoiler">Spoiler</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="col-span-2">
            <label className="mb-2 block text-sm font-medium text-gray-700">Ưu tiên</label>
            <select
              value={filters.priority}
              onChange={e => handleFilterChange('priority', e.target.value)}
              className="w-full rounded border-gray-300 text-gray-900 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="high">Cao</option>
              <option value="medium">Trung bình</option>
              <option value="low">Thấp</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="col-span-2">
            <label className="mb-2 block text-sm font-medium text-gray-700">Trạng thái</label>
            <select
              value={filters.status}
              onChange={e => handleFilterChange('status', e.target.value)}
              className="w-full rounded border-gray-300 text-gray-900 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="pending">Chờ duyệt</option>
              <option value="resolved">Đã xử lý</option>
            </select>
          </div>
        </div>
      </div>

      {/* Items List */}
      <div className="overflow-hidden rounded-lg bg-white shadow">
        {/* Table Header */}
        <div className="border-b bg-gray-50 px-6 py-3">
          <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-700">
            <div className="col-span-1">
              <input
                type="checkbox"
                checked={selectedItems.length === filteredItems.length && filteredItems.length > 0}
                onChange={() =>
                  selectedItems.length === filteredItems.length
                    ? onClearSelection()
                    : onSelectAll(filteredItems.map(item => item.id))
                }
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
            </div>
            <div className="col-span-1">Loại</div>
            <div className="col-span-3">Review</div>
            <div className="col-span-2">Tác giả</div>
            <div className="col-span-1">Ưu tiên</div>
            <div className="col-span-1">Trạng thái</div>
            <div
              className="col-span-2 cursor-pointer hover:text-indigo-600"
              onClick={() => handleSort('createdAt')}
            >
              Tạo lúc {sortBy === 'createdAt' && (sortOrder === 'asc' ? '↑' : '↓')}
            </div>
            <div className="col-span-1">Hành động</div>
          </div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-gray-200">
          {loading ? (
            <div className="py-12 text-center">
              <div className="mx-auto size-12 animate-spin rounded-full border-b-2 border-blue-500"></div>
              <p className="mt-4 text-gray-600">Đang tải...</p>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="py-12 text-center">
              <div className="mb-4 text-6xl text-gray-400">📝</div>
              <h3 className="mb-2 text-lg font-medium text-gray-900">Không có items nào</h3>
              <p className="text-gray-600">Thử thay đổi bộ lọc hoặc tìm kiếm khác</p>
            </div>
          ) : (
            filteredItems.map((item, index) => (
              <div
                key={`${item.id}_${item.created_at}_${index}`}
                className={`px-6 py-4 transition-colors hover:bg-gray-50 ${
                  selectedItems.includes(item.id) ? 'bg-indigo-50' : ''
                }`}
              >
                <div className="grid grid-cols-12 items-center gap-4">
                  {/* Checkbox */}
                  <div className="col-span-1">
                    <input
                      type="checkbox"
                      checked={selectedItems.includes(item.id)}
                      onChange={() => onSelectItem(item.id)}
                      className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
                    />
                  </div>

                  {/* Type */}
                  <div className="col-span-1">
                    <div className="flex flex-col items-center">
                      <span className="mb-1 text-2xl">
                        {item.type === 'report' || item.type === 'both'
                          ? '🚨'
                          : item.type === 'spoiler'
                            ? '⚠️'
                            : '📝'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {item.type === 'report'
                          ? 'Báo cáo'
                          : item.type === 'spoiler'
                            ? 'Spoiler'
                            : item.type === 'both'
                              ? 'Cả hai'
                              : 'Review'}
                      </span>
                    </div>
                  </div>

                  {/* Title and Content */}
                  <div className="col-span-3">
                    <div className="mb-1 font-medium text-gray-900">
                      {item.title || 'Không có tiêu đề'}
                    </div>
                    <div className="line-clamp-2 text-sm text-gray-600">
                      {item.content?.substring(0, 100)}...
                    </div>
                    {/* Moderation reasons */}
                    <div className="mt-2 flex flex-wrap gap-1">
                      {getModerationReasons(item).map((reason, reasonIndex) => (
                        <span
                          key={`${item.id}_reason_${reasonIndex}_${reason.text}`}
                          className={`rounded-full px-2 py-1 text-xs ${reason.color}`}
                        >
                          {reason.text}
                        </span>
                      ))}
                    </div>
                  </div>

                  {/* Author */}
                  <div className="col-span-2">
                    <div className="flex items-center">
                      <span className="text-sm font-medium text-gray-900">
                        {item.user || 'Unknown'}
                      </span>
                    </div>
                  </div>

                  {/* Priority */}
                  <div className="col-span-1">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${getPriorityColor(
                        item.priority || 'low'
                      )}`}
                    >
                      {item.priority === 'high'
                        ? 'Cao'
                        : item.priority === 'medium'
                          ? 'TB'
                          : 'Thấp'}
                    </span>
                  </div>

                  {/* Status */}
                  <div className="col-span-1">
                    <span
                      className={`rounded-full px-2 py-1 text-xs font-medium ${getStatusColor(
                        item.status || 'backlog'
                      )}`}
                    >
                      {item.status === 'backlog'
                        ? 'Chờ'
                        : item.status === 'in_progress'
                          ? 'Đang xử lý'
                          : item.status === 'review'
                            ? 'Xem xét'
                            : item.status === 'completed'
                              ? 'Hoàn thành'
                              : 'Chờ'}
                    </span>
                  </div>

                  {/* Created Date */}
                  <div className="col-span-2">
                    <div className="text-sm text-gray-600">{formatDate(item.created_at)}</div>
                  </div>

                  {/* Actions */}
                  <div className="col-span-1">
                    <div className="flex space-x-1">
                      <button
                        className="p-1 text-green-600 hover:text-green-800"
                        title="Duyệt"
                        onClick={() => handleModerate(item.id, 'approve')}
                      >
                        ✅
                      </button>
                      <button
                        className="p-1 text-red-600 hover:text-red-800"
                        title="Từ chối"
                        onClick={() => handleModerate(item.id, 'reject')}
                      >
                        ❌
                      </button>
                      <button
                        className="p-1 text-blue-600 hover:text-blue-800"
                        title="Xem chi tiết"
                        onClick={() => {
                          if (item.review_data?.movie?.id) {
                            window.open(`/movies/${item.review_data.movie.id}`, '_blank');
                          }
                        }}
                      >
                        👁️
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="flex items-center justify-between border-t bg-white px-6 py-4">
            <div className="text-sm text-gray-700">
              Trang {currentPage} của {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Trước
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              >
                Sau
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueueList;
