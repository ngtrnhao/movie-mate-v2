import { useState } from 'react';

const BulkActions = ({ selectedCount, onBulkAction, selectedItems, onClearSelection, isAdmin }) => {
  const [showConfirmation, setShowConfirmation] = useState(false);
  const [confirmationAction, setConfirmationAction] = useState(null);
  const [loading, setLoading] = useState(false);

  const bulkActions = [
    {
      id: 'approve',
      label: 'Duyệt',
      icon: '✅',
      color: 'bg-green-600 hover:bg-green-700',
      confirmMessage: 'Bạn có chắc chắn muốn duyệt {count} items đã chọn?',
    },
    {
      id: 'reject',
      label: 'Từ chối',
      icon: '❌',
      color: 'bg-red-600 hover:bg-red-700',
      confirmMessage: 'Bạn có chắc chắn muốn từ chối {count} items đã chọn?',
    },
    {
      id: 'assign',
      label: 'Phân công',
      icon: '👥',
      color: 'bg-blue-600 hover:bg-blue-700',
      confirmMessage: 'Bạn có chắc chắn muốn phân công {count} items đã chọn?',
    },
    {
      id: 'priority_high',
      label: 'Đặt High Priority',
      icon: '🔥',
      color: 'bg-orange-600 hover:bg-orange-700',
      confirmMessage: 'Bạn có chắc chắn muốn đặt {count} items thành High Priority?',
    },
    {
      id: 'mark_reviewed',
      label: 'Đánh dấu đã xem',
      icon: '👁️',
      color: 'bg-purple-600 hover:bg-purple-700',
      confirmMessage: 'Bạn có chắc chắn muốn đánh dấu {count} items đã được xem?',
    },
    {
      id: 'export',
      label: 'Xuất dữ liệu',
      icon: '📤',
      color: 'bg-gray-600 hover:bg-gray-700',
      confirmMessage: 'Bạn có chắc chắn muốn xuất dữ liệu {count} items đã chọn?',
    },
  ];

  const handleActionClick = action => {
    setConfirmationAction(action);
    setShowConfirmation(true);
  };

  const handleConfirmAction = async () => {
    if (!confirmationAction) return;

    setLoading(true);
    try {
      await onBulkAction(confirmationAction.id, selectedItems);
      setShowConfirmation(false);
      setConfirmationAction(null);
    } catch (error) {
      console.error('Bulk action failed:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelAction = () => {
    setShowConfirmation(false);
    setConfirmationAction(null);
  };

  return (
    <>
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <span className="text-sm font-medium text-indigo-800">
              {selectedCount} items được chọn
            </span>
            <button
              onClick={onClearSelection}
              className="text-sm text-indigo-600 underline hover:text-indigo-800"
            >
              Xóa lựa chọn
            </button>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          {bulkActions.map(action => (
            <button
              key={action.id}
              onClick={() => handleActionClick(action)}
              disabled={loading}
              className={`inline-flex items-center rounded-md px-3 py-2 text-sm font-medium text-white transition-colors ${
                action.color
              } ${loading ? 'cursor-not-allowed opacity-50' : ''}`}
            >
              <span className="mr-2">{action.icon}</span>
              {action.label}
            </button>
          ))}
        </div>
      </div>

      {/* Confirmation Modal */}
      {showConfirmation && confirmationAction && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="mx-4 w-full max-w-md rounded-lg bg-white p-6">
            <div className="mb-4 flex items-center">
              <div className="shrink-0">
                <span className="text-3xl">{confirmationAction.icon}</span>
              </div>
              <div className="ml-3">
                <h3 className="text-lg font-medium text-gray-900">Xác nhận thao tác</h3>
                <p className="mt-1 text-sm text-gray-600">
                  {confirmationAction.confirmMessage.replace('{count}', selectedCount)}
                </p>
              </div>
            </div>

            {/* Action Details */}
            <div className="mb-4 rounded-lg bg-gray-50 p-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Thao tác:</span>
                <span className="text-sm text-gray-900">{confirmationAction.label}</span>
              </div>
              <div className="mt-2 flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">Số lượng:</span>
                <span className="text-sm text-gray-900">{selectedCount} items</span>
              </div>
            </div>

            {/* Additional Options for specific actions */}
            {confirmationAction.id === 'assign' && (
              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Phân công cho:
                </label>
                <select className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                  <option value="">Chọn người được phân công</option>
                  <option value="moderator-a">Moderator A</option>
                  <option value="moderator-b">Moderator B</option>
                  <option value="moderator-c">Moderator C</option>
                  <option value="admin">Admin</option>
                </select>
              </div>
            )}

            {confirmationAction.id === 'reject' && (
              <div className="mb-4">
                <label className="mb-2 block text-sm font-medium text-gray-700">
                  Lý do từ chối:
                </label>
                <textarea
                  className="w-full rounded-md border border-gray-300 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  rows={3}
                  placeholder="Nhập lý do từ chối (tùy chọn)"
                />
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex justify-end space-x-3">
              <button
                onClick={handleCancelAction}
                disabled={loading}
                className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-gray-50 disabled:opacity-50"
              >
                Hủy
              </button>
              <button
                onClick={handleConfirmAction}
                disabled={loading}
                className={`rounded-md px-4 py-2 text-sm font-medium text-white transition-colors ${
                  confirmationAction.color
                } ${loading ? 'cursor-not-allowed opacity-50' : ''}`}
              >
                {loading ? (
                  <div className="flex items-center">
                    <div className="mr-2 size-4 animate-spin rounded-full border-b-2 border-white"></div>
                    Đang xử lý...
                  </div>
                ) : (
                  `Xác nhận ${confirmationAction.label}`
                )}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Quick Stats */}
      <div className="mt-4 rounded-lg bg-indigo-50 p-3">
        <div className="flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <div className="flex items-center">
              <span className="font-medium text-indigo-600">Tổng:</span>
              <span className="ml-1 text-indigo-800">{selectedCount}</span>
            </div>
            <div className="flex items-center">
              <span className="font-medium text-indigo-600">Có thể duyệt:</span>
              <span className="ml-1 text-green-600">{Math.floor(selectedCount * 0.8)}</span>
            </div>
            <div className="flex items-center">
              <span className="font-medium text-indigo-600">Cần xem xét:</span>
              <span className="ml-1 text-yellow-600">{Math.floor(selectedCount * 0.2)}</span>
            </div>
          </div>
          <div className="text-indigo-600">
            💡 Mẹo: Sử dụng Ctrl/Cmd để chọn nhiều items cùng lúc
          </div>
        </div>
      </div>
    </>
  );
};

export default BulkActions;
