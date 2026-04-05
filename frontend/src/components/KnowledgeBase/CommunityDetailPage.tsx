import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  Grid,
  Chip,
  Button,
  IconButton,
  Divider,
  Skeleton,
  Alert,
  Card,
  CardContent,
  Avatar,
  Rating,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Snackbar,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
} from '@mui/material';
import {
  LocationOn as LocationIcon,
  AttachMoney as MoneyIcon,
  Home as HomeIcon,
  Business as BusinessIcon,
  Apartment as ApartmentIcon,
  Park as ParkIcon,
  LocalHospital as HospitalIcon,
  School as SchoolIcon,
  Subway as SubwayIcon,
  ShoppingBag as MallIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Share as ShareIcon,
  Visibility as ViewIcon,
  Article as ArticleIcon,
  TrendingUp as TrendingIcon,
  ArrowBack as ArrowBackIcon,
  Star as StarIcon,
  Send as SendIcon,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from 'recharts';

interface CommunityDetail {
  id: string;
  name: string;
  alias: string | null;
  city: string | null;
  district: string | null;
  street: string | null;
  address: string | null;
  lng: number | null;
  lat: number | null;
  avg_price: number | null;
  price_unit: string;
  total_units: number | null;
  completion_year: number | null;
  developer: string | null;
  property_company: string | null;
  property_fee: number | null;
  green_rate: number | null;
  volume_rate: number | null;
  parking_ratio: number | null;
  building_type: string | null;
  heating_type: string | null;
  description: string | null;
  data_source: string | null;
  confidence: number | null;
  view_count: number;
  favorite_count: number;
  price_trend: Array<{ date: string; price: number }>;
  pois: Record<string, Array<{ id: string; name: string; address: string | null; distance: number | null; rating: number | null }>>;
  article: {
    id: string;
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
  } | null;
  created_at: string | null;
}

interface Review {
  id: string;
  user_id: string;
  rating: number;
  content: string;
  is_anonymous: boolean;
  created_at: string;
}

const POI_ICONS: Record<string, React.ReactElement> = {
  school: <SchoolIcon />,
  hospital: <HospitalIcon />,
  subway: <SubwayIcon />,
  mall: <MallIcon />,
  park: <ParkIcon />,
};

const POI_NAMES: Record<string, string> = {
  school: '教育资源',
  hospital: '医疗资源',
  subway: '交通出行',
  mall: '商业配套',
  park: '休闲娱乐',
};

const CommunityDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [community, setCommunity] = useState<CommunityDetail | null>(null);
  const [reviews, setReviews] = useState<Review[]>([]);
  const [reviewStats, setReviewStats] = useState({ total: 0, avg_rating: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFavorited, setIsFavorited] = useState(false);
  const [tabValue, setTabValue] = useState(0);
  const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
  const [newReview, setNewReview] = useState({ rating: 5, content: '' });
  const [snackbar, setSnackbar] = useState({ open: false, message: '' });

  const fetchCommunityDetail = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/communities/${id}`);
      const data = await response.json();
      if (data.success) {
        setCommunity(data.data);
      } else {
        setError('获取小区信息失败');
      }
    } catch (err) {
      setError('网络错误');
      console.error('Failed to fetch community:', err);
    } finally {
      setLoading(false);
    }
  }, [id]);

  const fetchReviews = useCallback(async () => {
    if (!id) return;
    try {
      const response = await fetch(`/api/communities/${id}/reviews`);
      const data = await response.json();
      if (data.success) {
        setReviews(data.data);
        setReviewStats(data.stats);
      }
    } catch (err) {
      console.error('Failed to fetch reviews:', err);
    }
  }, [id]);

  useEffect(() => {
    fetchCommunityDetail();
    fetchReviews();
  }, [fetchCommunityDetail, fetchReviews]);

  const handleFavorite = async () => {
    const userId = 'demo-user';
    try {
      const response = await fetch(`/api/communities/${id}/favorite?user_id=${userId}`, {
        method: 'POST',
      });
      const data = await response.json();
      if (data.success) {
        setIsFavorited(data.action === 'favorited');
        setSnackbar({ open: true, message: data.message });
        fetchCommunityDetail();
      }
    } catch (err) {
      console.error('Failed to toggle favorite:', err);
    }
  };

  const handleSubmitReview = async () => {
    if (!newReview.content.trim()) return;
    const userId = 'demo-user';
    try {
      const response = await fetch(
        `/api/communities/${id}/review?user_id=${userId}&rating=${newReview.rating}&content=${encodeURIComponent(newReview.content)}`,
        { method: 'POST' }
      );
      const data = await response.json();
      if (data.success) {
        setSnackbar({ open: true, message: '评论提交成功' });
        setReviewDialogOpen(false);
        setNewReview({ rating: 5, content: '' });
        fetchReviews();
      }
    } catch (err) {
      console.error('Failed to submit review:', err);
    }
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return '暂无';
    if (price >= 10000) {
      return `${(price / 10000).toFixed(1)}万`;
    }
    return price.toLocaleString();
  };

  const handleShare = () => {
    if (navigator.share) {
      navigator.share({
        title: community?.name,
        text: `${community?.name} - ${community?.city}${community?.district}，均价${formatPrice(community?.avg_price)}元/㎡`,
        url: window.location.href,
      });
    } else {
      navigator.clipboard.writeText(window.location.href);
      setSnackbar({ open: true, message: '链接已复制到剪贴板' });
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Skeleton variant="rectangular" height={200} sx={{ mb: 3 }} />
        <Skeleton variant="text" height={40} />
        <Skeleton variant="text" height={20} />
        <Skeleton variant="rectangular" height={300} sx={{ mt: 3 }} />
      </Container>
    );
  }

  if (error || !community) {
    return (
      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Alert severity="error">{error || '小区不存在'}</Alert>
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
          py: 4,
        }}
      >
        <Container maxWidth="lg">
          <Button
            startIcon={<ArrowBackIcon />}
            onClick={() => navigate('/communities')}
            sx={{ color: 'white', mb: 2 }}
          >
            返回知识库
          </Button>
          <Typography variant="h4" fontWeight="bold">
            {community.name}
            {community.alias && (
              <Typography component="span" variant="h6" sx={{ ml: 2, opacity: 0.8 }}>
                ({community.alias})
              </Typography>
            )}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', mt: 1, opacity: 0.9 }}>
            <LocationIcon fontSize="small" sx={{ mr: 1 }} />
            <Typography>
              {[community.city, community.district, community.address].filter(Boolean).join(' · ')}
            </Typography>
          </Box>
          <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 2, mt: 3 }}>
            <Typography variant="h3" fontWeight="bold">
              {formatPrice(community.avg_price)}
            </Typography>
            <Typography variant="h6">{community.price_unit}</Typography>
          </Box>
          <Box sx={{ display: 'flex', gap: 2, mt: 2 }}>
            <Button
              variant="contained"
              startIcon={isFavorited ? <FavoriteIcon /> : <FavoriteBorderIcon />}
              onClick={handleFavorite}
              sx={{ bgcolor: 'white', color: 'primary.main', '&:hover': { bgcolor: 'grey.100' } }}
            >
              {isFavorited ? '已收藏' : '收藏'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<ShareIcon />}
              onClick={handleShare}
              sx={{ borderColor: 'white', color: 'white' }}
            >
              分享
            </Button>
          </Box>
        </Container>
      </Box>

      <Container maxWidth="lg" sx={{ py: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={8}>
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                基本信息
              </Typography>
              <Grid container spacing={2}>
                {[
                  { icon: <BusinessIcon />, label: '开发商', value: community.developer },
                  { icon: <ApartmentIcon />, label: '物业公司', value: community.property_company },
                  { icon: <MoneyIcon />, label: '物业费', value: community.property_fee ? `${community.property_fee}元/㎡/月` : null },
                  { icon: <HomeIcon />, label: '建成年代', value: community.completion_year ? `${community.completion_year}年` : null },
                  { icon: <HomeIcon />, label: '总户数', value: community.total_units ? `${community.total_units}户` : null },
                  { icon: <ParkIcon />, label: '绿化率', value: community.green_rate ? `${(community.green_rate * 100).toFixed(1)}%` : null },
                ]
                  .filter((item) => item.value)
                  .map((item, index) => (
                    <Grid item xs={6} sm={4} key={index}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Box sx={{ color: 'primary.main' }}>{item.icon}</Box>
                        <Box>
                          <Typography variant="caption" color="text.secondary">
                            {item.label}
                          </Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {item.value}
                          </Typography>
                        </Box>
                      </Box>
                    </Grid>
                  ))}
              </Grid>
              {community.description && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                    小区简介
                  </Typography>
                  <Typography variant="body2">{community.description}</Typography>
                </Box>
              )}
            </Paper>

            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                <TrendingIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                价格走势
              </Typography>
              {community.price_trend.length > 0 ? (
                <Box sx={{ height: 300 }}>
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={community.price_trend}>
                      <CartesianGrid strokeDasharray="3 3" />
                      <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                      <YAxis
                        tickFormatter={(value) => `${(value / 10000).toFixed(0)}万`}
                        tick={{ fontSize: 12 }}
                      />
                      <Tooltip
                        formatter={(value: number) => [`${formatPrice(value)}元/㎡`, '均价']}
                      />
                      <Line
                        type="monotone"
                        dataKey="price"
                        stroke="#667eea"
                        strokeWidth={2}
                        dot={{ fill: '#667eea' }}
                      />
                    </LineChart>
                  </ResponsiveContainer>
                </Box>
              ) : (
                <Typography color="text.secondary">暂无价格走势数据</Typography>
              )}
            </Paper>

            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                周边配套
              </Typography>
              {Object.keys(community.pois).length > 0 ? (
                <Grid container spacing={3}>
                  {Object.entries(community.pois).map(([type, items]) => (
                    <Grid item xs={12} sm={6} key={type}>
                      <Card variant="outlined">
                        <CardContent>
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                            <Box sx={{ color: 'primary.main' }}>
                              {POI_ICONS[type] || <LocationIcon />}
                            </Box>
                            <Typography variant="subtitle1" fontWeight="bold">
                              {POI_NAMES[type] || type}
                            </Typography>
                          </Box>
                          <List dense>
                            {items.slice(0, 5).map((poi) => (
                              <ListItem key={poi.id} sx={{ px: 0 }}>
                                <ListItemText
                                  primary={poi.name}
                                  secondary={poi.distance ? `距离 ${Math.round(poi.distance)}米` : null}
                                />
                                {poi.rating && (
                                  <Box sx={{ display: 'flex', alignItems: 'center' }}>
                                    <StarIcon sx={{ fontSize: 16, color: 'warning.main', mr: 0.5 }} />
                                    <Typography variant="caption">{poi.rating}</Typography>
                                  </Box>
                                )}
                              </ListItem>
                            ))}
                          </List>
                        </CardContent>
                      </Card>
                    </Grid>
                  ))}
                </Grid>
              ) : (
                <Typography color="text.secondary">暂无周边配套数据</Typography>
              )}
            </Paper>

            {community.article && (
              <Paper sx={{ p: 3, mb: 3 }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                  <Typography variant="h6" fontWeight="bold">
                    <ArticleIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
                    专业分析文章
                  </Typography>
                  <Button
                    variant="outlined"
                    onClick={() => navigate(`/community/article/${community.article?.id}`)}
                  >
                    阅读全文
                  </Button>
                </Box>
                <Typography variant="h6" gutterBottom>
                  {community.article.title}
                </Typography>
                {community.article.summary && (
                  <Typography color="text.secondary" paragraph>
                    {community.article.summary}
                  </Typography>
                )}
              </Paper>
            )}

            <Paper sx={{ p: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" fontWeight="bold">
                  用户评价 ({reviewStats.total})
                </Typography>
                <Button variant="contained" onClick={() => setReviewDialogOpen(true)}>
                  写评价
                </Button>
              </Box>
              {reviewStats.avg_rating > 0 && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Rating value={reviewStats.avg_rating} precision={0.1} readOnly />
                  <Typography>{reviewStats.avg_rating.toFixed(1)}分</Typography>
                </Box>
              )}
              {reviews.length > 0 ? (
                reviews.map((review) => (
                  <Box key={review.id} sx={{ py: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                      <Avatar sx={{ width: 32, height: 32 }}>
                        {review.user_id[0].toUpperCase()}
                      </Avatar>
                      <Typography variant="body2">{review.user_id.slice(0, 8)}***</Typography>
                      <Rating value={review.rating} size="small" readOnly />
                    </Box>
                    <Typography variant="body2">{review.content}</Typography>
                  </Box>
                ))
              ) : (
                <Typography color="text.secondary">暂无评价</Typography>
              )}
            </Paper>
          </Grid>

          <Grid item xs={12} md={4}>
            <Paper sx={{ p: 3, position: 'sticky', top: 20 }}>
              <Typography variant="h6" fontWeight="bold" gutterBottom>
                统计信息
              </Typography>
              <Box sx={{ display: 'flex', justifyContent: 'space-around', py: 2 }}>
                <Box sx={{ textAlign: 'center' }}>
                  <ViewIcon sx={{ fontSize: 32, color: 'primary.main' }} />
                  <Typography variant="h6">{community.view_count}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    浏览量
                  </Typography>
                </Box>
                <Box sx={{ textAlign: 'center' }}>
                  <FavoriteIcon sx={{ fontSize: 32, color: 'error.main' }} />
                  <Typography variant="h6">{community.favorite_count}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    收藏数
                  </Typography>
                </Box>
              </Box>
              <Divider sx={{ my: 2 }} />
              <Typography variant="body2" color="text.secondary">
                数据来源：{community.data_source || '网络采集'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                数据可信度：{community.confidence ? `${(community.confidence * 100).toFixed(0)}%` : '80%'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                更新时间：{community.created_at ? new Date(community.created_at).toLocaleDateString() : '未知'}
              </Typography>
            </Paper>
          </Grid>
        </Grid>
      </Container>

      <Dialog open={reviewDialogOpen} onClose={() => setReviewDialogOpen(false)}>
        <DialogTitle>写评价</DialogTitle>
        <DialogContent>
          <Box sx={{ py: 2 }}>
            <Typography gutterBottom>评分</Typography>
            <Rating
              value={newReview.rating}
              onChange={(_, value) => setNewReview({ ...newReview, rating: value || 5 })}
            />
            <TextField
              fullWidth
              multiline
              rows={4}
              label="评价内容"
              value={newReview.content}
              onChange={(e) => setNewReview({ ...newReview, content: e.target.value })}
              sx={{ mt: 2 }}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setReviewDialogOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSubmitReview} startIcon={<SendIcon />}>
            提交
          </Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={snackbar.open}
        autoHideDuration={3000}
        onClose={() => setSnackbar({ ...snackbar, open: false })}
        message={snackbar.message}
      />
    </Box>
  );
};

export default CommunityDetailPage;
