import {
  ClockIcon,
  CalendarIcon,
  TagIcon,
  ChartBarIcon,
  EyeIcon,
  MagnifyingGlassIcon,
  DocumentCheckIcon,
  GlobeAltIcon,
  ShieldCheckIcon,
  UserGroupIcon,
  StarIcon,
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import Modal from './Modal';

const MetricItem = ({ icon: Icon, label, value }) => (
  <div className="flex items-center space-x-2">
    <Icon className="size-5 text-gray-400" />
    <span className="text-sm text-gray-500">{label}:</span>
    <span className="text-sm font-medium text-gray-900">{value}</span>
  </div>
);

const MovieDetailsModal = ({ movie, open, onClose }) => {
  if (!movie) return null;

  const {
    title,
    original_title,
    release_date,
    runtime,
    genres,
    overviews,
    production_metrics,
    approval_info,
    admin_control,
    content_completeness,
    quality_score,
  } = movie;

  const formatDate = date => {
    if (!date) return 'N/A';
    return new Date(date).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getApprovalStatusColor = status => {
    const colors = {
      APPROVED: 'text-green-600 bg-green-50 border border-green-200 px-3 py-1 rounded-full',
      PENDING: 'text-yellow-600 bg-yellow-50 border border-yellow-200 px-3 py-1 rounded-full',
      REJECTED: 'text-red-600 bg-red-50 border border-red-200 px-3 py-1 rounded-full',
      NEEDS_REVIEW: 'text-orange-600 bg-orange-50 border border-orange-200 px-3 py-1 rounded-full',
    };
    return (
      colors[status] || 'text-gray-600 bg-gray-50 border border-gray-200 px-3 py-1 rounded-full'
    );
  };

  const getApprovalIcon = status => {
    const icons = {
      APPROVED: CheckCircleIcon,
      PENDING: ClockIcon,
      REJECTED: XCircleIcon,
      NEEDS_REVIEW: ExclamationTriangleIcon,
    };
    return icons[status] || ClockIcon;
  };

  const ApprovalIcon = getApprovalIcon(approval_info?.status);

  return (
    <Modal open={open} onClose={onClose} title="Chi tiết phim">
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        {/* Column 1: Basic Info & Overview */}
        <div className="space-y-6 lg:col-span-2">
          {/* Basic Info */}
          <div className="space-y-4">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-2xl font-bold text-gray-900">{title}</h3>
                {original_title && original_title !== title && (
                  <p className="mt-1 text-sm text-gray-500">{original_title}</p>
                )}
              </div>
              <div className={`flex items-center ${getApprovalStatusColor(approval_info?.status)}`}>
                <ApprovalIcon className="mr-1.5 size-5" />
                <span className="text-sm font-medium">{approval_info?.status || 'PENDING'}</span>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <MetricItem
                icon={CalendarIcon}
                label="Ngày phát hành"
                value={formatDate(release_date)}
              />
              <MetricItem
                icon={ClockIcon}
                label="Thời lượng"
                value={runtime ? `${runtime} phút` : 'N/A'}
              />
              <MetricItem
                icon={TagIcon}
                label="Thể loại"
                value={genres?.map(g => g.name).join(', ') || 'N/A'}
              />
              <MetricItem
                icon={GlobeAltIcon}
                label="Trạng thái"
                value={admin_control?.visibility_status || 'DRAFT'}
              />
            </div>
          </div>

          {/* Overview */}
          <div className="space-y-2">
            <h4 className="text-lg font-semibold text-gray-900">Nội dung</h4>
            <div className="space-y-3 rounded-lg bg-gray-50 p-4">
              {overviews?.vi && (
                <p className="text-sm">
                  <span className="font-medium text-gray-700">Tiếng Việt:</span>{' '}
                  <span className="text-gray-900">{overviews.vi}</span>
                </p>
              )}
              {overviews?.en && (
                <p className="text-sm">
                  <span className="font-medium text-gray-700">English:</span>{' '}
                  <span className="text-gray-900">{overviews.en}</span>
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Column 2: Metrics & Admin Info */}
        <div className="space-y-6">
          {/* Metrics */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-gray-900">Chỉ số hiệu suất</h4>
            <div className="space-y-3 rounded-lg bg-gray-50 p-4">
              <MetricItem
                icon={ChartBarIcon}
                label="Điểm hiệu suất"
                value={(production_metrics?.performance_score || 0).toFixed(1)}
              />
              <MetricItem
                icon={DocumentCheckIcon}
                label="Độ hoàn thiện"
                value={`${(content_completeness || 0).toFixed(1)}%`}
              />
              <MetricItem
                icon={EyeIcon}
                label="Lượt xem trang chủ"
                value={production_metrics?.homepage_views?.toLocaleString() || 0}
              />
              <MetricItem
                icon={MagnifyingGlassIcon}
                label="Lượt xuất hiện tìm kiếm"
                value={production_metrics?.search_appearances?.toLocaleString() || 0}
              />
            </div>
          </div>

          {/* Admin Control */}
          <div className="space-y-4">
            <h4 className="text-lg font-semibold text-gray-900">Thông tin quản trị</h4>
            <div className="space-y-3 rounded-lg bg-gray-50 p-4">
              <MetricItem
                icon={UserGroupIcon}
                label="Người duyệt"
                value={approval_info?.approved_by || 'Chưa duyệt'}
              />
              <MetricItem
                icon={CalendarIcon}
                label="Ngày duyệt"
                value={formatDate(approval_info?.approved_at)}
              />
              <MetricItem
                icon={StarIcon}
                label="Featured"
                value={admin_control?.admin_featured ? 'Có' : 'Không'}
              />
              <MetricItem
                icon={ShieldCheckIcon}
                label="Chất lượng"
                value={`${(quality_score || 0).toFixed(1)}/10`}
              />
            </div>
          </div>
        </div>
      </div>
    </Modal>
  );
};

export default MovieDetailsModal;
