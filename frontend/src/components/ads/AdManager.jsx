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

const AdManager = ({ cooldownMinutes = 10 }) => {
  useEffect(() => {
    // TEMP: Bỏ kiểm tra cooldown để test ở local
    if (!canShowVemAd(cooldownMinutes)) return;
    const script = document.createElement('script');
    script.src = 'https://fpyf8.com/88/tag.min.js';
    script.async = true;
    script.setAttribute('data-zone', '152884');
    script.setAttribute('data-cfasync', 'false');
    document.body.appendChild(script);
    setVemAdShown();
    return () => {
      if (script.parentNode) script.parentNode.removeChild(script);
    };
  }, [cooldownMinutes]);
  return null;
};

export default AdManager;
