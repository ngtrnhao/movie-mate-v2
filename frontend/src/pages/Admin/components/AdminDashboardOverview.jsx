import React, { useState, useEffect } from 'react';

const AdminDashboardOverview = () => {
  const [stats, setStats] = useState({
    systemStats: {},
    userStats: {},
    contentStats: {},
    moderationStats: {},
    securityStats: {},
  });
  const [recentActivity, setRecentActivity] = useState([]);
  const [systemHealth, setSystemHealth] = useState({});
  const [loading, setLoading] = useState(true);

  // Mock data - replace with actual API calls
  useEffect(() => {
    const mockStats = {
      systemStats: {
        uptime: 99.8,
        responseTime: 245,
        errorRate: 0.2,
        serverLoad: 65,
        databaseConnections: 45,
        cacheHitRate: 92.5,
      },
      userStats: {
        totalUsers: 1250,
        newUsers: 45,
        activeUsers: 890,
        bannedUsers: 23,
        moderators: 8,
        admins: 2,
        userGrowth: 12.5,
        retentionRate: 78.3,
      },
      contentStats: {
        totalMovies: 8934,
        totalReviews: 15678,
        totalComments: 45678,
        reportedContent: 234,
        pendingModeration: 47,
        contentGrowth: 8.3,
        averageRating: 4.2,
      },
      moderationStats: {
        pendingReviews: 47,
        processedToday: 156,
        averageResponseTime: 2.3,
        moderatorEfficiency: 94.2,
        autoModerationRate: 67.8,
        falsePositiveRate: 2.1,
      },
      securityStats: {
        failedLogins: 12,
        suspiciousActivities: 5,
        blockedIPs: 8,
        securityAlerts: 2,
        lastBackup: '2024-01-15T10:00:00Z',
        backupStatus: 'success',
      },
    };

    const mockActivity = [
      {
        id: 1,
        type: 'system',
        action: 'Backup completed',
        content: 'System backup completed successfully',
        user: 'System',
        time: '2 phút trước',
        priority: 'low',
      },
      {
        id: 2,
        type: 'user',
        action: 'User banned',
        content: 'Permanently banned user "spam_user"',
        user: 'Admin',
        time: '15 phút trước',
        priority: 'high',
      },
      {
        id: 3,
        type: 'moderation',
        action: 'Moderator promoted',
        content: 'Promoted "john_doe" to Moderator',
        user: 'Admin',
        time: '1 giờ trước',
        priority: 'medium',
      },
      {
        id: 4,
        type: 'security',
        action: 'Security alert',
        content: 'Multiple failed login attempts detected',
        user: 'System',
        time: '2 giờ trước',
        priority: 'high',
      },
      {
        id: 5,
        type: 'content',
        action: 'Bulk approval',
        content: 'Approved 25 items in bulk',
        user: 'Admin',
        time: '3 giờ trước',
        priority: 'medium',
      },
    ];

    const mockSystemHealth = {
      database: { status: 'healthy', responseTime: 45, connections: 45 },
      cache: { status: 'healthy', hitRate: 92.5, memory: 78 },
      api: { status: 'healthy', responseTime: 245, requests: 1250 },
      storage: { status: 'warning', usage: 85, available: 15 },
      queue: { status: 'busy', pending: 47, processed: 156 },
    };

    setTimeout(() => {
      setStats(mockStats);
      setRecentActivity(mockActivity);
      setSystemHealth(mockSystemHealth);
      setLoading(false);
    }, 1000);
  }, []);

  const getStatusColor = status => {
    switch (status) {
      case 'healthy':
        return 'bg-green-100 text-green-800';
      case 'warning':
        return 'bg-yellow-100 text-yellow-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      case 'busy':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getActivityIcon = type => {
    switch (type) {
      case 'system':
        return '🖥️';
      case 'user':
        return '👤';
      case 'moderation':
        return '🛡️';
      case 'security':
        return '🔒';
      case 'content':
        return '📝';
      default:
        return '📋';
    }
  };

  const getPriorityColor = priority => {
    switch (priority) {
      case 'high':
        return 'text-red-600';
      case 'medium':
        return 'text-yellow-600';
      case 'low':
        return 'text-green-600';
      default:
        return 'text-gray-600';
    }
  };

  const formatDate = dateString => {
    const date = new Date(dateString);
    return date.toLocaleDateString('vi-VN', {
      day: '2-digit',
      month: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-purple-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-purple-600 to-indigo-600 rounded-lg p-6 text-white">
        <h2 className="text-2xl font-bold mb-2">Chào mừng, Admin! 👑</h2>
        <p className="text-purple-100">
          Tổng quan hệ thống quản trị Movie Recommendation - Quản lý toàn diện hệ thống
        </p>
      </div>

      {/* System Health Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-green-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Uptime</p>
              <p className="text-3xl font-bold text-green-600">{stats.systemStats.uptime}%</p>
            </div>
            <div className="bg-green-100 rounded-full p-3">
              <span className="text-2xl">🟢</span>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">Hệ thống ổn định</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-blue-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Người dùng hoạt động</p>
              <p className="text-3xl font-bold text-blue-600">{stats.userStats.activeUsers}</p>
            </div>
            <div className="bg-blue-100 rounded-full p-3">
              <span className="text-2xl">👥</span>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">+{stats.userStats.newUsers} mới hôm nay</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-orange-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Chờ kiểm duyệt</p>
              <p className="text-3xl font-bold text-orange-600">
                {stats.moderationStats.pendingReviews}
              </p>
            </div>
            <div className="bg-orange-100 rounded-full p-3">
              <span className="text-2xl">⏳</span>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">Cần xử lý</p>
        </div>

        <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-purple-500">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Hiệu suất hệ thống</p>
              <p className="text-3xl font-bold text-purple-600">
                {stats.moderationStats.moderatorEfficiency}%
              </p>
            </div>
            <div className="bg-purple-100 rounded-full p-3">
              <span className="text-2xl">⚡</span>
            </div>
          </div>
          <p className="text-sm text-gray-500 mt-2">Moderator efficiency</p>
        </div>
      </div>

      {/* Detailed Stats Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* User Management */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">👥</span>
            Quản lý người dùng
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Tổng người dùng</span>
              <span className="text-sm font-medium text-gray-900">
                {stats.userStats.totalUsers.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Moderators</span>
              <span className="text-sm font-medium text-blue-600">
                {stats.userStats.moderators}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Admins</span>
              <span className="text-sm font-medium text-purple-600">{stats.userStats.admins}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Bị cấm</span>
              <span className="text-sm font-medium text-red-600">
                {stats.userStats.bannedUsers}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Tỷ lệ giữ chân</span>
              <span className="text-sm font-medium text-green-600">
                {stats.userStats.retentionRate}%
              </span>
            </div>
          </div>
        </div>

        {/* Content Management */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">📝</span>
            Quản lý nội dung
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Tổng phim</span>
              <span className="text-sm font-medium text-gray-900">
                {stats.contentStats.totalMovies.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Đánh giá</span>
              <span className="text-sm font-medium text-gray-900">
                {stats.contentStats.totalReviews.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Bình luận</span>
              <span className="text-sm font-medium text-gray-900">
                {stats.contentStats.totalComments.toLocaleString()}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Bị báo cáo</span>
              <span className="text-sm font-medium text-red-600">
                {stats.contentStats.reportedContent}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Đánh giá TB</span>
              <span className="text-sm font-medium text-yellow-600">
                {stats.contentStats.averageRating}/5
              </span>
            </div>
          </div>
        </div>

        {/* System Health */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🖥️</span>
            Tình trạng hệ thống
          </h3>
          <div className="space-y-4">
            {Object.entries(systemHealth).map(([service, data]) => (
              <div key={service} className="flex justify-between items-center">
                <span className="text-sm text-gray-600 capitalize">{service}</span>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(data.status)}`}
                  >
                    {data.status}
                  </span>
                  {service === 'database' && (
                    <span className="text-xs text-gray-500">{data.responseTime}ms</span>
                  )}
                  {service === 'cache' && (
                    <span className="text-xs text-gray-500">{data.hitRate}%</span>
                  )}
                  {service === 'storage' && (
                    <span className="text-xs text-gray-500">{data.usage}%</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Security & Moderation */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Security Overview */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🔒</span>
            Bảo mật hệ thống
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Đăng nhập thất bại</span>
              <span className="text-sm font-medium text-red-600">
                {stats.securityStats.failedLogins}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Hoạt động nghi vấn</span>
              <span className="text-sm font-medium text-orange-600">
                {stats.securityStats.suspiciousActivities}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">IP bị chặn</span>
              <span className="text-sm font-medium text-red-600">
                {stats.securityStats.blockedIPs}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Cảnh báo bảo mật</span>
              <span className="text-sm font-medium text-red-600">
                {stats.securityStats.securityAlerts}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Backup cuối</span>
              <span className="text-sm font-medium text-green-600">
                {formatDate(stats.securityStats.lastBackup)}
              </span>
            </div>
          </div>
        </div>

        {/* Moderation Performance */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🛡️</span>
            Hiệu suất kiểm duyệt
          </h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Đã xử lý hôm nay</span>
              <span className="text-sm font-medium text-green-600">
                {stats.moderationStats.processedToday}
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Thời gian phản hồi TB</span>
              <span className="text-sm font-medium text-blue-600">
                {stats.moderationStats.averageResponseTime}h
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Tự động kiểm duyệt</span>
              <span className="text-sm font-medium text-green-600">
                {stats.moderationStats.autoModerationRate}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">False positive</span>
              <span className="text-sm font-medium text-orange-600">
                {stats.moderationStats.falsePositiveRate}%
              </span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-sm text-gray-600">Hiệu suất tổng thể</span>
              <span className="text-sm font-medium text-purple-600">
                {stats.moderationStats.moderatorEfficiency}%
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Hoạt động gần đây</h3>
        <div className="space-y-4">
          {recentActivity.map(activity => (
            <div key={activity.id} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
              <div className="flex-shrink-0">
                <span className="text-2xl">{getActivityIcon(activity.type)}</span>
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm text-gray-900">
                    <span className={`font-medium ${getPriorityColor(activity.priority)}`}>
                      {activity.action}
                    </span>
                    {': '}
                    {activity.content}
                  </p>
                  <span
                    className={`px-2 py-1 rounded-full text-xs font-medium ${getPriorityColor(activity.priority).replace('text-', 'bg-').replace('-600', '-100')} ${getPriorityColor(activity.priority)}`}
                  >
                    {activity.priority}
                  </span>
                </div>
                <p className="text-xs text-gray-500 mt-1">
                  bởi {activity.user} • {activity.time}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Thao tác nhanh</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <button className="flex items-center justify-center px-4 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <span className="mr-2">👥</span>
            Quản lý người dùng
          </button>
          <button className="flex items-center justify-center px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
            <span className="mr-2">📊</span>
            Xem Analytics
          </button>
          <button className="flex items-center justify-center px-4 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors">
            <span className="mr-2">💾</span>
            Backup hệ thống
          </button>
          <button className="flex items-center justify-center px-4 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors">
            <span className="mr-2">⚙️</span>
            Cài đặt hệ thống
          </button>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboardOverview;
