import { useEffect } from 'react';
import PropellerAdsBanner from '../common/PropellerAdsBanner';
import propellerAdsService from '../../services/propellerAdsService';

function canShowOverlayAd(cooldownMinutes = 10) {
  const lastShown = localStorage.getItem('overlayAdLastShown');
  if (!lastShown) return true;
  const diff = (Date.now() - parseInt(lastShown, 10)) / 1000 / 60;
  return diff >= cooldownMinutes;
}

function setOverlayAdShown() {
  localStorage.setItem('overlayAdLastShown', Date.now().toString());
}

const AdContent = ({ position = 'TOP', className = '' }) => {
  useEffect(() => {
    // Khởi tạo PropellerAds service
    propellerAdsService.init();
  }, []);

  // Inject custom script for MIDDLE position
  useEffect(() => {
    if (position.toUpperCase() === 'MIDDLE') {
      if (!canShowOverlayAd(10)) return;
      const script = document.createElement('script');
      script.src = 'https://vemtoutcheeg.com/400/9465780';
      script.async = true;
      try {
        (document.body || document.documentElement).appendChild(script);
        setOverlayAdShown();
      } catch (e) {
        console.error('Failed to append ad script:', e);
      }
      return () => {
        try {
          (document.body || document.documentElement).removeChild(script);
        } catch (e) {
          console.error('Failed to remove ad script:', e);
        }
      };
    }
  }, [position]);

  const zoneType = `CONTENT_${position.toUpperCase()}`;
  const adConfig = propellerAdsService.getAdConfig(zoneType, {
    style: {
      display: 'block',
      minHeight: '250px',
      margin: '20px auto',
      maxWidth: '100%',
      textAlign: 'center',
    },
    className: `ad-content-${position.toLowerCase()} ${className}`,
  });

  return (
    <div className={`ad-content-container ad-content-${position.toLowerCase()}`}>
      <PropellerAdsBanner {...adConfig} />
    </div>
  );
};

export default AdContent;
