import { useState, useEffect } from 'react';
import {
  ExclamationTriangleIcon,
  FlagIcon,
  ClockIcon,
  CheckIcon,
  XMarkIcon,
  EyeIcon,
  MagnifyingGlassIcon,
} from '@heroicons/react/24/outline';
import { getReviewReports, moderateReview } from '../../../api/movieService';

const ReportsList = ({ isAdmin }) => {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    reason: 'all',
    priority: 'all',
    status: 'all',
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [stats, setStats] = useState({
    total_reported_reviews: 0,
    high_priority: 0,
    medium_priority: 0,
    low_priority: 0,
    reason_stats: {},
  });
  const [expandedContent, setExpandedContent] = useState(new Set());

  // Fetch reports from API
  const fetchReports = async () => {
    try {
      setLoading(true);
      const data = await getReviewReports(currentPage, 20);
      setReports(data.data || []);
      setTotalPages(data.total_pages || 1);
      setStats(data.stats || {});
    } catch (error) {
      console.error('Error fetching reports:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReports();
  }, [currentPage]);

  // Filter reports
  const filteredReports = reports.filter(report => {
    if (
      filters.reason !== 'all' &&
      !report.report_summary?.unique_reasons?.includes(filters.reason)
    ) {
      return false;
    }
    if (filters.priority !== 'all' && report.report_summary?.priority !== filters.priority) {
      return false;
    }
    if (filters.status !== 'all') {
      if (filters.status === 'pending' && report.is_approved !== null) {
        return false;
      }
      if (filters.status === 'resolved' && report.is_approved === null) {
        return false;
      }
    }
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        report.title?.toLowerCase().includes(searchLower) ||
        report.content?.toLowerCase().includes(searchLower) ||
        report.user?.username?.toLowerCase().includes(searchLower) ||
        report.report_summary?.reporters?.some(r => r.toLowerCase().includes(searchLower))
      );
    }
    return true;
  });

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'bg-red-100 text-red-700 border-red-200';
      case 'medium':
        return 'bg-yellow-100 text-yellow-700 border-yellow-200';
      case 'low':
        return 'bg-green-100 text-green-700 border-green-200';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-200';
    }
  };

  const getReasonColor = reason => {
    switch (reason) {
      case 'offensive':
        return 'bg-red-100 text-red-700';
      case 'abuse':
        return 'bg-red-100 text-red-700';
      case 'spam':
        return 'bg-yellow-100 text-yellow-700';
      case 'spoiler':
        return 'bg-purple-100 text-purple-700';
      case 'irrelevant':
        return 'bg-blue-100 text-blue-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const generateReportTitle = report => {
    // Luôn sinh title động, không dùng title gốc nữa
    // Lấy thông tin báo cáo
    const reasons = report.report_summary?.unique_reasons || [];
    const priority = report.report_summary?.priority || 'low';
    const movieTitle = report.movie?.title || 'Phim không xác định';
    const totalReports = report.report_summary?.total_reports || 0;
    const username = report.user?.username || 'Người dùng không xác định';

    // Tạo title dựa trên lý do báo cáo chính
    let reasonText = '';
    let prefix = '';

    if (reasons.includes('offensive')) {
      reasonText = 'Ngôn ngữ xúc phạm';
      prefix = '🚨';
    } else if (reasons.includes('abuse')) {
      reasonText = 'Lạm dụng/Quấy rối';
      prefix = '⚠️';
    } else if (reasons.includes('spam')) {
      reasonText = 'Spam/Quảng cáo';
      prefix = '📢';
    } else if (reasons.includes('spoiler')) {
      reasonText = 'Chứa spoiler';
      prefix = '🎬';
    } else if (reasons.includes('irrelevant')) {
      reasonText = 'Nội dung không liên quan';
      prefix = '❓';
    } else {
      reasonText = 'Vi phạm khác';
      prefix = '🚫';
    }

    // Tạo title với format phù hợp
    let title = `${prefix} ${reasonText}`;

    // Thêm thông tin về review
    title += ` - Review của ${username} cho "${movieTitle}"`;

    // Thêm thông tin về số lượng báo cáo nếu có nhiều
    if (totalReports > 1) {
      title += ` (${totalReports} người báo cáo)`;
    }

    // Thêm mức độ ưu tiên nếu cao
    if (priority === 'high') {
      title += ' 🔥';
    } else if (priority === 'medium') {
      title += ' ⚡';
    }

    return title;
  };

  const handleModerate = async (reviewId, action) => {
    try {
      const reason = action === 'approve' ? 'Approved by moderator' : 'Rejected due to violations';
      await moderateReview(reviewId, action, reason);

      // Refresh reports
      fetchReports();
    } catch (error) {
      console.error('Error moderating review:', error);
    }
  };

  const formatDate = dateString => {
    return new Date(dateString).toLocaleDateString('vi-VN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const toggleContentExpansion = reportId => {
    setExpandedContent(prev => {
      const newSet = new Set(prev);
      if (newSet.has(reportId)) {
        newSet.delete(reportId);
      } else {
        newSet.add(reportId);
      }
      return newSet;
    });
  };

  const isContentExpanded = reportId => {
    return expandedContent.has(reportId);
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="size-12 animate-spin rounded-full border-b-2 border-blue-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-4">
        <div className="rounded-lg border-l-4 border-red-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <FlagIcon className="mr-3 size-6 text-red-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Tổng báo cáo</p>
              <p className="text-2xl font-bold text-gray-900">{stats.total_reported_reviews}</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border-l-4 border-red-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <ExclamationTriangleIcon className="mr-3 size-6 text-red-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên cao</p>
              <p className="text-2xl font-bold text-gray-900">{stats.high_priority}</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border-l-4 border-yellow-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <ClockIcon className="mr-3 size-6 text-yellow-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên trung bình</p>
              <p className="text-2xl font-bold text-gray-900">{stats.medium_priority}</p>
            </div>
          </div>
        </div>
        <div className="rounded-lg border-l-4 border-green-500 bg-white p-4 shadow">
          <div className="flex items-center">
            <CheckIcon className="mr-3 size-6 text-green-600" />
            <div>
              <p className="text-sm font-medium text-gray-600">Ưu tiên thấp</p>
              <p className="text-2xl font-bold text-gray-900">{stats.low_priority}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="rounded-lg bg-white p-4 shadow">
        <div className="flex flex-col gap-4 md:flex-row">
          <div className="flex-1">
            <label className="mb-1 block text-sm font-medium text-blue-700">Tìm kiếm</label>
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-blue-400" />
              <input
                type="text"
                placeholder="Tìm kiếm báo cáo..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="w-full rounded-lg border border-gray-300 bg-white py-2 pl-10 pr-4 text-gray-900 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Lý do</label>
              <select
                value={filters.reason}
                onChange={e => setFilters({ ...filters, reason: e.target.value })}
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              >
                <option value="all" className="text-gray-900">
                  Tất cả lý do
                </option>
                <option value="offensive" className="text-red-700">
                  Ngôn ngữ xúc phạm
                </option>
                <option value="abuse" className="text-red-700">
                  Lạm dụng
                </option>
                <option value="spam" className="text-yellow-700">
                  Spam
                </option>
                <option value="spoiler" className="text-purple-700">
                  Spoiler
                </option>
                <option value="irrelevant" className="text-blue-700">
                  Không liên quan
                </option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Ưu tiên</label>
              <select
                value={filters.priority}
                onChange={e => setFilters({ ...filters, priority: e.target.value })}
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              >
                <option value="all" className="text-gray-900">
                  Tất cả ưu tiên
                </option>
                <option value="high" className="text-red-700">
                  Cao
                </option>
                <option value="medium" className="text-orange-700">
                  Trung bình
                </option>
                <option value="low" className="text-green-700">
                  Thấp
                </option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-blue-700">Trạng thái</label>
              <select
                value={filters.status}
                onChange={e => setFilters({ ...filters, status: e.target.value })}
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-transparent focus:ring-2 focus:ring-blue-500"
              >
                <option value="all" className="text-gray-900">
                  Tất cả trạng thái
                </option>
                <option value="pending" className="text-yellow-700">
                  Chờ xử lý
                </option>
                <option value="resolved" className="text-green-700">
                  Đã xử lý
                </option>
              </select>
            </div>
          </div>
        </div>
      </div>

      {/* Reports List */}
      <div className="rounded-lg bg-white shadow">
        <div className="border-b border-gray-200 px-6 py-4">
          <h3 className="text-lg font-medium text-gray-900">
            Danh sách báo cáo ({filteredReports.length})
          </h3>
        </div>
        <div className="divide-y divide-gray-200">
          {filteredReports.length === 0 ? (
            <div className="px-6 py-8 text-center">
              <FlagIcon className="mx-auto mb-4 size-12 text-gray-400" />
              <p className="text-gray-500">Không có báo cáo nào</p>
            </div>
          ) : (
            filteredReports.map(report => (
              <div key={report.id} className="p-6 transition-colors hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="mb-2 flex items-center gap-3">
                      <h4 className="text-lg font-medium text-gray-900">
                        {generateReportTitle(report)}
                      </h4>
                      <span
                        className={`rounded-full border px-2 py-1 text-xs font-medium ${getPriorityColor(report.report_summary?.priority)}`}
                      >
                        {report.report_summary?.priority === 'high'
                          ? 'Cao'
                          : report.report_summary?.priority === 'medium'
                            ? 'Trung bình'
                            : 'Thấp'}
                      </span>
                    </div>

                    <div className="mb-3 text-sm text-gray-600">
                      <div className="mb-2">
                        <strong>Nội dung:</strong>
                        <div className="mt-1 whitespace-pre-wrap rounded-lg bg-gray-50 p-3 text-gray-700">
                          {isContentExpanded(report.id)
                            ? report.content || 'Không có nội dung'
                            : report.content?.length > 300
                              ? `${report.content.substring(0, 300)}...`
                              : report.content || 'Không có nội dung'}
                        </div>
                        {report.content && report.content.length > 300 && (
                          <button
                            onClick={() => toggleContentExpansion(report.id)}
                            className="mt-2 text-xs font-medium text-blue-600 hover:text-blue-800"
                          >
                            {isContentExpanded(report.id) ? 'Thu gọn' : 'Xem thêm'}
                          </button>
                        )}
                      </div>
                      <p className="mb-1">
                        <strong>Tác giả:</strong> {report.user?.username}
                      </p>
                      <p className="mb-1">
                        <strong>Số báo cáo:</strong> {report.report_summary?.total_reports}
                      </p>
                      <p className="mb-1">
                        <strong>Người báo cáo:</strong>{' '}
                        {report.report_summary?.reporters?.join(', ')}
                      </p>
                      <p className="mb-1">
                        <strong>Báo cáo cuối:</strong>{' '}
                        {formatDate(report.report_summary?.latest_report)}
                      </p>
                    </div>

                    <div className="mb-4 flex flex-wrap gap-2">
                      {report.report_summary?.unique_reasons?.map(reason => (
                        <span
                          key={reason}
                          className={`rounded-full px-2 py-1 text-xs font-medium ${getReasonColor(reason)}`}
                        >
                          {reason === 'offensive'
                            ? 'Xúc phạm'
                            : reason === 'abuse'
                              ? 'Lạm dụng'
                              : reason === 'spam'
                                ? 'Spam'
                                : reason === 'spoiler'
                                  ? 'Spoiler'
                                  : reason === 'irrelevant'
                                    ? 'Không liên quan'
                                    : reason}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>Tạo lúc: {formatDate(report.created_at)}</span>
                      {report.is_approved !== null && (
                        <span
                          className={`rounded-full px-2 py-1 text-xs font-medium ${
                            report.is_approved
                              ? 'bg-green-100 text-green-700'
                              : 'bg-red-100 text-red-700'
                          }`}
                        >
                          {report.is_approved ? 'Đã duyệt' : 'Đã từ chối'}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="ml-4 flex flex-col gap-2">
                    <button
                      onClick={() => handleModerate(report.id, 'approve')}
                      className="inline-flex items-center rounded-md border border-transparent bg-green-600 px-3 py-2 text-sm font-medium text-white hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 focus:ring-offset-2"
                    >
                      <CheckIcon className="mr-1 size-4" />
                      Duyệt
                    </button>
                    <button
                      onClick={() => handleModerate(report.id, 'reject')}
                      className="inline-flex items-center rounded-md border border-transparent bg-red-600 px-3 py-2 text-sm font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2"
                    >
                      <XMarkIcon className="mr-1 size-4" />
                      Từ chối
                    </button>
                    <button
                      onClick={() => window.open(`/movies/${report.movie?.id}`, '_blank')}
                      className="inline-flex items-center rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                    >
                      <EyeIcon className="mr-1 size-4" />
                      Xem
                    </button>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between rounded-lg bg-white px-6 py-4 shadow">
          <div className="text-sm text-gray-700">
            Trang {currentPage} của {totalPages}
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Trước
            </button>
            <button
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
            >
              Sau
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ReportsList;
