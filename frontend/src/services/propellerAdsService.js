// PropellerAds Service - Chỉ kiểm soát tần suất inject script nhúng
class PropellerAdsService {
  // Kiểm soát tần suất toàn cục cho quảng cáo
  canShowAd(globalLimit = 1, windowMinutes = 1) {
    try {
      const key = 'globalAdShownTimestamps';
      const now = Date.now();
      let timestamps = [];
      const raw = localStorage.getItem(key);
      if (raw) {
        timestamps = JSON.parse(raw).filter(ts => now - ts < windowMinutes * 60 * 1000);
      }
      return timestamps.length < globalLimit;
    } catch (e) {
      // Nếu lỗi, cho phép hiển thị để tránh chặn nhầm
      return true;
    }
  }

  recordAdShown(windowMinutes = 1) {
    try {
      const key = 'globalAdShownTimestamps';
      const now = Date.now();
      let timestamps = [];
      const raw = localStorage.getItem(key);
      if (raw) {
        timestamps = JSON.parse(raw).filter(ts => now - ts < windowMinutes * 60 * 1000);
      }
      timestamps.push(now);
      localStorage.setItem(key, JSON.stringify(timestamps));
    } catch (e) {
      // Bỏ qua lỗi
    }
  }
}

const propellerAdsService = new PropellerAdsService();

export default propellerAdsService;
