// Global animation cache để track các element đã từng animate
// Sử dụng để tránh re-animate khi component bị unmount/remount

class AnimationCache {
  constructor() {
    this.animatedElements = new Set();
    this.animatedMovies = new Set();
    this.animatedPosters = new Set();
    this.cacheVersion = 'v1.0';
  }

  // Mark movie card as animated
  markMovieAnimated(movieId) {
    if (movieId) {
      this.animatedMovies.add(movieId);
    }
  }

  // Check if movie card has been animated
  isMovieAnimated(movieId) {
    return movieId ? this.animatedMovies.has(movieId) : false;
  }

  // Mark poster as animated
  markPosterAnimated(posterPath) {
    if (posterPath) {
      this.animatedPosters.add(posterPath);
    }
  }

  // Check if poster has been animated
  isPosterAnimated(posterPath) {
    return posterPath ? this.animatedPosters.has(posterPath) : false;
  }

  // Mark generic element as animated
  markElementAnimated(elementId) {
    if (elementId) {
      this.animatedElements.add(elementId);
    }
  }

  // Check if element has been animated
  isElementAnimated(elementId) {
    return elementId ? this.animatedElements.has(elementId) : false;
  }

  // Clear all cache
  clearAll() {
    this.animatedElements.clear();
    this.animatedMovies.clear();
    this.animatedPosters.clear();
  }

  // Clear specific cache
  clearMovies() {
    this.animatedMovies.clear();
  }

  clearPosters() {
    this.animatedPosters.clear();
  }

  // Get cache stats (for debugging)
  getStats() {
    return {
      movies: this.animatedMovies.size,
      posters: this.animatedPosters.size,
      elements: this.animatedElements.size,
      version: this.cacheVersion,
    };
  }

  // Persist cache to localStorage (optional)
  persistToStorage() {
    try {
      const cacheData = {
        animatedMovies: Array.from(this.animatedMovies),
        animatedPosters: Array.from(this.animatedPosters),
        animatedElements: Array.from(this.animatedElements),
        version: this.cacheVersion,
        timestamp: Date.now(),
      };
      localStorage.setItem('animationCache', JSON.stringify(cacheData));
    } catch (error) {
      console.warn('Failed to persist animation cache:', error);
    }
  }

  // Load cache from localStorage (optional)
  loadFromStorage() {
    try {
      const cacheData = localStorage.getItem('animationCache');
      if (cacheData) {
        const parsed = JSON.parse(cacheData);
        if (parsed.version === this.cacheVersion) {
          this.animatedMovies = new Set(parsed.animatedMovies || []);
          this.animatedPosters = new Set(parsed.animatedPosters || []);
          this.animatedElements = new Set(parsed.animatedElements || []);
        }
      }
    } catch (error) {
      console.warn('Failed to load animation cache:', error);
    }
  }
}

// Create singleton instance
const animationCache = new AnimationCache();

// Auto-load from storage on initialization
if (typeof window !== 'undefined') {
  animationCache.loadFromStorage();

  // Auto-save cache periodically
  setInterval(() => {
    animationCache.persistToStorage();
  }, 30000); // Save every 30 seconds
}

export default animationCache;
