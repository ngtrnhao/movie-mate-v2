import React, { useState, useEffect } from 'react';
import { ClockIcon, XMarkIcon, PencilIcon } from '@heroicons/react/24/outline';
import {
  getScheduledTasks,
  cancelScheduledTask,
  rescheduleTask,
} from '../../../api/adminMovieService';

const ScheduledTasksInfo = ({ movieId, onUpdate }) => {
  const [tasks, setTasks] = useState({});
  const [loading, setLoading] = useState(false);
  const [showRescheduleModal, setShowRescheduleModal] = useState(false);
  const [rescheduleData, setRescheduleData] = useState({
    actionType: '',
    newDate: '',
    newTime: '',
  });

  useEffect(() => {
    if (movieId) {
      fetchScheduledTasks();
    }
  }, [movieId]);

  const fetchScheduledTasks = async () => {
    setLoading(true);
    try {
      const result = await getScheduledTasks(movieId);
      setTasks(result.tasks || {});
    } catch (error) {
      console.error('Error fetching scheduled tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCancelTask = async actionType => {
    try {
      await cancelScheduledTask(movieId, actionType);
      alert(`Đã hủy lịch trình ${actionType} thành công!`);
      fetchScheduledTasks();
      if (onUpdate) onUpdate();
    } catch (error) {
      alert(error.error || `Không thể hủy lịch trình ${actionType}`);
    }
  };

  const handleRescheduleTask = async () => {
    try {
      const newDateTime = `${rescheduleData.newDate}T${rescheduleData.newTime}:00`;
      await rescheduleTask(movieId, rescheduleData.actionType, newDateTime);
      alert(`Đã thay đổi lịch trình ${rescheduleData.actionType} thành công!`);
      setShowRescheduleModal(false);
      setRescheduleData({ actionType: '', newDate: '', newTime: '' });
      fetchScheduledTasks();
      if (onUpdate) onUpdate();
    } catch (error) {
      alert(error.error || `Không thể thay đổi lịch trình ${rescheduleData.actionType}`);
    }
  };

  const openRescheduleModal = actionType => {
    setRescheduleData({ ...rescheduleData, actionType });
    setShowRescheduleModal(true);
  };

  const getActionTypeLabel = actionType => {
    const labels = {
      publish: 'Xuất bản',
      unpublish: 'Ngừng xuất bản',
      feature: 'Featured',
      unfeature: 'Bỏ featured',
    };
    return labels[actionType] || actionType;
  };

  const getActionTypeColor = actionType => {
    const colors = {
      publish: 'bg-green-100 text-green-800 border-green-200',
      unpublish: 'bg-red-100 text-red-800 border-red-200',
      feature: 'bg-blue-100 text-blue-800 border-blue-200',
      unfeature: 'bg-gray-100 text-gray-800 border-gray-200',
    };
    return colors[actionType] || 'bg-gray-100 text-gray-800 border-gray-200';
  };

  if (loading) {
    return (
      <div className="p-4">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-2"></div>
          <div className="h-3 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    );
  }

  const hasScheduledTasks = Object.keys(tasks).length > 0;

  if (!hasScheduledTasks) {
    return (
      <div className="p-4 text-center text-gray-500">
        <ClockIcon className="h-8 w-8 mx-auto mb-2 text-gray-400" />
        <p>Không có lịch trình nào được đặt</p>
      </div>
    );
  }

  return (
    <div className="p-4">
      <h3 className="text-lg font-semibold mb-3 flex items-center">
        <ClockIcon className="h-5 w-5 mr-2" />
        Lịch Trình Đã Đặt
      </h3>

      <div className="space-y-3">
        {Object.entries(tasks).map(([actionType, taskInfo]) => (
          <div key={actionType} className="border rounded-lg p-3 bg-white shadow-sm">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getActionTypeColor(
                    actionType
                  )}`}
                >
                  {getActionTypeLabel(actionType)}
                </span>
                <span className="text-sm text-gray-600">
                  Task ID: {taskInfo.task_id?.slice(-8)}...
                </span>
              </div>

              <div className="flex items-center space-x-2">
                <button
                  onClick={() => openRescheduleModal(actionType)}
                  className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded"
                  title="Thay đổi lịch trình"
                >
                  <PencilIcon className="h-4 w-4" />
                </button>
                <button
                  onClick={() => handleCancelTask(actionType)}
                  className="p-1 text-red-600 hover:text-red-800 hover:bg-red-50 rounded"
                  title="Hủy lịch trình"
                >
                  <XMarkIcon className="h-4 w-4" />
                </button>
              </div>
            </div>

            <div className="mt-2 text-sm text-gray-600">
              <span className="font-medium">Trạng thái:</span> {taskInfo.status}
            </div>
          </div>
        ))}
      </div>

      {/* Reschedule Modal */}
      {showRescheduleModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
          <div className="bg-white rounded-lg p-6 w-96">
            <h3 className="text-lg font-semibold mb-4">
              Thay Đổi Lịch Trình {getActionTypeLabel(rescheduleData.actionType)}
            </h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Ngày mới</label>
                <input
                  type="date"
                  value={rescheduleData.newDate}
                  onChange={e => setRescheduleData({ ...rescheduleData, newDate: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Giờ mới</label>
                <input
                  type="time"
                  value={rescheduleData.newTime}
                  onChange={e => setRescheduleData({ ...rescheduleData, newTime: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-3 mt-6">
              <button
                onClick={() => setShowRescheduleModal(false)}
                className="px-4 py-2 text-gray-600 border border-gray-300 rounded-md hover:bg-gray-50"
              >
                Hủy
              </button>
              <button
                onClick={handleRescheduleTask}
                disabled={!rescheduleData.newDate || !rescheduleData.newTime}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Thay Đổi
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ScheduledTasksInfo;
