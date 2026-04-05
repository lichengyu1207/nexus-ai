import api from '@/services/api';

export interface MapFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    name: string;
    count: number;
    level: 'province' | 'city' | 'district' | 'point';
    province?: string;
    city?: string;
    district?: string;
    community?: string;
    is_new?: boolean;
    created_at?: string;
  };
}

export interface NewLocation {
  community: string;
  district: string;
  city: string;
  province: string;
  longitude: number;
  latitude: number;
  created_at: string;
  count: number;
}

export interface MapDataResponse {
  type: 'FeatureCollection';
  features: MapFeature[];
  metadata: {
    zoom_level: number;
    aggregation_level: string;
    total_features: number;
  };
}

export interface HeatmapResponse {
  data: [number, number][];
  metadata: {
    total_points: number;
    radius: number;
  };
}

export interface LocationSummary {
  total_locations: number;
  geocoded_locations: number;
  top_provinces: Array<{ province: string; count: number }>;
  top_cities: Array<{ city: string; count: number }>;
  by_source: Record<string, number>;
}

export interface MapStats {
  total_locations: number;
  geocoded_locations: number;
  by_source: Record<string, number>;
  top_cities: Array<{ name: string; count: number }>;
  top_provinces: Array<{ name: string; count: number }>;
  top_districts: Array<{ name: string; city: string; count: number }>;
  new_communities_last_30d: number;
}

export interface MapBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export const adminMapApi = {
  getData: async (params: {
    zoom_level: number;
    bounds?: MapBounds;
    start_date?: string;
    end_date?: string;
  }): Promise<MapDataResponse> => {
    const queryParams: Record<string, any> = {
      zoom_level: params.zoom_level,
    };
    
    if (params.bounds) {
      queryParams.north = params.bounds.north;
      queryParams.south = params.bounds.south;
      queryParams.east = params.bounds.east;
      queryParams.west = params.bounds.west;
    }
    
    if (params.start_date) queryParams.start_date = params.start_date;
    if (params.end_date) queryParams.end_date = params.end_date;
    
    const response = await api.get('/admin/map/data', { params: queryParams });
    return response.data;
  },

  getHeatmap: async (params?: {
    bounds?: MapBounds;
    start_date?: string;
    end_date?: string;
    radius?: number;
  }): Promise<HeatmapResponse> => {
    const queryParams: Record<string, any> = {};
    
    if (params?.bounds) {
      queryParams.north = params.bounds.north;
      queryParams.south = params.bounds.south;
      queryParams.east = params.bounds.east;
      queryParams.west = params.bounds.west;
    }
    
    if (params?.start_date) queryParams.start_date = params.start_date;
    if (params?.end_date) queryParams.end_date = params.end_date;
    if (params?.radius) queryParams.radius = params.radius;
    
    const response = await api.get('/admin/map/heatmap', { params: queryParams });
    return response.data;
  },

  getSummary: async (): Promise<LocationSummary> => {
    const response = await api.get('/admin/map/summary');
    return response.data;
  },

  getStats: async (): Promise<MapStats> => {
    const response = await api.get('/admin/map/stats');
    return response.data;
  },

  getClusters: async (params: {
    zoom_level: number;
    bounds?: MapBounds;
    cluster_radius?: number;
  }): Promise<MapDataResponse> => {
    const queryParams: Record<string, any> = {
      zoom_level: params.zoom_level,
    };
    
    if (params.bounds) {
      queryParams.north = params.bounds.north;
      queryParams.south = params.bounds.south;
      queryParams.east = params.bounds.east;
      queryParams.west = params.bounds.west;
    }
    
    if (params.cluster_radius) queryParams.cluster_radius = params.cluster_radius;
    
    const response = await api.get('/admin/map/clusters', { params: queryParams });
    return response.data;
  },

  exportData: async (params?: {
    format?: 'geojson' | 'csv';
    start_date?: string;
    end_date?: string;
  }): Promise<Blob> => {
    const queryParams: Record<string, any> = {};
    
    if (params?.format) queryParams.format = params.format;
    if (params?.start_date) queryParams.start_date = params.start_date;
    if (params?.end_date) queryParams.end_date = params.end_date;
    
    const response = await api.get('/admin/map/export', {
      params: queryParams,
      responseType: 'blob',
    });
    return response.data;
  },

  getNewLocations: async (params?: {
    days?: number;
    limit?: number;
  }): Promise<{ locations: NewLocation[]; days: number; total: number }> => {
    const queryParams: Record<string, any> = {};
    
    if (params?.days) queryParams.days = params.days;
    if (params?.limit) queryParams.limit = params.limit;
    
    const response = await api.get('/admin/map/new-locations', { params: queryParams });
    return response.data;
  },
};
