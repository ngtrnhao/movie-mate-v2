import React, { useState, useEffect } from 'react';
import { getCommunityStats } from '../../../api/movieService';

const ModerationStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchModerationStats();
  }, []);

  const fetchModerationStats = async () => {
    try {
      setLoading(true);
      // For now, using community stats as placeholder
      // TODO: Create proper moderator API endpoint for moderation stats
      const response = await getCommunityStats();
      setStats(response);
    } catch (err) {
      setError('Không thể tải thống kê kiểm duyệt');
      console.error('Error fetching moderation stats:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {[1, 2, 3].map(i => (
              <div key={i} className="bg-gray-200 h-32 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Lỗi</h3>
              <div className="mt-2 text-sm text-red-700">{error}</div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-6">
        <p className="text-gray-500">Không có dữ liệu</p>
      </div>
    );
  }

  const StatCard = ({ title, value, icon, color, description }) => (
    <div className="bg-white overflow-hidden shadow rounded-lg">
      <div className="p-5">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <div className={`w-8 h-8 rounded-md flex items-center justify-center ${color}`}>
              <span className="text-white text-lg">{icon}</span>
            </div>
          </div>
          <div className="ml-5 w-0 flex-1">
            <dl>
              <dt className="text-sm font-medium text-gray-500 truncate">{title}</dt>
              <dd className="text-lg font-medium text-gray-900">{value}</dd>
              {description && <dd className="text-sm text-gray-500">{description}</dd>}
            </dl>
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Thống kê kiểm duyệt</h2>
        <p className="text-gray-600">Thống kê hoạt động kiểm duyệt nội dung</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <StatCard
          title="Review mới (30 ngày)"
          value={stats.new_reviews_30d?.toLocaleString() || '0'}
          icon="📝"
          color="bg-blue-500"
          description="Review được tạo trong 30 ngày qua"
        />
        <StatCard
          title="Review có vấn đề"
          value={stats.low_helpful_reviews?.toLocaleString() || '0'}
          icon="⚠️"
          color="bg-yellow-500"
          description="Review có tỷ lệ hữu ích thấp"
        />
        <StatCard
          title="Hành động kiểm duyệt"
          value={stats.moderation_actions?.toLocaleString() || '0'}
          icon="✅"
          color="bg-green-500"
          description="Số hành động kiểm duyệt đã thực hiện"
        />
      </div>

      {/* Language Distribution */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">
            Review theo ngôn ngữ (30 ngày)
          </h3>
          <div className="space-y-3">
            {stats.reviews_by_language?.map((lang, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-500">
                  {lang.language === 'en'
                    ? 'English'
                    : lang.language === 'vi'
                      ? 'Tiếng Việt'
                      : lang.language.toUpperCase()}
                </span>
                <div className="flex items-center">
                  <div className="w-32 bg-gray-200 rounded-full h-2 mr-3">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${Math.min((lang.count / 10) * 100, 100)}%` }}
                    ></div>
                  </div>
                  <span className="text-sm font-semibold text-gray-900 w-8 text-right">
                    {lang.count}
                  </span>
                </div>
              </div>
            ))}
          </div>
          {(!stats.reviews_by_language || stats.reviews_by_language.length === 0) && (
            <div className="text-center py-8">
              <p className="text-gray-500">Không có dữ liệu review theo ngôn ngữ</p>
            </div>
          )}
        </div>
      </div>

      {/* Moderation Activity */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Hoạt động kiểm duyệt</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="text-center">
              <div className="text-3xl font-bold text-green-600 mb-2">
                {stats.new_reviews_30d || '0'}
              </div>
              <div className="text-sm text-gray-500">Review cần kiểm duyệt</div>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold text-blue-600 mb-2">
                {stats.moderation_actions || '0'}
              </div>
              <div className="text-sm text-gray-500">Hành động đã thực hiện</div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-3">Hướng dẫn kiểm duyệt</h4>
            <div className="bg-gray-50 rounded-lg p-4">
              <ul className="text-sm text-gray-600 space-y-2">
                <li className="flex items-start">
                  <span className="text-green-500 mr-2">✓</span>
                  <span>Phê duyệt review có nội dung chất lượng, không vi phạm</span>
                </li>
                <li className="flex items-start">
                  <span className="text-red-500 mr-2">✗</span>
                  <span>Từ chối review spam, quảng cáo, hoặc nội dung không phù hợp</span>
                </li>
                <li className="flex items-start">
                  <span className="text-yellow-500 mr-2">⚠</span>
                  <span>Chú ý review có tỷ lệ hữu ích thấp, có thể cần kiểm tra thêm</span>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ModerationStats;
