import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  MapPinIcon,
  ArrowPathIcon,
  ArrowDownTrayIcon,
  FunnelIcon,
  SparklesIcon,
  ShieldCheckIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { adminMapApi, MapDataResponse, LocationSummary, NewLocation, MapStats } from '@/api/admin/map';
import { MapStatsPanel } from '@/components/admin';
import showToast from '@/utils/toast';
import { LoadingCard } from '@/components/Loading';

const PRIVACY_AGREEMENT_KEY = 'map_privacy_agreed';

const PRIVACY_AGREEMENT = `
本地图功能仅展示聚合数据，不显示具体用户个人信息。

使用本功能时，您需要遵守以下规定：

1. 不得尝试识别或追踪特定用户
2. 数据仅用于系统管理和统计分析
3. 不得将数据用于任何商业目的
4. 访问记录将被系统审计
5. 违反规定可能导致权限被撤销

点击"同意"即表示您已阅读并同意遵守以上规定。
`;

const CHINA_CENTER = { lng: 104.1954, lat: 35.8617 };
const CHINA_ZOOM = 4;

const LEVEL_COLORS: Record<string, string> = {
  province: '#3b82f6',
  city: '#10b981',
  district: '#f59e0b',
  point: '#ef4444',
};

const NEW_POINT_COLOR = '#fbbf24';

