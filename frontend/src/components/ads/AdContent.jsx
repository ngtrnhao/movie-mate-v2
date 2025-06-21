import { useEffect, useRef } from 'react';
import useAdDisplay from '../../hooks/useAdDisplay';

const DOMAIN = 'vemtoutcheeg.com';
const ZONE = 9465780;

const AdContent = ({ position = 'TOP', className = '' }) => {
  const scriptRef = useRef(null);
  const shouldShowAds = useAdDisplay();

  useEffect(() => {
    // Chỉ hiển thị quảng cáo nếu điều kiện phù hợp
    if (!shouldShowAds) return;

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
  }, [position, shouldShowAds]);

  // Không render gì nếu không nên hiển thị quảng cáo
  if (!shouldShowAds) {
    return null;
  }

  return (
    <div
      className={`ad-content-container ad-content-${position.toLowerCase()} ${className}`}
      style={{ minHeight: 250 }}
    />
  );
};

export default AdContent;
