import { useEffect } from 'react';

const ScriptLoader = ({ zoneId }) => {
  useEffect(() => {
    const script = document.createElement('script');
    script.src = `//autchoog.net/400/${zoneId}`;
    script.async = true;
    document.body.appendChild(script);
    return () => {
      document.body.removeChild(script);
    };
  }, [zoneId]);
  return null;
};

export default ScriptLoader;
