import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adCooldownService from '../../services/adCooldownService';

const AD_TYPE = 'popup';
const COOLDOWN_MINUTES = 10;

const AdManager = () => {
  const shouldShowAds = useAdDisplay();
  const adShownRef = useRef(false);

  useEffect(() => {
    // Điều kiện 1: Logic chỉ chạy một lần duy nhất
    if (adShownRef.current) {
      return;
    }

    // Điều kiện 2: Phải là đối tượng được hiển thị quảng cáo
    if (!shouldShowAds) {
      return;
    }

    // Điều kiện 3: Cooldown phải hết hạn
    if (!adCooldownService.canShowAd(AD_TYPE, COOLDOWN_MINUTES)) {
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://fpyf8.com/88/tag.min.js';
    script.async = true;
    script.setAttribute('data-zone', '152884');
    script.setAttribute('data-cfasync', 'false');

    document.body.appendChild(script);

    // Ghi lại là quảng cáo đã hiển thị
    adCooldownService.recordAdShown(AD_TYPE);
    adShownRef.current = true; // Đánh dấu đã chạy, để không chạy lại

    return () => {
      if (script.parentNode) {
        script.parentNode.removeChild(script);
      }
    };
    // Dependency array rỗng để đảm bảo effect chỉ chạy MỘT LẦN khi component mount
  }, [shouldShowAds]);

  return null;
};

export default AdManager;
