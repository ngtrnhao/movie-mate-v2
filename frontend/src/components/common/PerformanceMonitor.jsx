// import { useEffect, useRef, useState, useCallback } from 'react';
// import { useImagePreloader } from './ImagePreloader';

// const PerformanceMonitor = ({ enabled = process.env.NODE_ENV === 'development' }) => {
//   const [metrics, setMetrics] = useState({});
//   const [isVisible, setIsVisible] = useState(false);
//   const observerRef = useRef(null);
//   const { getCacheStats } = useImagePreloader();

//   // Memoize getCacheStats để tránh infinite loop
//   const memoizedGetCacheStats = useCallback(() => {
//     return getCacheStats();
//   }, []);

//   useEffect(() => {
//     if (!enabled) return;

//     // Measure initial load performance
//     const measureInitialLoad = () => {
//       const navigation = performance.getEntriesByType('navigation')[0];
//       const paint = performance.getEntriesByType('paint');

//       const fcp = paint.find(entry => entry.name === 'first-contentful-paint');
//       const lcp = paint.find(entry => entry.name === 'largest-contentful-paint');

//       setMetrics(prev => ({
//         ...prev,
//         initialLoad: {
//           domContentLoaded:
//             navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart,
//           loadComplete: navigation?.loadEventEnd - navigation?.loadEventStart,
//           firstContentfulPaint: fcp?.startTime,
//           largestContentfulPaint: lcp?.startTime,
//           totalTime: navigation?.loadEventEnd - navigation?.fetchStart,
//         },
//       }));
//     };

//     // Measure LCP specifically
//     const measureLCP = () => {
//       const observer = new PerformanceObserver(list => {
//         const entries = list.getEntries();
//         const lastEntry = entries[entries.length - 1];

//         setMetrics(prev => ({
//           ...prev,
//           lcp: {
//             value: lastEntry.startTime,
//             element: lastEntry.element?.tagName || 'Unknown',
//             url: lastEntry.url || 'Unknown',
//             size: lastEntry.size || 0,
//           },
//         }));
//       });

//       observer.observe({ entryTypes: ['largest-contentful-paint'] });
//       return () => observer.disconnect();
//     };

//     // Measure resource loading
//     const measureResources = () => {
//       const resources = performance.getEntriesByType('resource');
//       const jsResources = resources.filter(r => r.name.includes('.js'));
//       const cssResources = resources.filter(r => r.name.includes('.css'));
//       const imageResources = resources.filter(
//         r => r.name.includes('.jpg') || r.name.includes('.png') || r.name.includes('.webp')
//       );

//       setMetrics(prev => ({
//         ...prev,
//         resources: {
//           total: resources.length,
//           js: jsResources.length,
//           css: cssResources.length,
//           images: imageResources.length,
//           totalSize: resources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
//           imageSize: imageResources.reduce((sum, r) => sum + (r.transferSize || 0), 0),
//         },
//       }));
//     };

//     // Measure React render performance
//     const measureReactPerformance = () => {
//       const observer = new PerformanceObserver(list => {
//         const entries = list.getEntries();
//         entries.forEach(entry => {
//           if (entry.entryType === 'measure') {
//             setMetrics(prev => ({
//               ...prev,
//               react: {
//                 ...prev.react,
//                 [entry.name]: entry.duration,
//               },
//             }));
//           }
//         });
//       });

//       observer.observe({ entryTypes: ['measure'] });
//       observerRef.current = observer;

//       return () => observer.disconnect();
//     };

//     // Measure layout shifts
//     const measureLayoutShifts = () => {
//       let cls = 0;
//       const observer = new PerformanceObserver(list => {
//         const entries = list.getEntries();
//         entries.forEach(entry => {
//           if (!entry.hadRecentInput) {
//             cls += entry.value;
//           }
//         });

//         setMetrics(prev => ({
//           ...prev,
//           layoutShifts: {
//             cumulative: cls,
//             count: entries.length,
//           },
//         }));
//       });

//       observer.observe({ entryTypes: ['layout-shift'] });
//       return () => observer.disconnect();
//     };

