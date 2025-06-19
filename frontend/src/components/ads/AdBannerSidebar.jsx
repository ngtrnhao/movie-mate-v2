import { useEffect } from 'react';
import PropellerAdsBanner from '../common/PropellerAdsBanner';
import propellerAdsService from '../../services/propellerAdsService';

const AdBannerSidebar = () => {
  useEffect(() => {
    // Khởi tạo PropellerAds service
    propellerAdsService.init();
  }, []);

  const adConfig = propellerAdsService.getAdConfig('BANNER_SIDEBAR', {
    style: {
      display: 'block',
      minHeight: '250px',
      margin: '20px 0',
      width: '100%',
    },
    className: 'ad-banner-sidebar',
  });

  return (
    <div className="ad-banner-sidebar-container">
      <PropellerAdsBanner {...adConfig} />
    </div>
  );
};

export default AdBannerSidebar;
