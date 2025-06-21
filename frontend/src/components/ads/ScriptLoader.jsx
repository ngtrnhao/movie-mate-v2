import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adCooldownService from '../../services/adCooldownService';

const AD_TYPE = 'script_loader_overlay';
const INITIAL_DELAY_MS = 4000; // Trì hoãn 4 giây

const ScriptLoader = ({ zoneId, domain = 'autchoog.net', cooldownMinutes = 10 }) => {
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

      const dynamicAdType = `${AD_TYPE}_${zoneId}`;

      if (!adCooldownService.canShowAd(dynamicAdType, cooldownMinutes)) {
        return;
      }

      const script = document.createElement('script');
      script.src = `https://${domain}/400/${zoneId}`;
      script.async = true;

      try {
        document.body.appendChild(script);
        adCooldownService.recordAdShown(dynamicAdType);
        adShownRef.current = true;
      } catch (e) {
        console.warn('Failed to inject script from ScriptLoader:', e);
      }
    }, INITIAL_DELAY_MS);

    return () => clearTimeout(timer);
  }, [shouldShowAds, zoneId, domain, cooldownMinutes]);

  return null;
};

export default ScriptLoader;
