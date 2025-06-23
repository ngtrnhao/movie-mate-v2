import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adFrequencyService from '../../services/adFrequencyService';

const AD_TYPE = 'banner_sidebar';
const DOMAIN = 'vemtoutcheeg.com';
const ZONE = 9465780;
const INITIAL_DELAY_MS = 4500; // Trì hoãn 4.5 giây

const AdBannerSidebar = () => {
  const adDisplayInfo = useAdDisplay(AD_TYPE);
  const adShownRef = useRef(false);

  useEffect(() => {
    if (!adDisplayInfo.shouldShow) {
      return;
    }

    const timer = setTimeout(() => {
      if (adShownRef.current || !adDisplayInfo.shouldShow) {
        return;
      }

      const s = document.createElement('script');
      s.src = `https://${DOMAIN}/400/${ZONE}`;
      s.async = true;

      try {
        (document.body || document.documentElement).appendChild(s);
        adFrequencyService.recordAdShown(AD_TYPE);
        adShownRef.current = true;
        console.log(`Ad ${AD_TYPE} injected successfully`);
      } catch (e) {
        console.warn('Failed to inject ad script:', e);
      }
    }, INITIAL_DELAY_MS);

    return () => clearTimeout(timer);
  }, [adDisplayInfo.shouldShow]);

  // Hiển thị thông báo nếu đang chờ thời gian ban đầu
  if (adDisplayInfo.reason === 'initial_delay') {
    return (
      <div className="ad-banner-sidebar-container bg-gray-100 dark:bg-gray-800 p-4 text-center">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Quảng cáo sẽ hiển thị sau {adDisplayInfo.timeRemaining} phút
        </div>
      </div>
    );
  }

  // Hiển thị thông báo nếu đang trong cooldown
  if (adDisplayInfo.reason === 'cooldown_or_limit') {
    return (
      <div className="ad-banner-sidebar-container bg-gray-100 dark:bg-gray-800 p-4 text-center">
        <div className="text-sm text-gray-600 dark:text-gray-400">
          Quảng cáo tiếp theo sau {adDisplayInfo.timeRemaining} phút
        </div>
      </div>
    );
  }

  if (!adDisplayInfo.shouldShow) {
    return null;
  }

  return <div className="ad-banner-sidebar-container" style={{ minHeight: 250 }} />;
};

export default AdBannerSidebar;
