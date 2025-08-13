import React, { useState } from 'react';
import { XMarkIcon, CalendarIcon, ClockIcon } from '@heroicons/react/24/outline';

const SchedulePublishModal = ({ isOpen, onClose, onSchedule, movieTitle }) => {
  const [scheduleData, setScheduleData] = useState({
    scheduled_date: '',
    scheduled_time: '09:00',
    end_date: '',
    end_time: '23:59',
    campaign_name: '',
    priority: 1,
    auto_unpublish: false,
  });

  const handleSubmit = e => {
    e.preventDefault();

    if (!scheduleData.scheduled_date) {
      alert('Vui lòng chọn ngày xuất bản');
      return;
    }

    const scheduled_datetime = `${scheduleData.scheduled_date}T${scheduleData.scheduled_time}:00`;
    const end_datetime =
      scheduleData.auto_unpublish && scheduleData.end_date
        ? `${scheduleData.end_date}T${scheduleData.end_time}:00`
        : null;

    onSchedule({
      scheduled_datetime,
      end_datetime,
      campaign_name: scheduleData.campaign_name || 'Manual scheduled publish',
      priority: scheduleData.priority,
      auto_unpublish: scheduleData.auto_unpublish,
    });
  };

  const handleClose = () => {
    setScheduleData({
      scheduled_date: '',
      scheduled_time: '09:00',
      end_date: '',
      end_time: '23:59',
      campaign_name: '',
      priority: 1,
      auto_unpublish: false,
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-full items-end justify-center p-4 text-center sm:items-center sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={handleClose}
        />

        <div className="relative transform overflow-hidden rounded-lg bg-white text-left shadow-xl transition-all sm:my-8 sm:w-full sm:max-w-lg">
          <div className="bg-white px-4 pb-4 pt-5 sm:p-6 sm:pb-4">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-medium leading-6 text-gray-900">
                Lên lịch xuất bản phim
              </h3>
              <button
                onClick={handleClose}
                className="rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>

            {movieTitle && (
              <div className="mb-4 p-3 bg-blue-50 rounded-md">
                <p className="text-sm text-blue-800">
                  <strong>Phim:</strong> {movieTitle}
                </p>
              </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Ngày xuất bản */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <CalendarIcon className="inline h-4 w-4 mr-1" />
                  Ngày xuất bản *
                </label>
                <input
                  type="date"
                  required
                  value={scheduleData.scheduled_date}
                  onChange={e =>
                    setScheduleData(prev => ({ ...prev, scheduled_date: e.target.value }))
                  }
                  min={new Date().toISOString().split('T')[0]}
                  className="block w-full text-black rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              {/* Giờ xuất bản */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  <ClockIcon className="inline h-4 w-4 mr-1" />
                  Giờ xuất bản
                </label>
                <input
                  type="time"
                  value={scheduleData.scheduled_time}
                  onChange={e =>
                    setScheduleData(prev => ({ ...prev, scheduled_time: e.target.value }))
                  }
                  className="block w-full text-black rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              {/* Tên chiến dịch */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Tên chiến dịch
                </label>
                <input
                  type="text"
                  value={scheduleData.campaign_name}
                  onChange={e =>
                    setScheduleData(prev => ({ ...prev, campaign_name: e.target.value }))
                  }
                  placeholder="VD: Xuất bản phim Việt Nam"
                  className="block w-full text-black rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                />
              </div>

              {/* Độ ưu tiên */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Độ ưu tiên</label>
                <select
                  value={scheduleData.priority}
                  onChange={e =>
                    setScheduleData(prev => ({ ...prev, priority: parseInt(e.target.value) }))
                  }
                  className="block w-full text-black rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                >
                  <option className="text-black" value={1}>
                    Thấp
                  </option>
                  <option className="text-black" value={5}>
                    Trung bình
                  </option>
                  <option className="text-black" value={10}>
                    Cao
                  </option>
                </select>
              </div>

              {/* Tự động ngừng xuất bản */}
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="auto_unpublish"
                  checked={scheduleData.auto_unpublish}
                  onChange={e =>
                    setScheduleData(prev => ({ ...prev, auto_unpublish: e.target.checked }))
                  }
                  className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
                <label htmlFor="auto_unpublish" className="ml-2 block text-sm text-gray-900">
                  Tự động ngừng xuất bản
                </label>
              </div>

              {/* Ngày ngừng xuất bản (nếu có) */}
              {scheduleData.auto_unpublish && (
                <div className="space-y-2">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ngày ngừng xuất bản
                    </label>
                    <input
                      type="date"
                      value={scheduleData.end_date}
                      onChange={e =>
                        setScheduleData(prev => ({ ...prev, end_date: e.target.value }))
                      }
                      min={scheduleData.scheduled_date || new Date().toISOString().split('T')[0]}
                      className="block w-full text-black rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Giờ ngừng xuất bản
                    </label>
                    <input
                      type="time"
                      value={scheduleData.end_time}
                      onChange={e =>
                        setScheduleData(prev => ({ ...prev, end_time: e.target.value }))
                      }
                      className="block w-full text-black rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm"
                    />
                  </div>
                </div>
              )}

              {/* Preview thời gian */}
              {scheduleData.scheduled_date && (
                <div className="p-3 bg-gray-50 rounded-md">
                  <p className="text-sm text-gray-600">
                    <strong>Thời gian xuất bản:</strong>
                    <br />
                    {new Date(
                      `${scheduleData.scheduled_date}T${scheduleData.scheduled_time}`
                    ).toLocaleString('vi-VN')}
                  </p>
                  {scheduleData.auto_unpublish && scheduleData.end_date && (
                    <p className="text-sm text-gray-600 mt-1">
                      <strong>Thời gian ngừng:</strong>
                      <br />
                      {new Date(`${scheduleData.end_date}T${scheduleData.end_time}`).toLocaleString(
                        'vi-VN'
                      )}
                    </p>
                  )}
                </div>
              )}
            </form>
          </div>

          <div className="bg-gray-50 px-4 py-3 sm:flex sm:flex-row-reverse sm:px-6">
            <button
              type="submit"
              onClick={handleSubmit}
              className="inline-flex w-full justify-center rounded-md bg-indigo-600 px-3 py-2 text-sm font-semibold text-white shadow-sm hover:bg-indigo-500 sm:ml-3 sm:w-auto"
            >
              Lên lịch
            </button>
            <button
              type="button"
              onClick={handleClose}
              className="mt-3 inline-flex w-full justify-center rounded-md bg-white px-3 py-2 text-sm font-semibold text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 hover:bg-gray-50 sm:mt-0 sm:w-auto"
            >
              Hủy
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SchedulePublishModal;
