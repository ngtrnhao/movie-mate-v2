import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { CheckCircle, X, AlertTriangle, Info } from 'lucide-react';

const Toast = ({ message, type = 'success', duration = 3000, onClose }) => {
  const [isVisible, setIsVisible] = useState(true);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => setMounted(false);
  }, []);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(() => {
        onClose && onClose();
      }, 300); // Wait for fade out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const getIcon = () => {
    switch (type) {
      case 'success':
        return <CheckCircle className="size-5 text-green-400" />;
      case 'error':
        return <AlertTriangle className="size-5 text-red-400" />;
      case 'warning':
        return <AlertTriangle className="size-5 text-yellow-400" />;
      default:
        return <Info className="size-5 text-blue-400" />;
    }
  };

  const getBgColor = () => {
    switch (type) {
      case 'success':
        return 'bg-green-500/20 border-green-500/30';
      case 'error':
        return 'bg-red-500/20 border-red-500/30';
      case 'warning':
        return 'bg-yellow-500/20 border-yellow-500/30';
      default:
        return 'bg-blue-500/20 border-blue-500/30';
    }
  };

  const getTextColor = () => {
    switch (type) {
      case 'success':
        return 'text-green-300';
      case 'error':
        return 'text-red-300';
      case 'warning':
        return 'text-yellow-300';
      default:
        return 'text-blue-300';
    }
  };

  if (!mounted) return null;

  const toastContent = (
    <div
      className={`fixed bottom-4 right-4 z-[9998] transition-all duration-300${
        isVisible ? 'translate-x-0 opacity-100' : 'translate-x-full opacity-0'
      }`}
    >
      <div className={`flex items-center gap-3 rounded-lg border p-4 shadow-lg ${getBgColor()}`}>
        {getIcon()}
        <p className={`text-sm font-medium ${getTextColor()}`}>{message}</p>
        <button
          onClick={() => {
            setIsVisible(false);
            setTimeout(() => {
              onClose && onClose();
            }, 300);
          }}
          className="text-gray-400 hover:text-white"
        >
          <X className="size-4" />
        </button>
      </div>
    </div>
  );

  // Use Portal to render at the top level of DOM
  return createPortal(toastContent, document.body);
};

export default Toast;
