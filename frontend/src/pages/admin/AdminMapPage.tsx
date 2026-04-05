import React, { useState, useEffect } from 'react';

interface MapStats {
  total_locations: number;
  new_districts: number;
  top_cities: { city: string; count: number }[];
}

interface LocationData {
  id: string;
  user_id: string;
  city: string;
  district: string;
  lat: number;
  lng: number;
  created_at: string;
}

const AdminMapPage: React.FC = () => {
  const [stats, setStats] = useState<MapStats | null>(null);
  const [locations, setLocations] = useState<LocationData[]>([]);
  const [loading, setLoading] = useState(true);
  const [mapCenter, setMapCenter] = useState({ lat: 35.8617, lng: 104.1954 });
  const [zoom, setZoom] = useState(4);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [statsRes, locationsRes] = await Promise.all([
        fetch('http://localhost:8000/api/admin/map/stats', { headers }),
        fetch('http://localhost:8000/api/admin/map/data', { headers }),
      ]);

      if (statsRes.ok) {
        const data = await statsRes.json();
        setStats(data);
      }
      if (locationsRes.ok) {
        const data = await locationsRes.json();
        setLocations(data.locations || []);
      }
    } catch (error) {
      console.error('Failed to fetch map data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getCityCount = () => {
    const cityCount: Record<string, number> = {};
    locations.forEach(loc => {
      cityCount[loc.city] = (cityCount[loc.city] || 0) + 1;
    });
    return Object.entries(cityCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
  };

  const getDistrictCount = () => {
    const districtCount: Record<string, number> = {};
    locations.forEach(loc => {
      const key = `${loc.city}-${loc.district}`;
      districtCount[key] = (districtCount[key] || 0) + 1;
    });
    return Object.entries(districtCount)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10);
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="text-center py-10">加载中...</div>
      </div>
    );
  }

  const cityCount = getCityCount();
  const districtCount = getDistrictCount();

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">用户地图</h1>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="p-4 border-b">
              <h2 className="text-lg font-medium">用户地理分布</h2>
            </div>
            <div className="relative h-[500px] bg-gray-100">
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center text-gray-500">
                  <div className="text-6xl mb-4">🗺️</div>
                  <p className="text-lg">地图可视化</p>
                  <p className="text-sm mt-2">
                    集成地图服务（如高德地图、百度地图）以显示用户分布
                  </p>
                  <div className="mt-4 p-4 bg-white rounded shadow">
                    <p className="text-sm font-medium mb-2">当前数据概览</p>
                    <div className="grid grid-cols-2 gap-4 text-sm">
                      <div>
                        <span className="text-gray-500">总位置记录:</span>
                        <span className="ml-2 font-medium">{locations.length}</span>
                      </div>
                      <div>
                        <span className="text-gray-500">覆盖城市:</span>
                        <span className="ml-2 font-medium">{cityCount.length}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className="absolute top-4 right-4 bg-white rounded shadow p-2">
                <div className="flex gap-2">
                  <button
                    onClick={() => setZoom(z => Math.min(18, z + 1))}
                    className="w-8 h-8 border rounded hover:bg-gray-100"
                  >
                    +
                  </button>
                  <button
                    onClick={() => setZoom(z => Math.max(1, z - 1))}
                    className="w-8 h-8 border rounded hover:bg-gray-100"
                  >
                    -
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {stats && (
            <div className="bg-white rounded-lg shadow p-4">
              <h3 className="text-lg font-medium mb-4">统计信息</h3>
              <div className="space-y-4">
                <div>
                  <div className="text-sm text-gray-500">总位置记录</div>
                  <div className="text-2xl font-bold">{stats.total_locations}</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500">新增小区</div>
                  <div className="text-2xl font-bold text-green-600">{stats.new_districts}</div>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-medium mb-4">热门城市 TOP 10</h3>
            <div className="space-y-2">
              {cityCount.map(([city, count], index) => (
                <div key={city} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                      index < 3 ? 'bg-yellow-100 text-yellow-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {index + 1}
                    </span>
                    <span className="text-sm">{city}</span>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <h3 className="text-lg font-medium mb-4">热门区域 TOP 10</h3>
            <div className="space-y-2">
              {districtCount.map(([district, count], index) => (
                <div key={district} className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className={`w-6 h-6 rounded-full flex items-center justify-center text-xs ${
                      index < 3 ? 'bg-blue-100 text-blue-700' : 'bg-gray-100 text-gray-600'
                    }`}>
                      {index + 1}
                    </span>
                    <span className="text-sm">{district}</span>
                  </div>
                  <span className="text-sm font-medium">{count}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className="mt-6 bg-white rounded-lg shadow overflow-hidden">
        <div className="p-4 border-b">
          <h2 className="text-lg font-medium">位置记录</h2>
        </div>
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">区域</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">坐标</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {locations.slice(0, 20).map((loc) => (
              <tr key={loc.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(loc.created_at).toLocaleString('zh-CN')}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{loc.city}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{loc.district}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {loc.lat.toFixed(4)}, {loc.lng.toFixed(4)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default AdminMapPage;
