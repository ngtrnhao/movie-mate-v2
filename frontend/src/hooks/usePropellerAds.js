import { useEffect, useState, useCallback } from 'react';
import propellerAdsService from '../services/propellerAdsService';
import useAdDisplay from './useAdDisplay';

const usePropellerAds = zoneType => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [isError, setIsError] = useState(false);
  const [adStats, setAdStats] = useState({});
  const shouldShowAds = useAdDisplay();

  // Khởi tạo service
  useEffect(() => {
    // Chỉ khởi tạo nếu nên hiển thị quảng cáo
    if (!shouldShowAds) {
      setIsLoaded(false);
      return;
    }

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
  }, [shouldShowAds]);

  // Lấy cấu hình quảng cáo
  const getAdConfig = useCallback(
    (options = {}) => {
      if (!shouldShowAds) {
        return { ...options, disabled: true };
      }
      return propellerAdsService.getAdConfig(zoneType, options);
    },
    [zoneType, shouldShowAds]
  );

  // Track sự kiện
  const trackEvent = useCallback(
    (eventType, data = {}) => {
      if (!shouldShowAds) return;
      propellerAdsService.trackEvent(zoneType, eventType, data);
    },
    [zoneType, shouldShowAds]
  );

  // Lấy thống kê
  const getStats = useCallback(() => {
    if (!shouldShowAds) return {};
    const stats = propellerAdsService.getAdStats(zoneType);
    setAdStats(stats);
    return stats;
  }, [zoneType, shouldShowAds]);

  // Hiển thị popup
  const showPopup = useCallback(() => {
    if (!shouldShowAds) return;
    propellerAdsService.showPopup();
  }, [shouldShowAds]);

  // Hiển thị interstitial
  const showInterstitial = useCallback(() => {
    if (!shouldShowAds) return;
    propellerAdsService.showInterstitial();
  }, [shouldShowAds]);

  return {
    isLoaded: shouldShowAds ? isLoaded : false,
    isError: shouldShowAds ? isError : false,
    adStats: shouldShowAds ? adStats : {},
    shouldShowAds,
    getAdConfig,
    trackEvent,
    getStats,
    showPopup,
    showInterstitial,
  };
};

export default usePropellerAds;
