import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adCooldownService from '../../services/adCooldownService';

const AD_TYPE_PREFIX = 'banner_content';
const DOMAIN = 'vemtoutcheeg.com';
const ZONE = 9465780;
const INITIAL_DELAY_MS = 3500; // Trì hoãn 3.5 giây

const AdContent = ({ position = 'TOP', className = '' }) => {
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

      const dynamicAdType = `${AD_TYPE_PREFIX}_${position.toLowerCase()}`;
      if (!adCooldownService.canShowAd(dynamicAdType)) {
        return;
      }

      const s = document.createElement('script');
      s.src = `https://${DOMAIN}/400/${ZONE}`;
      s.async = true;

      try {
        (document.body || document.documentElement).appendChild(s);
        adCooldownService.recordAdShown(dynamicAdType);
        adShownRef.current = true;
      } catch (e) {
        console.warn('Failed to inject ad script:', e);
      }
    }, INITIAL_DELAY_MS);

    return () => clearTimeout(timer);
  }, [shouldShowAds, position]);

  if (!shouldShowAds) {
    return null;
  }

  return (
    <div
      className={`ad-content-container ad-content-${position.toLowerCase()} ${className}`}
      style={{ minHeight: 250 }}
    />
  );
};

export default AdContent;
