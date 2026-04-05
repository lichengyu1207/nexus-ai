import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Button,
  IconButton,
  Skeleton,
  Alert,
  Chip,
  Divider,
  Card,
  CardContent,
  Avatar,
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Share as ShareIcon,
  Visibility as ViewIcon,
  Favorite as FavoriteIcon,
  LocationOn as LocationIcon,
  AccessTime as TimeIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import ReactMarkdown from 'react-markdown';
import { useParams, useNavigate } from 'react-router-dom';

interface ArticleDetail {
  id: string;
  community_id: string;
  community_name: string;
  city: string | null;
  district: string | null;
  title: string;
  summary: string | null;
  content: string;
  seo_title: string | null;
  seo_description: string | null;
  seo_keywords: string | null;
  slug: string | null;
  status: string;
  views: number;
  published_at: string | null;
  created_at: string | null;
}

const ArticleDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [article, setArticle] = useState<ArticleDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchArticle = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/communities/article/${id}`);
      const data = await response.json();
      if (data.success) {
        setArticle(data.data);
        if (data.data.seo_title) {
          document.title = data.data.seo_title;
        }
        if (data.data.seo_description) {
          const metaDesc = document.querySelector('meta[name="description"]');
          if (metaDesc) {
            metaDesc.setAttribute('content', data.data.seo_description);
          }
        }
        if (data.data.seo_keywords) {
          const metaKeywords = document.querySelector('meta[name="keywords"]');
          if (metaKeywords) {
            metaKeywords.setAttribute('content', data.data.seo_keywords);
          }
        }
      } else {
        setError('文章不存在');
      }
    } catch (err) {
      setError('网络错误');
      console.error('Failed to fetch article:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    fetchArticle();
    return () => {
      document.title = '房都督AI';
    };
  }, [fetchArticle]);

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: article?.title,
        text: article?.summary || article?.title,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      alert('链接已复制到剪贴板');
    }
  };

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '未知';
    return new Date(dateStr).toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Skeleton variant="text" height={60} />
        <Skeleton variant="text" width="40%" />
        <Skeleton variant="rectangular" height={400} sx={{ mt: 3 }} />
      </Container>
    );
  }

  if (error || !article) {
    return (
      <Container maxWidth="md" sx={{ py: 4 }}>
        <Alert severity="error">{error || '文章不存在'}</Alert>
        <Button startIcon={<ArrowBackIcon />} onClick={() => navigate(-1)} sx={{ mt: 2 }}>
          返回
        </Button>
      </Container>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 6,
        }}
      >
        <Container maxWidth="md">
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate(-1)}
            sx={{ color: 'white', mb: 2 }}
          >
            返回
          </Button>
          <Typography variant="h4" fontWeight="bold" gutterBottom>
            {article.title}
          </Typography>
          {article.summary && (
            <Typography variant="body1" sx={{ opacity: 0.9, mt: 2 }}>
              {article.summary}
            </Typography>
          )}
          <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 2, mt: 3, opacity: 0.9 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <LocationIcon fontSize="small" />
              <Typography variant="body2">
                {[article.city, article.district].filter(Boolean).join(' · ')}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <TimeIcon fontSize="small" />
              <Typography variant="body2">{formatDate(article.published_at)}</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <ViewIcon fontSize="small" />
              <Typography variant="body2">{article.views} 次阅读</Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            {article.seo_keywords?.split(',').slice(0, 5).map((keyword, index) => (
              <Chip
                key={index}
                label={keyword.trim()}
                size="small"
                sx={{ bgcolor: 'rgba(255,255,255,0.2)', color: 'white' }}
              />
            ))}
          </Box>
        </Container>
      </Box>

      <Container maxWidth="md" sx={{ py: 4 }}>
        <Paper sx={{ p: { xs: 2, md: 4 } }}>
          <Box
            sx={{
              '& h1': { fontSize: '1.75rem', fontWeight: 'bold', mt: 3, mb: 2 },
              '& h2': { fontSize: '1.5rem', fontWeight: 'bold', mt: 3, mb: 2 },
              '& h3': { fontSize: '1.25rem', fontWeight: 'bold', mt: 2, mb: 1 },
              '& h4': { fontSize: '1.1rem', fontWeight: 'bold', mt: 2, mb: 1 },
              '& p': { mb: 2, lineHeight: 1.8 },
              '& ul, & ol': { pl: 3, mb: 2 },
              '& li': { mb: 0.5, lineHeight: 1.6 },
              '& blockquote': {
                borderLeft: '4px solid',
                borderColor: 'primary.main',
                pl: 2,
                py: 1,
                my: 2,
                bgcolor: 'grey.100',
                fontStyle: 'italic',
              },
              '& code': {
                bgcolor: 'grey.100',
                px: 0.5,
                py: 0.25,
                borderRadius: 0.5,
                fontFamily: 'monospace',
              },
              '& pre': {
                bgcolor: 'grey.900',
                color: 'grey.100',
                p: 2,
                borderRadius: 1,
                overflow: 'auto',
                my: 2,
              },
              '& pre code': {
                bgcolor: 'transparent',
                p: 0,
              },
              '& table': {
                width: '100%',
                borderCollapse: 'collapse',
                my: 2,
              },
              '& th, & td': {
                border: '1px solid',
                borderColor: 'divider',
                p: 1,
                textAlign: 'left',
              },
              '& th': {
                bgcolor: 'grey.100',
                fontWeight: 'bold',
              },
              '& hr': {
                border: 'none',
                borderTop: '1px solid',
                borderColor: 'divider',
                my: 3,
              },
              '& img': {
                maxWidth: '100%',
                height: 'auto',
                borderRadius: 1,
                my: 2,
              },
              '& a': {
                color: 'primary.main',
                textDecoration: 'none',
                '&:hover': {
                  textDecoration: 'underline',
                },
              },
            }}
          >
            <ReactMarkdown>{article.content}</ReactMarkdown>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button
              variant="outlined"
              startIcon={<ArrowBackIcon />}
              onClick={() => navigate(`/communities/${article.community_id}`)}
            >
              查看小区详情
            </Button>
            <Button variant="contained" startIcon={<ShareIcon />} onClick={handleShare}>
              分享文章
            </Button>
          </Box>
        </Paper>

        <Card sx={{ mt: 3 }}>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              关于 {article.community_name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              本文由房都督平台自动生成，内容基于公开数据和AI分析。仅供参考，不构成投资建议。
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
              发布时间：{formatDate(article.published_at)}
            </Typography>
          </CardContent>
        </Card>
      </Container>
    </Box>
  );
};

export default ArticleDetailPage;
