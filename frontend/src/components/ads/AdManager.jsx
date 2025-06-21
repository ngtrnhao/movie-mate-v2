import { useEffect } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';

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
  const shouldShowAds = useAdDisplay();

  useEffect(() => {
    // Chỉ hiển thị quảng cáo nếu điều kiện phù hợp
    if (!shouldShowAds) return;

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
  }, [cooldownMinutes, shouldShowAds]);

  return null;
};

export default AdManager;
