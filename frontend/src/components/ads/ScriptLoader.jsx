import { useEffect } from 'react';

function canShowOverlayAd(cooldownMinutes = 10) {
  const lastShown = localStorage.getItem('overlayAdLastShown');
  if (!lastShown) return true;
  const diff = (Date.now() - parseInt(lastShown, 10)) / 1000 / 60;
  return diff >= cooldownMinutes;
}

function setOverlayAdShown() {
  localStorage.setItem('overlayAdLastShown', Date.now().toString());
}

const ScriptLoader = ({ zoneId, cooldownMinutes = 10 }) => {
  useEffect(() => {
    if (!canShowOverlayAd(cooldownMinutes)) return;
    const script = document.createElement('script');
    script.src = `//autchoog.net/400/${zoneId}`;
    script.async = true;
    document.body.appendChild(script);
    setOverlayAdShown();
    return () => {
      document.body.removeChild(script);
    };
  }, [zoneId, cooldownMinutes]);
  return null;
};

export default ScriptLoader;
