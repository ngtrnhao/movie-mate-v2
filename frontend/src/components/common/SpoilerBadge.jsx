import React from 'react';
import { AlertTriangle } from 'lucide-react';

const SpoilerBadge = ({
  isSpoiler,
  size = 'sm',
  variant = 'default',
  className = '',
  showIcon = true,
}) => {
  if (!isSpoiler) return null;

  const sizeClasses = {
    xs: 'px-1.5 py-0.5 text-xs',
    sm: 'px-2 py-1 text-xs',
    md: 'px-2.5 py-1 text-sm',
    lg: 'px-3 py-1.5 text-sm',
  };

  const variantClasses = {
    default: 'bg-orange-500/20 text-orange-400 border border-orange-500/30',
    warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
    danger: 'bg-red-500/20 text-red-400 border border-red-500/30',
    subtle: 'bg-gray-500/20 text-gray-400 border border-gray-500/30',
  };

  const iconSizes = {
    xs: 10,
    sm: 12,
    md: 14,
    lg: 16,
  };

  return (
    <span
      className={`
        inline-flex items-center gap-1 rounded-full font-medium
        ${sizeClasses[size]}
        ${variantClasses[variant]}
        ${className}
      `}
    >
      {showIcon && <AlertTriangle className="flex-shrink-0" size={iconSizes[size]} />}
      Spoiler
    </span>
  );
};

export default SpoilerBadge;
