import { useEffect } from 'react';
import PropellerAdsBanner from '../common/PropellerAdsBanner';
import propellerAdsService from '../../services/propellerAdsService';

const AdBannerFooter = () => {
  useEffect(() => {
    // Khởi tạo PropellerAds service
    propellerAdsService.init();
  }, []);

  const adConfig = propellerAdsService.getAdConfig('BANNER_FOOTER', {
    style: {
      display: 'block',
      minHeight: '90px',
      margin: '0 auto',
      maxWidth: '728px',
      textAlign: 'center',
    },
    className: 'ad-banner-footer',
  });

  return (
    <div className="ad-banner-footer-container bg-gray-800 py-4">
      <div className="container mx-auto px-4">
        <PropellerAdsBanner {...adConfig} />
      </div>
    </div>
  );
};

export default AdBannerFooter;
