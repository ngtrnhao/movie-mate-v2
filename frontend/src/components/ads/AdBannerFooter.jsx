import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adCooldownService from '../../services/adCooldownService';

const AD_TYPE = 'banner_footer';
const DOMAIN = 'gizokraijaw.net';
const PATH = '401';
const ZONE = 9467684;
const COOLDOWN_MINUTES = 5;

const AdBannerFooter = () => {
  const shouldShowAds = useAdDisplay();
  const adShownRef = useRef(false);

  useEffect(() => {
    if (adShownRef.current || !shouldShowAds) {
      return;
    }

    if (!adCooldownService.canShowAd(AD_TYPE, COOLDOWN_MINUTES)) {
      return;
    }

    const s = document.createElement('script');
    s.src = `https://${DOMAIN}/${PATH}/${ZONE}`;
    s.async = true;

    try {
      (document.body || document.documentElement).appendChild(s);
      adCooldownService.recordAdShown(AD_TYPE);
      adShownRef.current = true;
    } catch (e) {
      console.warn('Failed to inject vignette banner script:', e);
    }

    return () => {
      if (s.parentNode) {
        s.parentNode.removeChild(s);
      }
    };
  }, [shouldShowAds]);

  if (!shouldShowAds) {
    return null;
  }

  return <div className="ad-banner-footer-container" />;
};

export default AdBannerFooter;
