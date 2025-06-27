import { useEffect, useRef } from 'react';

// Global image preloader service
class ImagePreloaderService {
  constructor() {
    this.cache = new Map();
    this.queue = new Set();
    this.maxConcurrent = 6; // Giới hạn số lượng image load đồng thời
    this.currentLoading = 0;
  }

  // Preload single image
  preloadImage(src) {
    if (!src || this.cache.has(src) || this.queue.has(src)) {
      return Promise.resolve(src);
    }

    return new Promise((resolve, reject) => {
      this.queue.add(src);

      const loadImage = () => {
        if (this.currentLoading >= this.maxConcurrent) {
          // Queue for later
          setTimeout(loadImage, 100);
          return;
        }

        this.currentLoading++;
        const img = new Image();

        img.onload = () => {
          this.cache.set(src, src);
          this.queue.delete(src);
          this.currentLoading--;
          resolve(src);
        };

        img.onerror = () => {
          this.queue.delete(src);
          this.currentLoading--;
          reject(new Error(`Failed to load image: ${src}`));
        };

        img.src = src;
      };

      loadImage();
    });
  }

  // Preload multiple images
  preloadImages(urls) {
    return Promise.allSettled(urls.map(url => this.preloadImage(url)));
  }

  // Get cache stats
  getCacheStats() {
    return {
      cached: this.cache.size,
      queued: this.queue.size,
      loading: this.currentLoading,
    };
  }

  // Clear cache
  clearCache() {
    this.cache.clear();
    this.queue.clear();
    this.currentLoading = 0;
  }
}

// Global instance
const imagePreloader = new ImagePreloaderService();

// React hook for image preloading
export const useImagePreloader = () => {
  const preloadRef = useRef(new Set());

  const preloadImage = src => {
    if (!src || preloadRef.current.has(src)) {
      return Promise.resolve(src);
    }

    preloadRef.current.add(src);
    return imagePreloader.preloadImage(src);
  };

  const preloadImages = urls => {
    const newUrls = urls.filter(url => !preloadRef.current.has(url));
    newUrls.forEach(url => preloadRef.current.add(url));
    return imagePreloader.preloadImages(newUrls);
  };

  const getCacheStats = () => imagePreloader.getCacheStats();

  return {
    preloadImage,
    preloadImages,
    getCacheStats,
  };
};

// Component for preloading critical images
const ImagePreloader = ({ images = [], children }) => {
  const { preloadImages } = useImagePreloader();

  useEffect(() => {
    if (images.length > 0) {
      preloadImages(images);
    }
  }, [images, preloadImages]);

  return children;
};

export default ImagePreloader;
