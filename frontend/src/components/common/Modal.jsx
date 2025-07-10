import React from 'react';

const Modal = ({ open, onClose, title, children }) => {
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
      <div className="bg-white rounded-lg shadow-lg max-w-lg w-full p-6 relative animate-fade-in">
        <button
          onClick={onClose}
          className="absolute top-3 right-3 text-gray-400 hover:text-gray-600 text-xl font-bold focus:outline-none"
          aria-label="Đóng"
        >
          ×
        </button>
        {title && <h2 className="text-lg font-semibold mb-4 text-gray-900">{title}</h2>}
        <div>{children}</div>
      </div>
    </div>
  );
};

export default Modal;
