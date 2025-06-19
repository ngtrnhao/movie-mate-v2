import { useEffect } from 'react';
import PropellerAdsBanner from '../common/PropellerAdsBanner';
import propellerAdsService from '../../services/propellerAdsService';

const AdContent = ({ position = 'TOP', className = '' }) => {
  useEffect(() => {
    // Khởi tạo PropellerAds service
    propellerAdsService.init();
  }, []);

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
