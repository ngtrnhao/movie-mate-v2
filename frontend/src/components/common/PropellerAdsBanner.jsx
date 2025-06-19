import { useEffect, useRef } from 'react';

const PropellerAdsBanner = ({ zoneId, style, className = '' }) => {
  // Không inject script nữa, chỉ render container
  if (process.env.NODE_ENV !== 'production') {
    return (
      <div
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

  // Render container cho quảng cáo PropellerAds
  return (
    <ins className={`propeller-ads-container ${className}`} style={style} data-zone={zoneId} />
  );
};

export default PropellerAdsBanner;
