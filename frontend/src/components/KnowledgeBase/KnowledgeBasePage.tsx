import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Typography,
  TextField,
  InputAdornment,
  IconButton,
  Card,
  CardContent,
  CardActions,
  Button,
  Chip,
  Grid,
  Paper,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Collapse,
  Divider,
  Skeleton,
  Alert,
  Pagination,
  Tooltip,
  Badge,
} from '@mui/material';
import {
  Search as SearchIcon,
  FilterList as FilterIcon,
  LocationOn as LocationIcon,
  AttachMoney as MoneyIcon,
  Home as HomeIcon,
  Star as StarIcon,
  Visibility as ViewIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  Article as ArticleIcon,
  TrendingUp as TrendingIcon,
  Clear as ClearIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface Community {
  id: string;
  name: string;
  alias: string | null;
  city: string | null;
  district: string | null;
  address: string | null;
  avg_price: number | null;
  price_unit: string;
  total_units: number | null;
  completion_year: number | null;
  developer: string | null;
  property_company: string | null;
  property_fee: number | null;
  green_rate: number | null;
  volume_rate: number | null;
  building_type: string | null;
  description: string | null;
  view_count: number;
  favorite_count: number;
  has_article: boolean;
  created_at: string | null;
}

interface City {
  id: string;
  name: string;
  province: string | null;
  avg_price: number | null;
  hot_districts: string | null;
  is_hot: boolean;
}

interface SearchParams {
  keyword: string;
  city: string;
  district: string;
  price_min: number | null;
  price_max: number | null;
  year_min: number | null;
  year_max: number | null;
  sort_by: string;
}

const KnowledgeBasePage: React.FC = () => {
  const navigate = useNavigate();
  const [communities, setCommunities] = useState<Community[]>([]);
  const [cities, setCities] = useState<City[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;

  const [searchParams, setSearchParams] = useState<SearchParams>({
    keyword: '',
    city: '',
    district: '',
    price_min: null,
    price_max: null,
    year_min: null,
    year_max: null,
    sort_by: 'updated',
  });

  const [priceRange, setPriceRange] = useState<number[]>([0, 200000]);
  const [yearRange, setYearRange] = useState<number[]>([1990, 2025]);

  const fetchCities = useCallback(async () => {
    try {
      const response = await fetch('/api/communities/cities');
      const data = await response.json();
      if (data.success) {
        setCities(data.data);
      }
    } catch (err) {
      console.error('Failed to fetch cities:', err);
    }
  }, []);

  const fetchCommunities = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams();
      params.append('page', page.toString());
      params.append('page_size', pageSize.toString());
      params.append('sort_by', searchParams.sort_by);

      if (searchParams.keyword) {
        params.append('keyword', searchParams.keyword);
      }
      if (searchParams.city) {
        params.append('city', searchParams.city);
      }
      if (searchParams.district) {
        params.append('district', searchParams.district);
      }
      if (searchParams.price_min !== null) {
        params.append('price_min', searchParams.price_min.toString());
      }
      if (searchParams.price_max !== null) {
        params.append('price_max', searchParams.price_max.toString());
      }
      if (searchParams.year_min !== null) {
        params.append('year_min', searchParams.year_min.toString());
      }
      if (searchParams.year_max !== null) {
        params.append('year_max', searchParams.year_max.toString());
      }

      const response = await fetch(`/api/communities/search?${params.toString()}`);
      const data = await response.json();

      if (data.success) {
        setCommunities(data.data);
        setTotal(data.pagination.total);
        setTotalPages(data.pagination.total_pages);
      } else {
        setError('搜索失败，请稍后重试');
      }
    } catch (err) {
      setError('网络错误，请检查网络连接');
      console.error('Failed to fetch communities:', err);
    } finally {
      setLoading(false);
    }
  }, [page, searchParams]);

  useEffect(() => {
    fetchCities();
  }, [fetchCities]);

  useEffect(() => {
    fetchCommunities();
  }, [fetchCommunities]);

  const handleSearch = () => {
    setPage(1);
    fetchCommunities();
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSearch();
    }
  };

  const handleClearFilters = () => {
    setSearchParams({
      keyword: '',
      city: '',
      district: '',
      price_min: null,
      price_max: null,
      year_min: null,
      year_max: null,
      sort_by: 'updated',
    });
    setPriceRange([0, 200000]);
    setYearRange([1990, 2025]);
    setPage(1);
  };

  const handlePriceChange = (_event: Event, newValue: number | number[]) => {
    setPriceRange(newValue as number[]);
    setSearchParams(prev => ({
      ...prev,
      price_min: (newValue as number[])[0] > 0 ? (newValue as number[])[0] : null,
      price_max: (newValue as number[])[1] < 200000 ? (newValue as number[])[1] : null,
    }));
  };

  const handleYearChange = (_event: Event, newValue: number | number[]) => {
    setYearRange(newValue as number[]);
    setSearchParams(prev => ({
      ...prev,
      year_min: (newValue as number[])[0] > 1990 ? (newValue as number[])[0] : null,
      year_max: (newValue as number[])[1] < 2025 ? (newValue as number[])[1] : null,
    }));
  };

  const formatPrice = (price: number | null) => {
    if (price === null) return '暂无';
    if (price >= 10000) {
      return `${(price / 10000).toFixed(1)}万`;
    }
    return price.toLocaleString();
  };

  const handleCommunityClick = (id: string) => {
    navigate(`/communities/${id}`);
  };

  const handleArticleClick = (e: React.MouseEvent, id: string) => {
    e.stopPropagation();
    navigate(`/community/article/${id}`);
  };

  return (
    <Box sx={{ minHeight: '100vh', bgcolor: 'grey.50' }}>
      <Box
        sx={{
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          py: 6,
          mb: 4,
        }}
      >
        <Container maxWidth="lg">
          <Typography variant="h3" fontWeight="bold" gutterBottom>
            小区知识库
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.9 }}>
            搜索全国小区信息，查看房价走势、周边配套、专业分析文章
          </Typography>

          <Paper
            sx={{
              mt: 4,
              p: 2,
              display: 'flex',
              gap: 2,
              alignItems: 'center',
            }}
          >
            <TextField
              fullWidth
              placeholder="搜索小区名称、地址..."
              value={searchParams.keyword}
              onChange={(e) => setSearchParams(prev => ({ ...prev, keyword: e.target.value }))}
              onKeyPress={handleKeyPress}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
              sx={{ flex: 1 }}
            />
            <FormControl sx={{ minWidth: 120 }}>
              <InputLabel>城市</InputLabel>
              <Select
                value={searchParams.city}
                label="城市"
                onChange={(e) => setSearchParams(prev => ({ ...prev, city: e.target.value }))}
              >
                <MenuItem value="">全部</MenuItem>
                {cities.map((city) => (
                  <MenuItem key={city.id} value={city.name}>
                    {city.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <Button
              variant="contained"
              size="large"
              onClick={handleSearch}
              sx={{ px: 4 }}
            >
              搜索
            </Button>
            <IconButton
              onClick={() => setShowFilters(!showFilters)}
              color={showFilters ? 'primary' : 'default'}
            >
              <FilterIcon />
            </IconButton>
          </Paper>

          <Collapse in={showFilters}>
            <Paper sx={{ mt: 2, p: 3 }}>
              <Grid container spacing={3}>
                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>
                    价格区间：{formatPrice(priceRange[0])} - {formatPrice(priceRange[1])} 元/㎡
                  </Typography>
                  <Slider
                    value={priceRange}
                    onChange={handlePriceChange}
                    min={0}
                    max={200000}
                    step={5000}
                    valueLabelDisplay="auto"
                    valueLabelFormat={(value) => formatPrice(value)}
                  />
                </Grid>
                <Grid item xs={12} md={6}>
                  <Typography gutterBottom>
                    建成年份：{yearRange[0]} - {yearRange[1]}
                  </Typography>
                  <Slider
                    value={yearRange}
                    onChange={handleYearChange}
                    min={1990}
                    max={2025}
                    step={1}
                    valueLabelDisplay="auto"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <FormControl fullWidth>
                    <InputLabel>排序方式</InputLabel>
                    <Select
                      value={searchParams.sort_by}
                      label="排序方式"
                      onChange={(e) => setSearchParams(prev => ({ ...prev, sort_by: e.target.value }))}
                    >
                      <MenuItem value="updated">最新更新</MenuItem>
                      <MenuItem value="price">价格从高到低</MenuItem>
                      <MenuItem value="views">浏览量最高</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="outlined"
                    startIcon={<ClearIcon />}
                    onClick={handleClearFilters}
                  >
                    清除筛选
                  </Button>
                </Grid>
              </Grid>
            </Paper>
          </Collapse>
        </Container>
      </Box>

      <Container maxWidth="lg">
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="body1" color="text.secondary">
            共找到 <strong>{total}</strong> 个小区
          </Typography>
        </Box>

        {loading ? (
          <Grid container spacing={3}>
            {[...Array(6)].map((_, i) => (
              <Grid item xs={12} md={6} key={i}>
                <Card>
                  <CardContent>
                    <Skeleton variant="text" width="60%" height={32} />
                    <Skeleton variant="text" width="40%" />
                    <Skeleton variant="text" width="80%" />
                    <Skeleton variant="rectangular" height={100} sx={{ mt: 2 }} />
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        ) : communities.length === 0 ? (
          <Paper sx={{ p: 6, textAlign: 'center' }}>
            <HomeIcon sx={{ fontSize: 64, color: 'grey.400', mb: 2 }} />
            <Typography variant="h6" color="text.secondary">
              未找到符合条件的小区
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              请尝试调整搜索条件
            </Typography>
          </Paper>
        ) : (
          <Grid container spacing={3}>
            {communities.map((community) => (
              <Grid item xs={12} md={6} key={community.id}>
                <Card
                  sx={{
                    height: '100%',
                    cursor: 'pointer',
                    transition: 'all 0.3s',
                    '&:hover': {
                      transform: 'translateY(-4px)',
                      boxShadow: 4,
                    },
                  }}
                  onClick={() => handleCommunityClick(community.id)}
                >
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Box>
                        <Typography variant="h6" fontWeight="bold">
                          {community.name}
                          {community.alias && (
                            <Typography component="span" variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                              ({community.alias})
                            </Typography>
                          )}
                        </Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                          <LocationIcon fontSize="small" color="action" sx={{ mr: 0.5 }} />
                          <Typography variant="body2" color="text.secondary">
                            {[community.city, community.district, community.address].filter(Boolean).join(' · ')}
                          </Typography>
                        </Box>
                      </Box>
                      {community.has_article && (
                        <Chip
                          icon={<ArticleIcon />}
                          label="有文章"
                          size="small"
                          color="primary"
                          variant="outlined"
                        />
                      )}
                    </Box>

                    <Box sx={{ display: 'flex', alignItems: 'baseline', gap: 1, mb: 2 }}>
                      <Typography variant="h4" color="primary" fontWeight="bold">
                        {formatPrice(community.avg_price)}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {community.price_unit}
                      </Typography>
                    </Box>

                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mb: 2 }}>
                      {community.completion_year && (
                        <Chip
                          label={`${community.completion_year}年建成`}
                          size="small"
                          variant="outlined"
                        />
                      )}
                      {community.building_type && (
                        <Chip label={community.building_type} size="small" variant="outlined" />
                      )}
                      {community.total_units && (
                        <Chip label={`${community.total_units}户`} size="small" variant="outlined" />
                      )}
                    </Box>

                    {community.description && (
                      <Typography
                        variant="body2"
                        color="text.secondary"
                        sx={{
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          display: '-webkit-box',
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: 'vertical',
                        }}
                      >
                        {community.description}
                      </Typography>
                    )}

                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 2, color: 'text.secondary' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <ViewIcon fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="caption">{community.view_count}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <FavoriteIcon fontSize="small" sx={{ mr: 0.5 }} />
                        <Typography variant="caption">{community.favorite_count}</Typography>
                      </Box>
                    </Box>
                  </CardContent>
                  {community.has_article && (
                    <CardActions sx={{ justifyContent: 'flex-end', pt: 0 }}>
                      <Button
                        size="small"
                        startIcon={<ArticleIcon />}
                        onClick={(e) => handleArticleClick(e, community.id)}
                      >
                        查看文章
                      </Button>
                    </CardActions>
                  )}
                </Card>
              </Grid>
            ))}
          </Grid>
        )}

        {totalPages > 1 && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4, mb: 4 }}>
            <Pagination
              count={totalPages}
              page={page}
              onChange={(_, newPage) => setPage(newPage)}
              color="primary"
              size="large"
              showFirstButton
              showLastButton
            />
          </Box>
        )}

        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" fontWeight="bold" gutterBottom sx={{ mt: 4 }}>
            热门城市
          </Typography>
          <Grid container spacing={2}>
            {cities.filter(c => c.is_hot).map((city) => (
              <Grid item key={city.id}>
                <Card
                  sx={{
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    '&:hover': {
                      boxShadow: 3,
                    },
                  }}
                  onClick={() => {
                    setSearchParams(prev => ({ ...prev, city: city.name }));
                    setPage(1);
                  }}
                >
                  <CardContent sx={{ py: 2, px: 3 }}>
                    <Typography variant="subtitle1" fontWeight="bold">
                      {city.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      均价 {formatPrice(city.avg_price)} 元/㎡
                    </Typography>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </Box>
      </Container>
    </Box>
  );
};

export default KnowledgeBasePage;
