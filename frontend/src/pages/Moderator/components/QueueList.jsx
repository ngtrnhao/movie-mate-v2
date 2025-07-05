import React, { useState, useEffect } from 'react';
import { getModerationQueue, moderateReview } from '../../../api/movieService';

const QueueList = ({
  selectedItems,
  onSelectItem,
  onSelectAll,
  onClearSelection,
  isAdmin,
  filterType = 'all',
}) => {
  const [items, setItems] = useState([]);
  const [filteredItems, setFilteredItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    type: 'all',
    priority: 'all',
    status: 'all',
  });
  const [sortBy, setSortBy] = useState('createdAt');
  const [sortOrder, setSortOrder] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState({
    high: 0,
    medium: 0,
    low: 0,
    total: 0,
  });

  // Fetch moderation queue from API
  const fetchModerationQueue = async () => {
    try {
      setLoading(true);
      const apiFilters = {};

      if (filters.priority !== 'all') {
        apiFilters.priority = filters.priority;
      }
      if (filters.status !== 'all') {
        apiFilters.status = filters.status;
      }

      const data = await getModerationQueue(currentPage, 20, apiFilters);
      setItems(data.data || []);
      setTotalPages(data.total_pages || 1);
      setStats(data.priority_stats || {});
    } catch (error) {
      console.error('Error fetching moderation queue:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchModerationQueue();
  }, [currentPage, filters.priority, filters.status]);

  // Filter and sort items
  useEffect(() => {
    let filtered = [...items];

    // Lọc theo loại
    if (filters.type === 'reported') {
      filtered = filtered.filter(item => item.moderation_analysis?.report_count > 0);
    } else if (filters.type === 'spoiler') {
      filtered = filtered.filter(
        item =>
          item.is_spoiler ||
          item.moderation_analysis?.moderation_reasons?.includes('auto_detected_spoiler') ||
          item.moderation_analysis?.moderation_reasons?.includes('marked_spoiler')
      );
    }

    // Lọc theo ưu tiên
    if (filters.priority !== 'all') {
      filtered = filtered.filter(
        item => (item.moderation_analysis?.priority_level || 'low') === filters.priority
      );
    }

    // Lọc theo trạng thái
    if (filters.status !== 'all') {
      if (filters.status === 'pending') {
        filtered = filtered.filter(item => item.is_approved === null);
      } else if (filters.status === 'resolved') {
        filtered = filtered.filter(item => item.is_approved !== null);
      }
    }

    // Apply search
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      filtered = filtered.filter(
        item =>
          item.title?.toLowerCase().includes(searchLower) ||
          item.content?.toLowerCase().includes(searchLower) ||
          item.user?.username?.toLowerCase().includes(searchLower)
      );
    }

    // Apply sorting (ưu tiên report, priority, thời gian)
    filtered.sort((a, b) => {
      if (
        (a.moderation_analysis?.report_count || 0) !== (b.moderation_analysis?.report_count || 0)
      ) {
        return (
          (b.moderation_analysis?.report_count || 0) - (a.moderation_analysis?.report_count || 0)
        );
      }
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      const aPriority = priorityOrder[a.moderation_analysis?.priority_level] ?? 3;
      const bPriority = priorityOrder[b.moderation_analysis?.priority_level] ?? 3;
      if (aPriority !== bPriority) {
        return aPriority - bPriority;
      }
      const aDate = new Date(a.created_at);
      const bDate = new Date(b.created_at);
      return bDate - aDate;
    });

    setFilteredItems(filtered);
  }, [items, filters, searchTerm]);

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
      case 'pending':
        return 'bg-yellow-100 text-yellow-700';
      case 'reviewing':
        return 'bg-blue-100 text-blue-700';
      case 'approved':
        return 'bg-green-100 text-green-700';
      case 'rejected':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const handleModerate = async (reviewId, action) => {
    try {
      const reason = action === 'approve' ? 'Approved by moderator' : 'Rejected due to violations';
      await moderateReview(reviewId, action, reason);

      // Refresh queue
      fetchModerationQueue();
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

  const getModerationReasons = review => {
    const reasons = [];

    if (review.moderation_analysis?.moderation_reasons) {
      review.moderation_analysis.moderation_reasons.forEach(reason => {
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

    if (review.moderation_analysis?.report_count > 0) {
      reasons.push({
        text: `${review.moderation_analysis.report_count} báo cáo`,
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
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-red-500">
          <div className="flex items-center">
            <div className="w-6 h-6 text-red-600 mr-3">🚨</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên cao</p>
              <p className="text-2xl font-bold text-gray-900">{stats.high || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-yellow-500">
          <div className="flex items-center">
            <div className="w-6 h-6 text-yellow-600 mr-3">⚠️</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên trung bình</p>
              <p className="text-2xl font-bold text-gray-900">{stats.medium || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-green-500">
          <div className="flex items-center">
            <div className="w-6 h-6 text-green-600 mr-3">✅</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên thấp</p>
              <p className="text-2xl font-bold text-gray-900">{stats.low || 0}</p>
            </div>
          </div>
        </div>
        <div className="bg-white rounded-lg shadow p-4 border-l-4 border-blue-500">
          <div className="flex items-center">
            <div className="w-6 h-6 text-blue-600 mr-3">📊</div>
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng cộng</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total || 0}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-12 gap-4">
          {/* Search */}
          <div className="col-span-6">
            <label className="block text-sm font-medium text-gray-700 mb-2">Tìm kiếm</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Loại</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Ưu tiên</label>
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Trạng thái</label>
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
      <div className="bg-white rounded-lg shadow overflow-hidden">
        {/* Table Header */}
        <div className="bg-gray-50 px-6 py-3 border-b">
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
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
              <p className="mt-4 text-gray-600">Đang tải...</p>
            </div>
          ) : filteredItems.length === 0 ? (
            <div className="text-center py-12">
              <div className="text-gray-400 text-6xl mb-4">📝</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">Không có items nào</h3>
              <p className="text-gray-600">Thử thay đổi bộ lọc hoặc tìm kiếm khác</p>
            </div>
          ) : (
            filteredItems.map(item => (
              <div
                key={item.id}
                className={`px-6 py-4 hover:bg-gray-50 transition-colors ${
                  selectedItems.includes(item.id) ? 'bg-indigo-50' : ''
                }`}
              >
                <div className="grid grid-cols-12 gap-4 items-center">
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
                      <span className="text-2xl mb-1">
                        {item.moderation_analysis?.report_count > 0
                          ? '🚨'
                          : item.is_spoiler
                            ? '⚠️'
                            : '📝'}
                      </span>
                      <span className="text-xs text-gray-500">
                        {item.moderation_analysis?.report_count > 0
                          ? 'Báo cáo'
                          : item.is_spoiler
                            ? 'Spoiler'
                            : 'Review'}
                      </span>
                    </div>
                  </div>

                  {/* Title and Content */}
                  <div className="col-span-3">
                    <div className="font-medium text-gray-900 mb-1">
                      {item.title || 'Không có tiêu đề'}
                    </div>
                    <div className="text-sm text-gray-600 line-clamp-2">
                      {item.content?.substring(0, 100)}...
                    </div>
                    {/* Moderation reasons */}
                    <div className="flex flex-wrap gap-1 mt-2">
                      {getModerationReasons(item).map((reason, index) => (
                        <span
                          key={index}
                          className={`px-2 py-1 text-xs rounded-full ${reason.color}`}
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
                        {item.user?.username || 'Unknown'}
                      </span>
                    </div>
                  </div>

                  {/* Priority */}
                  <div className="col-span-1">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(
                        item.moderation_analysis?.priority_level || 'low'
                      )}`}
                    >
                      {item.moderation_analysis?.priority_level === 'high'
                        ? 'Cao'
                        : item.moderation_analysis?.priority_level === 'medium'
                          ? 'TB'
                          : 'Thấp'}
                    </span>
                  </div>

                  {/* Status */}
                  <div className="col-span-1">
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(
                        item.is_approved === null
                          ? 'pending'
                          : item.is_approved
                            ? 'approved'
                            : 'rejected'
                      )}`}
                    >
                      {item.is_approved === null ? 'Chờ' : item.is_approved ? 'Duyệt' : 'Từ chối'}
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
                        onClick={() => window.open(`/movies/${item.movie?.id}`, '_blank')}
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
          <div className="flex items-center justify-between bg-white px-6 py-4 border-t">
            <div className="text-sm text-gray-700">
              Trang {currentPage} của {totalPages}
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                disabled={currentPage === 1}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Trước
              </button>
              <button
                onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                disabled={currentPage === totalPages}
                className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
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
