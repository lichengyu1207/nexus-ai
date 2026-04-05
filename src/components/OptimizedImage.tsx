import React, { useState, useRef, useEffect, CSSProperties } from 'react';

interface OptimizedImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  style?: CSSProperties;
  placeholder?: string;
  fallback?: string;
  lazy?: boolean;
  quality?: 'low' | 'medium' | 'high';
  sizes?: string;
  onLoad?: () => void;
  onError?: () => void;
}

const getWebPSrc = (src: string): string | null => {
  if (src.endsWith('.webp')) return null;
  if (src.endsWith('.png') || src.endsWith('.jpg') || src.endsWith('.jpeg')) {
    return src.replace(/\.(png|jpg|jpeg)$/, '.webp');
  }
  return null;
};

const getOptimizedSrc = (src: string, quality: string, width?: number): string => {
  if (src.startsWith('data:') || src.startsWith('blob:')) {
    return src;
  }
  
  const params = new URLSearchParams();
  if (width) params.set('w', width.toString());
  params.set('q', quality === 'low' ? '60' : quality === 'medium' ? '75' : '90');
  
  const separator = src.includes('?') ? '&' : '?';
  return `${src}${separator}${params.toString()}`;
};

export const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  width,
  height,
  className = '',
  style,
  placeholder,
  fallback,
  lazy = true,
  quality = 'medium',
  sizes,
  onLoad,
  onError,
}) => {
  const [isLoaded, setIsLoaded] = useState(false);
  const [hasError, setHasError] = useState(false);
  const [isInView, setIsInView] = useState(!lazy);
  const [currentSrc, setCurrentSrc] = useState<string | null>(null);
  const imgRef = useRef<HTMLImageElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!lazy) return;

    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true);
          observer.disconnect();
        }
      },
      {
        rootMargin: '50px',
        threshold: 0.01,
      }
    );

    if (containerRef.current) {
      observer.observe(containerRef.current);
    }

    return () => observer.disconnect();
  }, [lazy]);

  useEffect(() => {
    if (!isInView) return;

    const webpSrc = getWebPSrc(src);
    
    if (webpSrc && typeof document !== 'undefined') {
      const testImg = document.createElement('picture');
      const testSource = document.createElement('source');
      testSource.srcset = webpSrc;
      testSource.type = 'image/webp';
      testImg.appendChild(testSource);
      
      const img = new Image();
      img.onload = () => setCurrentSrc(webpSrc);
      img.onerror = () => setCurrentSrc(getOptimizedSrc(src, quality, width));
      img.src = webpSrc;
    } else {
      setCurrentSrc(getOptimizedSrc(src, quality, width));
    }
  }, [isInView, src, quality, width]);

  const handleLoad = () => {
    setIsLoaded(true);
    onLoad?.();
  };

  const handleError = () => {
    setHasError(true);
    if (fallback && currentSrc !== fallback) {
      setCurrentSrc(fallback);
    } else {
      onError?.();
    }
  };

  const containerStyle: CSSProperties = {
    position: 'relative',
    width: width ? `${width}px` : '100%',
    height: height ? `${height}px` : 'auto',
    overflow: 'hidden',
    backgroundColor: placeholder || '#f3f4f6',
    ...style,
  };

  const placeholderStyle: CSSProperties = {
    position: 'absolute',
    top: 0,
    left: 0,
    width: '100%',
    height: '100%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#f3f4f6',
  };

  return (
    <div ref={containerRef} className={className} style={containerStyle}>
      {!isLoaded && !hasError && (
        <div style={placeholderStyle}>
          <svg
            className="animate-pulse"
            width="40"
            height="40"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
            <circle cx="8.5" cy="8.5" r="1.5" />
            <polyline points="21 15 16 10 5 21" />
          </svg>
        </div>
      )}
      
      {isInView && currentSrc && (
        <img
          ref={imgRef}
          src={currentSrc}
          alt={alt}
          width={width}
          height={height}
          loading={lazy ? 'lazy' : 'eager'}
          decoding="async"
          sizes={sizes}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            opacity: isLoaded ? 1 : 0,
            transition: 'opacity 0.3s ease-in-out',
          }}
          onLoad={handleLoad}
          onError={handleError}
        />
      )}

      {hasError && fallback && (
        <img
          src={fallback}
          alt={alt}
          width={width}
          height={height}
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
          }}
        />
      )}
    </div>
  );
};

export const ResponsiveImage: React.FC<{
  srcSet: { [key: string]: string };
  alt: string;
  className?: string;
  sizes?: string;
  lazy?: boolean;
}> = ({ srcSet, alt, className, sizes = '100vw', lazy = true }) => {
  const sources = Object.entries(srcSet).map(([width, src]) => `${src} ${width}w`).join(', ');
  
  return (
    <img
      src={Object.values(srcSet)[0]}
      srcSet={sources}
      sizes={sizes}
      alt={alt}
      loading={lazy ? 'lazy' : 'eager'}
      decoding="async"
      className={className}
    />
  );
};

export const AvatarImage: React.FC<{
  src?: string;
  alt: string;
  size?: number;
  className?: string;
}> = ({ src, alt, size = 40, className = '' }) => {
  const fallbackSrc = `https://ui-avatars.com/api/?name=${encodeURIComponent(alt)}&size=${size}&background=random`;
  
  return (
    <OptimizedImage
      src={src || fallbackSrc}
      alt={alt}
      width={size}
      height={size}
      fallback={fallbackSrc}
      lazy
      className={`rounded-full ${className}`}
      style={{ borderRadius: '50%' }}
    />
  );
};

export default OptimizedImage;
