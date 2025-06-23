import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';
import adFrequencyService from '../../services/adFrequencyService';

const AD_TYPE_PREFIX = 'script_loader_overlay';
const INITIAL_DELAY_MS = 4000; // Trì hoãn 4 giây

const ScriptLoader = ({ zoneId, domain = 'autchoog.net' }) => {
  const dynamicAdType = `${AD_TYPE_PREFIX}_${zoneId}`;
  const adDisplayInfo = useAdDisplay(dynamicAdType);
  const adShownRef = useRef(false);

  useEffect(() => {
    if (!adDisplayInfo.shouldShow) {
      return;
    }

    const timer = setTimeout(() => {
      if (adShownRef.current || !adDisplayInfo.shouldShow) {
        return;
      }

      const script = document.createElement('script');
      script.src = `https://${domain}/400/${zoneId}`;
      script.async = true;

      try {
        document.body.appendChild(script);
        adFrequencyService.recordAdShown(dynamicAdType);
        adShownRef.current = true;
        console.log(`Ad ${dynamicAdType} injected successfully`);
      } catch (e) {
        console.warn('Failed to inject script from ScriptLoader:', e);
      }
    }, INITIAL_DELAY_MS);

    return () => clearTimeout(timer);
  }, [adDisplayInfo.shouldShow, zoneId, domain, dynamicAdType]);

  return null;
};

export default ScriptLoader;
