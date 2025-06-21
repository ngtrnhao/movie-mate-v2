import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adCooldownService from '../../services/adCooldownService';

const AD_TYPE = 'banner_top';
const DOMAIN = 'vemtoutcheeg.com';
const ZONE = 9465780;
const INITIAL_DELAY_MS = 3000; // Trì hoãn 3 giây

const AdBannerTop = () => {
  const shouldShowAds = useAdDisplay();
  const adShownRef = useRef(false);

  useEffect(() => {
    if (!shouldShowAds) {
      return;
    }

    const timer = setTimeout(() => {
      if (adShownRef.current || !shouldShowAds) {
        return;
      }

      if (!adCooldownService.canShowAd(AD_TYPE)) {
        return;
      }

      const s = document.createElement('script');
      s.src = `https://${DOMAIN}/400/${ZONE}`;
      s.async = true;

      try {
        (document.body || document.documentElement).appendChild(s);
        adCooldownService.recordAdShown(AD_TYPE);
        adShownRef.current = true;
      } catch (e) {
        console.warn('Failed to inject ad script:', e);
      }
    }, INITIAL_DELAY_MS);

    return () => clearTimeout(timer);
  }, [shouldShowAds]);

  if (!shouldShowAds) {
    return null;
  }

  return <div className="ad-banner-top-container" style={{ minHeight: 90 }} />;
};

export default AdBannerTop;
