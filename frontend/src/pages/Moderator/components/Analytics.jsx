import React, { useState } from 'react';

const Analytics = () => {
  const [timeRange, setTimeRange] = useState('week');

  const stats = [
    {
      title: 'Tổng nội dung xử lý',
      value: '1,234',
      change: '+12%',
      changeType: 'increase',
      icon: '📊',
      color: 'blue',
    },
    {
      title: 'Thời gian xử lý TB',
      value: '2.3 phút',
      change: '-15%',
      changeType: 'decrease',
      icon: '⏱️',
      color: 'green',
    },
    {
      title: 'Tỷ lệ chính xác',
      value: '95.2%',
      change: '+2.1%',
      changeType: 'increase',
      icon: '🎯',
      color: 'purple',
    },
    {
      title: 'Nội dung vi phạm',
      value: '8.7%',
      change: '-3.2%',
      changeType: 'decrease',
      icon: '🚨',
      color: 'red',
    },
  ];

  const chartData = {
    daily: [
      { day: 'T2', processed: 45, violations: 3, accuracy: 93 },
      { day: 'T3', processed: 52, violations: 4, accuracy: 92 },
      { day: 'T4', processed: 38, violations: 2, accuracy: 95 },
      { day: 'T5', processed: 61, violations: 5, accuracy: 92 },
      { day: 'T6', processed: 48, violations: 3, accuracy: 94 },
      { day: 'T7', processed: 55, violations: 4, accuracy: 93 },
      { day: 'CN', processed: 42, violations: 2, accuracy: 95 },
    ],
    weekly: [
      { week: 'Tuần 1', processed: 320, violations: 25, accuracy: 92 },
      { week: 'Tuần 2', processed: 345, violations: 28, accuracy: 92 },
      { week: 'Tuần 3', processed: 310, violations: 22, accuracy: 93 },
      { week: 'Tuần 4', processed: 365, violations: 30, accuracy: 92 },
    ],
  };

  const topViolations = [
    { type: 'Spam comments', count: 45, percentage: 32 },
    { type: 'Inappropriate content', count: 28, percentage: 20 },
    { type: 'Fake reviews', count: 22, percentage: 16 },
    { type: 'Harassment', count: 18, percentage: 13 },
    { type: 'Copyright violation', count: 15, percentage: 11 },
  ];

  const moderatorPerformance = [
    {
      name: 'Moderator A',
      processed: 156,
      accuracy: 96,
      avgTime: 1.8,
      status: 'active',
    },
    {
      name: 'Moderator B',
      processed: 142,
      accuracy: 94,
      avgTime: 2.1,
      status: 'active',
    },
    {
      name: 'Moderator C',
      processed: 128,
      accuracy: 92,
      avgTime: 2.5,
      status: 'break',
    },
  ];

  const getColorClasses = color => {
    const colors = {
      blue: 'bg-blue-50 border-blue-200 text-blue-800',
      green: 'bg-green-50 border-green-200 text-green-800',
      purple: 'bg-purple-50 border-purple-200 text-purple-800',
      red: 'bg-red-50 border-red-200 text-red-800',
    };
    return colors[color] || colors.blue;
  };

  return (
    <div className="space-y-6">
      {/* Time Range Selector */}
      <div className="flex justify-between items-center">
        <h2 className="text-xl font-bold text-gray-900">Phân tích hiệu suất</h2>
        <select
          value={timeRange}
          onChange={e => setTimeRange(e.target.value)}
          className="border border-gray-300 rounded-md px-3 py-2 text-sm"
        >
          <option value="week">Tuần này</option>
          <option value="month">Tháng này</option>
          <option value="quarter">Quý này</option>
          <option value="year">Năm nay</option>
        </select>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat, index) => (
          <div key={index} className={`p-6 rounded-xl border ${getColorClasses(stat.color)}`}>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium opacity-75">{stat.title}</p>
                <p className="text-3xl font-bold mt-2">{stat.value}</p>
              </div>
              <div className="text-3xl">{stat.icon}</div>
            </div>
            <div className="mt-4 flex items-center">
              <span
                className={`text-xs font-medium ${
                  stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'
                }`}
              >
                {stat.change}
              </span>
              <span className="text-xs opacity-75 ml-1">so với kỳ trước</span>
            </div>
          </div>
        ))}
      </div>

      {/* Charts and Analytics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Processing Trend */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Xu hướng xử lý</h3>
          <div className="space-y-4">
            {(timeRange === 'week' ? chartData.daily : chartData.weekly).map((item, index) => (
              <div key={index} className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  {timeRange === 'week' ? item.day : item.week}
                </span>
                <div className="flex items-center space-x-4">
                  <div className="flex items-center">
                    <span className="text-xs text-gray-500 mr-2">{item.processed}</span>
                    <div className="w-20 bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(item.processed / 70) * 100}%`,
                        }}
                      ></div>
                    </div>
                  </div>
                  <span className="text-xs text-red-600">{item.violations} vi phạm</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Top Violations */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Loại vi phạm phổ biến</h3>
          <div className="space-y-4">
            {topViolations.map((violation, index) => (
              <div key={index} className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm font-medium text-gray-700">{violation.type}</span>
                    <span className="text-sm text-gray-500">{violation.count} trường hợp</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-red-600 h-2 rounded-full"
                      style={{ width: `${violation.percentage}%` }}
                    ></div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Moderator Performance */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Hiệu suất Moderator</h3>
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Moderator
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Đã xử lý
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Độ chính xác
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Thời gian TB
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Trạng thái
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {moderatorPerformance.map((moderator, index) => (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="flex-shrink-0 h-8 w-8">
                        <div className="h-8 w-8 rounded-full bg-gray-300 flex items-center justify-center">
                          <span className="text-sm font-medium text-gray-700">
                            {moderator.name.charAt(0)}
                          </span>
                        </div>
                      </div>
                      <div className="ml-4">
                        <div className="text-sm font-medium text-gray-900">{moderator.name}</div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {moderator.processed}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-sm text-gray-900">{moderator.accuracy}%</span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {moderator.avgTime} phút
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        moderator.status === 'active'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {moderator.status === 'active' ? 'Đang làm việc' : 'Nghỉ'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Export Options */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Xuất báo cáo</h3>
        <div className="flex space-x-4">
          <button className="px-4 py-2 bg-green-600 text-white rounded-md text-sm hover:bg-green-700">
            📊 Xuất PDF
          </button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md text-sm hover:bg-blue-700">
            📈 Xuất Excel
          </button>
          <button className="px-4 py-2 bg-purple-600 text-white rounded-md text-sm hover:bg-purple-700">
            📋 Báo cáo chi tiết
          </button>
        </div>
      </div>
    </div>
  );
};

export default Analytics;
