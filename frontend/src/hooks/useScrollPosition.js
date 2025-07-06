import { useLayoutEffect, useRef } from 'react';
import { useLocation } from 'react-router-dom';

// Singleton scroll position manager
class ScrollPositionManager {
  constructor() {
    this.storageKey = 'moviemate_scroll_positions';
    this.isInitialized = false;
    this.currentPath = null;
    this.isRestoring = false;
    this.navigationMethod = 'unknown'; // 'programmatic', 'browser_back', etc.
  }

  init() {
    if (this.isInitialized) return;

    // Save scroll position before page unload
    window.addEventListener('beforeunload', () => {
      this.saveCurrentPosition();
    });

    // Listen for popstate (browser back/forward)
    window.addEventListener('popstate', event => {
      this.navigationMethod = 'browser_back';
      console.log('🔙 Browser back/forward detected');
    });

    this.isInitialized = true;
  }

  getStoredPositions() {
    try {
      const stored = sessionStorage.getItem(this.storageKey);
      return stored ? JSON.parse(stored) : {};
    } catch {
      return {};
    }
  }

  savePosition(path, position) {
    if (this.isRestoring) {
      console.log(`⏸️ Skipping save during restoration`);
      return; // Don't save while restoring
    }

    try {
      const positions = this.getStoredPositions();
      const previousPosition = positions[path];

      // Only save if position has changed significantly (more than 50px)
      if (previousPosition === undefined || Math.abs(previousPosition - position) > 50) {
        positions[path] = position;
        sessionStorage.setItem(this.storageKey, JSON.stringify(positions));
        console.log(
          `📍 Saved scroll position: ${position} for path: ${path} (previous: ${previousPosition || 'none'})`
        );
      } else {
        console.log(`⏭️ Position unchanged, skipping save: ${position}`);
      }
    } catch (error) {
      console.error('Failed to save scroll position:', error);
    }
  }

  saveCurrentPosition() {
    if (this.currentPath === '/movies' && !this.isRestoring) {
      this.savePosition('/movies', window.scrollY);
    }
  }

  restorePosition(path) {
    if (this.isRestoring) return;

    const positions = this.getStoredPositions();
    const savedPosition = positions[path];

    if (savedPosition !== undefined && savedPosition > 0) {
      console.log(
        `🔄 Restoring scroll position: ${savedPosition} for path: ${path} (method: ${this.navigationMethod})`
      );

      this.isRestoring = true;
      let attempts = 0;
      const maxAttempts = 3; // Reduced attempts

      const attemptRestore = () => {
        attempts++;

        // Scroll to the saved position
        window.scrollTo({
          top: savedPosition,
          behavior: 'auto',
        });

        // Check if we reached the target position after a delay
        setTimeout(() => {
          const currentPosition = window.scrollY;
          const difference = Math.abs(currentPosition - savedPosition);

          console.log(
            `📊 Attempt ${attempts}: Target=${savedPosition}, Current=${currentPosition}, Diff=${difference}`
          );

          if (difference > 100 && attempts < maxAttempts) {
            // If we're not close enough and haven't exceeded max attempts, try again
            console.log(`🔄 Retry attempt ${attempts + 1}`);
            setTimeout(attemptRestore, 150 * attempts); // Shorter delay
          } else {
            // We're close enough or we've tried enough times
            console.log(
              `✅ Scroll restoration ${difference <= 100 ? 'successful' : 'completed'} after ${attempts} attempts`
            );

            // Reset flag after completion
            setTimeout(() => {
              this.isRestoring = false;
              this.navigationMethod = 'unknown'; // Reset
            }, 200);
          }
        }, 50); // Shorter delay
      };

      // Start restoration immediately for browser back, with delay for programmatic navigation
      const startDelay = this.navigationMethod === 'browser_back' ? 0 : 100;

      setTimeout(() => {
        // Wait for content to load first
        if (document.readyState === 'complete') {
          attemptRestore();
        } else {
          window.addEventListener('load', attemptRestore, { once: true });
        }
      }, startDelay);

      return true;
    }
    return false;
  }

  updateCurrentPath(path) {
    // Simply update the current path - saving is handled in useLayoutEffect
    this.currentPath = path;
  }
}

// Global singleton instance
const scrollManager = new ScrollPositionManager();

export const useScrollPosition = () => {
  const location = useLocation();
  const isFirstRender = useRef(true);

  // Initialize manager once
  useLayoutEffect(() => {
    scrollManager.init();
  }, []);

  // Handle path changes
  useLayoutEffect(() => {
    const previousPath = scrollManager.currentPath;
    const currentPath = location.pathname;

    console.log(
      `🚀 Path change: ${previousPath} → ${currentPath} (method: ${scrollManager.navigationMethod})`
    );

    // Save previous position before updating current path
    if (previousPath === '/movies' && currentPath !== '/movies' && !scrollManager.isRestoring) {
      const currentPosition = window.scrollY;
      console.log(`💾 Saving position before leaving movies: ${currentPosition}`);
      scrollManager.savePosition('/movies', currentPosition);
    }

    // Update current path in manager
    scrollManager.updateCurrentPath(currentPath);

    // Handle movies page entry
    if (currentPath === '/movies') {
      const positions = scrollManager.getStoredPositions();
      const savedPosition = positions['/movies'];

      if (savedPosition !== undefined && savedPosition > 0) {
        // For browser back navigation, prevent scroll flash immediately
        if (scrollManager.navigationMethod === 'browser_back') {
          console.log(`⚡ Immediate scroll prevention for browser back: ${savedPosition}`);
          window.scrollTo(0, savedPosition);
        }

        // Then do proper restoration
        setTimeout(
          () => {
            if (scrollManager.restorePosition('/movies')) {
              console.log(`🎯 Restoration initiated for /movies`);
            }
          },
          scrollManager.navigationMethod === 'browser_back' ? 10 : 50
        );
      } else {
        console.log(`📍 No saved position found for /movies`);
      }
    }

    // Reset navigation method after handling
    if (scrollManager.navigationMethod !== 'unknown') {
      setTimeout(() => {
        scrollManager.navigationMethod = 'unknown';
      }, 1000);
    }

    isFirstRender.current = false;
  }, [location.pathname]);

  // Save position on unmount
  useLayoutEffect(() => {
    return () => {
      scrollManager.saveCurrentPosition();
    };
  }, []);

  return {
    saveScrollPosition: () => {
      scrollManager.saveCurrentPosition();
    },
  };
};
