import { useEffect, useRef } from 'react';

const PropellerAdsBanner = ({ zoneId, style, className = '', onAdLoad, onAdError, onAdClick }) => {
  const adRef = useRef(null);

  useEffect(() => {
    // Chỉ load quảng cáo trong production và khi có zoneId
    if (process.env.NODE_ENV === 'production' && zoneId && window.propellerads) {
      try {
        // Tạo container cho quảng cáo
        const adContainer = adRef.current;
        if (adContainer) {
          // Xóa nội dung cũ nếu có
          adContainer.innerHTML = '';

          // Tạo script element cho PropellerAds
          const script = document.createElement('script');
          script.async = true;
          script.src = `https://cdn.propellerads.com/propellerads.js`;
          script.setAttribute('data-zone', zoneId);

          // Thêm event listeners
          script.addEventListener('load', () => {
            if (onAdLoad) onAdLoad();
          });

          script.addEventListener('error', error => {
            console.error('PropellerAds load error:', error);
            if (onAdError) onAdError(error);
          });

          // Thêm script vào container
          adContainer.appendChild(script);

          // Track click events
          adContainer.addEventListener('click', e => {
            if (e.target.tagName === 'A' || e.target.closest('a')) {
              if (onAdClick) onAdClick();
            }
          });
        }
      } catch (error) {
        console.error('Error loading PropellerAds:', error);
        if (onAdError) onAdError(error);
      }
    }
  }, [zoneId, onAdLoad, onAdError, onAdClick]);

  // Placeholder cho development
  if (process.env.NODE_ENV !== 'production') {
    return (
      <div
        ref={adRef}
        className={`propeller-ads-placeholder ${className}`}
        style={{
          ...style,
          background:
            'linear-gradient(45deg, #f0f0f0 25%, transparent 25%), linear-gradient(-45deg, #f0f0f0 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #f0f0f0 75%), linear-gradient(-45deg, transparent 75%, #f0f0f0 75%)',
          backgroundSize: '20px 20px',
          backgroundPosition: '0 0, 0 10px, 10px -10px, -10px 0px',
          border: '2px dashed #ccc',
          borderRadius: '8px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          fontSize: '14px',
          fontWeight: '500',
          minHeight: '90px',
        }}
      >
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '16px', marginBottom: '4px' }}>📢 PropellerAds</div>
          <div style={{ fontSize: '12px' }}>Zone: {zoneId || 'N/A'}</div>
        </div>
      </div>
    );
  }

  return (
    <div
      ref={adRef}
      className={`propeller-ads-container ${className}`}
      style={style}
      data-zone-id={zoneId}
    />
  );
};

export default PropellerAdsBanner;
