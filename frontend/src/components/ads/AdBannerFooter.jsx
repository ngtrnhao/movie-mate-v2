import { useEffect, useRef } from 'react';

const NATIVE_BANNER_ZONE_ID = 9467684;

const AdBannerFooter = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    // Xóa script cũ nếu có
    const oldScript = document.getElementById('propeller_native_banner_script');
    if (oldScript) oldScript.remove();

    // Tạo script mới
    const script = document.createElement('script');
    script.id = 'propeller_native_banner_script';
    script.async = true;
    script.src = `https://ad.propellerads.com/zone/${NATIVE_BANNER_ZONE_ID}.js`;

    // Gắn script vào đúng container
    if (containerRef.current) {
      containerRef.current.innerHTML = '';
      containerRef.current.appendChild(script);
    }

    // Cleanup khi unmount
    return () => {
      if (containerRef.current) containerRef.current.innerHTML = '';
    };
  }, []);

  return (
    <div
      ref={containerRef}
      id="propeller_ad_native_banner"
      className="ad-banner-footer-container"
      style={{ minHeight: 90 }}
    />
  );
};

export default AdBannerFooter;
