import { useState } from 'react';

const SystemSettings = () => {
  const [settings, setSettings] = useState({
    siteName: 'Movie Recommendation System',
    siteDescription: 'Hệ thống review và gợi ý phim',
    maxReviewsPerUser: 1000,
    maxReviewsPerDay: 50,
    enableRegistration: true,
    requireEmailVerification: true,
    enableModeration: true,
    autoApproveReviews: false,
    maxFileSize: 5,
    allowedFileTypes: ['jpg', 'jpeg', 'png', 'gif'],
    maintenanceMode: false,
    debugMode: false,
  });

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  const handleSettingChange = (key, value) => {
    setSettings(prev => ({
      ...prev,
      [key]: value,
    }));
  };

  const handleSave = async () => {
    setLoading(true);
    try {
      // This would be implemented with a proper API endpoint
      console.log('Saving settings:', settings);

      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));

      setMessage('Cài đặt đã được lưu thành công!');
      setTimeout(() => setMessage(''), 3000);
    } catch (error) {
      setMessage('Có lỗi xảy ra khi lưu cài đặt');
      setTimeout(() => setMessage(''), 3000);
    } finally {
      setLoading(false);
    }
  };

  const SettingItem = ({ label, description, children }) => (
    <div className="border-b border-gray-200 py-4 last:border-b-0">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <label className="text-sm font-medium text-gray-900">{label}</label>
          {description && <p className="mt-1 text-sm text-gray-500">{description}</p>}
        </div>
        <div className="ml-6">{children}</div>
      </div>
    </div>
  );

  return (
    <div className="p-6">
      <div className="mb-8">
        <h2 className="mb-2 text-2xl font-bold text-gray-900">Cài đặt hệ thống</h2>
        <p className="text-gray-600">Cấu hình các tham số hệ thống</p>
      </div>

      {message && (
        <div
          className={`mb-6 rounded-md p-4 ${
            message.includes('thành công')
              ? 'border border-green-200 bg-green-50 text-green-800'
              : 'border border-red-200 bg-red-50 text-red-800'
          }`}
        >
          {message}
        </div>
      )}

      <div className="rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-6 text-lg font-medium leading-6 text-gray-900">Cài đặt chung</h3>

          <div className="space-y-0">
            <SettingItem label="Tên website" description="Tên hiển thị của website">
              <input
                type="text"
                value={settings.siteName}
                onChange={e => handleSettingChange('siteName', e.target.value)}
                className="w-64 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
            </SettingItem>

            <SettingItem label="Mô tả website" description="Mô tả ngắn về website">
              <textarea
                value={settings.siteDescription}
                onChange={e => handleSettingChange('siteDescription', e.target.value)}
                rows={2}
                className="w-64 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
            </SettingItem>

            <SettingItem
              label="Giới hạn review mỗi người dùng"
              description="Số lượng review tối đa mỗi người dùng có thể tạo"
            >
              <input
                type="number"
                value={settings.maxReviewsPerUser}
                onChange={e => handleSettingChange('maxReviewsPerUser', parseInt(e.target.value))}
                className="w-32 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
            </SettingItem>

            <SettingItem
              label="Giới hạn review mỗi ngày"
              description="Số lượng review tối đa mỗi người dùng có thể tạo trong một ngày"
            >
              <input
                type="number"
                value={settings.maxReviewsPerDay}
                onChange={e => handleSettingChange('maxReviewsPerDay', parseInt(e.target.value))}
                className="w-32 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
            </SettingItem>
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-6 text-lg font-medium leading-6 text-gray-900">
            Cài đặt đăng ký và xác thực
          </h3>

          <div className="space-y-0">
            <SettingItem
              label="Cho phép đăng ký"
              description="Cho phép người dùng mới đăng ký tài khoản"
            >
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={settings.enableRegistration}
                  onChange={e => handleSettingChange('enableRegistration', e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
              </label>
            </SettingItem>

            <SettingItem
              label="Yêu cầu xác thực email"
              description="Yêu cầu người dùng xác thực email sau khi đăng ký"
            >
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={settings.requireEmailVerification}
                  onChange={e => handleSettingChange('requireEmailVerification', e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
              </label>
            </SettingItem>
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-6 text-lg font-medium leading-6 text-gray-900">Cài đặt kiểm duyệt</h3>

          <div className="space-y-0">
            <SettingItem
              label="Bật kiểm duyệt"
              description="Bật hệ thống kiểm duyệt review trước khi hiển thị"
            >
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={settings.enableModeration}
                  onChange={e => handleSettingChange('enableModeration', e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
              </label>
            </SettingItem>

            <SettingItem
              label="Tự động phê duyệt review"
              description="Tự động phê duyệt review mà không cần kiểm duyệt thủ công"
            >
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={settings.autoApproveReviews}
                  onChange={e => handleSettingChange('autoApproveReviews', e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
              </label>
            </SettingItem>
          </div>
        </div>
      </div>

      <div className="mt-6 rounded-lg bg-white shadow">
        <div className="px-4 py-5 sm:p-6">
          <h3 className="mb-6 text-lg font-medium leading-6 text-gray-900">Cài đặt hệ thống</h3>

          <div className="space-y-0">
            <SettingItem
              label="Chế độ bảo trì"
              description="Bật chế độ bảo trì để tạm thời vô hiệu hóa website"
            >
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={settings.maintenanceMode}
                  onChange={e => handleSettingChange('maintenanceMode', e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
              </label>
            </SettingItem>

            <SettingItem
              label="Chế độ debug"
              description="Bật chế độ debug để hiển thị thông tin lỗi chi tiết"
            >
              <label className="relative inline-flex cursor-pointer items-center">
                <input
                  type="checkbox"
                  checked={settings.debugMode}
                  onChange={e => handleSettingChange('debugMode', e.target.checked)}
                  className="peer sr-only"
                />
                <div className="peer h-6 w-11 rounded-full bg-gray-200 after:absolute after:left-[2px] after:top-[2px] after:size-5 after:rounded-full after:border after:border-gray-300 after:bg-white after:transition-all after:content-[''] peer-checked:bg-blue-600 peer-checked:after:translate-x-full peer-checked:after:border-white peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300"></div>
              </label>
            </SettingItem>

            <SettingItem
              label="Kích thước file tối đa (MB)"
              description="Kích thước file tối đa cho upload avatar"
            >
              <input
                type="number"
                value={settings.maxFileSize}
                onChange={e => handleSettingChange('maxFileSize', parseInt(e.target.value))}
                className="w-32 rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-indigo-500 focus:outline-none focus:ring-indigo-500"
              />
            </SettingItem>
          </div>
        </div>
      </div>

      <div className="mt-6 flex justify-end">
        <button
          onClick={handleSave}
          disabled={loading}
          className="inline-flex items-center rounded-md border border-transparent bg-indigo-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? (
            <>
              <svg
                className="-ml-1 mr-3 size-5 animate-spin text-white"
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                ></circle>
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                ></path>
              </svg>
              Đang lưu...
            </>
          ) : (
            'Lưu cài đặt'
          )}
        </button>
      </div>
    </div>
  );
};

export default SystemSettings;
