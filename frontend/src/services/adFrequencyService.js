/**
 * Service để kiểm soát tần suất và thời gian hiển thị quảng cáo
 * Chỉ hiển thị quảng cáo sau khi người dùng ở trang web được 15 phút
 */
class AdFrequencyService {
  constructor() {
    this.sessionStartTime = null;
    this.lastAdShown = {};
    this.adCooldowns = {
      banner_top: 5 * 60 * 1000, // 5 phút
      banner_sidebar: 8 * 60 * 1000, // 8 phút
      banner_footer: 10 * 60 * 1000, // 10 phút
      banner_content: 6 * 60 * 1000, // 6 phút
      popup: 15 * 60 * 1000, // 15 phút
      script_loader_overlay: 12 * 60 * 1000, // 12 phút
    };
    this.initialDelay = 15 * 60 * 1000; // 15 phút
    this.maxAdsPerHour = 10; // Tối đa 10 quảng cáo mỗi giờ
    this.adsShownThisHour = 0;
    this.hourStartTime = null;

    this.init();
  }

  /**
   * Khởi tạo service
   */
  init() {
    // Lấy thời gian bắt đầu session từ localStorage hoặc tạo mới
    const savedSessionStart = localStorage.getItem('ad_session_start_time');
    if (savedSessionStart) {
      this.sessionStartTime = parseInt(savedSessionStart);
    } else {
      this.sessionStartTime = Date.now();
      localStorage.setItem('ad_session_start_time', this.sessionStartTime.toString());
    }

    // Lấy thời gian bắt đầu giờ hiện tại
    this.hourStartTime = this.getHourStartTime();

    // Lấy số lượng quảng cáo đã hiển thị trong giờ hiện tại
    const savedAdsThisHour = localStorage.getItem('ad_ads_this_hour');
    if (savedAdsThisHour) {
      const { count, hourStart } = JSON.parse(savedAdsThisHour);
      if (hourStart === this.hourStartTime) {
        this.adsShownThisHour = count;
      } else {
        this.adsShownThisHour = 0;
        this.saveAdsThisHour();
      }
    }

    // Lấy thời gian hiển thị quảng cáo cuối cùng
    const savedLastAdShown = localStorage.getItem('ad_last_shown');
    if (savedLastAdShown) {
      this.lastAdShown = JSON.parse(savedLastAdShown);
    }

    console.log('AdFrequencyService initialized:', {
      sessionStartTime: new Date(this.sessionStartTime),
      timeUntilAds: this.getTimeUntilAdsCanShow(),
      adsThisHour: this.adsShownThisHour,
      maxAdsPerHour: this.maxAdsPerHour,
    });
  }

  /**
   * Lấy thời gian bắt đầu của giờ hiện tại
   */
  getHourStartTime() {
    const now = new Date();
    return new Date(
      now.getFullYear(),
      now.getMonth(),
      now.getDate(),
      now.getHours(),
      0,
      0,
      0
    ).getTime();
  }

  /**
   * Lưu số lượng quảng cáo trong giờ hiện tại
   */
  saveAdsThisHour() {
    localStorage.setItem(
      'ad_ads_this_hour',
      JSON.stringify({
        count: this.adsShownThisHour,
        hourStart: this.hourStartTime,
      })
    );
  }

  /**
   * Kiểm tra xem đã đủ 15 phút chưa
   */
  hasInitialDelayPassed() {
    const timeElapsed = Date.now() - this.sessionStartTime;
    return timeElapsed >= this.initialDelay;
  }

  /**
   * Lấy thời gian còn lại trước khi có thể hiển thị quảng cáo
   */
  getTimeUntilAdsCanShow() {
    if (this.hasInitialDelayPassed()) {
      return 0;
    }
    const timeElapsed = Date.now() - this.sessionStartTime;
    return Math.max(0, this.initialDelay - timeElapsed);
  }

