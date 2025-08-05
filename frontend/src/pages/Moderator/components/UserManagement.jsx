import { useState, useEffect, useCallback } from 'react';
import { getFlaggedUsers, moderateUser } from '../../../api/moderatorService';
import moderationCacheService from '../../../services/moderationCacheService';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [filteredUsers, setFilteredUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [filters, setFilters] = useState({
    status: 'all',
    role: 'all',
    searchTerm: '',
  });
  const [activeTab, setActiveTab] = useState('flagged');
  const [pagination, setPagination] = useState({
    currentPage: 1,
    pageSize: 20,
    totalCount: 0,
    totalPages: 1,
    hasNext: false,
    hasPrevious: false,
  });
  const [summary, setSummary] = useState({
    total_flagged: 0,
    warning_users: 0,
    severe_users: 0,
    banned_users: 0,
  });
  const [error, setError] = useState(null);
  const [moderationLoading, setModerationLoading] = useState(false);

  // Dynamic tabs with real counts from API
  const tabs = [
    { id: 'flagged', label: 'Bị đánh dấu', icon: '🚩', count: summary.total_flagged },
    { id: 'warned', label: 'Đã cảnh báo', icon: '⚠️', count: summary.warning_users },
    { id: 'suspended', label: 'Tạm khóa', icon: '🔒', count: summary.severe_users },
    { id: 'banned', label: 'Bị cấm', icon: '🚫', count: summary.banned_users },
  ];

  // Fetch flagged users from API
  const fetchFlaggedUsers = useCallback(
    async (page = 1, pageSize = 20) => {
      try {
        setLoading(true);
        setError(null);

        // Map activeTab to API status filter
        let statusFilter = 'all';
        switch (activeTab) {
          case 'warned':
            statusFilter = 'warning';
            break;
          case 'suspended':
          case 'banned':
            statusFilter = 'banned';
            break;
          default:
            statusFilter = 'all';
        }

        // Use cache service for flagged users API
        const response = await moderationCacheService.cachedApiCall(
          'flagged_users',
          async () =>
            await getFlaggedUsers({
              page,
              pageSize,
              status: statusFilter,
              sortBy: 'report_count',
            }),
          { page, pageSize, status: statusFilter }
        );

        if (response.status === 'success' && response.data) {
          const usersData = response.data.users || [];

          // Transform API data to match component expectations
          const transformedUsers = usersData.map(user => ({
            id: user.id,
            username: user.username,
            email: user.email,
            role: 'user', // API doesn't provide role, assume user
            status: user.is_active ? 'active' : 'banned',
            joinDate: user.join_date,
            lastLogin: user.last_activity,
            reports: user.total_reports || 0,
            warnings:
              user.warning_status === 'warning' ? 1 : user.warning_status === 'severe' ? 2 : 0,
            isBanned: !user.is_active,
            banReason: user.warning_status === 'severe' ? 'Multiple violations' : '',
            totalReviews: user.total_reviews || 0,
            rejectedReviews: user.rejected_reviews || 0,
            reputationScore: user.reputation_score || 100,
            flags: user.flags || [],
            warningStatus: user.warning_status || 'none',
          }));

          setUsers(transformedUsers);

          // Update pagination
          setPagination({
            currentPage: response.data.pagination?.current_page || 1,
            pageSize: response.data.pagination?.page_size || 20,
            totalCount: response.data.pagination?.total_count || 0,
            totalPages: response.data.pagination?.total_pages || 1,
            hasNext: response.data.pagination?.has_next || false,
            hasPrevious: response.data.pagination?.has_previous || false,
          });

          // Update summary
          setSummary(
            response.data.summary || {
              total_flagged: 0,
              warning_users: 0,
              severe_users: 0,
              banned_users: 0,
            }
          );

          console.log('✅ Flagged users loaded:', {
            count: transformedUsers.length,
            totalCount: response.data.pagination?.total_count || 0,
            fromCache: response.__fromCache || false,
          });
        } else {
          throw new Error(response.error || 'Failed to fetch flagged users');
        }
      } catch (err) {
        console.error('Error fetching flagged users:', err);
        setError('Không thể tải danh sách người dùng bị đánh dấu');

        // Fallback to empty array if API fails
        setUsers([]);
        setPagination({
          currentPage: 1,
          pageSize: 20,
          totalCount: 0,
          totalPages: 1,
          hasNext: false,
          hasPrevious: false,
        });
      } finally {
        setLoading(false);
      }
    },
    [activeTab]
  );

  // Load users on component mount and tab change
  useEffect(() => {
    fetchFlaggedUsers(1, pagination.pageSize);
  }, [fetchFlaggedUsers, activeTab]);

  // Handle moderation actions
  const handleModerationAction = useCallback(
    async (userId, action, reason = '', durationDays = 0) => {
      try {
        setModerationLoading(true);

        const response = await moderateUser(userId, action, reason, durationDays);

        if (response.status === 'success') {
          // Refresh users list after action
          await fetchFlaggedUsers(pagination.currentPage, pagination.pageSize);

          // Clear cache to ensure fresh data
          moderationCacheService.clearCache('flagged_users');

          console.log('✅ User moderation action completed:', {
            userId,
            action,
            message: response.data?.message,
          });

          // Show success notification (you can implement a toast here)
          alert(response.data?.message || 'Thao tác thành công');
        } else {
          throw new Error(response.error || 'Failed to moderate user');
        }
      } catch (err) {
        console.error('Error moderating user:', err);
        alert(`Lỗi: ${err.error || err.message || 'Không thể thực hiện thao tác'}`);
      } finally {
        setModerationLoading(false);
      }
    },
    [fetchFlaggedUsers, pagination.currentPage, pagination.pageSize]
  );

  // Filter users (now working with real API data)
  useEffect(() => {
    let filtered = [...users];

    if (filters.status !== 'all') {
      filtered = filtered.filter(user => user.status === filters.status);
    }
    if (filters.role !== 'all') {
      filtered = filtered.filter(user => user.role === filters.role);
    }
    if (filters.searchTerm) {
      filtered = filtered.filter(
        user =>
          user.username.toLowerCase().includes(filters.searchTerm.toLowerCase()) ||
          user.email.toLowerCase().includes(filters.searchTerm.toLowerCase())
      );
    }

    setFilteredUsers(filtered);
  }, [users, filters]);

  const getStatusColor = status => {
    switch (status) {
      case 'active':
        return 'bg-green-100 text-green-800';
      case 'suspended':
        return 'bg-yellow-100 text-yellow-800';
      case 'banned':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getRoleColor = role => {
    switch (role) {
      case 'admin':
        return 'bg-purple-100 text-purple-800';
      case 'moderator':
        return 'bg-blue-100 text-blue-800';
      case 'user':
        return 'bg-gray-100 text-gray-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const handleUserAction = async (action, userId) => {
    setLoading(true);
    try {
      console.log('User action:', action, 'User ID:', userId);
      // API call would go here

      // Update local state
      setUsers(prev =>
        prev.map(user => {
          if (user.id === userId) {
            switch (action) {
              case 'ban':
                return { ...user, status: 'banned', isBanned: true };
              case 'unban':
                return { ...user, status: 'active', isBanned: false };
              case 'suspend':
                return { ...user, status: 'suspended' };
              case 'activate':
                return { ...user, status: 'active' };
              case 'promote_moderator':
                return { ...user, role: 'moderator' };
              case 'demote_user':
                return { ...user, role: 'user' };
              default:
                return user;
            }
          }
          return user;
        })
      );
    } catch (error) {
      console.error('User action failed:', error);
    } finally {
      setLoading(false);
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

  const handleSelectUser = userId => {
    setSelectedUsers(prev =>
      prev.includes(userId) ? prev.filter(id => id !== userId) : [...prev, userId]
    );
  };

  const handleSelectAll = () => {
    setSelectedUsers(users.map(user => user.id));
  };

  const handleClearSelection = () => {
    setSelectedUsers([]);
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="size-12 animate-spin rounded-full border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Quản lý người dùng</h2>
          <p className="text-gray-600">Quản lý tài khoản người dùng và phân quyền</p>
        </div>
        <div className="flex space-x-2">
          <button className="rounded-md bg-indigo-600 px-4 py-2 text-white transition-colors hover:bg-indigo-700">
            Thêm người dùng
          </button>
          <button className="rounded-md bg-green-600 px-4 py-2 text-white transition-colors hover:bg-green-700">
            Xuất danh sách
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center border-b-2 px-1 py-2 text-sm font-medium ${
                activeTab === tab.id
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
              <span className="ml-2 rounded-full bg-gray-100 px-2.5 py-0.5 text-xs text-gray-900">
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Actions */}
      <div className="flex items-center justify-between">
        <div className="flex space-x-4">
          <select className="rounded-md border border-gray-300 text-gray-500 bg-white px-3 py-2 text-sm">
            <option className="text-gray-500">Tất cả vi phạm</option>
            <option className="text-gray-500">1-2 vi phạm</option>
            <option className="text-gray-500">3-4 vi phạm</option>
            <option className="text-gray-500">5+ vi phạm</option>
          </select>
          <select className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-500">
            <option className="text-gray-500">Tất cả thời gian</option>
            <option className="text-gray-500">Hôm nay</option>
            <option className="text-gray-500">Tuần này</option>
            <option className="text-gray-500">Tháng này</option>
          </select>
        </div>
        <div className="flex space-x-2">
          {selectedUsers.length > 0 && (
            <>
              <button className="rounded-md bg-yellow-600 px-4 py-2 text-sm text-white hover:bg-yellow-700">
                Cảnh báo ({selectedUsers.length})
              </button>
              <button className="rounded-md bg-orange-600 px-4 py-2 text-sm text-white hover:bg-orange-700">
                Tạm khóa ({selectedUsers.length})
              </button>
              <button className="rounded-md bg-red-600 px-4 py-2 text-sm text-white hover:bg-red-700">
                Cấm ({selectedUsers.length})
              </button>
              <button
                onClick={handleClearSelection}
                className="rounded-md bg-gray-600 px-4 py-2 text-sm text-white hover:bg-gray-700"
              >
                Bỏ chọn
              </button>
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4">
        <div className="rounded-lg bg-white p-6 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng người dùng</p>
              <p className="text-3xl font-bold text-blue-600">{users.length}</p>
            </div>
            <div className="rounded-full bg-blue-100 p-3">
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Đang hoạt động</p>
              <p className="text-3xl font-bold text-green-600">
                {users.filter(u => u.status === 'active').length}
              </p>
            </div>
            <div className="rounded-full bg-green-100 p-3">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bị cấm</p>
              <p className="text-3xl font-bold text-red-600">
                {users.filter(u => u.isBanned).length}
              </p>
            </div>
            <div className="rounded-full bg-red-100 p-3">
              <span className="text-2xl">🚫</span>
            </div>
          </div>
        </div>

        <div className="rounded-lg bg-white p-6 shadow-md">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Moderators</p>
              <p className="text-3xl font-bold text-purple-600">
                {users.filter(u => u.role === 'moderator').length}
              </p>
            </div>
            <div className="rounded-full bg-purple-100 p-3">
              <span className="text-2xl">🛡️</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg bg-white p-4 shadow-sm">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
          <input
            type="text"
            placeholder="Tìm kiếm theo username hoặc email..."
            value={filters.searchTerm}
            onChange={e => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
            className="rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />

          <select
            value={filters.status}
            onChange={e => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="rounded-md border bg-white text-gray-500 border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option className="text-gray-500" value="all">
              Tất cả trạng thái
            </option>
            <option className="text-gray-500" value="active">
              Đang hoạt động
            </option>
            <option className="text-gray-500" value="suspended">
              Tạm khóa
            </option>
            <option className="text-gray-500" value="banned">
              Bị cấm
            </option>
          </select>

          <select
            value={filters.role}
            onChange={e => setFilters(prev => ({ ...prev, role: e.target.value }))}
            className="rounded-md border bg-white text-gray-500 border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option className="text-gray-500" value="all">
              Tất cả vai trò
            </option>
            <option className="text-gray-500" value="user">
              User
            </option>
            <option className="text-gray-500" value="moderator">
              Moderator
            </option>
            <option className="text-gray-500" value="admin">
              Admin
            </option>
          </select>

          <button
            onClick={() => setFilters({ status: 'all', role: 'all', searchTerm: '' })}
            className="rounded-md bg-gray-100 px-4 py-2 text-gray-700 transition-colors hover:bg-gray-200"
          >
            Xóa bộ lọc
          </button>
        </div>
      </div>

      {/* Users List */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 p-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">
              {tabs.find(tab => tab.id === activeTab)?.label}
            </h3>
            <button
              onClick={handleSelectAll}
              className="text-sm text-green-600 hover:text-green-700"
            >
              Chọn tất cả
            </button>
          </div>
        </div>
        <div className="divide-y divide-gray-200">
          {filteredUsers.map(user => (
            <div
              key={user.id}
              className={`p-4 transition-colors hover:bg-gray-50 ${
                selectedUsers.includes(user.id) ? 'bg-green-50' : ''
              }`}
            >
              <div className="flex items-center space-x-4">
                <input
                  type="checkbox"
                  checked={selectedUsers.includes(user.id)}
                  onChange={() => handleSelectUser(user.id)}
                  className="size-4 rounded border-gray-300 text-green-600 focus:ring-green-500"
                />
                <div className="shrink-0">
                  <div className="flex size-10 items-center justify-center rounded-full bg-gray-200 text-lg">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{user.username}</h4>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`rounded-full px-2 py-1 text-xs ${getStatusColor(user.status)}`}
                      >
                        {user.status === 'active'
                          ? 'Đang hoạt động'
                          : user.status === 'suspended'
                            ? 'Tạm khóa'
                            : 'Bị cấm'}
                      </span>
                    </div>
                  </div>
                  <div className="mt-2">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Lý do:</span>{' '}
                      {user.banReason || 'Không có lý do'}
                    </p>
                    <p className="mt-1 text-xs text-gray-500">
                      Hoạt động cuối: {formatDate(user.lastLogin)}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {user.isBanned ? (
                    <button
                      onClick={() => handleModerationAction(user.id, 'unban')}
                      className="text-green-600 hover:text-green-900"
                      disabled={moderationLoading}
                    >
                      Mở khóa
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() =>
                          handleModerationAction(
                            user.id,
                            'suspend',
                            'Tạm khóa do vi phạm nội quy',
                            7
                          )
                        }
                        className="text-yellow-600 hover:text-yellow-900"
                        disabled={moderationLoading}
                      >
                        Tạm khóa
                      </button>
                      <button
                        onClick={() =>
                          handleModerationAction(user.id, 'ban', 'Cấm do vi phạm nghiêm trọng', 365)
                        }
                        className="text-red-600 hover:text-red-900"
                        disabled={moderationLoading}
                      >
                        Cấm
                      </button>
                    </>
                  )}
                  {user.role === 'user' ? (
                    <button
                      onClick={() => handleModerationAction(user.id, 'promote_moderator')}
                      className="text-blue-600 hover:text-blue-900"
                      disabled={moderationLoading}
                    >
                      Thăng Moderator
                    </button>
                  ) : user.role === 'moderator' ? (
                    <button
                      onClick={() => handleModerationAction(user.id, 'demote_user')}
                      className="text-gray-600 hover:text-gray-900"
                      disabled={moderationLoading}
                    >
                      Hạ cấp
                    </button>
                  ) : null}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Empty State */}
      {filteredUsers.length === 0 && (
        <div className="py-12 text-center">
          <div className="mb-4 text-6xl text-gray-400">👥</div>
          <h3 className="mb-2 text-lg font-medium text-gray-900">Không tìm thấy người dùng</h3>
          <p className="text-gray-600">Thử thay đổi bộ lọc hoặc tìm kiếm khác</p>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
