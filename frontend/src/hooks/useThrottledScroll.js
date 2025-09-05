import { useState, useEffect, useRef } from 'react';

/**
 * Custom hook để throttle scroll events và prevent flooding
 * Giảm số lần intersection observers trigger khi scroll nhanh
 */
export const useThrottledScroll = (delay = 16) => {
  const [isScrolling, setIsScrolling] = useState(false);
  const [scrollDirection, setScrollDirection] = useState('down');
  const [scrollSpeed, setScrollSpeed] = useState(0);

  const lastScrollY = useRef(0);
  const lastScrollTime = useRef(Date.now());
  const throttleTimer = useRef(null);
  const scrollEndTimer = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      const currentScrollY = window.scrollY;
      const currentTime = Date.now();

      // Calculate scroll speed
      const scrollDistance = Math.abs(currentScrollY - lastScrollY.current);
      const scrollTime = currentTime - lastScrollTime.current;
      const speed = scrollTime > 0 ? scrollDistance / scrollTime : 0;

      // Update direction
      const direction = currentScrollY > lastScrollY.current ? 'down' : 'up';

      // Throttle updates
      if (throttleTimer.current) {
        clearTimeout(throttleTimer.current);
      }

      throttleTimer.current = setTimeout(() => {
        setScrollDirection(direction);
        setScrollSpeed(speed);
        setIsScrolling(true);

        // Clear scroll end timer
        if (scrollEndTimer.current) {
          clearTimeout(scrollEndTimer.current);
        }

        // Set scroll end timer
        scrollEndTimer.current = setTimeout(() => {
          setIsScrolling(false);
          setScrollSpeed(0);
        }, 150); // Consider scrolling stopped after 150ms
      }, delay);

      lastScrollY.current = currentScrollY;
      lastScrollTime.current = currentTime;
    };

    window.addEventListener('scroll', handleScroll, { passive: true });

    return () => {
      window.removeEventListener('scroll', handleScroll);
      if (throttleTimer.current) clearTimeout(throttleTimer.current);
      if (scrollEndTimer.current) clearTimeout(scrollEndTimer.current);
    };
  }, [delay]);

  return {
    isScrolling,
    scrollDirection,
    scrollSpeed,
    isFastScrolling: scrollSpeed > 2, // Threshold for fast scrolling
  };
};
