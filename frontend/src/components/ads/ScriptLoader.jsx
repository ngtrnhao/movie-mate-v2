import { useEffect } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';

function canShowOverlayAd(cooldownMinutes = 10) {
  const lastShown = localStorage.getItem('overlayAdLastShown');
  if (!lastShown) return true;
  const diff = (Date.now() - parseInt(lastShown, 10)) / 1000 / 60;
  return diff >= cooldownMinutes;
}

function setOverlayAdShown() {
  localStorage.setItem('overlayAdLastShown', Date.now().toString());
}

const ScriptLoader = ({ zoneId, domain = 'autchoog.net', cooldownMinutes = 10 }) => {
  const shouldShowAds = useAdDisplay();

  useEffect(() => {
    if (!shouldShowAds) return;

    if (!canShowOverlayAd(cooldownMinutes)) return;
    const script = document.createElement('script');
    script.src = `https://${domain}/400/${zoneId}`;
    script.async = true;
    document.body.appendChild(script);
    setOverlayAdShown();
    return () => {
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, [zoneId, cooldownMinutes, domain, shouldShowAds]);

  return null;
};

export default ScriptLoader;
