// import { useEffect, useRef } from 'react';
// import useAdDisplay from '../../hooks/useAdDisplay';
// import adFrequencyService from '../../services/adFrequencyService';

// const AD_TYPE = 'popup';
// const INITIAL_DELAY_MS = 5000; // Trì hoãn 5 giây

// const AdManager = () => {
//   const adDisplayInfo = useAdDisplay(AD_TYPE);
//   const adShownRef = useRef(false);

//   useEffect(() => {
//     if (!adDisplayInfo.shouldShow) {
//       return;
//     }

//     // Thiết lập một bộ đếm thời gian để trì hoãn việc tải quảng cáo
//     const timer = setTimeout(() => {
//       // Kiểm tra lại các điều kiện sau khi hết thời gian trì hoãn
//       if (adShownRef.current || !adDisplayInfo.shouldShow) {
//         return;
//       }

//       const script = document.createElement('script');
//       script.src = 'https://fpyf8.com/88/tag.min.js';
//       script.async = true;
//       script.setAttribute('data-zone', '152884');
//       script.setAttribute('data-cfasync', 'false');

//       try {
//         document.body.appendChild(script);
//         adFrequencyService.recordAdShown(AD_TYPE);
//         adShownRef.current = true;
//         console.log(`Ad ${AD_TYPE} injected successfully`);
//       } catch (e) {
//         console.warn('Failed to inject ad script:', e);
//       }
//     }, INITIAL_DELAY_MS);

//     // Dọn dẹp bộ đếm thời gian nếu component bị unmount
//     return () => clearTimeout(timer);
//   }, [adDisplayInfo.shouldShow]);

//   return null;
// };

// export default AdManager;
