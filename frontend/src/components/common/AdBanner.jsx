import { useEffect } from 'react';

const AdBanner = ({ slot, style }) => {
  useEffect(() => {
    if (process.env.NODE_ENV === 'production') {
      try {
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      } catch (e) {
        // ignore error
      }
    }
  }, []);

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
