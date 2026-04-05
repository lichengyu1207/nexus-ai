import React, { useEffect } from 'react';

interface SEOHeadProps {
  title?: string;
  description?: string;
  keywords?: string;
  image?: string;
  url?: string;
  type?: 'website' | 'article';
  siteName?: string;
}

const SEOHead: React.FC<SEOHeadProps> = ({
  title,
  description,
  keywords,
  image,
  url,
  type = 'website',
  siteName = '房都督AI',
}) => {
  useEffect(() => {
    const fullTitle = title ? `${title} | ${siteName}` : siteName;
    
    document.title = fullTitle;
    
    const setMeta = (name: string, content: string, property = false) => {
      const selector = property ? `meta[property="${name}"]` : `meta[name="${name}"]`;
      let element = document.querySelector(selector) as HTMLMetaElement;
      
      if (!element) {
        element = document.createElement('meta');
        if (property) {
          element.setAttribute('property', name);
        } else {
          element.setAttribute('name', name);
        }
        document.head.appendChild(element);
      }
      element.setAttribute('content', content);
    };

    if (description) {
      setMeta('description', description);
      setMeta('og:description', description, true);
    }

    if (keywords) {
      setMeta('keywords', keywords);
    }

    setMeta('og:title', fullTitle, true);
    setMeta('og:type', type, true);
    setMeta('og:site_name', siteName, true);

    if (image) {
      setMeta('og:image', image, true);
    }

    if (url) {
      setMeta('og:url', url, true);
      const canonical = document.querySelector('link[rel="canonical"]') as HTMLLinkElement;
      if (!canonical) {
        const link = document.createElement('link');
        link.rel = 'canonical';
        link.href = url;
        document.head.appendChild(link);
      } else {
        canonical.href = url;
      }
    }

    return () => {
      // Cleanup optional
    };
  }, [title, description, keywords, image, url, type, siteName]);

  return null;
};

export default SEOHead;
