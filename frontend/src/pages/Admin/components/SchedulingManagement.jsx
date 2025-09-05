import { useState, useEffect, useCallback } from 'react';
import {
  CalendarIcon,
  ClockIcon,
  StarIcon,
  PlusIcon,
  CheckCircleIcon,
  XCircleIcon,
  TrashIcon,
  ExclamationTriangleIcon,
  BoltIcon,
  EyeIcon,
  PencilIcon,
  InformationCircleIcon,
} from '@heroicons/react/24/outline';
import {
  getAdminMovies,
  scheduleMovieAction,
  scheduleMoviePublish,
  cancelScheduledTask,
  cancelTaskById,
  getScheduledTasks,
  getScheduledActions,
  rescheduleTask,
} from '../../../api/adminMovieService';
import Modal from '../../../components/common/Modal';
import ScheduledTasksInfo from './ScheduledTasksInfo';

const SchedulingManagement = () => {
  const [movies, setMovies] = useState([]);
  const [scheduledActions, setScheduledActions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showScheduleModal, setShowScheduleModal] = useState(false);
  const [selectedMovie, setSelectedMovie] = useState(null);
  const [isEditing, setIsEditing] = useState(false);
  const [editingTaskId, setEditingTaskId] = useState(null);
  const [scheduleForm, setScheduleForm] = useState({
    action_type: 'publish',
    scheduled_date: '',
    scheduled_time: '00:00',
    end_date: '',
    end_time: '',
    campaign_name: '',
    campaign_type: 'feature',
    priority: 1,
    auto_unschedule: false,
  });

  // Fetch movies and scheduled actions
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [moviesData, actionsData] = await Promise.all([
        getAdminMovies({
          pageSize: 50,
          filters: { approval_status: ['PENDING', 'APPROVED'] },
        }),
        getScheduledActions(),
      ]);
      setMovies(moviesData.results || []);
      setScheduledActions(actionsData || []);
    } catch (error) {
      console.error('Error fetching scheduling data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Handle schedule action
  const handleScheduleAction = async () => {
    if (!selectedMovie) return;

    try {
      const newDateTime = `${scheduleForm.scheduled_date}T${scheduleForm.scheduled_time}:00`;

      if (isEditing && editingTaskId) {
        // Chỉnh sửa thời gian lịch trình hiện tại
        await rescheduleTask(selectedMovie.id, scheduleForm.action_type, newDateTime);
        alert('Thời gian lịch trình đã được cập nhật thành công!');
      } else {
        // Tạo lịch trình mới
        if (scheduleForm.action_type === 'publish') {
          await scheduleMoviePublish(
            selectedMovie.id,
            newDateTime,
            true // auto_approve
          );
        } else {
          // Xử lý các action khác nếu cần
          console.log('Scheduling other action:', scheduleForm);
        }
        alert('Lịch trình đã được tạo thành công!');
      }

      setShowScheduleModal(false);
      setSelectedMovie(null);
      setIsEditing(false);
      setEditingTaskId(null);
      resetScheduleForm();
      fetchData();
    } catch (error) {
      console.error('Error scheduling action:', error);
      alert(
        'Không thể ' +
          (isEditing ? 'cập nhật' : 'tạo') +
          ' lịch trình: ' +
          (error.error || error.message)
      );
    }
  };

  // Cancel scheduled action
  const handleCancelAction = async taskId => {
    try {
      console.log('🔄 Cancelling task ID:', taskId);

      const result = await cancelTaskById(taskId);
      console.log('📋 Cancel result:', result);

      if (result && result.status === 'success') {
        console.log('✅ Task cancelled successfully');
        alert('Đã hủy lịch trình thành công!');

        // Force refresh data
        console.log('🔄 Refreshing data...');
        await fetchData();
        console.log('✅ Data refreshed');
      } else {
        console.error('❌ Cancel failed:', result);
        alert('Không thể hủy lịch trình: ' + (result?.message || 'Lỗi không xác định'));
      }
    } catch (error) {
      console.error('💥 Error canceling scheduled action:', error);
      alert('Không thể hủy lịch trình: ' + (error.error || error.message || 'Lỗi kết nối'));
    }
  };

  // Edit scheduled action
  const handleEditAction = async action => {
    try {
      // Tạo object movie từ action data
      const movie = {
        id: action.movie_id,
        title: action.movie_title,
        // Thêm các field khác nếu cần
      };

      setSelectedMovie(movie);
      setIsEditing(true);
      setEditingTaskId(action.id);
      setScheduleForm({
        action_type: action.action_type,
        scheduled_date: new Date(action.scheduled_datetime).toISOString().split('T')[0],
        scheduled_time: new Date(action.scheduled_datetime).toTimeString().slice(0, 5),
        end_date: action.end_datetime
          ? new Date(action.end_datetime).toISOString().split('T')[0]
          : '',
        end_time: action.end_datetime
          ? new Date(action.end_datetime).toTimeString().slice(0, 5)
          : '',
        campaign_name: action.campaign_name || '',
        campaign_type: action.campaign_type || 'feature',
        priority: action.priority || 1,
        auto_unschedule: action.auto_unschedule || false,
      });
      setShowScheduleModal(true);
    } catch (error) {
      console.error('Error editing scheduled action:', error);
      alert('Không thể mở form chỉnh sửa: ' + error.message);
    }
  };

  // View action details
  const handleViewDetails = action => {
    // Có thể mở modal chi tiết hoặc navigate đến trang chi tiết
    console.log('View details for action:', action);
    alert(
      `Chi tiết lịch trình:\nPhim: ${action.movie_title}\nHành động: ${action.action_type}\nThời gian: ${new Date(action.scheduled_datetime).toLocaleString('vi-VN')}\nTrạng thái: ${action.status}`
    );
  };

  // Reset form
  const resetScheduleForm = () => {
    setScheduleForm({
      action_type: 'publish',
      scheduled_date: '',
      scheduled_time: '00:00',
      end_date: '',
      end_time: '',
      campaign_name: '',
      campaign_type: 'feature',
      priority: 1,
      auto_unschedule: false,
    });
  };

  // Open schedule modal
  const openScheduleModal = movie => {
    setSelectedMovie(movie);
    setIsEditing(false);
    setEditingTaskId(null);
    setShowScheduleModal(true);
  };

  // Close schedule modal
  const closeScheduleModal = () => {
    setShowScheduleModal(false);
    setSelectedMovie(null);
    setIsEditing(false);
    setEditingTaskId(null);
    resetScheduleForm();
  };

  // Get status badge for action
  const getActionStatusBadge = action => {
    const now = new Date();
    const scheduledDate = new Date(action.scheduled_datetime);
    const isOverdue = scheduledDate < now && action.status === 'PENDING';

    const statusStyles = {
      PENDING: isOverdue
        ? 'bg-red-100 text-red-800 border-red-200'
        : 'bg-yellow-100 text-yellow-800 border-yellow-200',
      COMPLETED: 'bg-green-100 text-green-800 border-green-200',
      CANCELLED: 'bg-gray-100 text-gray-800 border-gray-200',
      FAILED: 'bg-red-100 text-red-800 border-red-200',
    };

    const statusLabels = {
      PENDING: isOverdue ? 'Quá hạn' : 'Chờ thực hiện',
      COMPLETED: 'Hoàn thành',
      CANCELLED: 'Đã hủy',
      FAILED: 'Thất bại',
    };

    const statusIcons = {
      PENDING: isOverdue ? ExclamationTriangleIcon : ClockIcon,
      COMPLETED: CheckCircleIcon,
      CANCELLED: XCircleIcon,
      FAILED: XCircleIcon,
    };

    const StatusIcon = statusIcons[action.status];

    return (
      <span
        className={`inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium ${statusStyles[action.status]}`}
      >
        <StatusIcon className="mr-1 size-3" />
        {statusLabels[action.status]}
      </span>
    );
  };

  // Get action type label
  const getActionTypeLabel = actionType => {
    const typeLabels = {
      publish: 'Xuất bản',
      unpublish: 'Ẩn bài',
      feature: 'Featured',
      unfeature: 'Bỏ featured',
    };
    return typeLabels[actionType] || actionType;
  };

  // Get action type badge
  const getActionTypeBadge = actionType => {
    const typeStyles = {
      publish: 'bg-blue-100 text-blue-800',
      unpublish: 'bg-gray-100 text-gray-800',
      feature: 'bg-yellow-100 text-yellow-800',
      unfeature: 'bg-orange-100 text-orange-800',
    };

    const typeLabels = {
      publish: 'Xuất bản',
      unpublish: 'Ẩn bài',
      feature: 'Featured',
      unfeature: 'Bỏ featured',
    };

    const typeIcons = {
      publish: EyeIcon,
      unpublish: EyeIcon,
      feature: StarIcon,
      unfeature: StarIcon,
    };

    const TypeIcon = typeIcons[actionType];

    return (
      <span
        className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium ${typeStyles[actionType]}`}
      >
        <TypeIcon className="mr-1 size-3" />
        {typeLabels[actionType]}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="size-8 animate-spin rounded-full border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="flex items-center text-2xl font-bold text-gray-900">
              <CalendarIcon className="mr-3 size-8 text-blue-600" />
              Quản lý lịch trình
            </h1>
            <p className="mt-2 text-gray-600">
              Lên lịch xuất bản, featured và quản lý chiến dịch phim
            </p>
          </div>
          <button
            onClick={() => setShowScheduleModal(true)}
            className="inline-flex items-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700"
          >
            <PlusIcon className="mr-2 size-4" />
            Tạo lịch trình
          </button>
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ClockIcon className="size-6 text-blue-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Tổng lịch trình</p>
              <p className="text-2xl font-semibold text-gray-900">{scheduledActions.length}</p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CheckCircleIcon className="size-6 text-green-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Đang chờ</p>
              <p className="text-2xl font-semibold text-gray-900">
                {scheduledActions.filter(a => a.status === 'PENDING').length}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <StarIcon className="size-6 text-yellow-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Xuất bản</p>
              <p className="text-2xl font-semibold text-gray-900">
                {scheduledActions.filter(a => a.action_type === 'publish').length}
              </p>
            </div>
          </div>
        </div>

        <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <BoltIcon className="size-6 text-purple-600" />
            </div>
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Featured</p>
              <p className="text-2xl font-semibold text-gray-900">
                {scheduledActions.filter(a => a.action_type === 'feature').length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Scheduled Actions */}
      <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-medium text-gray-900">Lịch trình đã tạo</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Phim
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Hành động
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Thời gian
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Chiến dịch
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Trạng thái
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider text-gray-500">
                  Thao tác
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 bg-white">
              {scheduledActions.map(action => (
                <tr key={action.id}>
                  <td className="whitespace-nowrap px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{action.movie_title}</div>
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    {getActionTypeBadge(action.action_type)}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900">
                    {new Date(action.scheduled_datetime).toLocaleString('vi-VN')}
                    {action.end_datetime && (
                      <div className="text-xs text-gray-500">
                        đến {new Date(action.end_datetime).toLocaleString('vi-VN')}
                      </div>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">
                    {action.campaign_name ? (
                      <div className="text-sm text-gray-900">{action.campaign_name}</div>
                    ) : (
                      <span className="text-sm text-gray-500">Không có</span>
                    )}
                  </td>
                  <td className="whitespace-nowrap px-6 py-4">{getActionStatusBadge(action)}</td>
                  <td className="whitespace-nowrap px-6 py-4 text-sm font-medium">
                    <div className="flex items-center space-x-2">
                      {/* View Details Button */}
                      <button
                        onClick={() => handleViewDetails(action)}
                        className="text-blue-600 hover:text-blue-900"
                        title="Xem chi tiết"
                      >
                        <InformationCircleIcon className="size-4" />
                      </button>

                      {/* Edit Button - chỉ hiển thị cho PENDING actions */}
                      {action.status === 'PENDING' && (
                        <button
                          onClick={() => handleEditAction(action)}
                          className="text-orange-600 hover:text-orange-900"
                          title="Sửa lịch trình"
                        >
                          <PencilIcon className="size-4" />
                        </button>
                      )}

                      {/* Cancel Button - chỉ hiển thị cho PENDING actions */}
                      {action.status === 'PENDING' && (
                        <button
                          onClick={() => handleCancelAction(action.task_id || action.id)}
                          className="text-red-600 hover:text-red-900"
                          title="Hủy lịch trình"
                        >
                          <TrashIcon className="size-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Scheduled Tasks Info */}
      {scheduledActions.length > 0 && (
        <div className="rounded-lg border border-gray-200 bg-white shadow-sm">
          <div className="border-b border-gray-200 px-6 py-4">
            <h3 className="text-lg font-medium text-gray-900">Thông tin chi tiết lịch trình</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              {scheduledActions.map((action, index) => (
                <div key={action.id} className="border rounded-lg p-4 bg-gray-50">
                  <div className="flex items-center justify-between mb-3">
                    <h4 className="font-medium text-gray-900">{action.movie_title}</h4>
                    <span
                      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                        action.status === 'PENDING'
                          ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
                          : 'bg-green-100 text-green-800 border-green-200'
                      }`}
                    >
                      {action.status === 'PENDING' ? 'Chờ thực hiện' : 'Hoàn thành'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <span className="font-medium text-gray-700">Hành động:</span>
                      <span className="ml-2 text-gray-600">
                        {getActionTypeLabel(action.action_type)}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Thời gian:</span>
                      <span className="ml-2 text-gray-600">
                        {new Date(action.scheduled_datetime).toLocaleString('vi-VN')}
                      </span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Task ID:</span>
                      <span className="ml-2 text-gray-600 font-mono text-xs">{action.id}</span>
                    </div>
                    <div>
                      <span className="font-medium text-gray-700">Chiến dịch:</span>
                      <span className="ml-2 text-gray-600">
                        {action.campaign_name || 'Không có'}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Schedule Modal */}
      <Modal
        open={showScheduleModal}
        onClose={closeScheduleModal}
        title={isEditing ? 'Chỉnh sửa lịch trình' : 'Tạo lịch trình mới'}
      >
        <div className="space-y-6">
          {/* Movie Selection */}
          {!selectedMovie && (
            <div>
              <label className="mb-2 block text-sm font-medium text-gray-700">Chọn phim</label>
              <select
                value={selectedMovie?.id || ''}
                onChange={e => {
                  const movie = movies.find(m => m.id === parseInt(e.target.value));
                  setSelectedMovie(movie);
                }}
                className="block w-full text-gray-700 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
              >
                <option className="text-gray-700" value="">
                  Chọn phim...
                </option>
                {movies.map(movie => (
                  <option className="text-gray-700" key={movie.id} value={movie.id}>
                    {movie.title}
                  </option>
                ))}
              </select>
            </div>
          )}

          {selectedMovie && (
            <>
              {/* Selected Movie Display */}
              <div className="rounded-lg bg-gray-50 p-4">
                <h4 className="font-medium text-gray-900">{selectedMovie.title}</h4>
                <p className="text-sm text-gray-600">{selectedMovie.original_title}</p>
              </div>

              {/* Action Type - chỉ hiển thị khi tạo mới */}
              {!isEditing && (
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Loại hành động
                  </label>
                  <select
                    value={scheduleForm.action_type}
                    onChange={e =>
                      setScheduleForm({ ...scheduleForm, action_type: e.target.value })
                    }
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  >
                    <option value="publish">Xuất bản</option>
                    <option value="unpublish">Ẩn bài</option>
                    <option value="feature">Đánh dấu Featured</option>
                    <option value="unfeature">Bỏ Featured</option>
                  </select>
                </div>
              )}

              {/* Scheduled Date and Time */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Ngày thực hiện
                  </label>
                  <input
                    type="date"
                    value={scheduleForm.scheduled_date}
                    onChange={e =>
                      setScheduleForm({ ...scheduleForm, scheduled_date: e.target.value })
                    }
                    className="block w-full text-gray-700 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
                <div>
                  <label className="mb-2 block text-sm font-medium text-gray-700">
                    Giờ thực hiện
                  </label>
                  <input
                    type="time"
                    value={scheduleForm.scheduled_time}
                    onChange={e =>
                      setScheduleForm({ ...scheduleForm, scheduled_time: e.target.value })
                    }
                    className="block w-full text-gray-700 rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                  />
                </div>
              </div>

              {/* End Date and Time (for temporary actions) - chỉ hiển thị khi tạo mới */}
              {!isEditing &&
                (scheduleForm.action_type === 'feature' ||
                  scheduleForm.action_type === 'publish') && (
                  <>
                    <div className="flex items-center">
                      <input
                        type="checkbox"
                        checked={scheduleForm.auto_unschedule}
                        onChange={e =>
                          setScheduleForm({ ...scheduleForm, auto_unschedule: e.target.checked })
                        }
                        className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                      />
                      <label className="ml-2 text-sm text-gray-700">
                        Tự động hủy sau một khoảng thời gian
                      </label>
                    </div>

                    {scheduleForm.auto_unschedule && (
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <label className="mb-2 block text-sm font-medium text-gray-700">
                            Ngày kết thúc
                          </label>
                          <input
                            type="date"
                            value={scheduleForm.end_date}
                            onChange={e =>
                              setScheduleForm({ ...scheduleForm, end_date: e.target.value })
                            }
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                          />
                        </div>
                        <div>
                          <label className="mb-2 block text-sm font-medium text-gray-700">
                            Giờ kết thúc
                          </label>
                          <input
                            type="time"
                            value={scheduleForm.end_time}
                            onChange={e =>
                              setScheduleForm({ ...scheduleForm, end_time: e.target.value })
                            }
                            className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                          />
                        </div>
                      </div>
                    )}
                  </>
                )}

              {/* Campaign Information - chỉ hiển thị khi tạo mới */}
              {!isEditing && (
                <>
                  <div>
                    <label className="mb-2 block text-sm font-medium text-gray-700">
                      Tên chiến dịch (tùy chọn)
                    </label>
                    <input
                      type="text"
                      value={scheduleForm.campaign_name}
                      onChange={e =>
                        setScheduleForm({ ...scheduleForm, campaign_name: e.target.value })
                      }
                      placeholder="VD: Phim hot cuối tuần, Chiến dịch Tết 2024..."
                      className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Loại chiến dịch
                      </label>
                      <select
                        value={scheduleForm.campaign_type}
                        onChange={e =>
                          setScheduleForm({ ...scheduleForm, campaign_type: e.target.value })
                        }
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      >
                        <option value="feature">Feature</option>
                        <option value="promotion">Khuyến mãi</option>
                        <option value="seasonal">Theo mùa</option>
                        <option value="regular">Thường xuyên</option>
                      </select>
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium text-gray-700">
                        Mức độ ưu tiên
                      </label>
                      <input
                        type="number"
                        min="1"
                        max="10"
                        value={scheduleForm.priority}
                        onChange={e =>
                          setScheduleForm({ ...scheduleForm, priority: parseInt(e.target.value) })
                        }
                        className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                </>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={closeScheduleModal}
                  className="inline-flex justify-center rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 shadow-sm hover:bg-gray-50"
                >
                  Hủy
                </button>
                <button
                  type="button"
                  onClick={handleScheduleAction}
                  disabled={!scheduleForm.scheduled_date}
                  className="inline-flex justify-center rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <BoltIcon className="mr-2 size-4" />
                  {isEditing ? 'Cập nhật lịch trình' : 'Tạo lịch trình'}
                </button>
              </div>
            </>
          )}
        </div>
      </Modal>
    </div>
  );
};

export default SchedulingManagement;
