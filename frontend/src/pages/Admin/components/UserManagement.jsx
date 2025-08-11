import { useState, useEffect } from 'react';
import {
  listAdminUsers,
  updateAdminUserRole,
  setAdminUserActive,
  notifyAdminUser,
} from '../../../api/moderatorService';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterRole, setFilterRole] = useState('all');
  const [selectedUser, setSelectedUser] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [pagination, setPagination] = useState({ currentPage: 1, pageSize: 20, totalCount: 0 });
  const [newRole, setNewRole] = useState('');
  const [lockModalOpen, setLockModalOpen] = useState(false);
  const [lockReason, setLockReason] = useState('Vi phạm điều khoản sử dụng');
  const [lockNotify, setLockNotify] = useState(true);

  // Tự động fetch khi load trang lần đầu; khi nhập/đổi filter chỉ gọi API khi nhấn nút Tìm kiếm
  useEffect(() => {
    fetchUsers(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchUsers = async (page = 1) => {
    try {
      setLoading(true);
      setError(null);
      const response = await listAdminUsers({
        page,
        page_size: pagination.pageSize,
        search: searchTerm,
        role: filterRole,
      });
      const data = response?.data || response?.results || [];
      const pg = response?.pagination || {};
      setUsers(data);
      setPagination(prev => ({
        ...prev,
        currentPage: pg.current_page || page,
        totalCount: pg.total_count || data.length,
      }));
    } catch (err) {
      setError('Không thể tải danh sách người dùng');
      console.error('Error fetching users:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId, role) => {
    try {
      await updateAdminUserRole(userId, role);
      await fetchUsers(pagination.currentPage);
      setShowModal(false);
    } catch (err) {
      console.error('Error updating user role:', err);
      alert(err?.error || 'Không thể cập nhật vai trò');
    }
  };

  const handleToggleActive = async (userId, isActive) => {
    try {
      await setAdminUserActive(userId, isActive);
      if (!isActive && lockNotify) {
        await notifyAdminUser(
          userId,
          'Tài khoản của bạn đã bị khóa',
          lockReason || 'Tài khoản bị khóa do vi phạm chính sách cộng đồng.'
        );
      }
      await fetchUsers(pagination.currentPage);
    } catch (err) {
      console.error('Error updating user status:', err);
      alert(err?.error || 'Không thể cập nhật trạng thái');
    }
  };

  const filteredUsers = users.filter(user => {
    const matchesSearch =
      user.username?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      user.email?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesRole =
      filterRole === 'all' ||
      (filterRole === 'admin' && user.role === 'admin') ||
      (filterRole === 'moderator' && user.role === 'moderator') ||
      (filterRole === 'user' && user.role === 'user');

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
    if (user.role === 'admin') {
      return (
        <span className="inline-flex items-center rounded-full bg-purple-100 px-2.5 py-0.5 text-xs font-medium text-purple-800">
          Admin
        </span>
      );
    } else if (user.role === 'moderator') {
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

  // Note: user type badge không dùng ở Admin view hiện tại

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
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
          />
        </div>
        <div className="sm:w-48">
          <select
            value={filterRole}
            onChange={e => setFilterRole(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-gray-700 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
          >
            <option className="text-gray-700" value="all">
              Tất cả vai trò
            </option>
            <option className="text-gray-700" value="admin">
              Admin
            </option>
            <option className="text-gray-700" value="moderator">
              Moderator
            </option>
            <option className="text-gray-700" value="user">
              User
            </option>
          </select>
        </div>
        <div className="sm:w-40">
          <button
            onClick={() => fetchUsers(1)}
            className="w-full rounded-md border border-indigo-300 bg-indigo-600 px-3 py-2 text-sm font-medium text-white hover:bg-indigo-700 disabled:opacity-60"
            disabled={loading}
          >
            Tìm kiếm
          </button>
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
                        <div className="ml-2 flex space-x-1">{getRoleBadge(user)}</div>
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
                        if (user.is_active) {
                          setSelectedUser(user);
                          setLockReason('Vi phạm điều khoản sử dụng');
                          setLockNotify(true);
                          setLockModalOpen(true);
                        } else {
                          handleToggleActive(user.id, true);
                        }
                      }}
                      className={`inline-flex items-center rounded-md border px-3 py-1 text-sm ${
                        user.is_active
                          ? 'border-red-300 bg-red-50 text-red-700 hover:bg-red-100'
                          : 'border-green-300 bg-green-50 text-green-700 hover:bg-green-100'
                      }`}
                    >
                      {user.is_active ? 'Khóa' : 'Mở khóa'}
                    </button>
                    <button
                      onClick={() => {
                        setSelectedUser(user);
                        setNewRole(user.role);
                        setShowModal(true);
                      }}
                      className="inline-flex items-center rounded-md border border-indigo-300 bg-indigo-50 px-3 py-1 text-sm text-indigo-700 hover:bg-indigo-100"
                    >
                      Đổi vai trò
                    </button>
                  </div>
                </div>
              </div>
            </li>
          ))}
        </ul>
      </div>

      {/* Pagination */}
      <div className="mt-4 flex items-center justify-between">
        <button
          onClick={() => fetchUsers(Math.max(1, pagination.currentPage - 1))}
          className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-700 hover:bg-gray-50"
          disabled={pagination.currentPage <= 1}
        >
          Trước
        </button>
        <div className="text-sm text-gray-600">
          Trang {pagination.currentPage} /{' '}
          {Math.max(1, Math.ceil(pagination.totalCount / Math.max(1, pagination.pageSize)))}
        </div>
        <button
          onClick={() => fetchUsers(pagination.currentPage + 1)}
          className="rounded-md border border-gray-300 bg-white px-3 py-1 text-sm text-gray-700 hover:bg-gray-50"
          disabled={pagination.currentPage * pagination.pageSize >= pagination.totalCount}
        >
          Sau
        </button>
      </div>

      {filteredUsers.length === 0 && (
        <div className="py-12 text-center">
          <p className="text-gray-500">Không tìm thấy người dùng nào</p>
        </div>
      )}

      {/* Role Change Modal */}
      {showModal && selectedUser && (
        <div className="fixed inset-0 z-50 size-full overflow-y-auto bg-gray-600/50">
          <div className="relative top-20 mx-auto w-96 rounded-md border bg-white p-5 shadow-lg">
            <div className="mt-3">
              <h3 className="mb-4 text-lg font-medium text-gray-900">
                Thay đổi vai trò cho {selectedUser.username}
              </h3>
              <div className="space-y-3">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Vai trò mới
                  </label>
                  <select
                    className="w-full rounded-md border text-gray-700 border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
                    value={newRole}
                    onChange={e => setNewRole(e.target.value)}
                  >
                    <option className="text-gray-700" value="user">
                      User
                    </option>
                    <option className="text-gray-700" value="moderator">
                      Moderator
                    </option>
                    <option className="text-gray-700" value="admin">
                      Admin
                    </option>
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
                  onClick={() => handleRoleChange(selectedUser.id, newRole)}
                  className="rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
                >
                  Cập nhật
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {lockModalOpen && selectedUser && (
        <div className="fixed inset-0 z-50 size-full overflow-y-auto bg-gray-600/50">
          <div className="relative top-20 mx-auto w-full max-w-lg rounded-md border bg-white p-5 shadow-lg">
            <div className="mt-1">
              <h3 className="mb-3 text-lg font-medium text-gray-900">
                Khóa tài khoản: {selectedUser.username}
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">Lý do khóa</label>
                  <textarea
                    rows={3}
                    value={lockReason}
                    onChange={e => setLockReason(e.target.value)}
                    className="w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-red-500 focus:outline-none focus:ring-red-500"
                    placeholder="Nhập lý do khóa tài khoản..."
                  />
                </div>
                <label className="flex items-center space-x-2">
                  <input
                    type="checkbox"
                    checked={lockNotify}
                    onChange={e => setLockNotify(e.target.checked)}
                    className="rounded border-gray-300 text-red-600 focus:ring-red-500"
                  />
                  <span className="text-sm text-gray-700">Gửi thông báo cho người dùng</span>
                </label>
              </div>
              <div className="mt-5 flex justify-end space-x-3">
                <button
                  onClick={() => setLockModalOpen(false)}
                  className="rounded-md border border-gray-300 bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200 focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Hủy
                </button>
                <button
                  onClick={async () => {
                    await handleToggleActive(selectedUser.id, false);
                    setLockModalOpen(false);
                  }}
                  className="rounded-md border border-transparent bg-red-600 px-4 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                >
                  Xác nhận khóa
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
