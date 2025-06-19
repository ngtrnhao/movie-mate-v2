import { useEffect, useRef } from 'react';
import usePropellerAds from '../../hooks/usePropellerAds';

const AdManager = () => {
  const { showPopup, showInterstitial } = usePropellerAds('POPUP');
  const popupShownRef = useRef(false);
  const interstitialShownRef = useRef(false);

  useEffect(() => {
    // Hiển thị popup sau 5 giây
    if (process.env.NODE_ENV === 'production') return;
    const popupTimer = setTimeout(() => {
      if (!popupShownRef.current) {
        showPopup();
        popupShownRef.current = true;
      }
    }, 10000000000); //

    // Hiển thị interstitial khi user scroll xuống 50% trang
    const handleScroll = () => {
      const scrollPercent =
        (window.scrollY / (document.documentElement.scrollHeight - window.innerHeight)) * 100;

      if (scrollPercent > 50 && !interstitialShownRef.current) {
        showInterstitial();
        interstitialShownRef.current = true;
      }
    };

    window.addEventListener('scroll', handleScroll);

    return () => {
      clearTimeout(popupTimer);
      window.removeEventListener('scroll', handleScroll);
    };
  }, [showPopup, showInterstitial]);

  // Component này không render gì, chỉ quản lý quảng cáo
  return null;
};

export default AdManager;
