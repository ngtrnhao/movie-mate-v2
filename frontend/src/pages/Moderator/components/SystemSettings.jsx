import React, { useState, useEffect } from 'react';

const SystemSettings = () => {
  const [settings, setSettings] = useState({
    moderation: {
      autoApprove: false,
      requireModeration: true,
      maxReportsBeforeBan: 5,
      responseTimeLimit: 24,
      enableAutoModeration: true,
    },
    content: {
      maxReviewLength: 1000,
      allowAnonymousReviews: false,
      requireEmailVerification: true,
      enableContentFiltering: true,
    },
    system: {
      maintenanceMode: false,
      enableNotifications: true,
      backupFrequency: 'daily',
      logRetentionDays: 30,
    },
    security: {
      enableTwoFactor: true,
      sessionTimeout: 60,
      maxLoginAttempts: 5,
      enableRateLimiting: true,
    },
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Mock data - replace with actual API calls
  useEffect(() => {
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  }, []);

  const handleSettingChange = (category, key, value) => {
    setSettings(prev => ({
      ...prev,
      [category]: {
        ...prev[category],
        [key]: value,
      },
    }));
  };

  const handleSaveSettings = async () => {
    setSaving(true);
    try {
      // API call would go here
      console.log('Saving settings:', settings);
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulate API call
      // Show success notification
    } catch (error) {
      console.error('Failed to save settings:', error);
      // Show error notification
    } finally {
      setSaving(false);
    }
  };

  const handleResetSettings = () => {
    if (window.confirm('Bạn có chắc chắn muốn đặt lại tất cả cài đặt về mặc định?')) {
      // Reset to default settings
      setSettings({
        moderation: {
          autoApprove: false,
          requireModeration: true,
          maxReportsBeforeBan: 5,
          responseTimeLimit: 24,
          enableAutoModeration: true,
        },
        content: {
          maxReviewLength: 1000,
          allowAnonymousReviews: false,
          requireEmailVerification: true,
          enableContentFiltering: true,
        },
        system: {
          maintenanceMode: false,
          enableNotifications: true,
          backupFrequency: 'daily',
          logRetentionDays: 30,
        },
        security: {
          enableTwoFactor: true,
          sessionTimeout: 60,
          maxLoginAttempts: 5,
          enableRateLimiting: true,
        },
      });
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Cài đặt hệ thống</h2>
          <p className="text-gray-600">Cấu hình các thông số hệ thống và bảo mật</p>
        </div>
        <div className="flex space-x-2">
          <button
            onClick={handleResetSettings}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 transition-colors"
          >
            Đặt lại mặc định
          </button>
          <button
            onClick={handleSaveSettings}
            disabled={saving}
            className="px-4 py-2 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 transition-colors disabled:opacity-50"
          >
            {saving ? 'Đang lưu...' : 'Lưu cài đặt'}
          </button>
        </div>
      </div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Moderation Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🛡️</span>
            Cài đặt kiểm duyệt
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Tự động duyệt</label>
                <p className="text-xs text-gray-500">
                  Tự động duyệt nội dung từ người dùng đáng tin cậy
                </p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange('moderation', 'autoApprove', !settings.moderation.autoApprove)
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.moderation.autoApprove ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.moderation.autoApprove ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Yêu cầu kiểm duyệt</label>
                <p className="text-xs text-gray-500">
                  Tất cả nội dung phải được kiểm duyệt trước khi hiển thị
                </p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange(
                    'moderation',
                    'requireModeration',
                    !settings.moderation.requireModeration
                  )
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.moderation.requireModeration ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.moderation.requireModeration ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Số báo cáo tối đa trước khi cấm
              </label>
              <input
                type="number"
                value={settings.moderation.maxReportsBeforeBan}
                onChange={e =>
                  handleSettingChange('moderation', 'maxReportsBeforeBan', parseInt(e.target.value))
                }
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="1"
                max="20"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Thời gian phản hồi tối đa (giờ)
              </label>
              <input
                type="number"
                value={settings.moderation.responseTimeLimit}
                onChange={e =>
                  handleSettingChange('moderation', 'responseTimeLimit', parseInt(e.target.value))
                }
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="1"
                max="168"
              />
            </div>
          </div>
        </div>

        {/* Content Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">📝</span>
            Cài đặt nội dung
          </h3>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium text-gray-700">Độ dài tối đa đánh giá</label>
              <input
                type="number"
                value={settings.content.maxReviewLength}
                onChange={e =>
                  handleSettingChange('content', 'maxReviewLength', parseInt(e.target.value))
                }
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="100"
                max="5000"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">
                  Cho phép đánh giá ẩn danh
                </label>
                <p className="text-xs text-gray-500">
                  Người dùng có thể đánh giá mà không cần đăng nhập
                </p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange(
                    'content',
                    'allowAnonymousReviews',
                    !settings.content.allowAnonymousReviews
                  )
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.content.allowAnonymousReviews ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.content.allowAnonymousReviews ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Yêu cầu xác thực email</label>
                <p className="text-xs text-gray-500">
                  Người dùng phải xác thực email trước khi sử dụng
                </p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange(
                    'content',
                    'requireEmailVerification',
                    !settings.content.requireEmailVerification
                  )
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.content.requireEmailVerification ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.content.requireEmailVerification ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>

        {/* System Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">⚙️</span>
            Cài đặt hệ thống
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Chế độ bảo trì</label>
                <p className="text-xs text-gray-500">Tạm thời vô hiệu hóa hệ thống để bảo trì</p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange('system', 'maintenanceMode', !settings.system.maintenanceMode)
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.system.maintenanceMode ? 'bg-red-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.system.maintenanceMode ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Thông báo hệ thống</label>
                <p className="text-xs text-gray-500">Gửi thông báo cho người dùng về cập nhật</p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange(
                    'system',
                    'enableNotifications',
                    !settings.system.enableNotifications
                  )
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.system.enableNotifications ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.system.enableNotifications ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Tần suất backup</label>
              <select
                value={settings.system.backupFrequency}
                onChange={e => handleSettingChange('system', 'backupFrequency', e.target.value)}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="hourly">Hàng giờ</option>
                <option value="daily">Hàng ngày</option>
                <option value="weekly">Hàng tuần</option>
                <option value="monthly">Hàng tháng</option>
              </select>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Lưu trữ log (ngày)</label>
              <input
                type="number"
                value={settings.system.logRetentionDays}
                onChange={e =>
                  handleSettingChange('system', 'logRetentionDays', parseInt(e.target.value))
                }
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="1"
                max="365"
              />
            </div>
          </div>
        </div>

        {/* Security Settings */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <span className="mr-2">🔒</span>
            Cài đặt bảo mật
          </h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Xác thực 2 yếu tố</label>
                <p className="text-xs text-gray-500">Yêu cầu 2FA cho tài khoản admin</p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange(
                    'security',
                    'enableTwoFactor',
                    !settings.security.enableTwoFactor
                  )
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.security.enableTwoFactor ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.security.enableTwoFactor ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">
                Thời gian timeout phiên (phút)
              </label>
              <input
                type="number"
                value={settings.security.sessionTimeout}
                onChange={e =>
                  handleSettingChange('security', 'sessionTimeout', parseInt(e.target.value))
                }
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="5"
                max="1440"
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700">Số lần đăng nhập tối đa</label>
              <input
                type="number"
                value={settings.security.maxLoginAttempts}
                onChange={e =>
                  handleSettingChange('security', 'maxLoginAttempts', parseInt(e.target.value))
                }
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-indigo-500"
                min="3"
                max="10"
              />
            </div>

            <div className="flex items-center justify-between">
              <div>
                <label className="text-sm font-medium text-gray-700">Giới hạn tốc độ</label>
                <p className="text-xs text-gray-500">Giới hạn số request từ một IP</p>
              </div>
              <button
                onClick={() =>
                  handleSettingChange(
                    'security',
                    'enableRateLimiting',
                    !settings.security.enableRateLimiting
                  )
                }
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  settings.security.enableRateLimiting ? 'bg-indigo-600' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    settings.security.enableRateLimiting ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* System Status */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Trạng thái hệ thống</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl mb-2">🟢</div>
            <div className="text-sm font-medium text-gray-700">Database</div>
            <div className="text-xs text-green-600">Connected</div>
          </div>
          <div className="text-center p-4 bg-green-50 rounded-lg">
            <div className="text-2xl mb-2">🟢</div>
            <div className="text-sm font-medium text-gray-700">Cache</div>
            <div className="text-xs text-green-600">Online</div>
          </div>
          <div className="text-center p-4 bg-yellow-50 rounded-lg">
            <div className="text-2xl mb-2">🟡</div>
            <div className="text-sm font-medium text-gray-700">Queue</div>
            <div className="text-xs text-yellow-600">Busy</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SystemSettings;
