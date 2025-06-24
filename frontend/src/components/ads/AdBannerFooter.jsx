import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adFrequencyService from '../../services/adFrequencyService';

const AD_TYPE = 'banner_footer';
const DOMAIN = 'gizokraijaw.net';
const PATH = '401';
const ZONE = 9467684;
const INITIAL_DELAY_MS = 3000; // Trì hoãn 3 giây

const AdBannerFooter = () => {
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
      s.src = `https://${DOMAIN}/${PATH}/${ZONE}`;
      s.async = true;

      try {
        (document.body || document.documentElement).appendChild(s);
        adFrequencyService.recordAdShown(AD_TYPE);
        adShownRef.current = true;
        console.log(`Ad ${AD_TYPE} injected successfully`);
      } catch (e) {
        console.warn('Failed to inject vignette banner script:', e);
      }
    }, INITIAL_DELAY_MS);

    return () => clearTimeout(timer);
  }, [adDisplayInfo.shouldShow]);

  if (!adDisplayInfo.shouldShow) {
    return null;
  }

  return <div className="ad-banner-footer-container" />;
};

export default AdBannerFooter;
