import { useEffect } from 'react';

function canShowVemAd(cooldownMinutes = 10) {
  const lastShown = localStorage.getItem('vemAdLastShown');
  if (!lastShown) return true;
  const diff = (Date.now() - parseInt(lastShown, 10)) / 1000 / 60;
  return diff >= cooldownMinutes;
}

function setVemAdShown() {
  localStorage.setItem('vemAdLastShown', Date.now().toString());
}

const AdManager = ({ cooldownMinutes = 10, zoneId = 9465780, domain = 'vemtoutcheeg.com' }) => {
  useEffect(() => {
    if (!canShowVemAd(cooldownMinutes)) return;
    const s = document.createElement('script');
    s.src = `https://${domain}/400/${zoneId}`;
    try {
      (document.body || document.documentElement).appendChild(s);
    } catch (e) {
      // fallback: do nothing
    }
    setVemAdShown();
    return () => {
      if (s.parentNode) s.parentNode.removeChild(s);
    };
  }, [zoneId, cooldownMinutes, domain]);
  return null;
};

export default AdManager;
