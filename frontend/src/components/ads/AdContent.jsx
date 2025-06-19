import { useEffect, useRef } from 'react';

const DOMAIN = 'vemtoutcheeg.com';
const ZONE = 9465780;

const AdContent = ({ position = 'TOP', className = '' }) => {
  const scriptRef = useRef(null);

  useEffect(() => {
    const service = require('../../services/propellerAdsService').default;
    if (!service.canShowAd()) return;
    service.recordAdShown();

    // Inject script quảng cáo dạng IIFE
    const s = document.createElement('script');
    s.src = `https://${DOMAIN}/400/${ZONE}`;
    s.async = true;
    scriptRef.current = s;
    try {
      (document.body || document.documentElement).appendChild(s);
    } catch (e) {
      console.warn('Failed to inject ad script:', e);
    }
    return () => {
      if (scriptRef.current && scriptRef.current.parentNode) {
        scriptRef.current.parentNode.removeChild(scriptRef.current);
      }
    };
  }, [position]);

  return (
    <div
      className={`ad-content-container ad-content-${position.toLowerCase()} ${className}`}
      style={{ minHeight: 250 }}
    />
  );
};

export default AdContent;
