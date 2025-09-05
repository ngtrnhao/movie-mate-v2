import React from 'react';

const AccountLockedModal = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Tài khoản đã bị khóa</h3>
          <p className="mt-2 text-sm text-gray-600">
            Tài khoản của bạn hiện đang bị khóa do vi phạm chính sách cộng đồng. Bạn sẽ không thể
            thực hiện một số chức năng cho đến khi tài khoản được mở khóa.
          </p>
        </div>
        <div className="space-y-2 rounded-md bg-yellow-50 p-3 text-sm text-yellow-800">
          <p>
            Nếu bạn nghĩ đây là nhầm lẫn, vui lòng liên hệ bộ phận hỗ trợ hoặc gửi khiếu nại để được
            xem xét lại.
          </p>
        </div>
        <div className="mt-6 flex justify-end">
          <button
            onClick={onClose}
            className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            Đã hiểu
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccountLockedModal;
