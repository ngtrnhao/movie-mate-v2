import { memo, useState, useCallback, useEffect } from 'react';

const RetryImage = memo(
  ({
    src,
    alt,
    fallbackSrc,
    maxRetries = 3,
    retryDelay = 1000,
    className = '',
    onLoad,
    onError,
    loading = 'lazy',
    ...props
  }) => {
    const [imageUrl, setImageUrl] = useState(src);
    const [retryCount, setRetryCount] = useState(0);
    const [isLoading, setIsLoading] = useState(true);
    const [hasError, setHasError] = useState(false);

    // Logic retry cho image loading
    const handleImageError = useCallback(() => {
      if (retryCount < maxRetries) {
        setRetryCount(prev => prev + 1);
        setHasError(true);

        // Retry sau delay
        setTimeout(() => {
          setHasError(false);
          setIsLoading(true);
          // Force re-render bằng cách thay đổi URL
          setImageUrl(`${src}?retry=${retryCount + 1}&t=${Date.now()}`);
        }, retryDelay);
      } else {
        // Sau khi retry hết, sử dụng fallback
        setImageUrl(fallbackSrc);
        setIsLoading(false);
        setHasError(false);
        if (onError) onError();
      }
    }, [retryCount, maxRetries, src, retryDelay, fallbackSrc, onError]);

    const handleImageLoad = useCallback(() => {
      setIsLoading(false);
      setHasError(false);
      if (onLoad) onLoad();
    }, [onLoad]);

    // Update image URL khi src thay đổi
    useEffect(() => {
      setImageUrl(src);
      setRetryCount(0);
      setIsLoading(true);
      setHasError(false);
    }, [src]);

    return (
      <div className={`relative ${className}`}>
        {/* Loading overlay */}
        {isLoading && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800/50">
            <div className="size-8 animate-spin rounded-full border-2 border-red-500 border-t-transparent"></div>
          </div>
        )}

        {/* Error overlay */}
        {hasError && retryCount < maxRetries && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-800/50">
            <div className="text-center text-white">
              <div className="size-8 animate-spin rounded-full border-2 border-red-500 border-t-transparent mx-auto mb-2"></div>
              <p className="text-xs">
                Retrying... ({retryCount + 1}/{maxRetries})
              </p>
            </div>
          </div>
        )}

        {/* Image */}
        <img
          src={imageUrl}
          alt={alt}
          className={`${isLoading ? 'opacity-0' : 'opacity-100'} transition-opacity duration-300`}
          onLoad={handleImageLoad}
          onError={handleImageError}
          loading={loading}
          {...props}
        />
      </div>
    );
  }
);

RetryImage.displayName = 'RetryImage';

export default RetryImage;
