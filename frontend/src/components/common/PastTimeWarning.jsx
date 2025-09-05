import React from 'react';
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const PastTimeWarning = ({ isPastTime, pastTimeWarning, className = '' }) => {
  if (!isPastTime) return null;

  return (
    <div className={`p-3 bg-yellow-50 border border-yellow-200 rounded-md ${className}`}>
      <div className="flex items-center">
        <ExclamationTriangleIcon className="h-5 w-5 text-yellow-600 mr-2" />
        <p className="text-sm text-yellow-800 font-medium">Cảnh báo thời gian</p>
      </div>
      <p className="text-sm text-yellow-700 mt-1">{pastTimeWarning}</p>
    </div>
  );
};

export default PastTimeWarning;
