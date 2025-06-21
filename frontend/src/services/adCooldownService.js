const COOLDOWN_STORAGE_KEY = 'ad_cooldown_timestamps';
const DEFAULT_COOLDOWN_MINUTES = 2; // Thời gian chờ mặc định giữa các quảng cáo

/**
 * Service quản lý thời gian chờ (cooldown) cho tất cả các loại quảng cáo.
 * Sử dụng một key duy nhất trong localStorage để đảm bảo tính nhất quán.
 */
class AdCooldownService {
  /**
   * Lấy danh sách các dấu thời gian hiển thị quảng cáo gần đây từ localStorage.
   * @returns {number[]}
   */
  getTimestamps() {
    try {
      const raw = localStorage.getItem(COOLDOWN_STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (error) {
      console.error('Error parsing ad cooldown timestamps:', error);
      return [];
    }
  }

  /**
   * Lưu lại danh sách các dấu thời gian.
   * @param {number[]} timestamps
   */
  setTimestamps(timestamps) {
    try {
      localStorage.setItem(COOLDOWN_STORAGE_KEY, JSON.stringify(timestamps));
    } catch (error) {
      console.error('Error saving ad cooldown timestamps:', error);
    }
  }

  /**
   * Kiểm tra xem có thể hiển thị một loại quảng cáo cụ thể hay không.
   * @param {string} adType - Loại quảng cáo (e.g., 'popup', 'banner_footer').
   * @param {number} cooldownMinutes - Thời gian chờ (phút) cho loại quảng cáo này.
   * @returns {boolean}
   */
  canShowAd(adType, cooldownMinutes = DEFAULT_COOLDOWN_MINUTES) {
    const now = Date.now();
    const timestamps = this.getTimestamps();
    const adTimestamp = timestamps.find(t => t.type === adType);

    // Nếu quảng cáo loại này chưa từng được hiển thị, cho phép hiển thị.
    if (!adTimestamp) {
      return true;
    }

    // Kiểm tra xem thời gian chờ đã qua chưa.
    const minutesSinceLastShown = (now - adTimestamp.time) / (1000 * 60);
    return minutesSinceLastShown >= cooldownMinutes;
  }

  /**
   * Ghi lại thời điểm một quảng cáo đã được hiển thị.
   * @param {string} adType - Loại quảng cáo đã hiển thị.
   */
  recordAdShown(adType) {
    const now = Date.now();
    let timestamps = this.getTimestamps();

    // Xóa dấu thời gian cũ của cùng loại quảng cáo
    timestamps = timestamps.filter(t => t.type !== adType);

    // Thêm dấu thời gian mới
    timestamps.push({ type: adType, time: now });

    this.setTimestamps(timestamps);
  }

  /**
   * Xóa tất cả dữ liệu về thời gian chờ quảng cáo khỏi localStorage.
   * Thường được gọi khi người dùng đăng xuất.
   */
  clearAll() {
    try {
      localStorage.removeItem(COOLDOWN_STORAGE_KEY);
      console.log('Ad cooldown data cleared.');
    } catch (error) {
      console.error('Error clearing ad cooldown data:', error);
    }
  }
}

const adCooldownService = new AdCooldownService();
export default adCooldownService;
