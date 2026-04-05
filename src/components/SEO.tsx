import React from 'react';
import { Helmet } from 'react-helmet-async';
import { useTranslation } from 'react-i18next';

interface SEOProps {
  title?: string;
  description?: string;
  keywords?: string;
  image?: string;
  url?: string;
  type?: 'website' | 'article';
  author?: string;
  publishedTime?: string;
  modifiedTime?: string;
}

const SEO: React.FC<SEOProps> = ({
  title,
  description,
  keywords = '房产分析, 房产评估, 房价查询, 智能分析, AI房产, 房产数据, 房产投资',
  image = '/og-image.png',
  url = '',
  type = 'website',
  author,
  publishedTime,
  modifiedTime,
}) => {
  const { t, i18n } = useTranslation();
  
  const defaultTitle = `${t('landing.appNameEn')}AI - ${t('home.description').split('，')[0]}`;
  const defaultDescription = t('home.description');
  const defaultAuthor = `${t('landing.appNameEn')}AI`;
  
  const finalTitle = title || defaultTitle;
  const finalDescription = description || defaultDescription;
  const finalAuthor = author || defaultAuthor;
  const siteUrl = 'https://www.fangtanai.com';
  const fullUrl = url ? `${siteUrl}${url}` : siteUrl;
  const fullImage = image.startsWith('http') ? image : `${siteUrl}${image}`;

  return (
    <Helmet>
      <title>{finalTitle}</title>
      <meta name="description" content={finalDescription} />
      <meta name="keywords" content={keywords} />
      <meta name="author" content={finalAuthor} />
      <meta name="robots" content="index, follow" />
      <link rel="canonical" href={fullUrl} />

      <meta property="og:type" content={type} />
      <meta property="og:title" content={finalTitle} />
      <meta property="og:description" content={finalDescription} />
      <meta property="og:image" content={fullImage} />
      <meta property="og:url" content={fullUrl} />
      <meta property="og:site_name" content={finalAuthor} />
      <meta property="og:locale" content={i18n.language === 'zh' ? 'zh_CN' : 'en_US'} />

      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={finalTitle} />
      <meta name="twitter:description" content={finalDescription} />
      <meta name="twitter:image" content={fullImage} />

      {publishedTime && (
        <meta property="article:published_time" content={publishedTime} />
      )}
      {modifiedTime && (
        <meta property="article:modified_time" content={modifiedTime} />
      )}

      <script type="application/ld+json">
        {JSON.stringify({
          '@context': 'https://schema.org',
          '@type': type === 'article' ? 'Article' : 'WebPage',
          name: finalTitle,
          description: finalDescription,
          url: fullUrl,
          image: fullImage,
          author: {
            '@type': 'Organization',
            name: finalAuthor,
          },
          publisher: {
            '@type': 'Organization',
            name: finalAuthor,
            logo: {
              '@type': 'ImageObject',
              url: `${siteUrl}/logo.png`,
            },
          },
          ...(publishedTime && { datePublished: publishedTime }),
          ...(modifiedTime && { dateModified: modifiedTime }),
        })}
      </script>
    </Helmet>
  );
};

export default SEO;
