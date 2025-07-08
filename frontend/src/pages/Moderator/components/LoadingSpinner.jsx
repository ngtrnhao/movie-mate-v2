const LoadingSpinner = ({ message = 'Đang tải...', size = 'default' }) => {
  const sizeClasses = {
    small: 'h-6 w-6',
    default: 'h-8 w-8',
    large: 'h-12 w-12',
  };

  return (
    <div className="flex flex-col items-center justify-center space-y-4 p-8">
      <div
        className={`animate-spin rounded-full border-b-2 border-purple-600 ${sizeClasses[size]}`}
      ></div>
      <p className="text-sm font-medium text-gray-600">{message}</p>
    </div>
  );
};

LoadingSpinner.displayName = 'LoadingSpinner';

export default LoadingSpinner;
