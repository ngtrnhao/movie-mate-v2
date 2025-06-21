import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';

const DOMAIN = 'gizokraijaw.net';
const PATH = '401';
const ZONE = 9467684;
const COOLDOWN_MINUTES = 10;

function canShowFooterAd(cooldownMinutes = COOLDOWN_MINUTES) {
  const lastShown = localStorage.getItem('footerAdLastShown');
  if (!lastShown) return true;
  const diff = (Date.now() - parseInt(lastShown, 10)) / 1000 / 60;
  return diff >= cooldownMinutes;
}

function setFooterAdShown() {
  localStorage.setItem('footerAdLastShown', Date.now().toString());
}

const AdBannerFooter = () => {
  const scriptRef = useRef(null);
  const shouldShowAds = useAdDisplay();

  useEffect(() => {
    // Chỉ hiển thị quảng cáo nếu điều kiện phù hợp
    if (!shouldShowAds) return;

    if (!canShowFooterAd()) return;
    // Inject script Vignette Banner
    const s = document.createElement('script');
    s.src = `https://${DOMAIN}/${PATH}/${ZONE}`;
    s.async = true;
    scriptRef.current = s;
    try {
      (document.body || document.documentElement).appendChild(s);
    } catch (e) {
      console.warn('Failed to inject vignette banner script:', e);
    }
    setFooterAdShown();
    return () => {
      if (scriptRef.current && scriptRef.current.parentNode) {
        scriptRef.current.parentNode.removeChild(scriptRef.current);
      }
    };
  }, [shouldShowAds]);

  // Không render gì nếu không nên hiển thị quảng cáo
  if (!shouldShowAds) {
    return null;
  }

  return <div className="ad-banner-footer-container" />;
};

export default AdBannerFooter;
