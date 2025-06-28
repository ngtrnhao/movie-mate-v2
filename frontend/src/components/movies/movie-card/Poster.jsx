import { memo, useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { useInView } from 'react-intersection-observer';
import { useThrottledScroll } from '../../../hooks/useThrottledScroll';
import animationCache from '../../../utils/animationCache';

// Simplified image cache và loading queue
const imageCache = new Set();
const loadingQueue = new Map(); // Track loading priority
let activeLoading = 0;
const MAX_CONCURRENT_LOADING = 3; // Limit concurrent image loads

// Cache để track poster đã từng hiển thị (để tránh animate lại)
const shownPosters = new Set();

const Poster = memo(({ posterPath, title, priority = false, onLoadDone }) => {
  const [isImageLoaded, setIsImageLoaded] = useState(priority || imageCache.has(posterPath));
  const [imageError, setImageError] = useState(false);
  const [hasBeenVisible, setHasBeenVisible] = useState(animationCache.isPosterAnimated(posterPath));

  // Get scroll state để adjust loading behavior
  const { isFastScrolling, isScrolling } = useThrottledScroll();

  // Optimized useInView với dynamic settings based on scroll speed
  const { ref, inView } = useInView({
    triggerOnce: true,
    threshold: isFastScrolling ? 0.3 : 0.1, // Higher threshold khi scroll nhanh
    rootMargin: isFastScrolling ? '20px 0px' : '50px 0px', // Smaller margin khi scroll nhanh
    skip: priority, // Skip observer cho priority images
  });

  const shouldLoadImage = priority || (inView && !isFastScrolling);

  // Smart image loading với queue management
  const loadImageWithQueue = useCallback(
    imagePath => {
      return new Promise((resolve, reject) => {
        // Check cache first
        if (imageCache.has(imagePath)) {
          resolve(imagePath);
          return;
        }

        // Check if already in queue
        if (loadingQueue.has(imagePath)) {
          loadingQueue.get(imagePath).callbacks.push({ resolve, reject });
          return;
        }

        // Add to queue
        loadingQueue.set(imagePath, {
          callbacks: [{ resolve, reject }],
          priority: priority ? 1 : inView ? 2 : 3,
          timestamp: Date.now(),
        });

        // Process queue
        processImageQueue();
      });
    },
    [priority, inView]
  );

  // Process image loading queue với concurrency limit
  const processImageQueue = useCallback(() => {
    if (activeLoading >= MAX_CONCURRENT_LOADING) return;

    // Sort queue by priority (1 = highest)
    const sortedQueue = Array.from(loadingQueue.entries()).sort(([, a], [, b]) => {
      if (a.priority !== b.priority) return a.priority - b.priority;
      return a.timestamp - b.timestamp; // FIFO for same priority
    });

    for (const [imagePath, queueItem] of sortedQueue) {
      if (activeLoading >= MAX_CONCURRENT_LOADING) break;

      activeLoading++;
      loadingQueue.delete(imagePath);

      const img = new Image();

      img.onload = () => {
        imageCache.add(imagePath);
        activeLoading--;

        // Resolve all callbacks for this image
        queueItem.callbacks.forEach(({ resolve }) => resolve(imagePath));

        // Process next in queue
        if (loadingQueue.size > 0) {
          setTimeout(processImageQueue, 10);
        }
      };

      img.onerror = () => {
        activeLoading--;
        queueItem.callbacks.forEach(({ reject }) => reject(new Error('Image load failed')));

        // Process next in queue
        if (loadingQueue.size > 0) {
          setTimeout(processImageQueue, 10);
        }
      };

      img.src = imagePath;
    }
  }, []);

  // Load image when conditions are met
  useEffect(() => {
    if (shouldLoadImage && posterPath && !isImageLoaded && !imageError) {
      // Delay loading khi fast scrolling để prevent flooding
      const delay = isFastScrolling ? 100 : 0;

      const loadTimer = setTimeout(() => {
        loadImageWithQueue(posterPath)
          .then(() => {
            setIsImageLoaded(true);
          })
          .catch(() => {
            setImageError(true);
          });
      }, delay);

      return () => clearTimeout(loadTimer);
    }
  }, [shouldLoadImage, posterPath, isImageLoaded, imageError, isFastScrolling, loadImageWithQueue]);

  // Handle priority loading immediately
  useEffect(() => {
    if (priority && posterPath && !isImageLoaded && !imageError) {
      loadImageWithQueue(posterPath)
        .then(() => setIsImageLoaded(true))
        .catch(() => setImageError(true));
    }
  }, [priority, posterPath, isImageLoaded, imageError, loadImageWithQueue]);

  // Mark poster as shown when it comes into view and image is loaded
  useEffect(() => {
    if (inView && isImageLoaded && posterPath && !hasBeenVisible) {
      animationCache.markPosterAnimated(posterPath);
      setHasBeenVisible(true);
    }
  }, [inView, isImageLoaded, posterPath, hasBeenVisible]);

  const handleImageLoad = useCallback(() => {
    if (posterPath) {
      imageCache.add(posterPath);
      setIsImageLoaded(true);
      if (onLoadDone) onLoadDone();
    }
  }, [posterPath, onLoadDone]);

  const handleImageError = useCallback(() => {
    setImageError(true);
  }, []);

  // Memoize image component với loading state
  const imageComponent = useMemo(() => {
    if (!shouldLoadImage && !priority) {
      // Show placeholder during fast scroll
      return null;
    }

    if (!posterPath) return null;

    // Chỉ animate opacity nếu poster chưa từng được hiển thị trước đó
    const shouldAnimate = !hasBeenVisible;
    const opacityClass = shouldAnimate
      ? isImageLoaded
        ? 'opacity-100'
        : 'opacity-0'
      : 'opacity-100';

    return (
      <img
        src={posterPath}
        alt={title}
        loading={priority ? 'eager' : 'lazy'}
        fetchPriority={priority ? 'high' : 'auto'}
        onLoad={handleImageLoad}
        onError={handleImageError}
        className={`size-full object-cover will-change-transform group-hover:scale-105 ${
          shouldAnimate ? 'transition-opacity duration-300' : ''
        } ${opacityClass}`}
        decoding="async"
      />
    );
  }, [
    shouldLoadImage,
    priority,
    posterPath,
    title,
    isImageLoaded,
    hasBeenVisible,
    handleImageLoad,
    handleImageError,
  ]);

  // Optimized placeholder với loading state
  const placeholder = useMemo(() => {
    const showSpinner = isScrolling && shouldLoadImage && !isImageLoaded && !imageError;

    return (
      <div className="flex size-full items-center justify-center bg-gray-700">
        {showSpinner ? (
          <div className="animate-spin text-2xl">⭘</div>
        ) : (
          <span className="text-4xl text-gray-400">🎬</span>
        )}
      </div>
    );
  }, [isScrolling, shouldLoadImage, isImageLoaded, imageError]);

  // Error placeholder
  const errorPlaceholder = useMemo(
    () => (
      <div className="flex size-full items-center justify-center bg-gray-600">
        <span className="text-2xl text-gray-400">📽️</span>
      </div>
    ),
    []
  );

  return (
    <div ref={ref} className="relative aspect-[2/3] w-full overflow-hidden">
      {/* Image component */}
      {imageComponent}

      {/* Placeholder - với smart loading state */}
      {!isImageLoaded && !imageError && placeholder}

      {/* Error placeholder */}
      {imageError && errorPlaceholder}

      {/* Hover Overlay với CSS-only animation */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/40 to-transparent opacity-0 transition-opacity duration-300 group-hover:opacity-100">
        <div className="absolute inset-x-0 bottom-0 p-4">
          <h3 className="line-clamp-2 text-lg font-semibold text-white">{title}</h3>
        </div>
      </div>
    </div>
  );
});

Poster.displayName = 'Poster';

export default Poster;
