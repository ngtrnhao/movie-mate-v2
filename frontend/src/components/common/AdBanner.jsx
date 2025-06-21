import { useEffect } from 'react';
import useAdDisplay from '../hooks/useAdDisplay';

const AdBanner = ({ slot, style }) => {
  const shouldShowAds = useAdDisplay();

  useEffect(() => {
    // Chỉ hiển thị quảng cáo nếu điều kiện phù hợp
    if (!shouldShowAds) return;

    if (process.env.NODE_ENV === 'production') {
      try {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      } catch (e) {
        // ignore error
      }
    }
  }, [shouldShowAds]);

  // Không render gì nếu không nên hiển thị quảng cáo
  if (!shouldShowAds) {
    return null;
  }

  if (process.env.NODE_ENV !== 'production') {
    // Placeholder khi develop
    return <div style={{ ...style, background: '#eee', textAlign: 'center' }}>Ad Placeholder</div>;
  }

  return (
    <ins
      className="adsbygoogle"
      style={style || { display: 'block', minHeight: 90 }}
      data-ad-client="ca-pub-xxxxxxxxxxxxxxxx"
      data-ad-slot={slot || '1234567890'}
      data-ad-format="auto"
    />
  );
};

export default AdBanner;
