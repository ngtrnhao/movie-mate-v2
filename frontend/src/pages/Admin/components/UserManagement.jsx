import { useState, useEffect } from 'react';
import { getCommunityStats } from '../../../api/movieService';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    try {
      setLoading(true);
      // For now, using community stats as placeholder
      // TODO: Create proper admin API endpoint for user management
      const response = await getCommunityStats();
      // Mock user data for now
      setUsers([
        {
          id: 1,
          username: 'admin_user',
          email: 'admin@example.com',
          user_type: 'member',
          groups: ['Administrators'],
          created_at: '2024-01-01',
          avatar_url: '/images/avatar_default.jpg',
        },
      ]);
    } catch (err) {
      setError('Không thể tải danh sách người dùng');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, newRole) => {
    try {
      // This would be implemented with a proper API endpoint
      console.log(`Changing role for user ${userId} to ${newRole}`);
      // await api.patch(`/users/users/${userId}/`, { role: newRole });

      // Update local state
      setUsers(
        users.map(user =>
          user.id === userId
            ? {
                ...user,
                groups:
                  newRole === 'admin'
                    ? ['Administrators']
                    : newRole === 'moderator'
                      ? ['Moderators']
                      : [],
              }
            : user
        )
      );

      setShowModal(false);
    } catch (err) {
      console.error('Error updating user role:', err);
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesRole =
      filterRole === 'all' ||
      (filterRole === 'admin' && user.groups?.includes('Administrators')) ||
      (filterRole === 'moderator' && user.groups?.includes('Moderators')) ||
      (filterRole === 'user' && (!user.groups || user.groups.length === 0));

    return matchesSearch && matchesRole;
  });

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="mb-6 h-4 w-1/4 rounded bg-gray-200"></div>
          <div className="h-64 rounded-lg bg-gray-200"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="rounded-md border border-red-200 bg-red-50 p-4">
          <div className="flex">
            <div className="shrink-0">
              <svg className="size-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Lỗi</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  const getRoleBadge = user => {
    if (user.groups?.includes('Administrators')) {
      return (
        <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
          Admin
        </span>
      );
    } else if (user.groups?.includes('Moderators')) {
      return (
        <span className="inline-flex items-center rounded-full bg-blue-100 px-2.5 py-0.5 text-xs font-medium text-blue-800">
          Moderator
        </span>
      );
    } else {
      return (
        <span className="inline-flex items-center rounded-full bg-gray-100 px-2.5 py-0.5 text-xs font-medium text-gray-800">
          User
        </span>
      );
    }
  };

  const getUserTypeBadge = userType => {
    const typeMap = {
      member: { label: 'Member', color: 'bg-blue-100 text-blue-800' },
      premium_basic: { label: 'Premium Basic', color: 'bg-amber-100 text-amber-800' },
      premium_standard: { label: 'Premium Standard', color: 'bg-yellow-100 text-yellow-800' },
      premium_vip: { label: 'Premium VIP', color: 'bg-purple-100 text-purple-800' },
    };

    const type = typeMap[userType] || { label: userType, color: 'bg-gray-100 text-gray-800' };
    return (
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${type.color}`}
      >
        {type.label}
      </span>
    );
  };

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="mb-2 text-2xl font-bold text-gray-900">Quản lý người dùng</h2>
        <p className="text-gray-600">Quản lý tài khoản người dùng và phân quyền</p>
      </div>

      {/* Filters */}
      <div className="mb-6 flex flex-col gap-4 sm:flex-row">
        <div className="flex-1">
          <input
            type="text"
            placeholder="Tìm kiếm theo tên hoặc email..."
            value={searchTerm}
            onChange={e => setSearchTerm(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
          />
        </div>
        <div className="sm:w-48">
          <select
            value={filterRole}
            onChange={e => setFilterRole(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
          >
            <option value="all">Tất cả vai trò</option>
            <option value="admin">Admin</option>
            <option value="moderator">Moderator</option>
            <option value="user">User</option>
          </select>
        </div>
      </div>

      {/* Users Table */}
      <div className="overflow-hidden bg-white shadow sm:rounded-md">
        <ul className="divide-y divide-gray-200">
          {filteredUsers.map(user => (
            <li key={user.id}>
              <div className="p-4 sm:px-6">
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="size-10 shrink-0">
                      <img
                        className="size-10 rounded-full"
                        src={user.avatar_url || '/images/avatar_default.jpg'}
                        alt=""
                      />
                    </div>
                    <div className="ml-4">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">{user.username}</p>
                        <div className="ml-2 flex space-x-1">
                          {getRoleBadge(user)}
                          {getUserTypeBadge(user.user_type)}
                        </div>
                      </div>
                      <p className="text-sm text-gray-500">{user.email}</p>
                      <p className="text-sm text-gray-500">
                        Tham gia: {new Date(user.created_at).toLocaleDateString('vi-VN')}
                      </p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => {
                        setSelectedUser(user);
                        setShowModal(true);
                      }}
                      className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-3 py-1 text-sm font-medium leading-4 text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                    >
                      Chỉnh sửa
                    </button>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {filteredUsers.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-gray-500">Không tìm thấy người dùng nào</p>
        </div>
      )}

      {/* Role Change Modal */}
      {showModal && selectedUser && (
        <div className="fixed inset-0 z-50 size-full overflow-y-auto bg-gray-600 bg-opacity-50">
          <div className="relative top-20 mx-auto w-96 rounded-md border bg-white p-5 shadow-lg">
            <div className="mt-3">
              <h3 className="mb-4 text-lg font-medium text-gray-900">
                Thay đổi vai trò cho {selectedUser.username}
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Vai trò hiện tại
                  </label>
                  <div className="text-sm text-gray-500">
                    {selectedUser.groups?.includes('Administrators')
                      ? 'Admin'
                      : selectedUser.groups?.includes('Moderators')
                        ? 'Moderator'
                        : 'User'}
                  </div>
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Vai trò mới
                  </label>
                  <select
                    className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
                    defaultValue=""
                  >
                    <option value="" disabled>
                      Chọn vai trò
                    </option>
                    <option value="user">User</option>
                    <option value="moderator">Moderator</option>
                    <option value="admin">Admin</option>
                  </select>
                </div>
              </div>
              <div className="mt-6 flex justify-end space-x-3">
                <button
                  onClick={() => setShowModal(false)}
                  className="rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Hủy
                </button>
                <button
                  onClick={() => handleRoleChange(selectedUser.id, 'moderator')}
                  className="rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Cập nhật
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UserManagement;
