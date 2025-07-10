import {
  CheckCircleIcon,
  XCircleIcon,
  ChartBarIcon,
  Cog6ToothIcon,
  ArrowTrendingUpIcon,
  ArrowTrendingDownIcon,
} from '@heroicons/react/24/outline';

const DashboardOverview = ({ isAdmin: _isAdmin, isModerator: _isModerator }) => {
  const stats = [
    {
      title: 'Nội dung chờ duyệt',
      value: '23',
      change: '+5',
      changeType: 'increase',
      color: 'yellow',
    },
    {
      title: 'Báo cáo vi phạm',
      value: '12',
      change: '+3',
      changeType: 'increase',
      color: 'red',
    },
    {
      title: 'Đã duyệt hôm nay',
      value: '156',
      change: '+23',
      changeType: 'increase',
      color: 'green',
    },
    {
      title: 'Thời gian xử lý TB',
      value: '2.5h',
      change: '-0.3h',
      changeType: 'decrease',
      color: 'blue',
    },
  ];

  const recentActivities = [
    {
      id: 1,
      content: 'Đã duyệt review "Avengers: Endgame"',
      user: 'Moderator A',
      time: '2 phút trước',
    },
    {
      id: 2,
      content: 'Từ chối comment vi phạm',
      user: 'Moderator B',
      time: '5 phút trước',
    },
    {
      id: 3,
      content: 'Xử lý báo cáo spam',
      user: 'Moderator C',
      time: '10 phút trước',
    },
  ];

  const getStatusColor = status => {
    const colors = {
      yellow: 'bg-pink-50 border-pink-200 text-pink-700',
      red: 'bg-amber-50 border-amber-200 text-amber-700',
      green: 'bg-purple-50 border-purple-200 text-purple-700',
      blue: 'bg-gray-50 border-gray-200 text-gray-700',
    };
    return colors[status] || colors.blue;
  };

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat, index) => (
          <div key={index} className={`rounded-lg border p-4 ${getStatusColor(stat.color)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-purple-700 opacity-75">{stat.title}</p>
                <p className="mt-2 text-3xl font-bold text-purple-900">{stat.value}</p>
                <p className="mt-1 text-xs text-gray-600 opacity-75">{stat.description}</p>
              </div>
              <div className="flex items-center">
                {stat.changeType === 'increase' ? (
                  <ArrowTrendingUpIcon className="mr-1 size-4 text-green-600" />
                ) : (
                  <ArrowTrendingDownIcon className="mr-1 size-4 text-red-600" />
                )}
                <span
                  className={`text-xs font-medium ${
                    stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                  }`}
                >
                  {stat.change}
                </span>
                <span className="ml-1 text-xs text-gray-500 opacity-75">so với hôm qua</span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-semibold text-purple-900">Hoạt động gần đây</h3>
        <div className="space-y-4">
          {recentActivities.map((activity, index) => (
            <div
              key={index}
              className="flex items-start space-x-3 rounded-lg border border-pink-200 bg-gradient-to-r from-pink-50 to-amber-50 p-3"
            >
              <div className="mt-1 size-5 rounded-full bg-pink-600"></div>
              <div className="flex-1">
                <p className="text-sm font-medium text-purple-900">{activity.content}</p>
                <p className="text-xs text-pink-700">
                  {activity.time} • {activity.user}
                </p>
              </div>
            </div>
          ))}
        </div>
        <button className="mt-4 w-full text-sm font-medium text-pink-600 hover:text-pink-700">
          Xem tất cả hoạt động
        </button>
      </div>

      {/* Quick Actions */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-semibold text-purple-900">Hành động nhanh</h3>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
          <button className="flex w-full items-center rounded-lg bg-green-50 p-3 text-left transition-colors hover:bg-pink-50">
            <CheckCircleIcon className="mr-3 size-5 text-pink-600" />
            <div>
              <p className="font-medium text-purple-900">Duyệt tất cả</p>
              <p className="text-xs text-pink-700">Duyệt nội dung chờ</p>
            </div>
          </button>
          <button className="flex w-full items-center rounded-lg bg-red-50 p-3 text-left transition-colors hover:bg-pink-50">
            <XCircleIcon className="mr-3 size-5 text-pink-600" />
            <div>
              <p className="font-medium text-purple-900">Từ chối vi phạm</p>
              <p className="text-xs text-pink-700">Loại bỏ nội dung xấu</p>
            </div>
          </button>
          <button className="flex w-full items-center rounded-lg bg-blue-50 p-3 text-left transition-colors hover:bg-pink-50">
            <ChartBarIcon className="mr-3 size-5 text-purple-600" />
            <div>
              <p className="font-medium text-purple-900">Xem báo cáo</p>
              <p className="text-xs text-pink-700">Thống kê chi tiết</p>
            </div>
          </button>
          <button className="flex w-full items-center rounded-lg bg-purple-50 p-3 text-left transition-colors hover:bg-pink-50">
            <Cog6ToothIcon className="mr-3 size-5 text-purple-600" />
            <div>
              <p className="font-medium text-purple-900">Cài đặt</p>
              <p className="text-xs text-pink-700">Cấu hình hệ thống</p>
            </div>
          </button>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="rounded-lg bg-white p-6 shadow">
        <h3 className="mb-4 text-lg font-semibold text-purple-900">Hiệu suất kiểm duyệt</h3>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="text-center">
            <div className="text-3xl font-bold text-green-600">95%</div>
            <p className="mt-1 text-sm text-gray-600">Tỷ lệ chính xác</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-blue-600">2.3 phút</div>
            <p className="mt-1 text-sm text-gray-600">Thời gian xử lý TB</p>
          </div>
          <div className="text-center">
            <div className="text-3xl font-bold text-purple-600">156</div>
            <p className="mt-1 text-sm text-gray-600">Nội dung/ngày</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardOverview;