  /**
   * Kiểm tra xem có thể hiển thị quảng cáo không
   */
  canShowAd(adType) {
    // Kiểm tra thời gian ban đầu (15 phút)
    if (!this.hasInitialDelayPassed()) {
      console.log(`Ad ${adType}: Waiting for initial 15-minute delay`);
      return false;
    }

    // Kiểm tra giới hạn quảng cáo mỗi giờ
    if (this.adsShownThisHour >= this.maxAdsPerHour) {
      console.log(`Ad ${adType}: Hourly limit reached (${this.maxAdsPerHour} ads)`);
      return false;
    }

    // Kiểm tra cooldown cho loại quảng cáo cụ thể
    const cooldown = this.adCooldowns[adType] || 5 * 60 * 1000; // Default 5 phút
    const lastShown = this.lastAdShown[adType] || 0;
    const timeSinceLastShown = Date.now() - lastShown;

    if (timeSinceLastShown < cooldown) {
      const remainingCooldown = cooldown - timeSinceLastShown;
      console.log(
        `Ad ${adType}: Cooldown active, ${Math.ceil(remainingCooldown / 1000 / 60)} minutes remaining`
      );
      return false;
    }

    return true;
  }

  /**
   * Ghi nhận quảng cáo đã hiển thị
   */
  recordAdShown(adType) {
    const now = Date.now();

    // Cập nhật thời gian hiển thị cuối cùng
    this.lastAdShown[adType] = now;
    localStorage.setItem('ad_last_shown', JSON.stringify(this.lastAdShown));

    // Cập nhật số lượng quảng cáo trong giờ hiện tại
    const currentHourStart = this.getHourStartTime();
    if (currentHourStart !== this.hourStartTime) {
      // Giờ mới, reset counter
      this.hourStartTime = currentHourStart;
      this.adsShownThisHour = 1;
    } else {
      this.adsShownThisHour++;
    }
    this.saveAdsThisHour();

    console.log(
      `Ad ${adType} shown. Ads this hour: ${this.adsShownThisHour}/${this.maxAdsPerHour}`
    );
  }

  /**
   * Lấy thông tin trạng thái
   */
  getStatus() {
    const timeUntilAds = this.getTimeUntilAdsCanShow();
    const timeElapsed = Date.now() - this.sessionStartTime;

    return {
      sessionStartTime: this.sessionStartTime,
      timeElapsed: timeElapsed,
      timeUntilAds: timeUntilAds,
      hasInitialDelayPassed: this.hasInitialDelayPassed(),
      adsShownThisHour: this.adsShownThisHour,
      maxAdsPerHour: this.maxAdsPerHour,
      lastAdShown: this.lastAdShown,
      adCooldowns: this.adCooldowns,
    };
  }

  /**
   * Reset session (cho testing)
   */
  resetSession() {
    this.sessionStartTime = Date.now();
    this.lastAdShown = {};
    this.adsShownThisHour = 0;
    this.hourStartTime = this.getHourStartTime();

    localStorage.setItem('ad_session_start_time', this.sessionStartTime.toString());
    localStorage.removeItem('ad_last_shown');
    this.saveAdsThisHour();

    console.log('AdFrequencyService session reset');
  }

  /**
   * Lấy thời gian còn lại cho cooldown của một loại quảng cáo
   */
  getCooldownRemaining(adType) {
    const cooldown = this.adCooldowns[adType] || 5 * 60 * 1000;
    const lastShown = this.lastAdShown[adType] || 0;
    const timeSinceLastShown = Date.now() - lastShown;

    return Math.max(0, cooldown - timeSinceLastShown);
  }

  /**
   * Kiểm tra xem có đang trong cooldown không
   */
  isInCooldown(adType) {
    return this.getCooldownRemaining(adType) > 0;
  }

  /**
   * Lấy thời gian còn lại trước khi có thể hiển thị quảng cáo tiếp theo
   */
  getNextAdTime(adType) {
    if (!this.hasInitialDelayPassed()) {
      return this.getTimeUntilAdsCanShow();
    }

    if (this.adsShownThisHour >= this.maxAdsPerHour) {
      const nextHour = this.hourStartTime + 60 * 60 * 1000;
      return nextHour - Date.now();
    }

    return this.getCooldownRemaining(adType);
  }
}

// Tạo instance global
const adFrequencyService = new AdFrequencyService();
window.adFrequencyService = adFrequencyService;

export default adFrequencyService;
