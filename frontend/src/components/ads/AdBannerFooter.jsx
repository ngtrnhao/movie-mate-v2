import { useEffect, useRef } from 'react';

const DOMAIN = 'gizokraijaw.net';
const PATH = '401';
const ZONE = 9467684;

const AdBannerFooter = () => {
  const scriptRef = useRef(null);

  useEffect(() => {
    // Inject script Vignette Banner
    const s = document.createElement('script');
    s.src = `https://${DOMAIN}/${PATH}/${ZONE}`;
    s.async = true;
    scriptRef.current = s;
    try {
      (document.body || document.documentElement).appendChild(s);
    } catch (e) {
      console.warn('Failed to inject vignette banner script:', e);
    }
    return () => {
      if (scriptRef.current && scriptRef.current.parentNode) {
        scriptRef.current.parentNode.removeChild(scriptRef.current);
      }
    };
  }, []);

  return <div className="ad-banner-footer-container" style={{ minHeight: 90 }} />;
};

export default AdBannerFooter;
