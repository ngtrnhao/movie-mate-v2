// PropellerAds Service - Quản lý quảng cáo từ PropellerAds
class PropellerAdsService {
  constructor() {
    this.zones = {
      // Banner quảng cáo
      BANNER_TOP: process.env.REACT_APP_PROPELLER_ZONE_BANNER_TOP || '123456',
      BANNER_SIDEBAR: process.env.REACT_APP_PROPELLER_ZONE_BANNER_SIDEBAR || '123457',
      BANNER_FOOTER: process.env.REACT_APP_PROPELLER_ZONE_BANNER_FOOTER || '123458',

      // Quảng cáo nội dung
      CONTENT_TOP: process.env.REACT_APP_PROPELLER_ZONE_CONTENT_TOP || '123459',
      CONTENT_MIDDLE: process.env.REACT_APP_PROPELLER_ZONE_CONTENT_MIDDLE || '123460',
      CONTENT_BOTTOM: process.env.REACT_APP_PROPELLER_ZONE_CONTENT_BOTTOM || '123461',

      // Quảng cáo popup/interstitial
      POPUP: process.env.REACT_APP_PROPELLER_ZONE_POPUP || '123462',

      // Quảng cáo video
      VIDEO: process.env.REACT_APP_PROPELLER_ZONE_VIDEO || '123463',
    };

    this.isInitialized = false;
    this.adEvents = new Map();
  }

  // Khởi tạo PropellerAds
  init() {
    if (this.isInitialized || process.env.NODE_ENV !== 'production') {
      return Promise.resolve();
    }

    return new Promise((resolve, reject) => {
      try {
        // Load PropellerAds script
        const script = document.createElement('script');
        script.async = true;
        script.src = 'https://cdn.propellerads.com/propellerads.js';

        script.onload = () => {
          this.isInitialized = true;
          console.log('PropellerAds initialized successfully');
          resolve();
        };

        script.onerror = error => {
          console.error('Failed to load PropellerAds:', error);
          reject(error);
        };

        document.head.appendChild(script);
      } catch (error) {
        console.error('Error initializing PropellerAds:', error);
        reject(error);
      }
    });
  }

  // Lấy zone ID theo loại
  getZoneId(type) {
    return this.zones[type] || null;
  }

  // Track sự kiện quảng cáo
  trackEvent(zoneType, eventType, data = {}) {
    const eventData = {
      zoneType,
      eventType,
      timestamp: new Date().toISOString(),
      ...data,
    };

    // Lưu event vào memory
    if (!this.adEvents.has(zoneType)) {
      this.adEvents.set(zoneType, []);
    }
    this.adEvents.get(zoneType).push(eventData);

    // Gửi analytics nếu cần
    this.sendAnalytics(eventData);

    console.log('PropellerAds Event:', eventData);
  }

  // Gửi analytics
  sendAnalytics(eventData) {
    // Có thể tích hợp với Google Analytics hoặc service khác
    if (window.gtag) {
      window.gtag('event', 'propeller_ads_event', {
        event_category: 'advertising',
        event_label: eventData.zoneType,
        value: 1,
        custom_parameters: eventData,
      });
    }
  }

  // Lấy thống kê quảng cáo
  getAdStats(zoneType = null) {
    if (zoneType) {
      return this.adEvents.get(zoneType) || [];
    }

    const allStats = {};
    this.adEvents.forEach((events, zone) => {
      allStats[zone] = events;
    });

    return allStats;
  }

  // Kiểm tra xem có phải mobile không
  isMobile() {
    return /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(
      navigator.userAgent
    );
  }

  // Lấy zone phù hợp theo device
  getZoneByDevice(zoneType) {
    const baseZoneId = this.getZoneId(zoneType);
    if (!baseZoneId) return null;

    // Có thể có zone riêng cho mobile/desktop
    if (this.isMobile()) {
      return this.getZoneId(`${zoneType}_MOBILE`) || baseZoneId;
    }

    return this.getZoneId(`${zoneType}_DESKTOP`) || baseZoneId;
  }

  // Tạo cấu hình quảng cáo
  getAdConfig(zoneType, options = {}) {
    const zoneId = this.getZoneByDevice(zoneType);

    return {
      zoneId,
      style: {
        display: 'block',
        minHeight: '90px',
        margin: '10px 0',
        ...options.style,
      },
      className: `propeller-ad-${zoneType.toLowerCase()} ${options.className || ''}`,
      onAdLoad: data => {
        this.trackEvent(zoneType, 'load', data);
        if (options.onAdLoad) options.onAdLoad(data);
      },
      onAdError: error => {
        this.trackEvent(zoneType, 'error', { error: error.message });
        if (options.onAdError) options.onAdError(error);
      },
      onAdClick: data => {
        this.trackEvent(zoneType, 'click', data);
        if (options.onAdClick) options.onAdClick(data);
      },
    };
  }

  // Hiển thị popup quảng cáo
  showPopup() {
    const zoneId = this.getZoneId('POPUP');
    if (!zoneId || process.env.NODE_ENV !== 'production') return;

    try {
      if (window.propellerads && window.propellerads.showPopup) {
        window.propellerads.showPopup(zoneId);
        this.trackEvent('POPUP', 'show');
      }
    } catch (error) {
      console.error('Error showing popup ad:', error);
    }
  }

  // Hiển thị interstitial quảng cáo
  showInterstitial() {
    const zoneId = this.getZoneId('INTERSTITIAL');
    if (!zoneId || process.env.NODE_ENV !== 'production') return;

    try {
      if (window.propellerads && window.propellerads.showInterstitial) {
        window.propellerads.showInterstitial(zoneId);
        this.trackEvent('INTERSTITIAL', 'show');
      }
    } catch (error) {
      console.error('Error showing interstitial ad:', error);
    }
  }
}

// Tạo instance singleton
const propellerAdsService = new PropellerAdsService();

export default propellerAdsService;