//     // Initialize measurements
//     if (document.readyState === 'complete') {
//       measureInitialLoad();
//       measureResources();
//     } else {
//       window.addEventListener('load', () => {
//         setTimeout(() => {
//           measureInitialLoad();
//           measureResources();
//         }, 100);
//       });
//     }

//     measureReactPerformance();
//     measureLayoutShifts();
//     const lcpCleanup = measureLCP();

//     // Update image cache stats periodically
//     const imageStatsInterval = setInterval(() => {
//       try {
//         const cacheStats = memoizedGetCacheStats();
//         setMetrics(prev => ({
//           ...prev,
//           imageCache: cacheStats,
//         }));
//       } catch (error) {
//         console.warn('Failed to get cache stats:', error);
//       }
//     }, 2000);

//     // Cleanup
//     return () => {
//       if (observerRef.current) {
//         observerRef.current.disconnect();
//       }
//       lcpCleanup();
//       clearInterval(imageStatsInterval);
//     };
//   }, [enabled, memoizedGetCacheStats]);

//   // Toggle visibility
//   const toggleVisibility = () => setIsVisible(!isVisible);

//   if (!enabled) return null;

//   return (
//     <>
//       {/* Toggle button */}
//       <button
//         onClick={toggleVisibility}
//         className="fixed bottom-4 right-4 z-50 rounded-full bg-red-600 p-3 text-white shadow-lg hover:bg-red-700"
//         title="Performance Monitor"
//       >
//         📊
//       </button>

//       {/* Performance panel */}
//       {isVisible && (
//         <div className="fixed bottom-16 right-4 z-50 w-80 rounded-lg bg-gray-900 p-4 text-white shadow-xl">
//           <div className="mb-3 flex items-center justify-between">
//             <h3 className="text-lg font-semibold">Performance Monitor</h3>
//             <button onClick={toggleVisibility} className="text-gray-400 hover:text-white">
//               ✕
//             </button>
//           </div>

//           <div className="space-y-3 text-sm">
//             {/* Initial Load */}
//             {metrics.initialLoad && (
//               <div className="rounded bg-gray-800 p-3">
//                 <h4 className="mb-2 font-medium text-red-400">Initial Load</h4>
//                 <div className="space-y-1">
//                   <div className="flex justify-between">
//                     <span>DOM Ready:</span>
//                     <span>{metrics.initialLoad.domContentLoaded?.toFixed(0)}ms</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>FCP:</span>
//                     <span
//                       className={
//                         metrics.initialLoad.firstContentfulPaint > 1800
//                           ? 'text-red-400'
//                           : 'text-green-400'
//                       }
//                     >
//                       {metrics.initialLoad.firstContentfulPaint?.toFixed(0)}ms
//                     </span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>LCP:</span>
//                     <span
//                       className={
//                         metrics.initialLoad.largestContentfulPaint > 2500
//                           ? 'text-red-400'
//                           : 'text-green-400'
//                       }
//                     >
//                       {metrics.initialLoad.largestContentfulPaint?.toFixed(0)}ms
//                     </span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Total:</span>
//                     <span>{metrics.initialLoad.totalTime?.toFixed(0)}ms</span>
//                   </div>
//                 </div>
//               </div>
//             )}

//             {/* LCP Details */}
//             {metrics.lcp && (
//               <div className="rounded bg-gray-800 p-3">
//                 <h4 className="mb-2 font-medium text-yellow-400">LCP Element</h4>
//                 <div className="space-y-1">
//                   <div className="flex justify-between">
//                     <span>Time:</span>
//                     <span className={metrics.lcp.value > 2500 ? 'text-red-400' : 'text-green-400'}>
//                       {metrics.lcp.value?.toFixed(0)}ms
//                     </span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Element:</span>
//                     <span>{metrics.lcp.element}</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Size:</span>
//                     <span>{(metrics.lcp.size / 1024).toFixed(1)}KB</span>
//                   </div>
//                 </div>
//               </div>
//             )}

