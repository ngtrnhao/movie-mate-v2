import { XMarkIcon } from '@heroicons/react/24/outline';
import ReactDOM from 'react-dom';

const Modal = ({ open, onClose, title, children }) => {
  if (!open) return null;

  return ReactDOM.createPortal(
    <>
      {/* Overlay */}
      <div className="fixed inset-0 z-[9999] bg-black/40" />

      {/* Modal Container */}
      <div className="fixed inset-0 z-[9999] flex items-center justify-center p-4">
        <div className="w-full max-w-6xl animate-fade-in rounded-lg bg-white shadow-xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-gray-200 px-6 py-4">
            {title && <h2 className="text-xl font-semibold text-gray-900">{title}</h2>}
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600 focus:outline-none"
              aria-label="Đóng"
            >
              <XMarkIcon className="size-6" />
            </button>
          </div>

          {/* Content with scroll */}
          <div className="max-h-[calc(90vh-8rem)] overflow-y-auto px-6 py-4">{children}</div>
        </div>
      </div>
    </>,
    document.body
  );
};

export default Modal;
