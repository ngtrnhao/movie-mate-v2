import React, { useState, useEffect } from 'react';

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
    assignee: 'all',
    status: 'all',
  });
  const [sortBy, setSortBy] = useState('createdAt');
  const [sortOrder, setSortOrder] = useState('desc');
  const [searchTerm, setSearchTerm] = useState('');

  // Mock data - replace with actual API calls
  useEffect(() => {
    const mockItems = [
      {
        id: 'queue-1',
        title: 'Review phim "The Matrix"',
        content: 'Đánh giá phim có nội dung không phù hợp, cần xem xét kỹ lưỡng',
        type: 'review',
        priority: 'high',
        status: 'pending',
        assignee: 'Unassigned',
        reporter: 'user123',
        createdAt: '2024-01-15T10:00:00Z',
        tags: ['inappropriate', 'violence'],
      },
      {
        id: 'queue-2',
        title: 'Báo cáo spam comment',
        content: 'Người dùng spam nhiều comment không liên quan đến phim',
        type: 'report',
        priority: 'medium',
        status: 'pending',
        assignee: 'Moderator A',
        reporter: 'user456',
        createdAt: '2024-01-15T09:30:00Z',
        tags: ['spam', 'comment'],
      },
      {
        id: 'queue-3',
        title: 'Poster phim không phù hợp',
        content: 'Poster phim có nội dung bạo lực, không phù hợp với độ tuổi',
        type: 'content',
        priority: 'low',
        status: 'in_progress',
        assignee: 'Moderator B',
        reporter: 'system',
        createdAt: '2024-01-15T08:45:00Z',
        tags: ['poster', 'violence'],
      },
      {
        id: 'queue-4',
        title: 'Xem xét tài khoản nghi vấn',
        content: 'Tài khoản có hành vi bất thường, nghi vấn bot hoặc fake',
        type: 'user',
        priority: 'high',
        status: 'pending',
        assignee: 'Unassigned',
        reporter: 'system',
        createdAt: '2024-01-15T07:20:00Z',
        tags: ['suspicious', 'bot'],
      },
      {
        id: 'queue-5',
        title: 'Review nội dung đánh giá',
        content: 'Đánh giá có từ ngữ không phù hợp, cần kiểm duyệt',
        type: 'review',
        priority: 'medium',
        status: 'in_progress',
        assignee: 'Moderator C',
        reporter: 'user789',
        createdAt: '2024-01-15T06:15:00Z',
        tags: ['inappropriate', 'language'],
      },
      {
        id: 'queue-6',
        title: 'Phê duyệt thay đổi thông tin phim',
        content: 'Yêu cầu cập nhật thông tin phim, cần xác minh tính chính xác',
        type: 'content',
        priority: 'low',
        status: 'pending',
        assignee: 'Admin',
        reporter: 'user321',
        createdAt: '2024-01-15T05:30:00Z',
        tags: ['update', 'movie-info'],
      },
    ];

    setTimeout(() => {
      setItems(mockItems);
      setFilteredItems(mockItems);
      setLoading(false);
    }, 1000);
  }, []);

  // Filter and sort items
  useEffect(() => {
    let filtered = [...items];

    // Apply filters
    if (filters.type !== 'all') {
      filtered = filtered.filter(item => item.type === filters.type);
    }
    if (filters.priority !== 'all') {
      filtered = filtered.filter(item => item.priority === filters.priority);
    }
    if (filters.assignee !== 'all') {
      filtered = filtered.filter(item => item.assignee === filters.assignee);
    }
    if (filters.status !== 'all') {
      filtered = filtered.filter(item => item.status === filters.status);
    }

    // Apply search
    if (searchTerm) {
      filtered = filtered.filter(
        item =>
          item.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.content.toLowerCase().includes(searchTerm.toLowerCase()) ||
          item.tags.some(tag => tag.toLowerCase().includes(searchTerm.toLowerCase()))
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === 'createdAt') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }

      if (sortOrder === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredItems(filtered);
  }, [items, filters, searchTerm, sortBy, sortOrder]);

  const getTypeColor = type => {
    switch (type) {
      case 'review':
        return 'bg-purple-100 text-purple-700';
      case 'comment':
        return 'bg-amber-100 text-amber-700';
      case 'rating':
        return 'bg-pink-100 text-pink-700';
      case 'report':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'bg-pink-100 text-pink-700';
      case 'medium':
        return 'bg-amber-100 text-amber-700';
      case 'low':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusColor = status => {
    switch (status) {
      case 'pending':
        return 'bg-pink-100 text-pink-700';
      case 'reviewing':
        return 'bg-amber-100 text-amber-700';
      case 'approved':
        return 'bg-purple-100 text-purple-700';
      case 'rejected':
        return 'bg-gray-100 text-gray-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getAssigneeColor = assignee => {
    switch (assignee) {
      case 'me':
        return 'bg-pink-100 text-pink-700';
      case 'team':
        return 'bg-amber-100 text-amber-700';
      case 'unassigned':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getReporterColor = reporter => {
    switch (reporter) {
      case 'user':
        return 'bg-pink-100 text-pink-700';
      case 'system':
        return 'bg-amber-100 text-amber-700';
      case 'moderator':
        return 'bg-purple-100 text-purple-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const getTypeIcon = type => {
    switch (type) {
      case 'review':
        return '📝';
      case 'report':
        return '🚨';
      case 'content':
        return '🎬';
      case 'user':
        return '👤';
      default:
        return '📋';
    }
  };

  const formatDate = dateString => {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-bold text-purple-900">Queue List</h2>
          <p className="text-gray-600">
            Quản lý danh sách nội dung chờ kiểm duyệt và báo cáo vi phạm
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => onSelectAll(filteredItems)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              isAllSelected
                ? 'bg-indigo-600 text-white'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            {isAllSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả'}
          </button>
          {selectedItems.length > 0 && (
            <button
              onClick={onClearSelection}
              className="px-4 py-2 bg-red-100 text-red-700 rounded-md text-sm font-medium hover:bg-red-200 transition-colors"
            >
              Xóa lựa chọn
            </button>
          )}
        </div>
      </div>

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-700">
          {/* Search */}
          <div className="col-span-3">
            <label className="block text-sm font-medium text-purple-900 mb-2">
              Tìm kiếm theo title, content hoặc tags...
            </label>
            <input
              type="text"
              placeholder="Tìm kiếm theo title, content hoặc tags..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="w-full rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            />
          </div>

          {/* Type Filter */}
          <div className="col-span-3">
            <label className="block text-sm font-medium text-purple-900 mb-2">Loại nội dung</label>
            <select
              value={filters.type}
              onChange={e => handleFilterChange('type', e.target.value)}
              className="w-full rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="review">Review</option>
              <option value="comment">Comment</option>
              <option value="rating">Rating</option>
              <option value="report">Report</option>
            </select>
          </div>

          {/* Priority Filter */}
          <div className="col-span-3">
            <label className="block text-sm font-medium text-purple-900 mb-2">Độ ưu tiên</label>
            <select
              value={filters.priority}
              onChange={e => handleFilterChange('priority', e.target.value)}
              className="w-full rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>

          {/* Status Filter */}
          <div className="col-span-3">
            <label className="block text-sm font-medium text-purple-900 mb-2">Trạng thái</label>
            <select
              value={filters.status}
              onChange={e => handleFilterChange('status', e.target.value)}
              className="w-full rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="pending">Chờ duyệt</option>
              <option value="reviewing">Đang xem xét</option>
              <option value="approved">Đã duyệt</option>
              <option value="rejected">Đã từ chối</option>
            </select>
          </div>

          {/* Assignee Filter */}
          <div className="col-span-3">
            <label className="block text-sm font-medium text-purple-900 mb-2">
              Người được giao
            </label>
            <select
              value={filters.assignee}
              onChange={e => handleFilterChange('assignee', e.target.value)}
              className="w-full rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
            >
              <option value="all">Tất cả</option>
              <option value="me">Tôi</option>
              <option value="team">Team</option>
              <option value="unassigned">Chưa giao</option>
            </select>
          </div>
        </div>
      </div>

      {/* Items List */}
      <div className="bg-white rounded-lg shadow-sm overflow-hidden">
        {/* Table Header */}
        <div className="bg-gray-50 px-6 py-3 border-b">
          <div className="grid grid-cols-12 gap-4 text-sm font-medium text-gray-700">
            <div className="col-span-1">
              <input
                type="checkbox"
                checked={isAllSelected}
                onChange={() => (isAllSelected ? onClearSelection() : onSelectAll(filteredItems))}
                className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
              />
            </div>
            <div className="col-span-1">Type</div>
            <div
              className="col-span-3 cursor-pointer hover:text-indigo-600"
              onClick={() => handleSort('title')}
            >
              Title {sortBy === 'title' && (sortOrder === 'asc' ? '↑' : '↓')}
            </div>
            <div className="col-span-2">Assignee</div>
            <div className="col-span-1">Priority</div>
            <div className="col-span-1">Status</div>
            <div
              className="col-span-2 cursor-pointer hover:text-indigo-600"
              onClick={() => handleSort('createdAt')}
            >
              Created {sortBy === 'createdAt' && (sortOrder === 'asc' ? '↑' : '↓')}
            </div>
            <div className="col-span-1">Actions</div>
          </div>
        </div>

        {/* Table Body */}
        <div className="divide-y divide-gray-200">
          {filteredItems.map(item => (
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
                  <div className="flex items-center">
                    <span className="text-2xl mr-2">{getTypeIcon(item.type)}</span>
                    <span
                      className={`px-2 py-1 rounded-full text-xs font-medium ${getTypeColor(item.type)}`}
                    >
                      {item.type}
                    </span>
                  </div>
                </div>

                {/* Title and Content */}
                <div className="col-span-3">
                  <div className="font-medium text-gray-900 mb-1">{item.title}</div>
                  <div className="text-sm text-gray-600 line-clamp-2">{item.content}</div>
                  {item.tags && (
                    <div className="flex flex-wrap gap-1 mt-2">
                      {item.tags.map(tag => (
                        <span
                          key={tag}
                          className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                        >
                          #{tag}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Assignee */}
                <div className="col-span-2">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900">{item.assignee}</span>
                    <span className="ml-2 text-xs text-gray-500">by {item.reporter}</span>
                  </div>
                </div>

                {/* Priority */}
                <div className="col-span-1">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(item.priority)}`}
                  >
                    {item.priority}
                  </span>
                </div>

                {/* Status */}
                <div className="col-span-1">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(item.status)}`}
                  >
                    {item.status}
                  </span>
                </div>

                {/* Created Date */}
                <div className="col-span-2">
                  <div className="text-sm text-gray-600">{formatDate(item.createdAt)}</div>
                </div>

                {/* Actions */}
                <div className="col-span-1">
                  <div className="flex space-x-1">
                    <button className="p-1 text-green-600 hover:text-green-800" title="Approve">
                      ✅
                    </button>
                    <button className="p-1 text-red-600 hover:text-red-800" title="Reject">
                      ❌
                    </button>
                    <button className="p-1 text-blue-600 hover:text-blue-800" title="View Details">
                      👁️
                    </button>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Empty State */}
        {filteredItems.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 text-6xl mb-4">📝</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Không có items nào</h3>
            <p className="text-gray-600">Thử thay đổi bộ lọc hoặc tìm kiếm khác</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default QueueList;
