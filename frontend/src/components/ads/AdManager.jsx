import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adCooldownService from '../../services/adCooldownService';

const AD_TYPE = 'popup';
const COOLDOWN_MINUTES = 10;
const INITIAL_DELAY_MS = 5000; // Trì hoãn 5 giây

const AdManager = () => {
  const shouldShowAds = useAdDisplay();
  const adShownRef = useRef(false);

  useEffect(() => {
    if (!shouldShowAds) {
      return;
    }

    // Thiết lập một bộ đếm thời gian để trì hoãn việc tải quảng cáo
    const timer = setTimeout(() => {
      // Kiểm tra lại các điều kiện sau khi hết thời gian trì hoãn
      if (adShownRef.current || !shouldShowAds) {
        return;
      }

      if (!adCooldownService.canShowAd(AD_TYPE, COOLDOWN_MINUTES)) {
        return;
      }

      const script = document.createElement('script');
      script.src = 'https://fpyf8.com/88/tag.min.js';
      script.async = true;
      script.setAttribute('data-zone', '152884');
      script.setAttribute('data-cfasync', 'false');

      document.body.appendChild(script);

      adCooldownService.recordAdShown(AD_TYPE);
      adShownRef.current = true;
    }, INITIAL_DELAY_MS);

    // Dọn dẹp bộ đếm thời gian nếu component bị unmount
    return () => clearTimeout(timer);
  }, [shouldShowAds]);

  return null;
};

export default AdManager;
