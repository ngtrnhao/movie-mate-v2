import { useEffect, useState, useCallback } from 'react';
import propellerAdsService from '../services/propellerAdsService';

const usePropellerAds = zoneType => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const [adStats, setAdStats] = useState({});

  // Khởi tạo service
  useEffect(() => {
    const initAds = async () => {
      try {
        await propellerAdsService.init();
        setIsLoaded(true);
      } catch (error) {
        console.error('Failed to initialize PropellerAds:', error);
        setIsError(true);
      }
    };

    initAds();
  }, []);

  // Lấy cấu hình quảng cáo
  const getAdConfig = useCallback(
    (options = {}) => {
      return propellerAdsService.getAdConfig(zoneType, options);
    },
    [zoneType]
  );

  // Track sự kiện
  const trackEvent = useCallback(
    (eventType, data = {}) => {
      propellerAdsService.trackEvent(zoneType, eventType, data);
    },
    [zoneType]
  );

  // Lấy thống kê
  const getStats = useCallback(() => {
    const stats = propellerAdsService.getAdStats(zoneType);
    setAdStats(stats);
    return stats;
  }, [zoneType]);

  // Hiển thị popup
  const showPopup = useCallback(() => {
    propellerAdsService.showPopup();
  }, []);

  // Hiển thị interstitial
  const showInterstitial = useCallback(() => {
    propellerAdsService.showInterstitial();
  }, []);

  return {
    isLoaded,
    isError,
    adStats,
    getAdConfig,
    trackEvent,
    getStats,
    showPopup,
    showInterstitial,
  };
};

export default usePropellerAds;