//             {/* Resources */}
//             {metrics.resources && (
//               <div className="rounded bg-gray-800 p-3">
//                 <h4 className="mb-2 font-medium text-blue-400">Resources</h4>
//                 <div className="space-y-1">
//                   <div className="flex justify-between">
//                     <span>JS Files:</span>
//                     <span>{metrics.resources.js}</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>CSS Files:</span>
//                     <span>{metrics.resources.css}</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Images:</span>
//                     <span>{metrics.resources.images}</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Image Size:</span>
//                     <span>{(metrics.resources.imageSize / 1024).toFixed(1)}KB</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Total Size:</span>
//                     <span>{(metrics.resources.totalSize / 1024).toFixed(1)}KB</span>
//                   </div>
//                 </div>
//               </div>
//             )}

//             {/* Image Cache */}
//             {metrics.imageCache && (
//               <div className="rounded bg-gray-800 p-3">
//                 <h4 className="mb-2 font-medium text-green-400">Image Cache</h4>
//                 <div className="space-y-1">
//                   <div className="flex justify-between">
//                     <span>Cached:</span>
//                     <span>{metrics.imageCache.cached}</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Queued:</span>
//                     <span>{metrics.imageCache.queued}</span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Loading:</span>
//                     <span>{metrics.imageCache.loading}</span>
//                   </div>
//                 </div>
//               </div>
//             )}

//             {/* Layout Shifts */}
//             {metrics.layoutShifts && (
//               <div className="rounded bg-gray-800 p-3">
//                 <h4 className="mb-2 font-medium text-yellow-400">Layout Shifts</h4>
//                 <div className="space-y-1">
//                   <div className="flex justify-between">
//                     <span>CLS:</span>
//                     <span
//                       className={
//                         metrics.layoutShifts.cumulative > 0.1 ? 'text-red-400' : 'text-green-400'
//                       }
//                     >
//                       {metrics.layoutShifts.cumulative.toFixed(3)}
//                     </span>
//                   </div>
//                   <div className="flex justify-between">
//                     <span>Count:</span>
//                     <span>{metrics.layoutShifts.count}</span>
//                   </div>
//                 </div>
//               </div>
//             )}

//             {/* React Performance */}
//             {metrics.react && Object.keys(metrics.react).length > 0 && (
//               <div className="rounded bg-gray-800 p-3">
//                 <h4 className="mb-2 font-medium text-green-400">React</h4>
//                 <div className="space-y-1">
//                   {Object.entries(metrics.react).map(([key, value]) => (
//                     <div key={key} className="flex justify-between">
//                       <span>{key}:</span>
//                       <span>{value.toFixed(0)}ms</span>
//                     </div>
//                   ))}
//                 </div>
//               </div>
//             )}
//           </div>

//           {/* Performance Score */}
//           <div className="mt-3 rounded bg-gray-800 p-3">
//             <h4 className="mb-2 font-medium text-purple-400">Performance Score</h4>
//             <div className="flex items-center justify-between">
//               <span>Overall:</span>
//               <span className="text-lg font-bold text-green-400">
//                 {calculatePerformanceScore(metrics)}
//               </span>
//             </div>
//           </div>
//         </div>
//       )}
//     </>
//   );
// };

// // Calculate overall performance score
// const calculatePerformanceScore = metrics => {
//   let score = 100;

//   // Deduct points for slow FCP
//   if (metrics.initialLoad?.firstContentfulPaint > 2000) {
//     score -= 20;
//   } else if (metrics.initialLoad?.firstContentfulPaint > 1000) {
//     score -= 10;
//   }

//   // Deduct points for slow LCP
//   if (metrics.initialLoad?.largestContentfulPaint > 4000) {
//     score -= 25;
//   } else if (metrics.initialLoad?.largestContentfulPaint > 2500) {
//     score -= 15;
//   }

//   // Deduct points for high CLS
//   if (metrics.layoutShifts?.cumulative > 0.1) {
//     score -= 20;
//   } else if (metrics.layoutShifts?.cumulative > 0.05) {
//     score -= 10;
//   }

//   // Deduct points for large bundle
//   if (metrics.resources?.totalSize > 2000000) {
//     score -= 15;
//   } else if (metrics.resources?.totalSize > 1000000) {
//     score -= 7;
//   }

//   return Math.max(0, Math.round(score));
// };

// export default PerformanceMonitor;
