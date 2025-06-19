import { useEffect } from 'react';
import PropellerAdsBanner from '../common/PropellerAdsBanner';
import propellerAdsService from '../../services/propellerAdsService';

const AdBannerTop = () => {
  useEffect(() => {
    // Khởi tạo PropellerAds service
    propellerAdsService.init();
  }, []);

  const adConfig = propellerAdsService.getAdConfig('BANNER_TOP', {
    style: {
      display: 'block',
      minHeight: '90px',
      margin: '0 auto',
      maxWidth: '728px',
      textAlign: 'center',
    },
    className: 'ad-banner-top',
  });

  return (
    <div className="ad-banner-top-container bg-gray-800 py-4">
      <div className="container mx-auto px-4">
        <PropellerAdsBanner {...adConfig} />
      </div>
    </div>
  );
};

export default AdBannerTop;
