import React, { useState, useEffect } from 'react';

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

  const tabs = [
    { id: 'flagged', label: 'Bị đánh dấu', icon: '🚩', count: 8 },
    { id: 'warned', label: 'Đã cảnh báo', icon: '⚠️', count: 12 },
    { id: 'suspended', label: 'Tạm khóa', icon: '🔒', count: 5 },
    { id: 'banned', label: 'Bị cấm', icon: '🚫', count: 3 },
  ];

  // Mock data - replace with actual API calls
  useEffect(() => {
    const mockUsers = [
      {
        id: 'user-1',
        username: 'john_doe',
        email: 'john@example.com',
        role: 'user',
        status: 'active',
        joinDate: '2024-01-01T00:00:00Z',
        lastLogin: '2024-01-15T10:30:00Z',
        reports: 0,
        warnings: 0,
        isBanned: false,
      },
      {
        id: 'user-2',
        username: 'spam_user',
        email: 'spam@example.com',
        role: 'user',
        status: 'suspended',
        joinDate: '2024-01-05T00:00:00Z',
        lastLogin: '2024-01-14T15:20:00Z',
        reports: 5,
        warnings: 2,
        isBanned: true,
        banReason: 'Spam comments',
      },
      {
        id: 'user-3',
        username: 'moderator_a',
        email: 'moda@example.com',
        role: 'moderator',
        status: 'active',
        joinDate: '2023-12-01T00:00:00Z',
        lastLogin: '2024-01-15T09:15:00Z',
        reports: 0,
        warnings: 0,
        isBanned: false,
      },
      {
        id: 'user-4',
        username: 'troll_user',
        email: 'troll@example.com',
        role: 'user',
        status: 'banned',
        joinDate: '2024-01-10T00:00:00Z',
        lastLogin: '2024-01-13T20:45:00Z',
        reports: 12,
        warnings: 3,
        isBanned: true,
        banReason: 'Harassment and inappropriate content',
      },
    ];

    setTimeout(() => {
      setUsers(mockUsers);
      setFilteredUsers(mockUsers);
      setLoading(false);
    }, 1000);
  }, []);

  // Filter users
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
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Quản lý người dùng</h2>
          <p className="text-gray-600">Quản lý tài khoản người dùng và phân quyền</p>
        </div>
        <div className="flex space-x-2">
          <button className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors">
            Thêm người dùng
          </button>
          <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
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
              className={`py-2 px-1 border-b-2 font-medium text-sm flex items-center ${
                activeTab === tab.id
                  ? 'border-green-500 text-green-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
              <span className="ml-2 bg-gray-100 text-gray-900 py-0.5 px-2.5 rounded-full text-xs">
                {tab.count}
              </span>
            </button>
          ))}
        </nav>
      </div>

      {/* Actions */}
      <div className="flex justify-between items-center">
        <div className="flex space-x-4">
          <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
            <option>Tất cả vi phạm</option>
            <option>1-2 vi phạm</option>
            <option>3-4 vi phạm</option>
            <option>5+ vi phạm</option>
          </select>
          <select className="border border-gray-300 rounded-md px-3 py-2 text-sm">
            <option>Tất cả thời gian</option>
            <option>Hôm nay</option>
            <option>Tuần này</option>
            <option>Tháng này</option>
          </select>
        </div>
        <div className="flex space-x-2">
          {selectedUsers.length > 0 && (
            <>
              <button className="px-4 py-2 bg-yellow-600 text-white rounded-md text-sm hover:bg-yellow-700">
                Cảnh báo ({selectedUsers.length})
              </button>
              <button className="px-4 py-2 bg-orange-600 text-white rounded-md text-sm hover:bg-orange-700">
                Tạm khóa ({selectedUsers.length})
              </button>
              <button className="px-4 py-2 bg-red-600 text-white rounded-md text-sm hover:bg-red-700">
                Cấm ({selectedUsers.length})
              </button>
              <button
                onClick={handleClearSelection}
                className="px-4 py-2 bg-gray-600 text-white rounded-md text-sm hover:bg-gray-700"
              >
                Bỏ chọn
              </button>
            </>
          )}
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng người dùng</p>
              <p className="text-3xl font-bold text-blue-600">{users.length}</p>
            </div>
            <div className="bg-blue-100 rounded-full p-3">
              <span className="text-2xl">👥</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Đang hoạt động</p>
              <p className="text-3xl font-bold text-green-600">
                {users.filter(u => u.status === 'active').length}
              </p>
            </div>
            <div className="bg-green-100 rounded-full p-3">
              <span className="text-2xl">✅</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Bị cấm</p>
              <p className="text-3xl font-bold text-red-600">
                {users.filter(u => u.isBanned).length}
              </p>
            </div>
            <div className="bg-red-100 rounded-full p-3">
              <span className="text-2xl">🚫</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Moderators</p>
              <p className="text-3xl font-bold text-purple-600">
                {users.filter(u => u.role === 'moderator').length}
              </p>
            </div>
            <div className="bg-purple-100 rounded-full p-3">
              <span className="text-2xl">🛡️</span>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <input
            type="text"
            placeholder="Tìm kiếm theo username hoặc email..."
            value={filters.searchTerm}
            onChange={e => setFilters(prev => ({ ...prev, searchTerm: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />

          <select
            value={filters.status}
            onChange={e => setFilters(prev => ({ ...prev, status: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">Tất cả trạng thái</option>
            <option value="active">Đang hoạt động</option>
            <option value="suspended">Tạm khóa</option>
            <option value="banned">Bị cấm</option>
          </select>

          <select
            value={filters.role}
            onChange={e => setFilters(prev => ({ ...prev, role: e.target.value }))}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
          >
            <option value="all">Tất cả vai trò</option>
            <option value="user">User</option>
            <option value="moderator">Moderator</option>
            <option value="admin">Admin</option>
          </select>

          <button
            onClick={() => setFilters({ status: 'all', role: 'all', searchTerm: '' })}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            Xóa bộ lọc
          </button>
        </div>
      </div>

      {/* Users List */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="p-4 border-b border-gray-200">
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
              className={`p-4 hover:bg-gray-50 transition-colors ${
                selectedUsers.includes(user.id) ? 'bg-green-50' : ''
              }`}
            >
              <div className="flex items-center space-x-4">
                <input
                  type="checkbox"
                  checked={selectedUsers.includes(user.id)}
                  onChange={() => handleSelectUser(user.id)}
                  className="h-4 w-4 text-green-600 focus:ring-green-500 border-gray-300 rounded"
                />
                <div className="flex-shrink-0">
                  <div className="w-10 h-10 bg-gray-200 rounded-full flex items-center justify-center text-lg">
                    {user.username.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <div>
                      <h4 className="text-sm font-medium text-gray-900">{user.username}</h4>
                      <p className="text-sm text-gray-500">{user.email}</p>
                    </div>
                    <div className="flex items-center space-x-2">
                      <span
                        className={`px-2 py-1 text-xs rounded-full ${getStatusColor(user.status)}`}
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
                    <p className="text-xs text-gray-500 mt-1">
                      Hoạt động cuối: {formatDate(user.lastLogin)}
                    </p>
                  </div>
                </div>
                <div className="flex space-x-2">
                  {user.isBanned ? (
                    <button
                      onClick={() => handleUserAction('unban', user.id)}
                      className="text-green-600 hover:text-green-900"
                    >
                      Mở khóa
                    </button>
                  ) : (
                    <>
                      <button
                        onClick={() => handleUserAction('suspend', user.id)}
                        className="text-yellow-600 hover:text-yellow-900"
                      >
                        Tạm khóa
                      </button>
                      <button
                        onClick={() => handleUserAction('ban', user.id)}
                        className="text-red-600 hover:text-red-900"
                      >
                        Cấm
                      </button>
                    </>
                  )}
                  {user.role === 'user' ? (
                    <button
                      onClick={() => handleUserAction('promote_moderator', user.id)}
                      className="text-blue-600 hover:text-blue-900"
                    >
                      Thăng Moderator
                    </button>
                  ) : user.role === 'moderator' ? (
                    <button
                      onClick={() => handleUserAction('demote_user', user.id)}
                      className="text-gray-600 hover:text-gray-900"
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
        <div className="text-center py-12">
          <div className="text-gray-400 text-6xl mb-4">👥</div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Không tìm thấy người dùng</h3>
          <p className="text-gray-600">Thử thay đổi bộ lọc hoặc tìm kiếm khác</p>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