const MapPage: React.FC = () => {
  const mapRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [mapData, setMapData] = useState<MapDataResponse | null>(null);
  const [summary, setSummary] = useState<LocationSummary | null>(null);
  const [mapStats, setMapStats] = useState<MapStats | null>(null);
  const [newLocations, setNewLocations] = useState<NewLocation[]>([]);
  const [zoomLevel, setZoomLevel] = useState(CHINA_ZOOM);
  const [timeRange, setTimeRange] = useState<'7' | '30' | '90' | 'all'>('all');
  const [showFilters, setShowFilters] = useState(false);
  const [selectedPoint, setSelectedPoint] = useState<any>(null);
  const [showNewLocations, setShowNewLocations] = useState(false);
  const [activeSource, setActiveSource] = useState<string | null>(null);
  const [showPrivacyModal, setShowPrivacyModal] = useState(false);
  const [privacyAgreed, setPrivacyAgreed] = useState(false);
  
  const mapInstanceRef = useRef<any>(null);
  const markersRef = useRef<any[]>([]);
  const animationRef = useRef<number | null>(null);

  useEffect(() => {
    const agreed = localStorage.getItem(PRIVACY_AGREEMENT_KEY);
    if (agreed === 'true') {
      setPrivacyAgreed(true);
    } else {
      setShowPrivacyModal(true);
    }
  }, []);

  const handlePrivacyAgree = () => {
    localStorage.setItem(PRIVACY_AGREEMENT_KEY, 'true');
    setPrivacyAgreed(true);
    setShowPrivacyModal(false);
  };

  const getTimeRangeParams = () => {
    if (timeRange === 'all') return {};
    
    const endDate = new Date().toISOString().split('T')[0];
    const startDate = new Date(Date.now() - parseInt(timeRange) * 24 * 60 * 60 * 1000).toISOString().split('T')[0];
    
    return { start_date: startDate, end_date: endDate };
  };

  const loadData = useCallback(async () => {
    setIsLoading(true);
    try {
      const timeParams = getTimeRangeParams();
      
      const [dataRes, summaryRes, newLocationsRes, statsRes] = await Promise.all([
        adminMapApi.getData({
          zoom_level: zoomLevel,
          ...timeParams,
        }),
        adminMapApi.getSummary(),
        adminMapApi.getNewLocations({ days: 30, limit: 50 }),
        adminMapApi.getStats(),
      ]);
      
      setMapData(dataRes);
      setSummary(summaryRes);
      setNewLocations(newLocationsRes.locations);
      setMapStats(statsRes);
    } catch {
      showToast.error('加载地图数据失败');
    } finally {
      setIsLoading(false);
    }
  }, [zoomLevel, timeRange]);

  useEffect(() => {
    if (privacyAgreed) {
      loadData();
    }
  }, [loadData, privacyAgreed]);

  useEffect(() => {
    if (!mapRef.current || !mapData) return;
    
    renderMap();
  }, [mapData]);

  const renderMap = () => {
    if (!mapRef.current || !mapData) return;

    markersRef.current = [];
    
    if (animationRef.current) {
      cancelAnimationFrame(animationRef.current);
    }
    
    const container = mapRef.current;
    container.innerHTML = '';
    
    const canvas = document.createElement('canvas');
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    container.appendChild(canvas);
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const width = canvas.width;
    const height = canvas.height;
    
    ctx.fillStyle = '#1a1a2e';
    ctx.fillRect(0, 0, width, height);
    
    drawChinaOutline(ctx, width, height);
    
    const bounds = getChinaBounds();
    const lngToX = (lng: number) => ((lng - bounds.west) / (bounds.east - bounds.west)) * width;
    const latToY = (lat: number) => ((bounds.north - lat) / (bounds.north - bounds.south)) * height;
    
    const maxCount = Math.max(...mapData.features.map(f => f.properties.count));
    
    const newPoints: any[] = [];
    
    mapData.features.forEach((feature) => {
      const [lng, lat] = feature.geometry.coordinates;
      const x = lngToX(lng);
      const y = latToY(lat);
      const count = feature.properties.count;
      const level = feature.properties.level;
      const isNew = feature.properties.is_new;
      
      const baseRadius = level === 'point' ? 4 : Math.max(8, Math.min(30, (count / maxCount) * 30));
      const color = isNew ? NEW_POINT_COLOR : (LEVEL_COLORS[level] || '#3b82f6');
      
      if (isNew) {
        newPoints.push({ x, y, radius: baseRadius, color });
      }
      
      ctx.beginPath();
      ctx.arc(x, y, baseRadius, 0, Math.PI * 2);
      ctx.fillStyle = color + '40';
      ctx.fill();
      
      ctx.beginPath();
      ctx.arc(x, y, baseRadius * 0.6, 0, Math.PI * 2);
      ctx.fillStyle = color;
      ctx.fill();
      
      if (level !== 'point' && baseRadius > 15) {
        ctx.fillStyle = '#ffffff';
        ctx.font = 'bold 12px sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(count.toString(), x, y);
      }
      
      markersRef.current.push({
        x, y, feature, radius: baseRadius
      });
    });
    
    if (newPoints.length > 0) {
      let pulsePhase = 0;
      
      const animate = () => {
        ctx.fillStyle = '#1a1a2e';
        ctx.fillRect(0, 0, width, height);
        
        drawChinaOutline(ctx, width, height);
        
        mapData.features.forEach((feature) => {
          const [lng, lat] = feature.geometry.coordinates;
          const x = lngToX(lng);
          const y = latToY(lat);
          const count = feature.properties.count;
          const level = feature.properties.level;
          const isNew = feature.properties.is_new;
          
          const baseRadius = level === 'point' ? 4 : Math.max(8, Math.min(30, (count / maxCount) * 30));
          const color = isNew ? NEW_POINT_COLOR : (LEVEL_COLORS[level] || '#3b82f6');
          
          ctx.beginPath();
          ctx.arc(x, y, baseRadius, 0, Math.PI * 2);
          ctx.fillStyle = color + '40';
          ctx.fill();
          
          ctx.beginPath();
          ctx.arc(x, y, baseRadius * 0.6, 0, Math.PI * 2);
          ctx.fillStyle = color;
          ctx.fill();
          
          if (level !== 'point' && baseRadius > 15) {
            ctx.fillStyle = '#ffffff';
            ctx.font = 'bold 12px sans-serif';
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillText(count.toString(), x, y);
          }
        });
        
        newPoints.forEach(point => {
          const pulseRadius = point.radius + Math.sin(pulsePhase) * 8;
          const alpha = 0.3 + Math.sin(pulsePhase) * 0.2;
          
          ctx.beginPath();
          ctx.arc(point.x, point.y, pulseRadius, 0, Math.PI * 2);
          ctx.fillStyle = `rgba(251, 191, 36, ${alpha})`;
          ctx.fill();
          
          ctx.beginPath();
          ctx.arc(point.x, point.y, point.radius * 0.6, 0, Math.PI * 2);
          ctx.fillStyle = NEW_POINT_COLOR;
          ctx.fill();
        });
        
        pulsePhase += 0.1;
        animationRef.current = requestAnimationFrame(animate);
      };
      
      animate();
    }
    
    canvas.onclick = (e) => {
      const rect = canvas.getBoundingClientRect();
      const clickX = e.clientX - rect.left;
      const clickY = e.clientY - rect.top;
      
      const clicked = markersRef.current.find(marker => {
        const dx = marker.x - clickX;
        const dy = marker.y - clickY;
        return Math.sqrt(dx * dx + dy * dy) <= marker.radius + 5;
      });
      
      if (clicked) {
        setSelectedPoint(clicked.feature.properties);
      } else {
        setSelectedPoint(null);
      }
    };
  };

  const drawChinaOutline = (ctx: CanvasRenderingContext2D, width: number, height: number) => {
    ctx.strokeStyle = '#2d3748';
    ctx.lineWidth = 1;
    
    const bounds = getChinaBounds();
    const lngToX = (lng: number) => ((lng - bounds.west) / (bounds.east - bounds.west)) * width;
    const latToY = (lat: number) => ((bounds.north - lat) / (bounds.north - bounds.south)) * height;
    
    const provinces = [
      { name: '北京', lng: 116.4, lat: 39.9 },
      { name: '上海', lng: 121.5, lat: 31.2 },
      { name: '广州', lng: 113.3, lat: 23.1 },
      { name: '深圳', lng: 114.1, lat: 22.5 },
      { name: '成都', lng: 104.1, lat: 30.7 },
      { name: '杭州', lng: 120.2, lat: 30.3 },
      { name: '武汉', lng: 114.3, lat: 30.6 },
      { name: '西安', lng: 108.9, lat: 34.3 },
      { name: '南京', lng: 118.8, lat: 32.1 },
      { name: '重庆', lng: 106.5, lat: 29.6 },
    ];
    
    ctx.fillStyle = '#4a5568';
    ctx.font = '10px sans-serif';
    ctx.textAlign = 'center';
    
    provinces.forEach(p => {
      const x = lngToX(p.lng);
      const y = latToY(p.lat);
      ctx.fillText(p.name, x, y);
    });
  };

  const getChinaBounds = () => ({
    north: 55,
    south: 18,
    east: 135,
    west: 73,
  });

  const handleZoomIn = () => {
    if (zoomLevel < 18) {
      setZoomLevel(z => z + 2);
    }
  };

  const handleZoomOut = () => {
    if (zoomLevel > 1) {
      setZoomLevel(z => z - 2);
    }
  };

  const handleSourceFilter = (source: string | null) => {
    setActiveSource(source);
  };

  const handleExport = async () => {
    try {
      const blob = await adminMapApi.exportData({
        format: 'geojson',
        ...getTimeRangeParams(),
      });
      
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `map_data_${new Date().toISOString().split('T')[0]}.geojson`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      
      showToast.success('导出成功');
    } catch {
      showToast.error('导出失败');
    }
  };

  const getLevelLabel = (level: string) => {
    switch (level) {
      case 'province': return '省份';
      case 'city': return '城市';
      case 'district': return '区县';
      case 'point': return '位置';
      default: return level;
    }
  };

  if (showPrivacyModal) {
    return (
      <div className="flex items-center justify-center min-h-[600px]">
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg border border-gray-100 dark:border-gray-700 p-6 max-w-lg w-full mx-4">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-full bg-yellow-100 dark:bg-yellow-900/30 flex items-center justify-center">
              <ShieldCheckIcon className="w-6 h-6 text-yellow-600 dark:text-yellow-400" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                隐私保护协议
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                使用地图功能前请阅读并同意
              </p>
            </div>
          </div>
          
          <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-4 mb-4 max-h-64 overflow-y-auto">
            <pre className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-sans">
              {PRIVACY_AGREEMENT}
            </pre>
          </div>
          
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 mb-4 flex items-start gap-2">
            <ExclamationTriangleIcon className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
            <p className="text-sm text-yellow-700 dark:text-yellow-400">
              为保护用户隐私，地图仅显示聚合数据，且小区内用户数少于3人的区域将被隐藏。
            </p>
          </div>
          
          <div className="flex gap-3">
            <button
              onClick={() => window.history.back()}
              className="flex-1 px-4 py-2 text-sm bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600"
            >
              返回
            </button>
            <button
              onClick={handlePrivacyAgree}
              className="flex-1 px-4 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700"
            >
              同意并继续
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-white">用户地图</h2>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {summary ? `共 ${summary.total_locations} 个位置，${summary.geocoded_locations} 个已编码` : '加载中...'}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <select
            value={timeRange}
            onChange={(e) => setTimeRange(e.target.value as any)}
            className="px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300"
          >
            <option value="all">全部时间</option>
            <option value="7">最近7天</option>
            <option value="30">最近30天</option>
            <option value="90">最近90天</option>
          </select>
          
          <button
            onClick={loadData}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <ArrowPathIcon className="w-4 h-4" />
            刷新
          </button>
          
          <button
            onClick={handleExport}
            className="flex items-center gap-2 px-3 py-2 text-sm bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700"
          >
            <ArrowDownTrayIcon className="w-4 h-4" />
            导出
          </button>
        </div>
      </div>

      {/* Map Container */}
      <div className="flex gap-4">
        {/* Map */}
        <div className="flex-1 bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 overflow-hidden">
          {/* Map Controls */}
          <div className="absolute z-10 m-3 flex flex-col gap-2">
            <button
              onClick={handleZoomIn}
              className="w-8 h-8 bg-white dark:bg-gray-700 rounded-lg shadow flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              +
            </button>
            <button
              onClick={handleZoomOut}
              className="w-8 h-8 bg-white dark:bg-gray-700 rounded-lg shadow flex items-center justify-center text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-600"
            >
              -
            </button>
          </div>
          
          {/* Zoom Level Indicator */}
          <div className="absolute z-10 bottom-3 left-3 bg-white dark:bg-gray-700 rounded-lg shadow px-3 py-1.5 text-sm text-gray-600 dark:text-gray-300">
            缩放级别: {zoomLevel} ({mapData?.metadata.aggregation_level || '加载中'})
            {activeSource && (
              <span className="ml-2 text-primary-600 dark:text-primary-400">
                | 筛选: {activeSource}
              </span>
            )}
          </div>
          
          {/* Map */}
          <div 
            ref={mapRef} 
            className="relative h-[600px] w-full bg-gray-900"
          />
          
          {/* Selected Point Info */}
          {selectedPoint && (
            <div className="absolute z-10 top-3 right-3 bg-white dark:bg-gray-700 rounded-lg shadow-lg p-4 max-w-xs">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-gray-900 dark:text-white">
                    {selectedPoint.name}
                  </span>
                  {selectedPoint.is_new && (
                    <span className="px-2 py-0.5 text-xs font-medium bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-400 rounded-full">
                      新增
                    </span>
                  )}
                </div>
                <button
                  onClick={() => setSelectedPoint(null)}
                  className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
                >
                  ×
                </button>
              </div>
              <div className="space-y-1 text-sm text-gray-600 dark:text-gray-400">
                <p>级别: {getLevelLabel(selectedPoint.level)}</p>
                <p>用户数: {selectedPoint.count}</p>
                {selectedPoint.province && <p>省份: {selectedPoint.province}</p>}
                {selectedPoint.city && <p>城市: {selectedPoint.city}</p>}
                {selectedPoint.district && <p>区县: {selectedPoint.district}</p>}
                {selectedPoint.created_at && (
                  <p>添加时间: {new Date(selectedPoint.created_at).toLocaleDateString('zh-CN')}</p>
                )}
              </div>
            </div>
          )}
        </div>
        
        {/* Stats Panel */}
        <div className="w-80 flex-shrink-0">
          <MapStatsPanel 
            stats={mapStats}
            onSourceFilter={handleSourceFilter}
            activeSource={activeSource}
          />
        </div>
      </div>

      {/* Legend */}
      <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
        <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">图例</h3>
        <div className="flex flex-wrap gap-4">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: LEVEL_COLORS.province }} />
            <span className="text-sm text-gray-600 dark:text-gray-400">省份</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: LEVEL_COLORS.city }} />
            <span className="text-sm text-gray-600 dark:text-gray-400">城市</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: LEVEL_COLORS.district }} />
            <span className="text-sm text-gray-600 dark:text-gray-400">区县</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: LEVEL_COLORS.point }} />
            <span className="text-sm text-gray-600 dark:text-gray-400">位置点</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full animate-pulse" style={{ backgroundColor: NEW_POINT_COLOR }} />
            <span className="text-sm text-gray-600 dark:text-gray-400">新增位置</span>
          </div>
        </div>
      </div>

      {/* New Locations Sidebar */}
      {newLocations.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center gap-2">
              <SparklesIcon className="w-5 h-5 text-yellow-500" />
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                新点亮小区（近30天）
              </h3>
            </div>
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {newLocations.length} 个
            </span>
          </div>
          
          <div className="space-y-2 max-h-60 overflow-y-auto">
            {newLocations.slice(0, 10).map((location, index) => (
              <div 
                key={index}
                className="flex items-center justify-between p-2 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg"
              >
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-yellow-500 animate-pulse" />
                  <div>
                    <p className="text-sm font-medium text-gray-900 dark:text-white">
                      {location.community}
                    </p>
                    <p className="text-xs text-gray-500 dark:text-gray-400">
                      {location.district}, {location.city}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium text-yellow-600 dark:text-yellow-400">
                    {location.count} 位用户
                  </p>
                  <p className="text-xs text-gray-400 dark:text-gray-500">
                    {new Date(location.created_at).toLocaleDateString('zh-CN')}
                  </p>
                </div>
              </div>
            ))}
          </div>
          
          {newLocations.length > 10 && (
            <button
              onClick={() => setShowNewLocations(!showNewLocations)}
              className="w-full mt-2 text-sm text-primary-600 dark:text-primary-400 hover:underline"
            >
              {showNewLocations ? '收起' : `查看全部 ${newLocations.length} 个`}
            </button>
          )}
        </div>
      )}

      {/* Stats */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Top 5 省份</h3>
            <div className="space-y-2">
              {summary.top_provinces.map((p, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">{p.province}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{p.count}</span>
                </div>
              ))}
            </div>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-sm border border-gray-100 dark:border-gray-700 p-4">
            <h3 className="text-sm font-medium text-gray-900 dark:text-white mb-3">Top 5 城市</h3>
            <div className="space-y-2">
              {summary.top_cities.map((c, i) => (
                <div key={i} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 dark:text-gray-400">{c.city}</span>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{c.count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default MapPage;
