import React, { useState, useEffect } from 'react';

interface IndustrialPark {
  id: string;
  name: string;
  city: string;
  district?: string;
  industry_type?: string;
  industry_tags: string[];
  description?: string;
  development_goal?: string;
  latitude?: number;
  longitude?: number;
  status: string;
  nearby_property_price_min?: number;
  nearby_property_price_max?: number;
}

interface MapMarker {
  id: string;
  name: string;
  lat: number;
  lng: number;
  city: string;
  industry?: string;
  status: string;
  color: string;
}

interface CityIndex {
  city: string;
  overall_score: number;
  industry_score: number;
  infrastructure_score: number;
  policy_score: number;
  talent_score: number;
  investment_potential: string;
  key_industries: string[];
  star_rating: string;
}

const IndustrialParkMap: React.FC = () => {
  const [markers, setMarkers] = useState<MapMarker[]>([]);
  const [selectedPark, setSelectedPark] = useState<IndustrialPark | null>(null);
  const [cityIndex, setCityIndex] = useState<CityIndex | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchMapData();
  }, []);

  const fetchMapData = async () => {
    try {
      const response = await fetch('/api/industrial/map-data');
      const data = await response.json();
      setMarkers(data.markers);
    } catch (error) {
      console.error('Failed to fetch map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkerClick = async (marker: MapMarker) => {
    try {
      const response = await fetch(`/api/industrial/parks/${marker.id}`);
      const park = await response.json();
      setSelectedPark(park);

      const indexResponse = await fetch(`/api/industrial/index/${encodeURIComponent(marker.city)}`);
      if (indexResponse.ok) {
        const index = await indexResponse.json();
        setCityIndex(index);
      }
    } catch (error) {
      console.error('Failed to fetch park details:', error);
    }
  };

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      operating: 'bg-green-100 text-green-700',
      construction: 'bg-blue-100 text-blue-700',
      planning: 'bg-yellow-100 text-yellow-700'
    };
    const labels: Record<string, string> = {
      operating: '运营中',
      construction: '建设中',
      planning: '规划中'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs ${styles[status] || 'bg-gray-100 text-gray-700'}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-fluent-gold-500"></div>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2">
        <div className="bg-white rounded-2xl shadow-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold text-fluent-deepOcean-500">湖南省重点产业园区分布</h2>
            <span className="text-sm text-fluent-deepOcean-400">{markers.length} 个产业园区</span>
          </div>
          
          <div className="relative bg-gradient-to-br from-fluent-jade-50 to-fluent-deepOcean-50 rounded-xl h-96 overflow-hidden">
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="text-center">
                <div className="text-6xl mb-4">🗺️</div>
                <p className="text-fluent-deepOcean-400">湖南省产业园区地图</p>
                <p className="text-sm text-fluent-deepOcean-300 mt-2">点击标记查看详情</p>
              </div>
            </div>
            
            <div className="absolute inset-0 p-4">
              {markers.map((marker) => (
                <div
                  key={marker.id}
                  className="absolute cursor-pointer transform -translate-x-1/2 -translate-y-1/2 hover:scale-125 transition-transform"
                  style={{
                    left: `${((marker.lng - 111) / 4) * 100}%`,
                    top: `${((30 - marker.lat) / 5) * 100}%`
                  }}
                  onClick={() => handleMarkerClick(marker)}
                >
                  <div
                    className="w-4 h-4 rounded-full shadow-lg animate-pulse"
                    style={{ backgroundColor: marker.color }}
                  />
                  <div className="absolute top-5 left-1/2 transform -translate-x-1/2 whitespace-nowrap text-xs bg-white px-2 py-1 rounded shadow-sm">
                    {marker.name.split(/[项目|产业园]/)[0]}
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div className="mt-4 flex flex-wrap gap-2">
            {[
              { label: '新能源', color: '#4ECDC4' },
              { label: '锂电池', color: '#FF6B6B' },
              { label: '智能制造', color: '#45B7D1' },
              { label: '临空经济', color: '#96CEB4' },
              { label: '新材料', color: '#FFEAA7' }
            ].map((item) => (
              <div key={item.label} className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: item.color }} />
                <span className="text-sm text-fluent-deepOcean-400">{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {selectedPark ? (
          <>
            <div className="bg-white rounded-2xl shadow-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-bold text-fluent-deepOcean-500">{selectedPark.name}</h3>
                {getStatusBadge(selectedPark.status)}
              </div>
              
              <div className="space-y-3">
                <div className="flex items-center gap-2">
                  <span className="text-fluent-deepOcean-400">📍</span>
                  <span className="text-sm">{selectedPark.city}{selectedPark.district ? ` · ${selectedPark.district}` : ''}</span>
                </div>
                
                <div className="flex items-center gap-2">
                  <span className="text-fluent-deepOcean-400">🏭</span>
                  <span className="text-sm">{selectedPark.industry_type}</span>
                </div>
                
                {selectedPark.nearby_property_price_min && (
                  <div className="flex items-center gap-2">
                    <span className="text-fluent-deepOcean-400">💰</span>
                    <span className="text-sm">
                      周边房价: {selectedPark.nearby_property_price_min.toLocaleString()}-{selectedPark.nearby_property_price_max?.toLocaleString()}元/㎡
                    </span>
                  </div>
                )}
                
                {selectedPark.development_goal && (
                  <div className="mt-4 p-3 bg-fluent-deepOcean-50 rounded-lg">
                    <p className="text-sm text-fluent-deepOcean-400">{selectedPark.development_goal}</p>
                  </div>
                )}
                
                <div className="flex flex-wrap gap-2 mt-4">
                  {selectedPark.industry_tags.map((tag, idx) => (
                    <span key={idx} className="px-2 py-1 bg-fluent-gold-100 text-fluent-gold-600 rounded-full text-xs">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {cityIndex && (
              <div className="bg-gradient-to-br from-fluent-gold-50 to-fluent-jade-50 rounded-2xl shadow-lg p-6">
                <h4 className="text-lg font-bold text-fluent-deepOcean-500 mb-4">
                  {cityIndex.city} 产城融合指数
                </h4>
                
                <div className="text-center mb-4">
                  <span className="text-3xl">{cityIndex.star_rating}</span>
                  <p className="text-sm text-fluent-deepOcean-400 mt-1">投资潜力: {cityIndex.investment_potential}</p>
                </div>
                
                <div className="space-y-3">
                  {[
                    { label: '产业集聚', score: cityIndex.industry_score },
                    { label: '基础设施', score: cityIndex.infrastructure_score },
                    { label: '政策支持', score: cityIndex.policy_score },
                    { label: '人才储备', score: cityIndex.talent_score }
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-3">
                      <span className="text-sm text-fluent-deepOcean-400 w-16">{item.label}</span>
                      <div className="flex-1 h-2 bg-fluent-deepOcean-100 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-500 rounded-full"
                          style={{ width: `${(item.score / 5) * 100}%` }}
                        />
                      </div>
                      <span className="text-sm font-medium text-fluent-deepOcean-500">{item.score.toFixed(1)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        ) : (
          <div className="bg-white rounded-2xl shadow-lg p-6 text-center">
            <div className="text-6xl mb-4">🏭</div>
            <p className="text-fluent-deepOcean-400">点击地图标记查看产业园区详情</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default IndustrialParkMap;
