import React, { useState, useEffect } from 'react';
import { XMarkIcon, CalendarIcon, ClockIcon, PencilIcon } from '@heroicons/react/24/outline';
import { usePastTimeCheck } from '../../../hooks/usePastTimeCheck';
import PastTimeWarning from '../../../components/common/PastTimeWarning';

const SchedulePublishModal = ({
  isOpen,
  onClose,
  onSchedule,
  onReschedule,
  movieTitle,
  existingSchedule = null, // Thông tin lịch trình hiện có
  isEditMode = false, // Chế độ sửa lịch trình
}) => {
  const [scheduleData, setScheduleData] = useState({
    scheduled_date: '',
    scheduled_time: '09:00',
    end_date: '',
    end_time: '23:59',
    campaign_name: '',
    priority: 1,
    auto_unpublish: false,
  });

  // Sử dụng hook để kiểm tra thời gian trong quá khứ
  const { isPastTime, pastTimeWarning, updatePastTimeWarning, confirmPastTime } =
    usePastTimeCheck();

  // Khởi tạo dữ liệu từ existingSchedule nếu đang ở chế độ edit
  useEffect(() => {
    if (isEditMode && existingSchedule) {
      const scheduleDate = new Date(existingSchedule.scheduled_datetime);
      const endDate = existingSchedule.end_datetime
        ? new Date(existingSchedule.end_datetime)
        : null;

      const newScheduleData = {
        scheduled_date: scheduleDate.toISOString().split('T')[0],
        scheduled_time: scheduleDate.toTimeString().slice(0, 5),
        end_date: endDate ? endDate.toISOString().split('T')[0] : '',
        end_time: endDate ? endDate.toTimeString().slice(0, 5) : '23:59',
        campaign_name: existingSchedule.campaign_name || '',
        priority: existingSchedule.priority || 1,
        auto_unpublish: existingSchedule.auto_unpublish || false,
      };

      setScheduleData(newScheduleData);

      // Cập nhật warning cho thời gian hiện tại
      updatePastTimeWarning(newScheduleData.scheduled_date, newScheduleData.scheduled_time);
    } else {
      // Reset về giá trị mặc định cho lịch trình mới
      setScheduleData({
        scheduled_date: '',
        scheduled_time: '09:00',
        end_date: '',
        end_time: '23:59',
        campaign_name: '',
        priority: 1,
        auto_unpublish: false,
      });
    }
  }, [isEditMode, existingSchedule, isOpen, updatePastTimeWarning]);

  const handleSubmit = e => {
    e.preventDefault();

    if (!scheduleData.scheduled_date) {
      alert('Vui lòng chọn ngày xuất bản');
      return;
    }

    // Kiểm tra và xác nhận thời gian trong quá khứ
    const shouldContinue = confirmPastTime(
      scheduleData.scheduled_date,
      scheduleData.scheduled_time
    );
    if (!shouldContinue) {
      return;
    }

    const scheduled_datetime = `${scheduleData.scheduled_date}T${scheduleData.scheduled_time}:00`;
    const end_datetime =
      scheduleData.auto_unpublish && scheduleData.end_date
        ? `${scheduleData.end_date}T${scheduleData.end_time}:00`
        : null;

    const schedulePayload = {
      scheduled_datetime,
      end_datetime,
      campaign_name: scheduleData.campaign_name || 'Manual scheduled publish',
      priority: scheduleData.priority,
      auto_unpublish: scheduleData.auto_unpublish,
    };

    if (isEditMode && onReschedule) {
      // Gọi hàm reschedule nếu đang ở chế độ edit
      onReschedule(schedulePayload);
    } else {
      // Gọi hàm schedule cho lịch trình mới
      onSchedule(schedulePayload);
    }
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
              <h3 className="text-lg font-medium leading-6 text-gray-900 flex items-center">
                {isEditMode ? (
                  <>
                    <PencilIcon className="h-5 w-5 mr-2 text-orange-500" />
                    Sửa lịch trình xuất bản
                  </>
                ) : (
                  <>
                    <CalendarIcon className="h-5 w-5 mr-2 text-blue-500" />
                    Lên lịch xuất bản phim
                  </>
                )}
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
                {isEditMode && existingSchedule && (
                  <p className="text-sm text-orange-700 mt-1">
                    <strong>Lịch trình hiện tại:</strong>{' '}
                    {new Date(existingSchedule.scheduled_datetime).toLocaleString('vi-VN')}
                  </p>
                )}
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
                  onChange={e => {
                    const newDate = e.target.value;
                    setScheduleData(prev => ({ ...prev, scheduled_date: newDate }));
                    updatePastTimeWarning(newDate, scheduleData.scheduled_time);
                  }}
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
                  onChange={e => {
                    const newTime = e.target.value;
                    setScheduleData(prev => ({ ...prev, scheduled_time: newTime }));
                    updatePastTimeWarning(scheduleData.scheduled_date, newTime);
                  }}
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

              {/* Warning thời gian trong quá khứ */}
              <PastTimeWarning isPastTime={isPastTime} pastTimeWarning={pastTimeWarning} />

              {/* Preview thời gian */}
              {scheduleData.scheduled_date && (
                <div
                  className={`p-3 rounded-md ${
                    isPastTime ? 'bg-yellow-50 border border-yellow-200' : 'bg-gray-50'
                  }`}
                >
                  <p className={`text-sm ${isPastTime ? 'text-yellow-800' : 'text-gray-600'}`}>
                    <strong>Thời gian xuất bản:</strong>
                    <br />
                    {new Date(
                      `${scheduleData.scheduled_date}T${scheduleData.scheduled_time}`
                    ).toLocaleString('vi-VN')}
                  </p>
                  {scheduleData.auto_unpublish && scheduleData.end_date && (
                    <p
                      className={`text-sm mt-1 ${isPastTime ? 'text-yellow-700' : 'text-gray-600'}`}
                    >
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
              className={`inline-flex w-full justify-center rounded-md px-3 py-2 text-sm font-semibold text-white shadow-sm sm:ml-3 sm:w-auto ${
                isEditMode
                  ? 'bg-orange-600 hover:bg-orange-500'
                  : 'bg-indigo-600 hover:bg-indigo-500'
              }`}
            >
              {isEditMode ? 'Cập nhật lịch trình' : 'Lên lịch'}
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
