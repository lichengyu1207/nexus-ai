import React, { useState, useEffect } from 'react';
import { ChevronDownIcon, ChevronRightIcon, PlayIcon, StopIcon, ArrowPathIcon, PlusIcon, CogIcon, Bars3Icon } from '@heroicons/react/24/outline';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface TaskData {
  id: string;
  city_name: string;
  province_name?: string;
  task_type: string;
  status: 'pending' | 'processing' | 'completed' | 'failed' | 'cancelled';
  progress: number;
  total_items?: number;
  processed_items: number;
  message?: string;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  created_at?: string;
  updated_at?: string;
}

interface DashboardData {
  total_tasks: number;
  pending_tasks: number;
  processing_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  cities: Array<{
    city_name: string;
    province_name?: string;
    community_progress: number;
    community_status?: string;
    price_progress: number;
    price_status?: string;
    poi_progress: number;
    poi_status?: string;
  }>;
}

interface ProvinceData {
  name: string;
  prefecture_count: number;
  county_count: number;
  prefecture_city: number;
  district: number;
  county_city: number;
  county: number;
  autonomous_county: number;
  gdp: { [year: string]: number };
}

interface NationalStats {
  year: number;
  prefecture_count: number;
  prefecture_city: number;
  county_count: number;
  district: number;
  county_city: number;
  county: number;
  autonomous_county: number;
}

interface CityPriceData {
  name: string;
  newHouse: { mom: number; yoy: number };
  secondHand: { mom: number; yoy: number };
  newHouseBySize?: {
    small: { mom: number; yoy: number };
    medium: { mom: number; yoy: number };
    large: { mom: number; yoy: number };
  };
  secondHandBySize?: {
    small: { mom: number; yoy: number };
    medium: { mom: number; yoy: number };
    large: { mom: number; yoy: number };
  };
}

interface DataSource {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'error';
  lastRun?: string;
  nextRun?: string;
  collectionFrequency?: string;
  dataReportingInterval?: string;
  alertThreshold?: number;
}

interface DataSourceParams {
  collectionFrequency: string;
  dataReportingInterval: string;
  alertThreshold: number;
}

interface HeterogeneousDataSource {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'disconnected' | 'error';
  lastTest?: string;
  description: string;
}

interface DataQualityMetric {
  id: string;
  dataSourceId: string;
  dataSourceName: string;
  completeness: number;
  timeliness: number;
  accuracy: number;
  timestamp: string;
  issues?: Array<{
    type: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    suggestedFix: string;
  }>;
}

// 负载压力分析相关接口
interface LoadPressureData {
  id: string;
  taskQueue: string;
  timestamp: string;
  enqueueRate: number;
  processingRate: number;
  queueLength: number;
  resourceUtilization: number;
}

interface CrossCorrelationResult {
  lag: number;
  correlation: number;
}

interface TaskAccumulationResult {
  timestamp: string;
  accumulation: number;
}

interface LoadImpactFactor {
  id: string;
  name: string;
  weight: number;
  value: number;
  contribution: number;
}

// 智能体任务负载预测相关接口
interface AgentLoadPredictionParams {
  currentQueueLength: number;
  averageProcessingTime: number;
  concurrencyLimit: number;
  historicalLoadPeak: number;
  taskComplexityFactor: number;
}

interface AgentLoadPredictionResult {
  timestamp: string;
  predictedQueueLength: number;
  resourceUtilization: number;
  responseTime: number;
}

interface PredictionReport {
  id: string;
  generatedAt: string;
  peakLoadTime: string;
  recommendedScalingTime: string;
  potentialBottlenecks: string[];
  summary: string;
}

// 预警管理相关接口
interface Alert {
  id: string;
  timeRange: string;
  level: 'high' | 'medium' | 'low';
  tag: string;
  description: string;
  status: 'unprocessed' | 'processed' | 'ignored';
  timestamp: string;
}

interface BenchmarkData {
  id: string;
  region: string;
  timestamp: string;
  value: number;
}

// 任务工单相关接口
interface MaintenanceOrder {
  id: string;
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  source: string;
  suggestedProcessingTime: string;
  status: 'pending' | 'in-progress' | 'awaiting-approval' | 'completed';
  createdAt: string;
  updatedAt: string;
  assignee?: string;
}

// 系统高级功能相关接口
interface MultiDimensionAnalysisResult {
  id: string;
  timestamp: string;
  dimensions: {
    agentLoad: number;
    taskAccumulation: number;
    memoryAccessFrequency: number;
    systemResourceConsumption: number;
  };
  healthScore: number;
  correlations: Array<{
    dimension1: string;
    dimension2: string;
    correlation: number;
  }>;
}

interface PredictiveMaintenanceDecision {
  id: string;
  timestamp: string;
  recommendedScalingTime: string;
  resourceSchedulingStrategy: string;
  expectedBenefits: {
    responseTimeReduction: number;
    resourceCostIncrease: number;
  };
  risks: string[];
}

const PROVINCE_DATA: ProvinceData[] = [
  { name: "北京市", prefecture_count: 0, county_count: 16, prefecture_city: 0, district: 16, county_city: 0, county: 0, autonomous_county: 0, gdp: {"2024": 49670.2, "2023": 47353.7, "2022": 45222.4, "2021": 44350.7, "2020": 38503.6} },
  { name: "天津市", prefecture_count: 0, county_count: 16, prefecture_city: 0, district: 16, county_city: 0, county: 0, autonomous_county: 0, gdp: {"2024": 17931.3, "2023": 17211.8, "2022": 16588.5, "2021": 16093.2, "2020": 14230.8} },
  { name: "河北省", prefecture_count: 11, county_count: 167, prefecture_city: 11, district: 49, county_city: 21, county: 91, autonomous_county: 6, gdp: {"2024": 47448.1, "2023": 45660.0, "2022": 43198.3, "2021": 41205.4, "2020": 36821.5} },
  { name: "山西省", prefecture_count: 11, county_count: 117, prefecture_city: 11, district: 26, county_city: 11, county: 80, autonomous_county: 0, gdp: {"2024": 25353.5, "2023": 26050.8, "2022": 25653.2, "2021": 23087.8, "2020": 18202.7} },
  { name: "内蒙古自治区", prefecture_count: 12, county_count: 103, prefecture_city: 9, district: 23, county_city: 11, county: 17, autonomous_county: 0, gdp: {"2024": 26337.0, "2023": 25020.5, "2022": 23795.7, "2021": 21584.8, "2020": 17623.4} },
  { name: "辽宁省", prefecture_count: 14, county_count: 100, prefecture_city: 14, district: 59, county_city: 16, county: 17, autonomous_county: 8, gdp: {"2024": 32540.8, "2023": 31389.8, "2022": 29739.7, "2021": 28471.0, "2020": 25839.0} },
  { name: "吉林省", prefecture_count: 9, county_count: 60, prefecture_city: 8, district: 21, county_city: 20, county: 16, autonomous_county: 3, gdp: {"2024": 14305.0, "2023": 13942.7, "2022": 13121.4, "2021": 13431.1, "2020": 12499.5} },
  { name: "黑龙江省", prefecture_count: 13, county_count: 121, prefecture_city: 12, district: 54, county_city: 21, county: 45, autonomous_county: 1, gdp: {"2024": 16478.1, "2023": 16470.7, "2022": 16359.2, "2021": 15292.8, "2020": 14000.1} },
  { name: "上海市", prefecture_count: 0, county_count: 16, prefecture_city: 0, district: 16, county_city: 0, county: 0, autonomous_county: 0, gdp: {"2024": 53759.5, "2023": 51404.5, "2022": 48594.5, "2021": 47059.4, "2020": 41603.9} },
  { name: "江苏省", prefecture_count: 13, county_count: 95, prefecture_city: 13, district: 55, county_city: 21, county: 19, autonomous_county: 0, gdp: {"2024": 136696.9, "2023": 130924.3, "2022": 124564.2, "2021": 119853.2, "2020": 104566.6} },
  { name: "浙江省", prefecture_count: 11, county_count: 90, prefecture_city: 11, district: 37, county_city: 20, county: 32, autonomous_county: 1, gdp: {"2024": 90007.0, "2023": 85619.6, "2022": 80770.0, "2021": 76765.3, "2020": 67164.5} },
  { name: "安徽省", prefecture_count: 16, county_count: 104, prefecture_city: 16, district: 45, county_city: 9, county: 50, autonomous_county: 0, gdp: {"2024": 50646.7, "2023": 48227.5, "2022": 45525.1, "2021": 43102.8, "2020": 38628.8} },
  { name: "福建省", prefecture_count: 9, county_count: 84, prefecture_city: 9, district: 31, county_city: 11, county: 42, autonomous_county: 0, gdp: {"2024": 57476.6, "2023": 54801.7, "2022": 52099.6, "2021": 49602.6, "2020": 43682.0} },
  { name: "江西省", prefecture_count: 11, county_count: 100, prefecture_city: 11, district: 27, county_city: 12, county: 61, autonomous_county: 0, gdp: {"2024": 34227.9, "2023": 32677.1, "2022": 31568.1, "2021": 29838.2, "2020": 25825.4} },
  { name: "山东省", prefecture_count: 16, county_count: 136, prefecture_city: 16, district: 58, county_city: 26, county: 52, autonomous_county: 0, gdp: {"2024": 98406.9, "2023": 94206.4, "2022": 89519.4, "2021": 84838.0, "2020": 74355.9} },
  { name: "河南省", prefecture_count: 17, county_count: 157, prefecture_city: 17, district: 54, county_city: 21, county: 82, autonomous_county: 0, gdp: {"2024": 63557.1, "2023": 60627.7, "2022": 58807.4, "2021": 57806.9, "2020": 54160.6} },
  { name: "湖北省", prefecture_count: 13, county_count: 103, prefecture_city: 12, district: 39, county_city: 26, county: 35, autonomous_county: 2, gdp: {"2024": 59644.3, "2023": 56794.3, "2022": 53445.4, "2021": 50093.3, "2020": 43017.6} },
  { name: "湖南省", prefecture_count: 14, county_count: 122, prefecture_city: 13, district: 36, county_city: 19, county: 60, autonomous_county: 7, gdp: {"2024": 53084.7, "2023": 50667.5, "2022": 47957.9, "2021": 45751.9, "2020": 41693.7} },
  { name: "广东省", prefecture_count: 21, county_count: 122, prefecture_city: 21, district: 65, county_city: 20, county: 34, autonomous_county: 3, gdp: {"2024": 141488.9, "2023": 137905.4, "2022": 132547.1, "2021": 127577.4, "2020": 113708.9} },
  { name: "广西壮族自治区", prefecture_count: 14, county_count: 111, prefecture_city: 14, district: 41, county_city: 10, county: 48, autonomous_county: 12, gdp: {"2024": 28694.1, "2023": 27501.7, "2022": 26419.7, "2021": 25311.5, "2020": 22250.7} },
  { name: "海南省", prefecture_count: 4, county_count: 25, prefecture_city: 4, district: 10, county_city: 5, county: 4, autonomous_county: 6, gdp: {"2024": 7972.7, "2023": 7590.2, "2022": 6912.8, "2021": 6508.9, "2020": 5640.8} },
  { name: "重庆市", prefecture_count: 0, county_count: 38, prefecture_city: 0, district: 26, county_city: 0, county: 8, autonomous_county: 4, gdp: {"2024": 32046.7, "2023": 30614.3, "2022": 28771.8, "2021": 28092.5, "2020": 25158.1} },
  { name: "四川省", prefecture_count: 21, county_count: 183, prefecture_city: 18, district: 55, county_city: 19, county: 105, autonomous_county: 4, gdp: {"2024": 64537.9, "2023": 61353.4, "2022": 57609.4, "2021": 55131.3, "2020": 49445.1} },
  { name: "贵州省", prefecture_count: 9, county_count: 88, prefecture_city: 6, district: 16, county_city: 10, county: 50, autonomous_county: 11, gdp: {"2024": 22645.7, "2023": 21513.7, "2022": 20579.5, "2021": 19921.3, "2020": 18308.3} },
  { name: "云南省", prefecture_count: 16, county_count: 129, prefecture_city: 8, district: 17, county_city: 18, county: 65, autonomous_county: 29, gdp: {"2024": 31423.4, "2023": 30595.8, "2022": 29301.1, "2021": 27895.3, "2020": 25214.5} },
  { name: "西藏自治区", prefecture_count: 7, county_count: 74, prefecture_city: 6, district: 8, county_city: 2, county: 64, autonomous_county: 0, gdp: {"2024": 2789.1, "2023": 2532.9, "2022": 2235.4, "2021": 2145.1, "2020": 1956.5} },
  { name: "陕西省", prefecture_count: 10, county_count: 107, prefecture_city: 10, district: 31, county_city: 7, county: 69, autonomous_county: 0, gdp: {"2024": 35437.1, "2023": 33976.5, "2022": 33035.6, "2021": 30476.6, "2020": 26297.0} },
  { name: "甘肃省", prefecture_count: 14, county_count: 86, prefecture_city: 12, district: 17, county_city: 5, county: 57, autonomous_county: 7, gdp: {"2024": 13020.5, "2023": 12345.7, "2022": 11553.6, "2021": 10608.0, "2020": 9323.1} },
  { name: "青海省", prefecture_count: 8, county_count: 44, prefecture_city: 2, district: 7, county_city: 5, county: 25, autonomous_county: 7, gdp: {"2024": 3965.5, "2023": 3849.2, "2022": 3677.4, "2021": 3446.3, "2020": 3080.6} },
  { name: "宁夏回族自治区", prefecture_count: 5, county_count: 22, prefecture_city: 5, district: 9, county_city: 2, county: 11, autonomous_county: 0, gdp: {"2024": 5520.2, "2023": 5368.8, "2022": 5168.1, "2021": 4666.5, "2020": 4036.2} },
  { name: "新疆维吾尔自治区", prefecture_count: 14, county_count: 108, prefecture_city: 4, district: 13, county_city: 29, county: 60, autonomous_county: 6, gdp: {"2024": 20492.4, "2023": 19603.3, "2022": 18550.5, "2021": 16791.5, "2020": 14262.2} },
];

const NATIONAL_STATS: NationalStats[] = [
  { year: 2024, prefecture_count: 333, prefecture_city: 293, county_count: 2846, district: 977, county_city: 397, county: 1301, autonomous_county: 117 },
  { year: 2023, prefecture_count: 333, prefecture_city: 293, county_count: 2844, district: 977, county_city: 397, county: 1299, autonomous_county: 117 },
  { year: 2022, prefecture_count: 333, prefecture_city: 293, county_count: 2843, district: 977, county_city: 394, county: 1301, autonomous_county: 117 },
  { year: 2021, prefecture_count: 333, prefecture_city: 293, county_count: 2843, district: 977, county_city: 394, county: 1301, autonomous_county: 117 },
  { year: 2020, prefecture_count: 333, prefecture_city: 293, county_count: 2844, district: 973, county_city: 388, county: 1312, autonomous_county: 117 },
];

const CITY_PRICE_DATA: CityPriceData[] = [
  { name: "北京", newHouse: { mom: 99.7, yoy: 97.6 }, secondHand: { mom: 99.8, yoy: 91.3 }, newHouseBySize: { small: { mom: 100.0, yoy: 96.7 }, medium: { mom: 99.7, yoy: 97.0 }, large: { mom: 99.5, yoy: 98.7 } }, secondHandBySize: { small: { mom: 100.0, yoy: 90.1 }, medium: { mom: 99.7, yoy: 91.7 }, large: { mom: 99.5, yoy: 93.4 } } },
  { name: "天津", newHouse: { mom: 99.2, yoy: 96.0 }, secondHand: { mom: 99.3, yoy: 94.1 }, newHouseBySize: { small: { mom: 99.3, yoy: 96.2 }, medium: { mom: 99.0, yoy: 95.8 }, large: { mom: 99.8, yoy: 96.4 } }, secondHandBySize: { small: { mom: 99.5, yoy: 94.2 }, medium: { mom: 99.2, yoy: 93.9 }, large: { mom: 99.6, yoy: 94.2 } } },
  { name: "石家庄", newHouse: { mom: 99.7, yoy: 95.8 }, secondHand: { mom: 99.8, yoy: 94.7 }, newHouseBySize: { small: { mom: 99.9, yoy: 96.1 }, medium: { mom: 99.8, yoy: 96.2 }, large: { mom: 99.5, yoy: 95.2 } }, secondHandBySize: { small: { mom: 99.8, yoy: 94.4 }, medium: { mom: 99.7, yoy: 94.9 }, large: { mom: 99.9, yoy: 94.6 } } },
  { name: "太原", newHouse: { mom: 99.9, yoy: 98.8 }, secondHand: { mom: 99.4, yoy: 95.1 }, newHouseBySize: { small: { mom: 100.0, yoy: 98.2 }, medium: { mom: 99.9, yoy: 98.6 }, large: { mom: 100.0, yoy: 99.0 } }, secondHandBySize: { small: { mom: 99.3, yoy: 94.6 }, medium: { mom: 99.4, yoy: 95.5 }, large: { mom: 99.6, yoy: 94.7 } } },
  { name: "呼和浩特", newHouse: { mom: 99.3, yoy: 95.9 }, secondHand: { mom: 99.5, yoy: 94.4 }, newHouseBySize: { small: { mom: 99.5, yoy: 96.5 }, medium: { mom: 99.6, yoy: 96.1 }, large: { mom: 98.8, yoy: 95.4 } }, secondHandBySize: { small: { mom: 99.9, yoy: 94.6 }, medium: { mom: 99.3, yoy: 94.1 }, large: { mom: 99.5, yoy: 94.9 } } },
  { name: "沈阳", newHouse: { mom: 99.8, yoy: 99.6 }, secondHand: { mom: 100.0, yoy: 96.6 }, newHouseBySize: { small: { mom: 100.0, yoy: 100.1 }, medium: { mom: 99.8, yoy: 99.5 }, large: { mom: 99.6, yoy: 99.6 } }, secondHandBySize: { small: { mom: 99.9, yoy: 96.5 }, medium: { mom: 100.1, yoy: 96.5 }, large: { mom: 99.7, yoy: 97.5 } } },
  { name: "大连", newHouse: { mom: 100.2, yoy: 98.8 }, secondHand: { mom: 99.6, yoy: 94.5 }, newHouseBySize: { small: { mom: 99.7, yoy: 97.8 }, medium: { mom: 100.3, yoy: 99.0 }, large: { mom: 100.2, yoy: 99.5 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.8 }, medium: { mom: 99.7, yoy: 94.8 }, large: { mom: 99.8, yoy: 95.4 } } },
  { name: "长春", newHouse: { mom: 99.6, yoy: 97.1 }, secondHand: { mom: 99.8, yoy: 95.4 }, newHouseBySize: { small: { mom: 99.2, yoy: 95.9 }, medium: { mom: 99.7, yoy: 97.4 }, large: { mom: 99.8, yoy: 97.4 } }, secondHandBySize: { small: { mom: 99.7, yoy: 95.7 }, medium: { mom: 100.0, yoy: 95.6 }, large: { mom: 99.7, yoy: 94.2 } } },
  { name: "哈尔滨", newHouse: { mom: 99.9, yoy: 97.6 }, secondHand: { mom: 99.8, yoy: 95.0 }, newHouseBySize: { small: { mom: 99.7, yoy: 96.2 }, medium: { mom: 99.8, yoy: 97.7 }, large: { mom: 100.2, yoy: 98.2 } }, secondHandBySize: { small: { mom: 100.0, yoy: 94.6 }, medium: { mom: 99.8, yoy: 95.8 }, large: { mom: 99.8, yoy: 94.1 } } },
  { name: "上海", newHouse: { mom: 100.0, yoy: 104.2 }, secondHand: { mom: 99.6, yoy: 93.2 }, newHouseBySize: { small: { mom: 100.1, yoy: 103.0 }, medium: { mom: 99.8, yoy: 103.2 }, large: { mom: 100.3, yoy: 105.9 } }, secondHandBySize: { small: { mom: 99.4, yoy: 92.8 }, medium: { mom: 99.6, yoy: 93.2 }, large: { mom: 99.9, yoy: 94.1 } } },
  { name: "南京", newHouse: { mom: 99.6, yoy: 96.5 }, secondHand: { mom: 99.8, yoy: 91.4 }, newHouseBySize: { small: { mom: 99.8, yoy: 96.8 }, medium: { mom: 99.4, yoy: 96.2 }, large: { mom: 99.9, yoy: 97.0 } }, secondHandBySize: { small: { mom: 99.9, yoy: 91.5 }, medium: { mom: 99.8, yoy: 91.1 }, large: { mom: 99.5, yoy: 92.2 } } },
  { name: "杭州", newHouse: { mom: 99.7, yoy: 102.4 }, secondHand: { mom: 99.7, yoy: 95.8 }, newHouseBySize: { small: { mom: 99.5, yoy: 99.4 }, medium: { mom: 99.6, yoy: 100.9 }, large: { mom: 99.8, yoy: 104.0 } }, secondHandBySize: { small: { mom: 99.4, yoy: 95.7 }, medium: { mom: 99.9, yoy: 96.0 }, large: { mom: 99.8, yoy: 95.5 } } },
  { name: "宁波", newHouse: { mom: 99.8, yoy: 98.4 }, secondHand: { mom: 99.7, yoy: 93.1 }, newHouseBySize: { small: { mom: 99.5, yoy: 97.7 }, medium: { mom: 99.7, yoy: 97.7 }, large: { mom: 99.9, yoy: 99.3 } }, secondHandBySize: { small: { mom: 99.5, yoy: 92.5 }, medium: { mom: 99.8, yoy: 93.6 }, large: { mom: 99.7, yoy: 92.6 } } },
  { name: "合肥", newHouse: { mom: 100.1, yoy: 101.6 }, secondHand: { mom: 99.4, yoy: 92.5 }, newHouseBySize: { small: { mom: 100.1, yoy: 103.0 }, medium: { mom: 100.0, yoy: 101.4 }, large: { mom: 100.2, yoy: 101.9 } }, secondHandBySize: { small: { mom: 99.2, yoy: 92.5 }, medium: { mom: 99.4, yoy: 92.3 }, large: { mom: 99.6, yoy: 93.3 } } },
  { name: "福州", newHouse: { mom: 99.5, yoy: 96.7 }, secondHand: { mom: 99.4, yoy: 93.7 }, newHouseBySize: { small: { mom: 99.5, yoy: 96.1 }, medium: { mom: 99.7, yoy: 95.7 }, large: { mom: 99.4, yoy: 97.9 } }, secondHandBySize: { small: { mom: 99.7, yoy: 93.4 }, medium: { mom: 99.1, yoy: 93.6 }, large: { mom: 99.6, yoy: 94.7 } } },
  { name: "厦门", newHouse: { mom: 100.1, yoy: 97.0 }, secondHand: { mom: 99.8, yoy: 92.2 }, newHouseBySize: { small: { mom: 99.6, yoy: 96.0 }, medium: { mom: 100.1, yoy: 97.4 }, large: { mom: 100.5, yoy: 96.8 } }, secondHandBySize: { small: { mom: 99.9, yoy: 91.6 }, medium: { mom: 99.7, yoy: 92.5 }, large: { mom: 99.8, yoy: 92.6 } } },
  { name: "南昌", newHouse: { mom: 99.5, yoy: 95.2 }, secondHand: { mom: 99.0, yoy: 93.1 }, newHouseBySize: { small: { mom: 99.5, yoy: 95.7 }, medium: { mom: 99.7, yoy: 95.3 }, large: { mom: 98.8, yoy: 95.0 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.2 }, medium: { mom: 99.1, yoy: 92.8 }, large: { mom: 98.4, yoy: 93.7 } } },
  { name: "济南", newHouse: { mom: 99.6, yoy: 97.2 }, secondHand: { mom: 99.8, yoy: 94.6 }, newHouseBySize: { small: { mom: 99.4, yoy: 96.7 }, medium: { mom: 99.9, yoy: 97.6 }, large: { mom: 99.1, yoy: 96.6 } }, secondHandBySize: { small: { mom: 100.2, yoy: 96.7 }, medium: { mom: 99.7, yoy: 94.0 }, large: { mom: 99.8, yoy: 94.3 } } },
  { name: "青岛", newHouse: { mom: 99.4, yoy: 97.5 }, secondHand: { mom: 99.2, yoy: 93.6 }, newHouseBySize: { small: { mom: 99.4, yoy: 96.6 }, medium: { mom: 99.5, yoy: 97.6 }, large: { mom: 99.2, yoy: 97.5 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.9 }, medium: { mom: 99.3, yoy: 93.3 }, large: { mom: 98.8, yoy: 94.1 } } },
  { name: "郑州", newHouse: { mom: 99.6, yoy: 94.3 }, secondHand: { mom: 99.3, yoy: 91.1 }, newHouseBySize: { small: { mom: 99.8, yoy: 94.6 }, medium: { mom: 99.6, yoy: 94.9 }, large: { mom: 99.5, yoy: 93.2 } }, secondHandBySize: { small: { mom: 99.3, yoy: 91.4 }, medium: { mom: 99.2, yoy: 90.9 }, large: { mom: 99.4, yoy: 91.1 } } },
  { name: "武汉", newHouse: { mom: 100.1, yoy: 96.2 }, secondHand: { mom: 99.4, yoy: 90.8 }, newHouseBySize: { small: { mom: 100.2, yoy: 96.9 }, medium: { mom: 100.0, yoy: 95.9 }, large: { mom: 100.1, yoy: 96.9 } }, secondHandBySize: { small: { mom: 99.3, yoy: 91.1 }, medium: { mom: 99.4, yoy: 90.6 }, large: { mom: 99.9, yoy: 91.1 } } },
  { name: "长沙", newHouse: { mom: 99.7, yoy: 97.7 }, secondHand: { mom: 99.2, yoy: 91.8 }, newHouseBySize: { small: { mom: 99.6, yoy: 97.9 }, medium: { mom: 99.8, yoy: 97.7 }, large: { mom: 99.6, yoy: 97.8 } }, secondHandBySize: { small: { mom: 98.9, yoy: 91.7 }, medium: { mom: 99.2, yoy: 91.7 }, large: { mom: 99.4, yoy: 92.0 } } },
  { name: "广州", newHouse: { mom: 99.4, yoy: 94.7 }, secondHand: { mom: 99.3, yoy: 91.7 }, newHouseBySize: { small: { mom: 99.8, yoy: 94.9 }, medium: { mom: 99.3, yoy: 94.5 }, large: { mom: 99.5, yoy: 94.8 } }, secondHandBySize: { small: { mom: 99.3, yoy: 91.8 }, medium: { mom: 99.3, yoy: 91.7 }, large: { mom: 99.4, yoy: 91.5 } } },
  { name: "深圳", newHouse: { mom: 99.6, yoy: 95.1 }, secondHand: { mom: 99.4, yoy: 93.5 }, newHouseBySize: { small: { mom: 99.9, yoy: 95.2 }, medium: { mom: 99.4, yoy: 94.8 }, large: { mom: 99.8, yoy: 95.7 } }, secondHandBySize: { small: { mom: 99.2, yoy: 93.7 }, medium: { mom: 99.5, yoy: 93.5 }, large: { mom: 99.4, yoy: 93.2 } } },
  { name: "南宁", newHouse: { mom: 99.2, yoy: 98.4 }, secondHand: { mom: 99.3, yoy: 93.6 }, newHouseBySize: { small: { mom: 99.3, yoy: 98.0 }, medium: { mom: 99.3, yoy: 98.7 }, large: { mom: 99.2, yoy: 97.6 } }, secondHandBySize: { small: { mom: 99.0, yoy: 92.7 }, medium: { mom: 99.4, yoy: 94.1 }, large: { mom: 99.5, yoy: 93.1 } } },
  { name: "海口", newHouse: { mom: 99.9, yoy: 94.8 }, secondHand: { mom: 99.3, yoy: 93.9 }, newHouseBySize: { small: { mom: 99.9, yoy: 94.3 }, medium: { mom: 99.6, yoy: 94.4 }, large: { mom: 100.5, yoy: 95.5 } }, secondHandBySize: { small: { mom: 99.6, yoy: 93.7 }, medium: { mom: 99.2, yoy: 94.1 }, large: { mom: 99.3, yoy: 93.8 } } },
  { name: "重庆", newHouse: { mom: 99.8, yoy: 96.5 }, secondHand: { mom: 99.5, yoy: 93.9 }, newHouseBySize: { small: { mom: 100.0, yoy: 97.1 }, medium: { mom: 99.7, yoy: 96.2 }, large: { mom: 99.9, yoy: 97.0 } }, secondHandBySize: { small: { mom: 99.1, yoy: 93.5 }, medium: { mom: 99.9, yoy: 94.4 }, large: { mom: 99.3, yoy: 93.5 } } },
  { name: "成都", newHouse: { mom: 99.4, yoy: 96.9 }, secondHand: { mom: 99.6, yoy: 95.0 }, newHouseBySize: { small: { mom: 99.7, yoy: 97.9 }, medium: { mom: 99.5, yoy: 96.4 }, large: { mom: 99.4, yoy: 97.5 } }, secondHandBySize: { small: { mom: 99.7, yoy: 95.0 }, medium: { mom: 99.4, yoy: 94.8 }, large: { mom: 99.8, yoy: 95.2 } } },
  { name: "贵阳", newHouse: { mom: 99.6, yoy: 96.6 }, secondHand: { mom: 99.5, yoy: 94.8 }, newHouseBySize: { small: { mom: 99.4, yoy: 94.7 }, medium: { mom: 99.5, yoy: 97.1 }, large: { mom: 100.4, yoy: 95.3 } }, secondHandBySize: { small: { mom: 99.8, yoy: 95.0 }, medium: { mom: 99.4, yoy: 94.6 }, large: { mom: 99.4, yoy: 95.1 } } },
  { name: "昆明", newHouse: { mom: 99.7, yoy: 94.2 }, secondHand: { mom: 99.4, yoy: 92.8 }, newHouseBySize: { small: { mom: 99.6, yoy: 93.7 }, medium: { mom: 99.6, yoy: 94.2 }, large: { mom: 99.7, yoy: 94.3 } }, secondHandBySize: { small: { mom: 99.2, yoy: 92.7 }, medium: { mom: 99.4, yoy: 93.3 }, large: { mom: 99.4, yoy: 92.1 } } },
  { name: "西安", newHouse: { mom: 99.3, yoy: 94.4 }, secondHand: { mom: 99.2, yoy: 90.6 }, newHouseBySize: { small: { mom: 99.0, yoy: 94.4 }, medium: { mom: 99.4, yoy: 93.4 }, large: { mom: 99.2, yoy: 96.0 } }, secondHandBySize: { small: { mom: 99.4, yoy: 91.5 }, medium: { mom: 99.3, yoy: 89.9 }, large: { mom: 99.0, yoy: 91.3 } } },
  { name: "兰州", newHouse: { mom: 99.5, yoy: 95.5 }, secondHand: { mom: 99.3, yoy: 94.3 }, newHouseBySize: { small: { mom: 99.7, yoy: 94.9 }, medium: { mom: 99.5, yoy: 95.6 }, large: { mom: 99.2, yoy: 95.2 } }, secondHandBySize: { small: { mom: 99.2, yoy: 95.0 }, medium: { mom: 99.5, yoy: 93.9 }, large: { mom: 99.1, yoy: 94.2 } } },
  { name: "西宁", newHouse: { mom: 99.7, yoy: 96.9 }, secondHand: { mom: 99.6, yoy: 98.1 }, newHouseBySize: { small: { mom: 99.8, yoy: 96.0 }, medium: { mom: 99.9, yoy: 96.8 }, large: { mom: 99.1, yoy: 97.5 } }, secondHandBySize: { small: { mom: 99.6, yoy: 98.6 }, medium: { mom: 99.7, yoy: 98.5 }, large: { mom: 99.3, yoy: 95.8 } } },
  { name: "银川", newHouse: { mom: 99.7, yoy: 96.2 }, secondHand: { mom: 99.3, yoy: 93.0 }, newHouseBySize: { small: { mom: 99.6, yoy: 97.8 }, medium: { mom: 99.7, yoy: 96.2 }, large: { mom: 99.8, yoy: 96.1 } }, secondHandBySize: { small: { mom: 99.5, yoy: 94.3 }, medium: { mom: 99.4, yoy: 92.8 }, large: { mom: 99.0, yoy: 92.5 } } },
  { name: "乌鲁木齐", newHouse: { mom: 99.6, yoy: 100.5 }, secondHand: { mom: 99.5, yoy: 95.2 }, newHouseBySize: { small: { mom: 99.9, yoy: 100.9 }, medium: { mom: 99.6, yoy: 100.4 }, large: { mom: 99.3, yoy: 100.7 } }, secondHandBySize: { small: { mom: 99.7, yoy: 95.7 }, medium: { mom: 99.3, yoy: 94.7 }, large: { mom: 99.4, yoy: 95.9 } } },
  { name: "唐山", newHouse: { mom: 99.6, yoy: 93.8 }, secondHand: { mom: 99.3, yoy: 91.6 }, newHouseBySize: { small: { mom: 99.4, yoy: 94.0 }, medium: { mom: 99.8, yoy: 93.7 }, large: { mom: 99.2, yoy: 93.9 } }, secondHandBySize: { small: { mom: 99.1, yoy: 91.7 }, medium: { mom: 99.3, yoy: 91.4 }, large: { mom: 99.6, yoy: 91.7 } } },
  { name: "秦皇岛", newHouse: { mom: 99.5, yoy: 95.1 }, secondHand: { mom: 99.0, yoy: 91.9 }, newHouseBySize: { small: { mom: 99.6, yoy: 94.3 }, medium: { mom: 99.6, yoy: 95.6 }, large: { mom: 99.2, yoy: 94.3 } }, secondHandBySize: { small: { mom: 99.1, yoy: 91.5 }, medium: { mom: 99.0, yoy: 92.3 }, large: { mom: 98.9, yoy: 91.4 } } },
  { name: "包头", newHouse: { mom: 99.4, yoy: 92.8 }, secondHand: { mom: 99.0, yoy: 91.8 }, newHouseBySize: { small: { mom: 99.0, yoy: 91.9 }, medium: { mom: 99.4, yoy: 93.1 }, large: { mom: 99.5, yoy: 92.0 } }, secondHandBySize: { small: { mom: 98.8, yoy: 92.4 }, medium: { mom: 99.1, yoy: 91.3 }, large: { mom: 99.0, yoy: 91.6 } } },
  { name: "丹东", newHouse: { mom: 99.8, yoy: 97.3 }, secondHand: { mom: 99.7, yoy: 96.3 }, newHouseBySize: { small: { mom: 99.9, yoy: 96.9 }, medium: { mom: 99.7, yoy: 97.6 }, large: { mom: 99.9, yoy: 96.7 } }, secondHandBySize: { small: { mom: 99.8, yoy: 96.3 }, medium: { mom: 99.7, yoy: 96.4 }, large: { mom: 99.6, yoy: 96.5 } } },
  { name: "锦州", newHouse: { mom: 99.6, yoy: 96.8 }, secondHand: { mom: 99.7, yoy: 95.8 }, newHouseBySize: { small: { mom: 99.3, yoy: 97.2 }, medium: { mom: 99.7, yoy: 97.1 }, large: { mom: 99.3, yoy: 95.7 } }, secondHandBySize: { small: { mom: 99.2, yoy: 95.9 }, medium: { mom: 99.9, yoy: 95.8 }, large: { mom: 99.9, yoy: 95.6 } } },
  { name: "吉林", newHouse: { mom: 99.9, yoy: 97.0 }, secondHand: { mom: 99.8, yoy: 95.5 }, newHouseBySize: { small: { mom: 99.7, yoy: 96.6 }, medium: { mom: 100.0, yoy: 97.1 }, large: { mom: 99.8, yoy: 97.2 } }, secondHandBySize: { small: { mom: 99.9, yoy: 95.4 }, medium: { mom: 99.7, yoy: 95.8 }, large: { mom: 99.8, yoy: 94.7 } } },
  { name: "牡丹江", newHouse: { mom: 99.8, yoy: 98.2 }, secondHand: { mom: 99.7, yoy: 96.9 }, newHouseBySize: { small: { mom: 99.8, yoy: 97.4 }, medium: { mom: 99.9, yoy: 98.6 }, large: { mom: 99.5, yoy: 96.6 } }, secondHandBySize: { small: { mom: 99.6, yoy: 96.9 }, medium: { mom: 99.8, yoy: 96.8 }, large: { mom: 99.7, yoy: 97.1 } } },
  { name: "无锡", newHouse: { mom: 99.8, yoy: 95.0 }, secondHand: { mom: 99.3, yoy: 93.8 }, newHouseBySize: { small: { mom: 99.5, yoy: 95.4 }, medium: { mom: 99.7, yoy: 94.6 }, large: { mom: 99.9, yoy: 95.6 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.2 }, medium: { mom: 99.2, yoy: 93.7 }, large: { mom: 99.5, yoy: 94.8 } } },
  { name: "徐州", newHouse: { mom: 99.1, yoy: 94.5 }, secondHand: { mom: 99.0, yoy: 89.8 }, newHouseBySize: { small: { mom: 98.9, yoy: 94.7 }, medium: { mom: 99.0, yoy: 94.2 }, large: { mom: 99.2, yoy: 95.1 } }, secondHandBySize: { small: { mom: 99.0, yoy: 89.1 }, medium: { mom: 99.1, yoy: 90.1 }, large: { mom: 98.9, yoy: 89.4 } } },
  { name: "扬州", newHouse: { mom: 99.6, yoy: 95.0 }, secondHand: { mom: 100.4, yoy: 93.3 }, newHouseBySize: { small: { mom: 99.5, yoy: 94.4 }, medium: { mom: 99.7, yoy: 95.6 }, large: { mom: 99.4, yoy: 94.0 } }, secondHandBySize: { small: { mom: 100.1, yoy: 92.2 }, medium: { mom: 100.5, yoy: 93.9 }, large: { mom: 100.6, yoy: 93.7 } } },
  { name: "温州", newHouse: { mom: 99.5, yoy: 95.5 }, secondHand: { mom: 99.4, yoy: 93.4 }, newHouseBySize: { small: { mom: 99.5, yoy: 95.3 }, medium: { mom: 99.5, yoy: 95.5 }, large: { mom: 99.6, yoy: 95.6 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.5 }, medium: { mom: 99.4, yoy: 93.4 }, large: { mom: 99.4, yoy: 93.3 } } },
  { name: "金华", newHouse: { mom: 99.4, yoy: 96.1 }, secondHand: { mom: 99.5, yoy: 94.1 }, newHouseBySize: { small: { mom: 99.5, yoy: 96.9 }, medium: { mom: 99.4, yoy: 96.2 }, large: { mom: 99.4, yoy: 95.5 } }, secondHandBySize: { small: { mom: 99.5, yoy: 93.6 }, medium: { mom: 99.4, yoy: 94.4 }, large: { mom: 99.6, yoy: 94.1 } } },
  { name: "蚌埠", newHouse: { mom: 99.5, yoy: 96.1 }, secondHand: { mom: 99.4, yoy: 95.2 }, newHouseBySize: { small: { mom: 99.9, yoy: 96.9 }, medium: { mom: 99.4, yoy: 96.5 }, large: { mom: 99.6, yoy: 95.4 } }, secondHandBySize: { small: { mom: 99.5, yoy: 94.4 }, medium: { mom: 99.3, yoy: 95.5 }, large: { mom: 99.5, yoy: 94.2 } } },
  { name: "安庆", newHouse: { mom: 99.7, yoy: 96.4 }, secondHand: { mom: 99.4, yoy: 93.5 }, newHouseBySize: { small: { mom: 100.0, yoy: 98.0 }, medium: { mom: 99.7, yoy: 96.7 }, large: { mom: 99.3, yoy: 95.0 } }, secondHandBySize: { small: { mom: 99.4, yoy: 93.1 }, medium: { mom: 99.4, yoy: 93.9 }, large: { mom: 99.0, yoy: 92.0 } } },
  { name: "泉州", newHouse: { mom: 99.6, yoy: 97.4 }, secondHand: { mom: 99.7, yoy: 95.2 }, newHouseBySize: { small: { mom: 100.0, yoy: 98.4 }, medium: { mom: 99.5, yoy: 96.7 }, large: { mom: 99.8, yoy: 98.4 } }, secondHandBySize: { small: { mom: 99.5, yoy: 94.5 }, medium: { mom: 99.7, yoy: 95.2 }, large: { mom: 99.8, yoy: 95.9 } } },
  { name: "九江", newHouse: { mom: 99.7, yoy: 96.4 }, secondHand: { mom: 99.0, yoy: 93.2 }, newHouseBySize: { small: { mom: 99.6, yoy: 96.1 }, medium: { mom: 99.7, yoy: 96.2 }, large: { mom: 99.8, yoy: 97.4 } }, secondHandBySize: { small: { mom: 99.1, yoy: 94.0 }, medium: { mom: 98.9, yoy: 93.1 }, large: { mom: 98.9, yoy: 92.9 } } },
  { name: "赣州", newHouse: { mom: 99.5, yoy: 96.0 }, secondHand: { mom: 99.4, yoy: 94.2 }, newHouseBySize: { small: { mom: 99.2, yoy: 97.4 }, medium: { mom: 99.4, yoy: 96.0 }, large: { mom: 99.9, yoy: 95.9 } }, secondHandBySize: { small: { mom: 99.6, yoy: 93.9 }, medium: { mom: 99.4, yoy: 94.6 }, large: { mom: 99.2, yoy: 93.1 } } },
  { name: "烟台", newHouse: { mom: 99.5, yoy: 95.7 }, secondHand: { mom: 99.6, yoy: 93.1 }, newHouseBySize: { small: { mom: 99.7, yoy: 95.8 }, medium: { mom: 99.6, yoy: 95.9 }, large: { mom: 99.4, yoy: 95.3 } }, secondHandBySize: { small: { mom: 99.4, yoy: 91.0 }, medium: { mom: 99.7, yoy: 93.7 }, large: { mom: 99.5, yoy: 93.8 } } },
  { name: "济宁", newHouse: { mom: 99.3, yoy: 95.2 }, secondHand: { mom: 99.5, yoy: 93.4 }, newHouseBySize: { small: { mom: 100.0, yoy: 97.1 }, medium: { mom: 99.0, yoy: 94.5 }, large: { mom: 99.8, yoy: 96.6 } }, secondHandBySize: { small: { mom: 99.3, yoy: 91.5 }, medium: { mom: 99.6, yoy: 93.5 }, large: { mom: 99.4, yoy: 94.0 } } },
  { name: "洛阳", newHouse: { mom: 99.5, yoy: 96.1 }, secondHand: { mom: 99.7, yoy: 95.8 }, newHouseBySize: { small: { mom: 99.1, yoy: 95.0 }, medium: { mom: 99.6, yoy: 96.1 }, large: { mom: 99.4, yoy: 96.1 } }, secondHandBySize: { small: { mom: 99.5, yoy: 94.7 }, medium: { mom: 99.7, yoy: 96.3 }, large: { mom: 99.9, yoy: 95.8 } } },
  { name: "平顶山", newHouse: { mom: 99.7, yoy: 98.3 }, secondHand: { mom: 99.1, yoy: 93.1 }, newHouseBySize: { small: { mom: 99.6, yoy: 99.2 }, medium: { mom: 99.7, yoy: 98.1 }, large: { mom: 99.8, yoy: 98.7 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.7 }, medium: { mom: 99.1, yoy: 92.6 }, large: { mom: 99.0, yoy: 94.3 } } },
  { name: "宜昌", newHouse: { mom: 99.5, yoy: 100.0 }, secondHand: { mom: 99.7, yoy: 95.6 }, newHouseBySize: { small: { mom: 99.9, yoy: 100.2 }, medium: { mom: 99.4, yoy: 99.8 }, large: { mom: 99.8, yoy: 100.6 } }, secondHandBySize: { small: { mom: 99.9, yoy: 95.1 }, medium: { mom: 99.7, yoy: 95.9 }, large: { mom: 99.5, yoy: 95.1 } } },
  { name: "襄阳", newHouse: { mom: 99.1, yoy: 95.9 }, secondHand: { mom: 99.2, yoy: 93.0 }, newHouseBySize: { small: { mom: 98.7, yoy: 94.5 }, medium: { mom: 99.1, yoy: 95.9 }, large: { mom: 99.3, yoy: 96.3 } }, secondHandBySize: { small: { mom: 98.7, yoy: 93.3 }, medium: { mom: 99.3, yoy: 92.8 }, large: { mom: 99.3, yoy: 93.5 } } },
  { name: "岳阳", newHouse: { mom: 99.6, yoy: 95.3 }, secondHand: { mom: 99.3, yoy: 94.1 }, newHouseBySize: { small: { mom: 98.9, yoy: 94.8 }, medium: { mom: 99.6, yoy: 95.2 }, large: { mom: 99.7, yoy: 95.6 } }, secondHandBySize: { small: { mom: 99.1, yoy: 94.5 }, medium: { mom: 99.3, yoy: 93.9 }, large: { mom: 99.4, yoy: 94.5 } } },
  { name: "常德", newHouse: { mom: 99.5, yoy: 95.8 }, secondHand: { mom: 99.4, yoy: 92.1 }, newHouseBySize: { small: { mom: 99.3, yoy: 95.4 }, medium: { mom: 99.4, yoy: 95.8 }, large: { mom: 99.7, yoy: 96.2 } }, secondHandBySize: { small: { mom: 99.2, yoy: 92.0 }, medium: { mom: 99.5, yoy: 91.8 }, large: { mom: 99.4, yoy: 92.8 } } },
  { name: "韶关", newHouse: { mom: 99.8, yoy: 98.3 }, secondHand: { mom: 99.3, yoy: 95.2 }, newHouseBySize: { small: { mom: 100.0, yoy: 98.7 }, medium: { mom: 99.9, yoy: 98.5 }, large: { mom: 99.7, yoy: 97.6 } }, secondHandBySize: { small: { mom: 99.2, yoy: 94.8 }, medium: { mom: 99.3, yoy: 95.4 }, large: { mom: 99.3, yoy: 95.0 } } },
  { name: "湛江", newHouse: { mom: 99.5, yoy: 96.2 }, secondHand: { mom: 100.3, yoy: 94.9 }, newHouseBySize: { small: { mom: 99.4, yoy: 97.2 }, medium: { mom: 99.5, yoy: 96.0 }, large: { mom: 99.4, yoy: 96.0 } }, secondHandBySize: { small: { mom: 100.4, yoy: 94.8 }, medium: { mom: 100.2, yoy: 94.9 }, large: { mom: 100.6, yoy: 94.8 } } },
  { name: "惠州", newHouse: { mom: 99.7, yoy: 95.9 }, secondHand: { mom: 99.3, yoy: 93.0 }, newHouseBySize: { small: { mom: 99.2, yoy: 95.2 }, medium: { mom: 99.8, yoy: 96.2 }, large: { mom: 99.4, yoy: 95.5 } }, secondHandBySize: { small: { mom: 99.5, yoy: 93.6 }, medium: { mom: 99.2, yoy: 92.7 }, large: { mom: 99.5, yoy: 93.2 } } },
  { name: "桂林", newHouse: { mom: 99.4, yoy: 95.2 }, secondHand: { mom: 99.2, yoy: 93.3 }, newHouseBySize: { small: { mom: 99.3, yoy: 95.4 }, medium: { mom: 99.4, yoy: 95.2 }, large: { mom: 99.5, yoy: 94.9 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.4 }, medium: { mom: 99.2, yoy: 93.2 }, large: { mom: 99.2, yoy: 93.5 } } },
  { name: "北海", newHouse: { mom: 99.7, yoy: 94.0 }, secondHand: { mom: 98.8, yoy: 93.0 }, newHouseBySize: { small: { mom: 99.6, yoy: 93.7 }, medium: { mom: 99.8, yoy: 94.6 }, large: { mom: 99.5, yoy: 93.9 } }, secondHandBySize: { small: { mom: 98.8, yoy: 92.8 }, medium: { mom: 98.7, yoy: 93.0 }, large: { mom: 99.0, yoy: 93.4 } } },
  { name: "三亚", newHouse: { mom: 100.0, yoy: 99.1 }, secondHand: { mom: 99.4, yoy: 93.0 }, newHouseBySize: { small: { mom: 99.9, yoy: 99.6 }, medium: { mom: 100.0, yoy: 98.8 }, large: { mom: 100.0, yoy: 99.4 } }, secondHandBySize: { small: { mom: 99.3, yoy: 93.7 }, medium: { mom: 99.6, yoy: 92.6 }, large: { mom: 99.3, yoy: 92.4 } } },
  { name: "泸州", newHouse: { mom: 99.3, yoy: 93.9 }, secondHand: { mom: 99.1, yoy: 92.7 }, newHouseBySize: { small: { mom: 99.0, yoy: 94.2 }, medium: { mom: 99.3, yoy: 93.8 }, large: { mom: 99.4, yoy: 94.1 } }, secondHandBySize: { small: { mom: 99.2, yoy: 92.9 }, medium: { mom: 99.0, yoy: 92.5 }, large: { mom: 99.4, yoy: 93.6 } } },
  { name: "南充", newHouse: { mom: 100.1, yoy: 96.8 }, secondHand: { mom: 99.3, yoy: 95.1 }, newHouseBySize: { small: { mom: 100.4, yoy: 97.2 }, medium: { mom: 100.0, yoy: 96.8 }, large: { mom: 99.7, yoy: 96.1 } }, secondHandBySize: { small: { mom: 99.2, yoy: 95.2 }, medium: { mom: 99.4, yoy: 95.2 }, large: { mom: 99.1, yoy: 94.5 } } },
  { name: "遵义", newHouse: { mom: 99.8, yoy: 97.1 }, secondHand: { mom: 99.7, yoy: 95.1 }, newHouseBySize: { small: { mom: 98.9, yoy: 96.6 }, medium: { mom: 99.9, yoy: 97.3 }, large: { mom: 99.7, yoy: 96.2 } }, secondHandBySize: { small: { mom: 99.7, yoy: 94.6 }, medium: { mom: 99.8, yoy: 95.5 }, large: { mom: 99.6, yoy: 94.0 } } },
  { name: "大理", newHouse: { mom: 100.0, yoy: 95.8 }, secondHand: { mom: 99.2, yoy: 94.0 }, newHouseBySize: { small: { mom: 100.0, yoy: 95.9 }, medium: { mom: 100.1, yoy: 95.8 }, large: { mom: 99.9, yoy: 95.9 } }, secondHandBySize: { small: { mom: 99.2, yoy: 93.6 }, medium: { mom: 99.2, yoy: 94.7 }, large: { mom: 99.3, yoy: 93.6 } } },
];

const TreeNode: React.FC<{
  label: string;
  value?: string | number | React.ReactNode;
  children?: React.ReactNode;
  defaultOpen?: boolean;
  color?: string;
}> = ({ label, value, children, defaultOpen = false, color = 'blue' }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);
  const hasChildren = children && (Array.isArray(children) ? children.length > 0 : true);

  return (
    <div className="ml-2">
      <div
        className={`flex items-center gap-2 py-1 px-2 rounded hover:bg-gray-100 dark:hover:bg-gray-700 cursor-pointer`}
        onClick={() => hasChildren && setIsOpen(!isOpen)}
      >
        {hasChildren ? (
          isOpen ? (
            <ChevronDownIcon className="w-4 h-4 text-gray-500" />
          ) : (
            <ChevronRightIcon className="w-4 h-4 text-gray-500" />
          )
        ) : (
          <span className="w-4" />
        )}
        <span className={`font-medium text-${color}-600 dark:text-${color}-400`}>{label}</span>
        {value !== undefined && (
          <span className="text-gray-600 dark:text-gray-300 ml-auto">{value}</span>
        )}
      </div>
      {hasChildren && isOpen && (
        <div className="ml-4 border-l-2 border-gray-200 dark:border-gray-600 pl-2">
          {children}
        </div>
      )}
    </div>
  );
};

const PriceChangeBadge: React.FC<{ value: number }> = ({ value }) => {
  const isUp = value > 100;
  const isDown = value < 100;
  const change = (value - 100).toFixed(1);
  
  return (
    <span className={`px-2 py-0.5 rounded text-xs font-medium ${
      isUp ? 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400' :
      isDown ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' :
      'bg-gray-100 text-gray-700 dark:bg-gray-700 dark:text-gray-300'
    }`}>
      {isUp ? `+${change}%` : isDown ? `${change}%` : '0%'}
    </span>
  );
};

const API_BASE = '/api/admin/data-collection';

const getAuthHeaders = () => {
  const token = localStorage.getItem('token');
  return {
    'Content-Type': 'application/json',
    ...(token ? { 'Authorization': `Bearer ${token}` } : {})
  };
};

// 数据源类型定义
interface DataSource {
  id: string;
  name: string;
  status: 'running' | 'paused' | 'error';
  lastRun?: string;
  nextRun?: string;
  collectionFrequency?: string;
  dataReportingInterval?: string;
  alertThreshold?: number;
}

interface HeterogeneousDataSource {
  id: string;
  name: string;
  type: string;
  status: 'connected' | 'disconnected' | 'error';
  lastTest?: string;
  description: string;
}

interface DataQualityMetric {
  id: string;
  dataSourceId: string;
  dataSourceName: string;
  completeness: number;
  timeliness: number;
  accuracy: number;
  timestamp: string;
  issues?: Array<{
    type: string;
    description: string;
    severity: 'low' | 'medium' | 'high';
    suggestedFix: string;
  }>;
}

const fetchDashboard = async (): Promise<DashboardData> => {
  const res = await fetch(API_BASE + '/dashboard', { 
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
};

const fetchTasks = async (params: { city?: string; status?: string; task_type?: string }): Promise<TaskData[]> => {
  const query = new URLSearchParams(params as Record<string, string>);
  const res = await fetch(`${API_BASE}/tasks?${query}`, { 
    headers: getAuthHeaders(),
    credentials: 'include' 
  });
  if (!res.ok) throw new Error('Failed to fetch tasks');
  return res.json();
};

const createTask = async (task: { city_name: string; task_type: string; province_name?: string; total_items?: number }): Promise<TaskData> => {
  const res = await fetch(API_BASE + '/tasks', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(task),
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
};

const cancelTask = async (taskId: string): Promise<void> => {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/cancel`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to cancel task');
};

const retryTask = async (taskId: string): Promise<{ new_task_id: string }> => {
  const res = await fetch(`${API_BASE}/tasks/${taskId}/retry`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
  });
  if (!res.ok) throw new Error('Failed to retry task');
  return res.json();
};

// 数据源管理API函数
const fetchDataSources = async (): Promise<DataSource[]> => {
  // 调用真实的后端API
  const res = await fetch('/api/admin/data-sources', {
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to fetch data sources');
  return res.json();
};

const startDataSource = async (dataSourceId: string): Promise<DataSource> => {
  // 调用真实的后端API
  const res = await fetch(`/api/admin/data-sources/${dataSourceId}/start`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to start data source');
  return res.json();
};

const pauseDataSource = async (dataSourceId: string): Promise<DataSource> => {
  // 调用真实的后端API
  const res = await fetch(`/api/admin/data-sources/${dataSourceId}/pause`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to pause data source');
  return res.json();
};

const configureDataSource = async (dataSourceId: string, params: DataSourceParams): Promise<DataSource> => {
  // 调用真实的后端API
  const res = await fetch(`/api/admin/data-sources/${dataSourceId}/configure`, {
    method: 'PUT',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to configure data source');
  return res.json();
};

// 异构数据源管理API函数
const fetchHeterogeneousDataSources = async (): Promise<HeterogeneousDataSource[]> => {
  // 调用真实的后端API
  const res = await fetch('/api/admin/heterogeneous-data-sources', {
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to fetch heterogeneous data sources');
  return res.json();
};

const testDataSourceConnection = async (dataSourceId: string): Promise<{ success: boolean; message: string; timestamp: string }> => {
  // 调用真实的后端API
  const res = await fetch(`/api/admin/heterogeneous-data-sources/${dataSourceId}/test-connection`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to test data source connection');
  return res.json();
};

// 数据质量诊断API函数
const fetchDataQualityMetrics = async (): Promise<DataQualityMetric[]> => {
  // 调用真实的后端API
  const res = await fetch('/api/admin/data-quality-metrics', {
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to fetch data quality metrics');
  return res.json();
};

// 负载压力分析相关API函数
const fetchLoadPressureData = async (params: { taskQueue: string; startTime: string; endTime: string }): Promise<LoadPressureData[]> => {
  const query = new URLSearchParams(params as Record<string, string>);
  const res = await fetch(`/api/admin/load-pressure?${query}`, {
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to fetch load pressure data');
  return res.json();
};

const executeCrossCorrelation = async (params: { taskQueue: string; windowSize: number; sampleInterval: number; algorithm: string }): Promise<CrossCorrelationResult[]> => {
  const res = await fetch('/api/admin/load-pressure/cross-correlation', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to execute cross correlation');
  return res.json();
};

const calculateTaskAccumulation = async (params: { taskQueue: string; decayCoefficient: number; baseLoad: number; lagTime: number }): Promise<TaskAccumulationResult[]> => {
  const res = await fetch('/api/admin/load-pressure/task-accumulation', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to calculate task accumulation');
  return res.json();
};

const executeLoadImpactAnalysis = async (params: { loadModel: string; weights: Record<string, number> }): Promise<LoadImpactFactor[]> => {
  const res = await fetch('/api/admin/load-pressure/impact-analysis', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to execute load impact analysis');
  return res.json();
};
// 智能体任务负载预测相关API函数
const predictAgentLoad = async (params: AgentLoadPredictionParams): Promise<AgentLoadPredictionResult[]> => {
  const res = await fetch('/api/admin/agent-load-prediction', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to predict agent load');
  return res.json();
};

// 模拟负载影响因素数据
const MOCK_LOAD_IMPACT_FACTORS: LoadImpactFactor[] = [
  { id: '1', name: '任务复杂度', weight: 0.3, value: 0.8, contribution: 0.24 },
  { id: '2', name: '并发用户数', weight: 0.25, value: 0.7, contribution: 0.175 },
  { id: '3', name: '数据量大小', weight: 0.2, value: 0.6, contribution: 0.12 },
  { id: '4', name: '网络延迟', weight: 0.15, value: 0.5, contribution: 0.075 },
  { id: '5', name: '系统资源', weight: 0.1, value: 0.4, contribution: 0.04 }
];

const generatePredictionReport = async (params: AgentLoadPredictionParams): Promise<PredictionReport> => {
  const res = await fetch('/api/admin/agent-load-prediction/report', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to generate prediction report');
  return res.json();
};

const importHistoricalData = async (data: { dataSource: string; startTime: string; endTime: string; processingOptions: Record<string, any> }): Promise<{ success: boolean; importedRecords: number; message: string }> => {
  const res = await fetch('/api/admin/agent-load-prediction/import-historical', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to import historical data');
  return res.json();
};

const validateTaskComplexity = async (value: number): Promise<{ valid: boolean; message: string; range: { min: number; max: number } }> => {
  const res = await fetch('/api/admin/agent-load-prediction/validate-complexity', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify({ value })
  });
  if (!res.ok) throw new Error('Failed to validate task complexity');
  return res.json();
};
// 预警管理相关API函数
const generateAlertBenchmark = async (params: { region: string; complexityCoefficient: number }): Promise<BenchmarkData[]> => {
  const res = await fetch('/api/admin/alerts/generate-benchmark', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to generate alert benchmark');
  return res.json();
};

const generateAlerts = async (params: { region: string; logData?: string; useMockData: boolean }): Promise<Alert[]> => {
  const res = await fetch('/api/admin/alerts/generate', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to generate alerts');
  return res.json();
};

const processAlert = async (alertId: string, action: 'confirm' | 'ignore'): Promise<{ success: boolean; message: string }> => {
  const res = await fetch(`/api/admin/alerts/${alertId}/process`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify({ action })
  });
  if (!res.ok) throw new Error('Failed to process alert');
  return res.json();
};

const batchProcessAlerts = async (alertIds: string[], action: 'confirm' | 'ignore'): Promise<{ success: boolean; processed: number; message: string }> => {
  const res = await fetch('/api/admin/alerts/batch-process', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify({ alertIds, action })
  });
  if (!res.ok) throw new Error('Failed to batch process alerts');
  return res.json();
};
// 任务工单相关API函数
const fetchMaintenanceOrders = async (status?: string): Promise<MaintenanceOrder[]> => {
  const query = new URLSearchParams(status ? { status } : {});
  const res = await fetch(`/api/admin/maintenance-orders?${query}`, {
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to fetch maintenance orders');
  return res.json();
};

const processOrder = async (orderId: string, action: 'accept' | 'ignore'): Promise<{ success: boolean; message: string }> => {
  const res = await fetch(`/api/admin/maintenance-orders/${orderId}/process`, {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify({ action })
  });
  if (!res.ok) throw new Error('Failed to process maintenance order');
  return res.json();
};

const createEmergencyOrder = async (data: { title: string; description: string; priority: 'high' | 'medium' | 'low' }): Promise<{ success: boolean; orderId: string; message: string }> => {
  const res = await fetch('/api/admin/maintenance-orders/emergency', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create emergency maintenance order');
  return res.json();
};

// 系统高级功能相关API函数
const performMultiDimensionAnalysis = async (params: { analysisScenario: string; dimensions: string[] }): Promise<MultiDimensionAnalysisResult> => {
  const res = await fetch('/api/admin/system-analysis/multi-dimension', {
    method: 'POST',
    headers: getAuthHeaders(),
    credentials: 'include',
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error('Failed to perform multi-dimension analysis');
  return res.json();
};

const getPredictiveMaintenanceDecision = async (): Promise<PredictiveMaintenanceDecision> => {
  const res = await fetch('/api/admin/system-analysis/predictive-maintenance', {
    headers: getAuthHeaders(),
    credentials: 'include'
  });
  if (!res.ok) throw new Error('Failed to get predictive maintenance decision');
  return res.json();
};








const HeterogeneousDataTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [viewMode, setViewMode] = useState<'realtime' | 'history'>('realtime');
  const [testingDataSource, setTestingDataSource] = useState<string | null>(null);

  const { data: heterogeneousDataSources, isLoading: dataSourcesLoading } = useQuery({
    queryKey: ['heterogeneous-data-sources'],
    queryFn: fetchHeterogeneousDataSources,
    refetchInterval: 5000,
  });

  const { data: dataQualityMetrics, isLoading: qualityMetricsLoading } = useQuery({
    queryKey: ['data-quality-metrics'],
    queryFn: fetchDataQualityMetrics,
    refetchInterval: 3000,
  });

  const testConnectionMutation = useMutation({
    mutationFn: testDataSourceConnection,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['heterogeneous-data-sources'] });
      setTestingDataSource(null);
    },
  });

  const getHeterogeneousDataSourceStatusColor = (status: string) => {
    switch (status) {
      case 'connected': return 'text-green-600 bg-green-100';
      case 'disconnected': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getHeterogeneousDataSourceStatusText = (status: string) => {
    switch (status) {
      case 'connected': return '已连接';
      case 'disconnected': return '未连接';
      case 'error': return '错误';
      default: return status;
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-blue-600 bg-blue-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const handleTestConnection = (dataSourceId: string) => {
    setTestingDataSource(dataSourceId);
    testConnectionMutation.mutate(dataSourceId);
  };

  return (
    <div className="space-y-6">
      {/* 异构数据接入区域 */}
      <div>
        <h2 className="text-lg font-semibold mb-4">异构数据接入</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {dataSourcesLoading ? (
            Array(3).fill(0).map((_, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 animate-pulse">
                <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-4"></div>
                <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
              </div>
            ))
          ) : heterogeneousDataSources && heterogeneousDataSources.length > 0 ? (
            heterogeneousDataSources.map(dataSource => (
              <div key={dataSource.id} className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 border border-gray-200 dark:border-gray-700">
                <div className="flex justify-between items-start mb-2">
                  <h3 className="text-md font-medium text-gray-900 dark:text-white">{dataSource.name}</h3>
                  <span className={`px-2 py-1 text-xs rounded-full ${getHeterogeneousDataSourceStatusColor(dataSource.status)}`}>
                    {getHeterogeneousDataSourceStatusText(dataSource.status)}
                  </span>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-2">
                  <span className="font-medium">类型：</span>{dataSource.type}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">{dataSource.description}</p>
                {dataSource.lastTest && (
                  <div className="text-xs text-gray-500 dark:text-gray-400 mb-4">
                    最后测试：{dataSource.lastTest}
                  </div>
                )}
                <button
                  onClick={() => handleTestConnection(dataSource.id)}
                  disabled={testingDataSource === dataSource.id || testConnectionMutation.isPending}
                  className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {testingDataSource === dataSource.id ? '测试中...' : '测试连接'}
                </button>
              </div>
            ))
          ) : (
            <div className="col-span-full bg-white dark:bg-gray-800 rounded-lg shadow p-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">暂无异构数据源</p>
            </div>
          )}
        </div>
      </div>

      {/* 数据质量实时诊断区域 */}
      <div>
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">数据质量实时诊断</h2>
          <div className="flex gap-2">
            <button
              onClick={() => setViewMode('realtime')}
              className={`px-3 py-1 rounded-lg ${viewMode === 'realtime' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
            >
              实时视图
            </button>
            <button
              onClick={() => setViewMode('history')}
              className={`px-3 py-1 rounded-lg ${viewMode === 'history' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300'}`}
            >
              历史视图
            </button>
          </div>
        </div>

        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
          {qualityMetricsLoading ? (
            <div className="animate-pulse space-y-4">
              {Array(3).fill(0).map((_, index) => (
                <div key={index}>
                  <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded mb-1"></div>
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
                </div>
              ))}
            </div>
          ) : dataQualityMetrics && dataQualityMetrics.length > 0 ? (
            dataQualityMetrics.map(metric => (
              <div key={metric.id} className="mb-6 last:mb-0">
                <div className="flex justify-between items-center mb-3">
                  <h3 className="font-medium text-gray-900 dark:text-white">{metric.dataSourceName}</h3>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{metric.timestamp}</span>
                </div>
                
                <div className="space-y-3">
                  {/* 完整性 */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-400">完整性</span>
                      <span className="font-medium">{metric.completeness}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all ${metric.completeness >= 90 ? 'bg-green-500' : metric.completeness >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${metric.completeness}%` }}
                      />
                    </div>
                  </div>
                  
                  {/* 时效性 */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-400">时效性</span>
                      <span className="font-medium">{metric.timeliness}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all ${metric.timeliness >= 90 ? 'bg-green-500' : metric.timeliness >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${metric.timeliness}%` }}
                      />
                    </div>
                  </div>
                  
                  {/* 准确性 */}
                  <div>
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-600 dark:text-gray-400">准确性</span>
                      <span className="font-medium">{metric.accuracy}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                      <div 
                        className={`h-full transition-all ${metric.accuracy >= 90 ? 'bg-green-500' : metric.accuracy >= 70 ? 'bg-yellow-500' : 'bg-red-500'}`}
                        style={{ width: `${metric.accuracy}%` }}
                      />
                    </div>
                  </div>
                </div>
                
                {/* 数据质量问题 */}
                {metric.issues && metric.issues.length > 0 && (
                  <div className="mt-4">
                    <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">数据质量问题</h4>
                    <div className="space-y-2">
                      {metric.issues.map((issue, index) => (
                        <div key={index} className="bg-gray-50 dark:bg-gray-700 p-3 rounded-lg">
                          <div className="flex justify-between items-start mb-1">
                            <span className="text-sm font-medium text-gray-900 dark:text-white">{issue.type}</span>
                            <span className={`px-2 py-0.5 text-xs rounded-full ${getSeverityColor(issue.severity)}`}>
                              {issue.severity === 'high' ? '高' : issue.severity === 'medium' ? '中' : '低'}
                            </span>
                          </div>
                          <p className="text-xs text-gray-600 dark:text-gray-400 mb-2">{issue.description}</p>
                          <div className="text-xs text-blue-600 dark:text-blue-400">
                            <span className="font-medium">建议修复：</span>{issue.suggestedFix}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="py-8 text-center">
              <p className="text-gray-500 dark:text-gray-400">暂无数据质量指标</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const DataSourceTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [showConfigModal, setShowConfigModal] = useState(false);
  const [selectedDataSource, setSelectedDataSource] = useState<DataSource | null>(null);
  const [configParams, setConfigParams] = useState<DataSourceParams>({
    collectionFrequency: '每小时',
    dataReportingInterval: '每15分钟',
    alertThreshold: 90
  });

  const { data: dataSources, isLoading: dataSourcesLoading } = useQuery({
    queryKey: ['data-sources'],
    queryFn: fetchDataSources,
    refetchInterval: 5000,
  });

  const startMutation = useMutation({
    mutationFn: startDataSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
    },
  });

  const pauseMutation = useMutation({
    mutationFn: pauseDataSource,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
    },
  });

  const configureMutation = useMutation({
    mutationFn: (data: { id: string; params: DataSourceParams }) => configureDataSource(data.id, data.params),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-sources'] });
      setShowConfigModal(false);
      setSelectedDataSource(null);
    },
  });

  const getDataSourceStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-green-600 bg-green-100';
      case 'paused': return 'text-yellow-600 bg-yellow-100';
      case 'error': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getDataSourceStatusText = (status: string) => {
    switch (status) {
      case 'running': return '采集中';
      case 'paused': return '已暂停';
      case 'error': return '异常';
      default: return status;
    }
  };

  const handleConfigure = (dataSource: DataSource) => {
    setSelectedDataSource(dataSource);
    setConfigParams({
      collectionFrequency: dataSource.collectionFrequency || '每小时',
      dataReportingInterval: dataSource.dataReportingInterval || '每15分钟',
      alertThreshold: dataSource.alertThreshold || 90
    });
    setShowConfigModal(true);
  };

  const handleViewData = (dataSource: DataSource) => {
    // 跳转到数据监控或历史数据查询界面
    console.log('View data for:', dataSource.name);
    // 这里可以添加路由跳转逻辑
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">数据源采集任务管理</h2>
      </div>

      <div className="border rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">数据源名称</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">最后运行</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">下次运行</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {dataSourcesLoading ? (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">加载中...</td></tr>
            ) : dataSources && dataSources.length > 0 ? (
              dataSources.map(dataSource => (
                <tr key={dataSource.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{dataSource.name}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs rounded-full ${getDataSourceStatusColor(dataSource.status)}`}>
                      {getDataSourceStatusText(dataSource.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{dataSource.lastRun || '-'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{dataSource.nextRun || '-'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {dataSource.status !== 'running' ? (
                        <button
                          onClick={() => startMutation.mutate(dataSource.id)}
                          className="p-1 text-green-600 hover:bg-green-50 rounded"
                          title="启动采集"
                        >
                          <PlayIcon className="w-4 h-4" />
                        </button>
                      ) : (
                        <button
                          onClick={() => pauseMutation.mutate(dataSource.id)}
                          className="p-1 text-yellow-600 hover:bg-yellow-50 rounded"
                          title="暂停采集"
                        >
                          <StopIcon className="w-4 h-4" />
                        </button>
                      )}
                      <button
                        onClick={() => handleConfigure(dataSource)}
                        className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                        title="配置参数"
                      >
                        <CogIcon className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleViewData(dataSource)}
                        className="p-1 text-purple-600 hover:bg-purple-50 rounded"
                        title="查看数据"
                      >
                        <Bars3Icon className="w-4 h-4" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={5} className="px-4 py-8 text-center text-gray-500">暂无数据源</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showConfigModal && selectedDataSource && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">配置 {selectedDataSource.name} 参数</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">采集频率</label>
                <select
                  value={configParams.collectionFrequency}
                  onChange={e => setConfigParams({ ...configParams, collectionFrequency: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="每5分钟">每5分钟</option>
                  <option value="每15分钟">每15分钟</option>
                  <option value="每30分钟">每30分钟</option>
                  <option value="每小时">每小时</option>
                  <option value="每4小时">每4小时</option>
                  <option value="每天">每天</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">数据上报间隔</label>
                <select
                  value={configParams.dataReportingInterval}
                  onChange={e => setConfigParams({ ...configParams, dataReportingInterval: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="每5分钟">每5分钟</option>
                  <option value="每15分钟">每15分钟</option>
                  <option value="每30分钟">每30分钟</option>
                  <option value="每小时">每小时</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">报警阈值</label>
                <input
                  type="number"
                  value={configParams.alertThreshold}
                  onChange={e => setConfigParams({ ...configParams, alertThreshold: parseInt(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  min="0"
                  max="100"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowConfigModal(false);
                  setSelectedDataSource(null);
                }}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={() => configureMutation.mutate({ id: selectedDataSource.id, params: configParams })}
                disabled={configureMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {configureMutation.isPending ? '保存中...' : '保存配置'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const TaskMonitorTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newTask, setNewTask] = useState({ city_name: '', task_type: 'community', province_name: '', total_items: 100 });
  const [selectedCity, setSelectedCity] = useState<string | null>(null);

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['data-collection-dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 5000,
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['data-collection-tasks', selectedCity],
    queryFn: () => fetchTasks(selectedCity ? { city: selectedCity } : {}),
    refetchInterval: 3000,
  });

  const createMutation = useMutation({
    mutationFn: createTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-collection-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['data-collection-tasks'] });
      setShowCreateModal(false);
      setNewTask({ city_name: '', task_type: 'community', province_name: '', total_items: 100 });
    },
  });

  const cancelMutation = useMutation({
    mutationFn: cancelTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-collection-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['data-collection-tasks'] });
    },
  });

  const retryMutation = useMutation({
    mutationFn: retryTask,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['data-collection-dashboard'] });
      queryClient.invalidateQueries({ queryKey: ['data-collection-tasks'] });
    },
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-green-600 bg-green-100';
      case 'processing': return 'text-blue-600 bg-blue-100';
      case 'pending': return 'text-yellow-600 bg-yellow-100';
      case 'failed': return 'text-red-600 bg-red-100';
      case 'cancelled': return 'text-gray-600 bg-gray-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed': return '已完成';
      case 'processing': return '进行中';
      case 'pending': return '待处理';
      case 'failed': return '失败';
      case 'cancelled': return '已取消';
      default: return status;
    }
  };

  const getTaskTypeName = (type: string) => {
    switch (type) {
      case 'community': return '小区采集';
      case 'price': return '价格采集';
      case 'poi': return 'POI采集';
      default: return type;
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold">数据采集任务监控</h2>
        <button
          onClick={() => setShowCreateModal(true)}
          className="flex items-center gap-1 px-3 py-1.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <PlusIcon className="w-4 h-4" />
          新建任务
        </button>
      </div>

      {dashboard && (
        <div className="grid grid-cols-5 gap-3">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-gray-900 dark:text-white">{dashboard.total_tasks}</div>
            <div className="text-xs text-gray-500">总任务</div>
          </div>
          <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-yellow-600">{dashboard.pending_tasks}</div>
            <div className="text-xs text-gray-500">待处理</div>
          </div>
          <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-blue-600">{dashboard.processing_tasks}</div>
            <div className="text-xs text-gray-500">进行中</div>
          </div>
          <div className="bg-green-50 dark:bg-green-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-green-600">{dashboard.completed_tasks}</div>
            <div className="text-xs text-gray-500">已完成</div>
          </div>
          <div className="bg-red-50 dark:bg-red-900/20 rounded-lg p-3 text-center">
            <div className="text-2xl font-bold text-red-600">{dashboard.failed_tasks}</div>
            <div className="text-xs text-gray-500">失败</div>
          </div>
        </div>
      )}

      <div className="border rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">城市</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">任务类型</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">进度</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">消息</th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
            </tr>
          </thead>
          <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
            {tasksLoading ? (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">加载中...</td></tr>
            ) : tasks && tasks.length > 0 ? (
              tasks.map(task => (
                <tr key={task.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{task.city_name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{getTaskTypeName(task.task_type)}</td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                      {getStatusText(task.status)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2">
                      <div className="flex-1 h-2 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div 
                          className={`h-full transition-all ${task.status === 'completed' ? 'bg-green-500' : task.status === 'failed' ? 'bg-red-500' : 'bg-blue-500'}`}
                          style={{ width: `${task.progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-gray-500 w-10">{task.progress}%</span>
                    </div>
                    <div className="text-xs text-gray-400 mt-1">{task.processed_items}/{task.total_items || '?'}</div>
                  </td>
                  <td className="px-4 py-3 text-xs text-gray-500 max-w-xs truncate">{task.message || task.error_message || '-'}</td>
                  <td className="px-4 py-3">
                    <div className="flex gap-1">
                      {task.status === 'processing' && (
                        <button
                          onClick={() => cancelMutation.mutate(task.id)}
                          className="p-1 text-red-600 hover:bg-red-50 rounded"
                          title="取消"
                        >
                          <StopIcon className="w-4 h-4" />
                        </button>
                      )}
                      {(task.status === 'failed' || task.status === 'cancelled') && (
                        <button
                          onClick={() => retryMutation.mutate(task.id)}
                          className="p-1 text-blue-600 hover:bg-blue-50 rounded"
                          title="重试"
                        >
                          <ArrowPathIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            ) : (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">暂无任务</td></tr>
            )}
          </tbody>
        </table>
      </div>

      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">新建采集任务</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">城市名称</label>
                <input
                  type="text"
                  value={newTask.city_name}
                  onChange={e => setNewTask({ ...newTask, city_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  placeholder="如：深圳"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">省份</label>
                <input
                  type="text"
                  value={newTask.province_name}
                  onChange={e => setNewTask({ ...newTask, province_name: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  placeholder="如：广东省"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">任务类型</label>
                <select
                  value={newTask.task_type}
                  onChange={e => setNewTask({ ...newTask, task_type: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                >
                  <option value="community">小区采集</option>
                  <option value="price">价格采集</option>
                  <option value="poi">POI采集</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">预计数量</label>
                <input
                  type="number"
                  value={newTask.total_items}
                  onChange={e => setNewTask({ ...newTask, total_items: parseInt(e.target.value) || 100 })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={() => createMutation.mutate(newTask)}
                disabled={!newTask.city_name || createMutation.isPending}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
              >
                {createMutation.isPending ? '创建中...' : '创建任务'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const LoadPressureAnalysisTab: React.FC = () => {
  const [taskQueue, setTaskQueue] = useState('default');
  const [startTime, setStartTime] = useState('2024-01-15 00:00:00');
  const [endTime, setEndTime] = useState('2024-01-15 23:59:59');
  const [loadPressureData, setLoadPressureData] = useState<LoadPressureData[]>([]);
  const [crossCorrelationResults, setCrossCorrelationResults] = useState<CrossCorrelationResult[]>([]);
  const [taskAccumulationResults, setTaskAccumulationResults] = useState<TaskAccumulationResult[]>([]);
  const [loadImpactFactors, setLoadImpactFactors] = useState<LoadImpactFactor[]>(MOCK_LOAD_IMPACT_FACTORS);
  const [analysisResults, setAnalysisResults] = useState<{ totalAccumulation: number; averageResponseTime: number; systemLoadDeviation: number } | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [windowSize, setWindowSize] = useState(10);
  const [samplingInterval, setSamplingInterval] = useState(1);
  const [algorithm, setAlgorithm] = useState('pearson');
  const [decayFactor, setDecayFactor] = useState(0.1);
  const [baseLoad, setBaseLoad] = useState(10);
  const [lagTime, setLagTime] = useState(5);

  const handleFetchData = async () => {
    setIsLoading(true);
    try {
      const data = await fetchLoadPressureData(taskQueue, startTime, endTime);
      setLoadPressureData(data);
    } catch (error) {
      console.error('Failed to fetch load pressure data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCrossCorrelation = async () => {
    setIsLoading(true);
    try {
      const results = await executeCrossCorrelation({ windowSize, samplingInterval, algorithm });
      setCrossCorrelationResults(results);
    } catch (error) {
      console.error('Failed to execute cross correlation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCalculateAccumulation = async () => {
    setIsLoading(true);
    try {
      const results = await calculateTaskAccumulation({ decayFactor, baseLoad, lagTime });
      setTaskAccumulationResults(results);
    } catch (error) {
      console.error('Failed to calculate task accumulation:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLoadImpactAnalysis = async () => {
    setIsLoading(true);
    try {
      const results = await executeLoadImpactAnalysis(loadImpactFactors);
      setAnalysisResults(results);
    } catch (error) {
      console.error('Failed to execute load impact analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateFactor = (id: string, field: keyof LoadImpactFactor, value: number) => {
    setLoadImpactFactors(loadImpactFactors.map(factor => 
      factor.id === id ? { ...factor, [field]: value } : factor
    ));
  };

  return (
    <div className="space-y-6">
      {/* 基础数据查询 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">基础数据查询</h2>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">目标任务队列</label>
            <select
              value={taskQueue}
              onChange={e => setTaskQueue(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="default">默认队列</option>
              <option value="high-priority">高优先级队列</option>
              <option value="low-priority">低优先级队列</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">开始时间</label>
            <input
              type="datetime-local"
              value={startTime.replace(' ', 'T')}
              onChange={e => setStartTime(e.target.value.replace('T', ' '))}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">结束时间</label>
            <input
              type="datetime-local"
              value={endTime.replace(' ', 'T')}
              onChange={e => setEndTime(e.target.value.replace(' ', ' '))}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleFetchData}
              disabled={isLoading}
              className="w-full py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? '查询中...' : '查询分析数据'}
            </button>
          </div>
        </div>
      </div>

      {/* 滞后效应分析仪 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">滞后效应分析仪</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">滑动窗口</label>
            <input
              type="number"
              value={windowSize}
              onChange={e => setWindowSize(parseInt(e.target.value) || 10)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              min="1"
              max="30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">采样间隔</label>
            <input
              type="number"
              value={samplingInterval}
              onChange={e => setSamplingInterval(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              min="1"
              max="10"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">算法类型</label>
            <select
              value={algorithm}
              onChange={e => setAlgorithm(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="pearson">Pearson相关系数</option>
              <option value="spearman">Spearman等级相关</option>
              <option value="kendall">Kendall秩相关</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleCrossCorrelation}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 mb-4"
        >
          {isLoading ? '分析中...' : '执行互相关分析'}
        </button>
        <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-2">滞后时间相关性分析</h3>
          {crossCorrelationResults.length > 0 ? (
            <div className="h-48 overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr>
                    <th className="text-left text-xs font-medium text-gray-500">滞后时间</th>
                    <th className="text-left text-xs font-medium text-gray-500">相关系数</th>
                  </tr>
                </thead>
                <tbody>
                  {crossCorrelationResults.map((result, index) => (
                    <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                      <td className="py-2 text-sm">{result.lag}</td>
                      <td className="py-2 text-sm">{result.correlation.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
              执行互相关分析以查看结果
            </div>
          )}
        </div>
        <div className="flex gap-2 mt-4">
          <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
            自动标定
          </button>
          <button className="px-4 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
            手动确认
          </button>
        </div>
      </div>

      {/* 任务累积计算器 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">任务累积计算器</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">任务衰减系数</label>
            <input
              type="number"
              value={decayFactor}
              onChange={e => setDecayFactor(parseFloat(e.target.value) || 0.1)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              step="0.01"
              min="0"
              max="1"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">基准负载</label>
            <input
              type="number"
              value={baseLoad}
              onChange={e => setBaseLoad(parseFloat(e.target.value) || 10)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              step="1"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">滞后时间</label>
            <input
              type="number"
              value={lagTime}
              onChange={e => setLagTime(parseFloat(e.target.value) || 5)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              step="1"
              min="0"
            />
          </div>
        </div>
        <button
          onClick={handleCalculateAccumulation}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 mb-4"
        >
          {isLoading ? '计算中...' : '计算任务累积序列'}
        </button>
        <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          <h3 className="text-sm font-medium mb-2">任务积压曲线</h3>
          {taskAccumulationResults.length > 0 ? (
            <div className="h-48 overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr>
                    <th className="text-left text-xs font-medium text-gray-500">时间</th>
                    <th className="text-left text-xs font-medium text-gray-500">任务积压</th>
                  </tr>
                </thead>
                <tbody>
                  {taskAccumulationResults.map((result, index) => (
                    <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                      <td className="py-2 text-sm">{result.timestamp}</td>
                      <td className="py-2 text-sm">{result.accumulation.toFixed(2)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
              计算任务累积序列以查看结果
            </div>
          )}
        </div>
      </div>

      {/* 负载影响因素组合 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">负载影响因素组合</h2>
        <div className="space-y-4 mb-4">
          {loadImpactFactors.map(factor => (
            <div key={factor.id} className="flex gap-4 items-center">
              <div className="w-1/3">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">{factor.name}</label>
              </div>
              <div className="w-1/3">
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">权重系数</label>
                <input
                  type="number"
                  value={factor.weight}
                  onChange={e => handleUpdateFactor(factor.id, 'weight', parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  step="0.05"
                  min="0"
                  max="1"
                />
              </div>
              <div className="w-1/3">
                <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">影响值</label>
                <input
                  type="number"
                  value={factor.value}
                  onChange={e => handleUpdateFactor(factor.id, 'value', parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-1 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  step="0.05"
                  min="0"
                  max="1"
                />
              </div>
            </div>
          ))}
        </div>
        <button
          onClick={handleLoadImpactAnalysis}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 mb-4"
        >
          {isLoading ? '分析中...' : '执行影响组合'}
        </button>
        {analysisResults && (
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
            <h3 className="text-sm font-medium mb-2">分析结果</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">任务积压总时长</div>
                <div className="font-medium">{analysisResults.totalAccumulation} 分钟</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">平均响应时间</div>
                <div className="font-medium">{analysisResults.averageResponseTime} 秒</div>
              </div>
              <div>
                <div className="text-xs text-gray-500 dark:text-gray-400">系统负载偏差</div>
                <div className="font-medium">{analysisResults.systemLoadDeviation.toFixed(2)}</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 分析报告下载 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">分析报告</h2>
        <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
          下载完整分析报告
        </button>
      </div>
    </div>
  );
};

const AgentLoadPredictionTab: React.FC = () => {
  const [predictionParams, setPredictionParams] = useState<AgentLoadPredictionParams>({
    currentQueueLength: 100,
    averageProcessingTime: 2.5,
    concurrencyLimit: 50,
    historicalLoadPeak: 200,
    taskComplexityFactor: 1.0
  });
  const [predictionHorizon, setPredictionHorizon] = useState(24);
  const [predictionStep, setPredictionStep] = useState(1);
  const [modelVersion, setModelVersion] = useState('v1.0');
  const [predictionResults, setPredictionResults] = useState<AgentLoadPredictionResult[]>([]);
  const [predictionReport, setPredictionReport] = useState<PredictionReport | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isValidating, setIsValidating] = useState(false);
  const [validationMessage, setValidationMessage] = useState<string>('');
  const [showImportModal, setShowImportModal] = useState(false);
  const [showReportModal, setShowReportModal] = useState(false);

  const handleValidateParams = async () => {
    setIsValidating(true);
    try {
      const result = await validatePredictionParams(predictionParams);
      setValidationMessage(result.message);
    } catch (error) {
      console.error('Failed to validate parameters:', error);
    } finally {
      setIsValidating(false);
    }
  };

  const handleStartPrediction = async () => {
    setIsLoading(true);
    try {
      const results = await predictAgentLoad({
        ...predictionParams,
        predictionHorizon,
        predictionStep,
        modelVersion
      });
      setPredictionResults(results);
    } catch (error) {
      console.error('Failed to predict agent load:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateReport = async () => {
    if (predictionResults.length === 0) return;
    setIsLoading(true);
    try {
      const report = await generatePredictionReport(predictionResults);
      setPredictionReport(report);
      setShowReportModal(true);
    } catch (error) {
      console.error('Failed to generate prediction report:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* 模型输入配置 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">智能体任务负载预测模型输入配置</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">当前任务队列长度</label>
            <div className="flex gap-2">
              <input
                type="number"
                value={predictionParams.currentQueueLength}
                onChange={e => setPredictionParams({ ...predictionParams, currentQueueLength: parseInt(e.target.value) || 0 })}
                className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                min="0"
              />
              <button
                onClick={() => setShowImportModal(true)}
                className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700 whitespace-nowrap"
              >
                导入数据
              </button>
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">智能体平均处理时长（秒）</label>
            <input
              type="number"
              value={predictionParams.averageProcessingTime}
              onChange={e => setPredictionParams({ ...predictionParams, averageProcessingTime: parseFloat(e.target.value) || 0 })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              step="0.1"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">系统并发上限</label>
            <input
              type="number"
              value={predictionParams.concurrencyLimit}
              onChange={e => setPredictionParams({ ...predictionParams, concurrencyLimit: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              min="0"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">历史负载峰值</label>
            <input
              type="number"
              value={predictionParams.historicalLoadPeak}
              onChange={e => setPredictionParams({ ...predictionParams, historicalLoadPeak: parseInt(e.target.value) || 0 })}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              min="0"
            />
          </div>
          <div className="md:col-span-2">
            <div className="flex gap-2">
              <div className="flex-1">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">任务复杂度系数</label>
                <input
                  type="number"
                  value={predictionParams.taskComplexityFactor}
                  onChange={e => setPredictionParams({ ...predictionParams, taskComplexityFactor: parseFloat(e.target.value) || 0 })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  step="0.1"
                  min="0"
                  max="2"
                />
              </div>
              <div className="flex items-end">
                <button
                  onClick={handleValidateParams}
                  disabled={isValidating}
                  className="px-3 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
                >
                  {isValidating ? '校验中...' : '校验合理性'}
                </button>
              </div>
            </div>
            {validationMessage && (
              <div className="mt-2 text-sm text-gray-600 dark:text-gray-300">
                {validationMessage}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 预测控制台 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">智能体任务负载预测控制台</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">预测未来时长（小时）</label>
            <input
              type="number"
              value={predictionHorizon}
              onChange={e => setPredictionHorizon(parseInt(e.target.value) || 24)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              min="1"
              max="72"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">预测步长（小时）</label>
            <input
              type="number"
              value={predictionStep}
              onChange={e => setPredictionStep(parseInt(e.target.value) || 1)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
              min="1"
              max="6"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">模型版本</label>
            <select
              value={modelVersion}
              onChange={e => setModelVersion(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="v1.0">v1.0 - 基础模型</option>
              <option value="v2.0">v2.0 - 增强模型</option>
              <option value="v3.0">v3.0 - 深度学习模型</option>
            </select>
          </div>
        </div>
        <button
          onClick={handleStartPrediction}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 mb-4"
        >
          {isLoading ? '预测中...' : '开始启动预测'}
        </button>
        {isLoading && (
          <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 mb-4">
            <div className="bg-blue-600 h-2.5 rounded-full animate-pulse" style={{ width: '75%' }}></div>
          </div>
        )}
      </div>

      {/* 预测结果 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">未来任务负载变化曲线</h2>
        <div className="h-64 bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
          {predictionResults.length > 0 ? (
            <div className="h-48 overflow-auto">
              <table className="min-w-full">
                <thead>
                  <tr>
                    <th className="text-left text-xs font-medium text-gray-500">时间</th>
                    <th className="text-left text-xs font-medium text-gray-500">任务队列长度</th>
                    <th className="text-left text-xs font-medium text-gray-500">资源占用率</th>
                    <th className="text-left text-xs font-medium text-gray-500">响应时间</th>
                  </tr>
                </thead>
                <tbody>
                  {predictionResults.map((result, index) => (
                    <tr key={index} className="border-t border-gray-200 dark:border-gray-700">
                      <td className="py-2 text-sm">{result.timestamp}</td>
                      <td className="py-2 text-sm">{result.predictedQueueLength.toFixed(2)}</td>
                      <td className="py-2 text-sm">{result.resourceUtilization.toFixed(2)}%</td>
                      <td className="py-2 text-sm">{result.responseTime.toFixed(2)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="h-48 flex items-center justify-center text-gray-500 dark:text-gray-400">
              启动预测以查看结果
            </div>
          )}
        </div>
        <div className="mt-4">
          <button
            onClick={handleGenerateReport}
            disabled={isLoading || predictionResults.length === 0}
            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50"
          >
            预测报告生成
          </button>
        </div>
      </div>

      {/* 导入历史数据弹窗 */}
      {showImportModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">导入历史数据</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">数据源</label>
                <select className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600">
                  <option value="hippocampus">海马体记忆</option>
                  <option value="database">数据库记录</option>
                  <option value="file">文件导入</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">时间范围</label>
                <div className="grid grid-cols-2 gap-2">
                  <input type="datetime-local" className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                  <input type="datetime-local" className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600" />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">数据处理选项</label>
                <div className="space-y-2">
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">去除异常值</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">数据平滑</span>
                  </label>
                  <label className="flex items-center gap-2">
                    <input type="checkbox" className="rounded" />
                    <span className="text-sm">自动填充缺失值</span>
                  </label>
                </div>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowImportModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={() => setShowImportModal(false)}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                确认导入
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 预测报告弹窗 */}
      {showReportModal && predictionReport && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-2xl max-h-[80vh] overflow-y-auto">
            <h3 className="text-lg font-semibold mb-4">预测报告预览</h3>
            <div className="space-y-4">
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">生成时间</h4>
                <p className="text-sm">{new Date(predictionReport.generatedAt).toLocaleString()}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">峰值负载时间点</h4>
                <p className="text-sm">{predictionReport.peakLoadTime}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">建议的扩容时机</h4>
                <p className="text-sm">{predictionReport.recommendedScalingTime}</p>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">潜在的资源瓶颈</h4>
                <ul className="list-disc pl-5 text-sm space-y-1">
                  {predictionReport.potentialBottlenecks.map((bottleneck, index) => (
                    <li key={index}>{bottleneck}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">摘要</h4>
                <p className="text-sm">{predictionReport.summary}</p>
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowReportModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                关闭
              </button>
              <button
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
              >
                导出报告
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const AlertManagementTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [region, setRegion] = useState('深圳南山区');
  const [complexityFactor, setComplexityFactor] = useState(1.0);
  const [minTaskBenchmark, setMinTaskBenchmark] = useState(50);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleGenerateBenchmark = async () => {
    setIsLoading(true);
    try {
      const benchmarkData = await generateAlertBenchmark({ region, complexityCoefficient: complexityFactor });
      // 计算最小任务执行基准值
      setMinTaskBenchmark(Math.min(...benchmarkData.map(item => item.value)));
    } catch (error) {
      console.error('Failed to generate benchmark:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateAlerts = async () => {
    setIsLoading(true);
    try {
      const generatedAlerts = await generateAlerts({ region, useMockData: true });
      setAlerts(generatedAlerts);
    } catch (error) {
      console.error('Failed to generate alerts:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleUpdateAlertStatus = async (alertId: string, action: 'confirm' | 'ignore') => {
    try {
      await processAlert(alertId, action);
      const newStatus = action === 'confirm' ? 'processed' : 'ignored';
      setAlerts(alerts.map(alert => alert.id === alertId ? { ...alert, status: newStatus } : alert));
    } catch (error) {
      console.error('Failed to update alert status:', error);
    }
  };

  const handleMarkAllConfirmed = async () => {
    try {
      const unprocessedAlerts = alerts.filter(alert => alert.status === 'unprocessed');
      const alertIds = unprocessedAlerts.map(alert => alert.id);
      await batchProcessAlerts(alertIds, 'confirm');
      setAlerts(alerts.map(alert => alert.status === 'unprocessed' ? { ...alert, status: 'processed' } : alert));
    } catch (error) {
      console.error('Failed to mark all alerts as confirmed:', error);
    }
  };

  const getAlertLevelColor = (level: string) => {
    switch (level) {
      case 'high': return 'text-red-600 bg-red-100';
      case 'medium': return 'text-yellow-600 bg-yellow-100';
      case 'low': return 'text-green-600 bg-green-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getAlertStatusColor = (status: string) => {
    switch (status) {
      case 'processed': return 'text-green-600';
      case 'ignored': return 'text-gray-600';
      case 'unprocessed': return 'text-blue-600';
      default: return 'text-gray-600';
    }
  };

  return (
    <div className="space-y-6">
      {/* 预警生成区域 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">预警生成与列表管理</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">数据源（区域）</label>
            <select
              value={region}
              onChange={e => setRegion(e.target.value)}
              className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            >
              <option value="深圳南山区">深圳南山区</option>
              <option value="北京朝阳区">北京朝阳区</option>
              <option value="上海浦东新区">上海浦东新区</option>
              <option value="广州天河区">广州天河区</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">任务复杂度系数</label>
            <div className="flex gap-2 items-center">
              <input
                type="range"
                min="0.5"
                max="2.0"
                step="0.1"
                value={complexityFactor}
                onChange={e => setComplexityFactor(parseFloat(e.target.value))}
                className="flex-1"
              />
              <span className="text-sm w-16">{complexityFactor.toFixed(1)}</span>
            </div>
          </div>
          <div className="flex flex-col justify-between">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">最小任务执行基准值</label>
              <div className="text-lg font-medium">{minTaskBenchmark.toFixed(2)}</div>
            </div>
            <button
              onClick={handleGenerateBenchmark}
              disabled={isLoading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              {isLoading ? '生成中...' : '生成区域任务执行基准序列'}
            </button>
          </div>
        </div>
        
        <div className="mb-4">
          <h3 className="text-md font-medium mb-2">关联预警响应曲线</h3>
          <div className="flex gap-2">
            <button className="px-3 py-1 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
              导入实际任务执行日志
            </button>
            <button className="px-3 py-1 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
              使用模拟数据
            </button>
          </div>
        </div>
        
        <button
          onClick={handleGenerateAlerts}
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          {isLoading ? '生成中...' : '执行对比逻辑并生成预警列表'}
        </button>
      </div>

      {/* 预警列表区域 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">预警处置与工单衔接</h2>
        
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">时间范围</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">预警等级</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">标签编号</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">偏离描述</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {alerts.length > 0 ? (
                alerts.map(alert => (
                  <tr key={alert.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{alert.timeRange}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getAlertLevelColor(alert.level)}`}>
                        {alert.level === 'high' ? '高' : alert.level === 'medium' ? '中' : '低'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{alert.tag}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{alert.description}</td>
                    <td className="px-4 py-3">
                      <span className={`text-sm ${getAlertStatusColor(alert.status)}`}>
                        {alert.status === 'processed' ? '已处理' : alert.status === 'ignored' ? '已忽略' : '未处理'}
                      </span>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1">
                        {alert.status === 'unprocessed' && (
                          <>
                            <button
                              onClick={() => handleUpdateAlertStatus(alert.id, 'confirm')}
                              className="p-1 text-green-600 hover:bg-green-50 rounded"
                              title="确认"
                            >
                              ✓
                            </button>
                            <button
                              onClick={() => handleUpdateAlertStatus(alert.id, 'ignore')}
                              className="p-1 text-gray-600 hover:bg-gray-50 rounded"
                              title="忽略"
                            >
                              ×
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">暂无预警信息</td></tr>
              )}
            </tbody>
          </table>
        </div>
        
        {alerts.some(alert => alert.status === 'unprocessed') && (
          <div className="mt-4 flex justify-end">
            <button
              onClick={handleMarkAllConfirmed}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700"
            >
              全部标记确认
            </button>
          </div>
        )}
        
        {/* 时间轴与模式切换 */}
        <div className="mt-6">
          <div className="flex justify-between items-center mb-2">
            <h3 className="text-md font-medium">时间轴视图</h3>
            <div className="flex gap-2">
              <button className="px-2 py-1 text-sm bg-gray-200 dark:bg-gray-700 rounded">日</button>
              <button className="px-2 py-1 text-sm bg-blue-600 text-white rounded">周</button>
              <button className="px-2 py-1 text-sm bg-gray-200 dark:bg-gray-700 rounded">月</button>
            </div>
          </div>
          <div className="h-24 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 flex items-center justify-between">
            <div className="w-full flex items-center gap-1">
              {Array.from({ length: 7 }, (_, i) => (
                <div key={i} className="flex-1 h-12 border-r border-gray-200 dark:border-gray-600 flex flex-col items-center justify-center">
                  <div className="text-xs text-gray-500">{i + 1}日</div>
                  <div className="mt-1 w-2 h-2 rounded-full bg-blue-500"></div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

const WorkOrderManagementTab: React.FC = () => {
  const queryClient = useQueryClient();
  const [activeStatus, setActiveStatus] = useState<MaintenanceOrder['status']>('pending');
  const [orders, setOrders] = useState<MaintenanceOrder[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newOrder, setNewOrder] = useState({ title: '', description: '' });

  useEffect(() => {
    const fetchOrders = async () => {
      setIsLoading(true);
      try {
        const data = await fetchMaintenanceOrders(activeStatus);
        setOrders(data);
      } catch (error) {
        console.error('Failed to fetch orders:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchOrders();
  }, [activeStatus]);

  const handleProcessOrder = async (orderId: string, action: 'accept' | 'ignore') => {
    try {
      await processOrder(orderId, action);
      const newStatus = action === 'accept' ? 'in-progress' : 'ignored';
      setOrders(orders.map(order => order.id === orderId ? { ...order, status: newStatus } : order));
    } catch (error) {
      console.error('Failed to process order:', error);
    }
  };

  const handleCreateEmergencyOrder = async () => {
    if (!newOrder.title || !newOrder.description) return;
    
    setIsLoading(true);
    try {
      await createEmergencyOrder({ title: newOrder.title, description: newOrder.description, priority: 'high' });
      setShowCreateModal(false);
      setNewOrder({ title: '', description: '' });
      // 重新获取订单列表
      const data = await fetchMaintenanceOrders(activeStatus);
      setOrders(data);
    } catch (error) {
      console.error('Failed to create emergency order:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-600';
      case 'medium': return 'text-yellow-600';
      case 'low': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending': return 'text-blue-600';
      case 'in-progress': return 'text-yellow-600';
      case 'awaiting-approval': return 'text-purple-600';
      case 'completed': return 'text-green-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'pending': return '待处理';
      case 'in-progress': return '进行中';
      case 'awaiting-approval': return '待验收';
      case 'completed': return '已完成';
      default: return status;
    }
  };

  return (
    <div className="space-y-6">
      {/* 运维指令台 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">运维指令台</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {orders.filter(order => order.status === 'pending').map(order => (
            <div key={order.id} className="border rounded-lg p-4">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-medium text-gray-900 dark:text-white">{order.title}</h3>
                <span className={`text-sm font-medium ${getPriorityColor(order.priority)}`}>
                  {order.priority === 'high' ? '高' : order.priority === 'medium' ? '中' : '低'}优先级
                </span>
              </div>
              <p className="text-sm text-gray-600 dark:text-gray-300 mb-3">{order.description}</p>
              <div className="flex justify-between items-center text-xs text-gray-500 mb-3">
                <span>来源：{order.source}</span>
                <span>建议处理时间：{order.suggestedProcessingTime}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className={`text-sm ${getStatusColor(order.status)}`}>
                  {getStatusText(order.status)}
                </span>
                {order.status === 'pending' && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleProcessOrder(order.id, 'accept')}
                      className="px-3 py-1 bg-blue-600 text-white text-xs rounded hover:bg-blue-700"
                    >
                      确认执行
                    </button>
                    <button
                      onClick={() => handleProcessOrder(order.id, 'ignore')}
                      className="px-3 py-1 bg-gray-600 text-white text-xs rounded hover:bg-gray-700"
                    >
                      忽略
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 任务工单流管理 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-lg font-semibold">任务工单流管理</h2>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            创建紧急运维工单
          </button>
        </div>
        
        <div className="border-b dark:border-gray-700 mb-4">
          <div className="flex gap-2">
            {(['pending', 'in-progress', 'awaiting-approval', 'completed'] as MaintenanceOrder['status'][]).map(status => (
              <button
                key={status}
                onClick={() => setActiveStatus(status)}
                className={`px-4 py-2 font-medium whitespace-nowrap ${activeStatus === status ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
              >
                {getStatusText(status)}
              </button>
            ))}
          </div>
        </div>
        
        <div className="border rounded-lg overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">工单编号</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">标题</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">优先级</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">来源</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">状态</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">创建时间</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">操作</th>
              </tr>
            </thead>
            <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
              {isLoading ? (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">加载中...</td></tr>
              ) : orders.length > 0 ? (
                orders.map(order => (
                  <tr key={order.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                    <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{order.id}</td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{order.title}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getPriorityColor(order.priority) === 'text-red-600' ? 'bg-red-100 text-red-600' : getPriorityColor(order.priority) === 'text-yellow-600' ? 'bg-yellow-100 text-yellow-600' : 'bg-green-100 text-green-600'}`}>
                        {order.priority === 'high' ? '高' : order.priority === 'medium' ? '中' : '低'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{order.source}</td>
                    <td className="px-4 py-3">
                      <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(order.status) === 'text-blue-600' ? 'bg-blue-100 text-blue-600' : getStatusColor(order.status) === 'text-yellow-600' ? 'bg-yellow-100 text-yellow-600' : getStatusColor(order.status) === 'text-purple-600' ? 'bg-purple-100 text-purple-600' : 'bg-green-100 text-green-600'}`}>
                        {getStatusText(order.status)}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{new Date(order.createdAt).toLocaleString()}</td>
                    <td className="px-4 py-3">
                      <button className="text-blue-600 hover:underline text-sm">查看详情</button>
                    </td>
                  </tr>
                ))
              ) : (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-500">暂无工单</td></tr>
              )}
            </tbody>
          </table>
        </div>
        
        {/* 搜索和时间轴 */}
        <div className="mt-6 space-y-4">
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="搜索指令编号、智能体名称、时间范围"
              className="flex-1 px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
            />
            <button className="px-3 py-2 bg-gray-600 text-white rounded-lg hover:bg-gray-700">
              搜索
            </button>
          </div>
          
          <div>
            <h3 className="text-md font-medium mb-2">历史任务时间轴</h3>
            <div className="h-24 bg-gray-50 dark:bg-gray-700 rounded-lg p-4 flex items-center justify-between">
              <div className="w-full flex items-center gap-1">
                {Array.from({ length: 12 }, (_, i) => (
                  <div key={i} className="flex-1 h-12 border-r border-gray-200 dark:border-gray-600 flex flex-col items-center justify-center">
                    <div className="text-xs text-gray-500">{i + 1}月</div>
                    <div className="mt-1 w-2 h-2 rounded-full bg-green-500"></div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* 创建紧急工单弹窗 */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold mb-4">创建紧急运维工单</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">标题</label>
                <input
                  type="text"
                  value={newOrder.title}
                  onChange={e => setNewOrder({ ...newOrder, title: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  placeholder="工单标题"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">描述</label>
                <textarea
                  value={newOrder.description}
                  onChange={e => setNewOrder({ ...newOrder, description: e.target.value })}
                  className="w-full px-3 py-2 border rounded-lg dark:bg-gray-700 dark:border-gray-600"
                  rows={4}
                  placeholder="详细描述问题"
                />
              </div>
            </div>
            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => setShowCreateModal(false)}
                className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-lg"
              >
                取消
              </button>
              <button
                onClick={handleCreateEmergencyOrder}
                disabled={isLoading || !newOrder.title || !newOrder.description}
                className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
              >
                {isLoading ? '创建中...' : '创建工单'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

const SystemAdvancedFunctionsTab: React.FC = () => {
  const [multiDimensionAnalysis, setMultiDimensionAnalysis] = useState<MultiDimensionAnalysisResult | null>(null);
  const [predictiveMaintenanceDecision, setPredictiveMaintenanceDecision] = useState<PredictiveMaintenanceDecision | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleFetchMultiDimensionAnalysis = async () => {
    setIsLoading(true);
    try {
      const data = await performMultiDimensionAnalysis({ analysisScenario: 'default', dimensions: ['agentLoad', 'taskAccumulation', 'memoryAccessFrequency', 'systemResourceConsumption'] });
      setMultiDimensionAnalysis(data);
    } catch (error) {
      console.error('Failed to fetch multi-dimension analysis:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleFetchPredictiveMaintenanceDecision = async () => {
    setIsLoading(true);
    try {
      const data = await getPredictiveMaintenanceDecision();
      setPredictiveMaintenanceDecision(data);
    } catch (error) {
      console.error('Failed to fetch predictive maintenance decision:', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    handleFetchMultiDimensionAnalysis();
    handleFetchPredictiveMaintenanceDecision();
  }, []);

  return (
    <div className="space-y-6">
      {/* 多维度数据融合分析 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">多维度数据融合分析</h2>
        
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        ) : multiDimensionAnalysis ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">智能体负载</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{multiDimensionAnalysis.dimensions.agentLoad}%</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">任务积压</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{multiDimensionAnalysis.dimensions.taskAccumulation}%</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">记忆调用频次</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{multiDimensionAnalysis.dimensions.memoryAccessFrequency}%</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
                <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">系统资源消耗</div>
                <div className="text-2xl font-bold text-gray-900 dark:text-white">{multiDimensionAnalysis.dimensions.systemResourceConsumption}%</div>
              </div>
            </div>
            
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <div className="flex justify-between items-center mb-2">
                <h3 className="font-medium">综合健康度评分</h3>
                <div className="text-2xl font-bold text-blue-600">{multiDimensionAnalysis.healthScore}</div>
              </div>
              <div className="w-full h-4 bg-gray-200 dark:bg-gray-600 rounded-full overflow-hidden">
                <div 
                  className={`h-full transition-all ${multiDimensionAnalysis.healthScore >= 80 ? 'bg-green-500' : multiDimensionAnalysis.healthScore >= 60 ? 'bg-yellow-500' : 'bg-red-500'}`}
                  style={{ width: `${multiDimensionAnalysis.healthScore}%` }}
                />
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">数据关联分析</h3>
              <div className="border rounded-lg overflow-hidden">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  <thead className="bg-gray-50 dark:bg-gray-800">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">维度1</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">维度2</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">相关系数</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white dark:bg-gray-900 divide-y divide-gray-200 dark:divide-gray-700">
                    {multiDimensionAnalysis.correlations.map((correlation, index) => (
                      <tr key={index} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{correlation.dimension1}</td>
                        <td className="px-4 py-3 text-sm text-gray-900 dark:text-white">{correlation.dimension2}</td>
                        <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">{correlation.correlation.toFixed(2)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            
            <div className="flex gap-2">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
                定制分析场景
              </button>
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                生成分析报告
              </button>
            </div>
          </div>
        ) : (
          <div className="py-8 text-center text-gray-500">
            暂无分析数据
          </div>
        )}
      </div>

      {/* 预测性维护决策支持 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">预测性维护决策支持</h2>
        
        {isLoading ? (
          <div className="animate-pulse space-y-4">
            <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded"></div>
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
          </div>
        ) : predictiveMaintenanceDecision ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">推荐扩容时间</h3>
                <div className="text-lg font-bold text-gray-900 dark:text-white">{predictiveMaintenanceDecision.recommendedScalingTime}</div>
              </div>
              <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
                <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">资源调度策略</h3>
                <div className="text-sm text-gray-900 dark:text-white">{predictiveMaintenanceDecision.resourceSchedulingStrategy}</div>
              </div>
            </div>
            
            <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4">
              <h3 className="font-medium mb-2">预期收益</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">响应时间缩短比例</div>
                  <div className="text-lg font-bold text-green-600">{predictiveMaintenanceDecision.expectedBenefits.responseTimeReduction}%</div>
                </div>
                <div>
                  <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">资源成本增加估算</div>
                  <div className="text-lg font-bold text-orange-600">{predictiveMaintenanceDecision.expectedBenefits.resourceCostIncrease}%</div>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">潜在风险</h3>
              <ul className="list-disc pl-5 space-y-1 text-sm text-gray-600 dark:text-gray-300">
                {predictiveMaintenanceDecision.risks.map((risk, index) => (
                  <li key={index}>{risk}</li>
                ))}
              </ul>
            </div>
            
            <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700">
              生成决策报告
            </button>
          </div>
        ) : (
          <div className="py-8 text-center text-gray-500">
            暂无决策数据
          </div>
        )}
      </div>

      {/* 系统性能与可靠性保障 */}
      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h2 className="text-lg font-semibold mb-4">系统性能与可靠性保障</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">服务可用性</div>
            <div className="text-2xl font-bold text-green-600">99.9%</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">任务调度延迟</div>
            <div className="text-2xl font-bold text-blue-600">毫秒级</div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-700 rounded-lg p-4 text-center">
            <div className="text-sm text-gray-500 dark:text-gray-400 mb-1">配置历史版本</div>
            <div className="text-2xl font-bold text-purple-600">20个</div>
          </div>
        </div>
        
        <div className="mt-4 space-y-2">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">故障自动迁移（备用网关秒级接管）</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">数据冗余备份机制</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">全链路审计日志</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">分布式架构支持高并发</span>
          </div>
        </div>
      </div>
    </div>
  );
};

const DataCollectionPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'tasks' | 'datasource' | 'heterogeneous' | 'admin' | 'gdp' | 'national' | 'price' | 'load-pressure' | 'agent-load-prediction' | 'alert-management' | 'work-order' | 'system-advanced'>('tasks');

  const totalGDP2024 = PROVINCE_DATA.reduce((sum, p) => sum + (p.gdp['2024'] || 0), 0);
  const totalPrefecture = PROVINCE_DATA.reduce((sum, p) => sum + p.prefecture_count, 0);
  const totalCounty = PROVINCE_DATA.reduce((sum, p) => sum + p.county_count, 0);
  const risingCities = CITY_PRICE_DATA.filter(c => c.newHouse.yoy > 100);
  const fallingCities = CITY_PRICE_DATA.filter(c => c.newHouse.yoy < 100);

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">全国数据监控中心</h1>
      </div>

      <div className="grid grid-cols-5 gap-4">
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-blue-600">{PROVINCE_DATA.length}</div>
          <div className="text-gray-500 dark:text-gray-400">省级行政区</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-green-600">{totalPrefecture}</div>
          <div className="text-gray-500 dark:text-gray-400">地级区划总数</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-purple-600">{totalCounty}</div>
          <div className="text-gray-500 dark:text-gray-400">县级区划总数</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-orange-600">{CITY_PRICE_DATA.length}</div>
          <div className="text-gray-500 dark:text-gray-400">房价监测城市</div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-lg p-4 shadow">
          <div className="text-3xl font-bold text-cyan-600">30</div>
          <div className="text-gray-500 dark:text-gray-400">数据采集城市</div>
        </div>
      </div>

      <div className="flex gap-2 border-b dark:border-gray-700 overflow-x-auto">
        <button
          onClick={() => setActiveTab('tasks')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'tasks' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          ⚡ 任务监控
        </button>
        <button
          onClick={() => setActiveTab('datasource')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'datasource' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          📡 数据源管理
        </button>
        <button
          onClick={() => setActiveTab('heterogeneous')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'heterogeneous' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          🔄 异构数据接入与质量诊断
        </button>
        <button
          onClick={() => setActiveTab('load-pressure')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'load-pressure' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          ⚖️ 负载压力分析
        </button>
        <button
          onClick={() => setActiveTab('agent-load-prediction')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'agent-load-prediction' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          📈 智能体任务负载预测
        </button>
        <button
          onClick={() => setActiveTab('alert-management')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'alert-management' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          ⚠️ 预警管理
        </button>
        <button
          onClick={() => setActiveTab('work-order')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'work-order' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          📋 任务工单流管理
        </button>
        <button
          onClick={() => setActiveTab('system-advanced')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'system-advanced' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          🚀 系统高级功能
        </button>
        <button
          onClick={() => setActiveTab('admin')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'admin' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          📊 行政区划树状图
        </button>
        <button
          onClick={() => setActiveTab('gdp')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'gdp' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          💰 GDP数据树状图
        </button>
        <button
          onClick={() => setActiveTab('national')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'national' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          📈 全国统计趋势
        </button>
        <button
          onClick={() => setActiveTab('price')}
          className={`px-4 py-2 font-medium whitespace-nowrap ${activeTab === 'price' ? 'text-blue-600 border-b-2 border-blue-600' : 'text-gray-500'}`}
        >
          🏠 70城房价指数
        </button>
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4 max-h-[600px] overflow-y-auto">
        {activeTab === 'tasks' && <TaskMonitorTab />}
        {activeTab === 'datasource' && <DataSourceTab />}
        {activeTab === 'heterogeneous' && <HeterogeneousDataTab />}
        {activeTab === 'load-pressure' && <LoadPressureAnalysisTab />}
        {activeTab === 'agent-load-prediction' && <AgentLoadPredictionTab />}
        {activeTab === 'alert-management' && <AlertManagementTab />}
        {activeTab === 'work-order' && <WorkOrderManagementTab />}
        {activeTab === 'system-advanced' && <SystemAdvancedFunctionsTab />}
        
        {activeTab === 'admin' && (
          <div className="space-y-2">
            <TreeNode label="全国行政区划" value={`${PROVINCE_DATA.length}个省级行政区`} defaultOpen color="blue">
              <TreeNode label="直辖市" value="4个" color="red">
                {PROVINCE_DATA.filter(p => p.prefecture_count === 0 && p.county_count <= 20).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.county_count}个区`} color="gray">
                    <TreeNode label="市辖区" value={province.district} />
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="省" value="27个" color="green">
                {PROVINCE_DATA.filter(p => p.name.includes('省')).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.prefecture_count}地级 ${province.county_count}县级`} color="gray">
                    <TreeNode label="地级市" value={province.prefecture_city} />
                    <TreeNode label="市辖区" value={province.district} />
                    <TreeNode label="县级市" value={province.county_city} />
                    <TreeNode label="县" value={province.county} />
                    {province.autonomous_county > 0 && <TreeNode label="自治县" value={province.autonomous_county} />}
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="自治区" value="5个" color="purple">
                {PROVINCE_DATA.filter(p => p.name.includes('自治区')).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.prefecture_count}地级 ${province.county_count}县级`} color="gray">
                    <TreeNode label="地级市" value={province.prefecture_city} />
                    <TreeNode label="市辖区" value={province.district} />
                    <TreeNode label="县级市" value={province.county_city} />
                    <TreeNode label="县" value={province.county} />
                    {province.autonomous_county > 0 && <TreeNode label="自治县" value={province.autonomous_county} />}
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="特别行政区" value="2个" color="orange">
                <TreeNode label="香港特别行政区" />
                <TreeNode label="澳门特别行政区" />
              </TreeNode>
            </TreeNode>
          </div>
        )}

        {activeTab === 'gdp' && (
          <div className="space-y-2">
            <TreeNode label="全国GDP（2024年）" value={`${totalGDP2024.toFixed(1)}亿元`} defaultOpen color="blue">
              <TreeNode label="GDP超5万亿省份" value={`${PROVINCE_DATA.filter(p => p.gdp['2024'] > 50000).length}个`} color="green">
                {PROVINCE_DATA.filter(p => p.gdp['2024'] > 50000).sort((a, b) => b.gdp['2024'] - a.gdp['2024']).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.gdp['2024']}亿`} color="gray">
                    {Object.entries(province.gdp).sort((a, b) => parseInt(b[0]) - parseInt(a[0])).map(([year, gdp]) => (
                      <TreeNode key={year} label={`${year}年`} value={`${gdp}亿`} />
                    ))}
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="GDP 2-5万亿省份" value={`${PROVINCE_DATA.filter(p => p.gdp['2024'] >= 20000 && p.gdp['2024'] <= 50000).length}个`} color="yellow">
                {PROVINCE_DATA.filter(p => p.gdp['2024'] >= 20000 && p.gdp['2024'] <= 50000).sort((a, b) => b.gdp['2024'] - a.gdp['2024']).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.gdp['2024']}亿`} color="gray">
                    {Object.entries(province.gdp).sort((a, b) => parseInt(b[0]) - parseInt(a[0])).map(([year, gdp]) => (
                      <TreeNode key={year} label={`${year}年`} value={`${gdp}亿`} />
                    ))}
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="GDP 1-2万亿省份" value={`${PROVINCE_DATA.filter(p => p.gdp['2024'] >= 10000 && p.gdp['2024'] < 20000).length}个`} color="orange">
                {PROVINCE_DATA.filter(p => p.gdp['2024'] >= 10000 && p.gdp['2024'] < 20000).sort((a, b) => b.gdp['2024'] - a.gdp['2024']).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.gdp['2024']}亿`} color="gray">
                    {Object.entries(province.gdp).sort((a, b) => parseInt(b[0]) - parseInt(a[0])).map(([year, gdp]) => (
                      <TreeNode key={year} label={`${year}年`} value={`${gdp}亿`} />
                    ))}
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="GDP 1万亿以下省份" value={`${PROVINCE_DATA.filter(p => p.gdp['2024'] < 10000).length}个`} color="red">
                {PROVINCE_DATA.filter(p => p.gdp['2024'] < 10000).sort((a, b) => b.gdp['2024'] - a.gdp['2024']).map(province => (
                  <TreeNode key={province.name} label={province.name} value={`${province.gdp['2024']}亿`} color="gray">
                    {Object.entries(province.gdp).sort((a, b) => parseInt(b[0]) - parseInt(a[0])).map(([year, gdp]) => (
                      <TreeNode key={year} label={`${year}年`} value={`${gdp}亿`} />
                    ))}
                  </TreeNode>
                ))}
              </TreeNode>
            </TreeNode>
          </div>
        )}

        {activeTab === 'national' && (
          <div className="space-y-2">
            <TreeNode label="全国行政区划统计（2020-2024）" defaultOpen color="blue">
              {NATIONAL_STATS.map(stat => (
                <TreeNode key={stat.year} label={`${stat.year}年`} color="green">
                  <TreeNode label="地级区划数" value={stat.prefecture_count} />
                  <TreeNode label="地级市数" value={stat.prefecture_city} />
                  <TreeNode label="县级区划数" value={stat.county_count} />
                  <TreeNode label="市辖区数" value={stat.district} />
                  <TreeNode label="县级市数" value={stat.county_city} />
                  <TreeNode label="县数" value={stat.county} />
                  <TreeNode label="自治县数" value={stat.autonomous_county} />
                </TreeNode>
              ))}
            </TreeNode>
          </div>
        )}

        {activeTab === 'price' && (
          <div className="space-y-2">
            <TreeNode label="70城新建商品住宅价格指数（2026年1月）" defaultOpen color="blue">
              <TreeNode label="同比上涨城市" value={`${risingCities.length}个`} color="red">
                {risingCities.sort((a, b) => b.newHouse.yoy - a.newHouse.yoy).map(city => (
                  <TreeNode key={city.name} label={city.name} color="gray">
                    <TreeNode label="环比" value={<PriceChangeBadge value={city.newHouse.mom} />} />
                    <TreeNode label="同比" value={<PriceChangeBadge value={city.newHouse.yoy} />} />
                  </TreeNode>
                ))}
              </TreeNode>
              <TreeNode label="同比下跌城市" value={`${fallingCities.length}个`} color="green">
                {fallingCities.sort((a, b) => a.newHouse.yoy - b.newHouse.yoy).map(city => (
                  <TreeNode key={city.name} label={city.name} color="gray">
                    <TreeNode label="环比" value={<PriceChangeBadge value={city.newHouse.mom} />} />
                    <TreeNode label="同比" value={<PriceChangeBadge value={city.newHouse.yoy} />} />
                  </TreeNode>
                ))}
              </TreeNode>
            </TreeNode>
          </div>
        )}
      </div>

      <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-4">
        <h3 className="text-lg font-semibold mb-4 text-gray-900 dark:text-white">📊 数据来源</h3>
        <div className="text-sm text-gray-600 dark:text-gray-400 space-y-1">
          <p>• 任务监控：实时监控数据采集任务进度，支持创建、取消、重试操作</p>
          <p>• 数据源管理：管理采集任务的数据源，支持启动/暂停采集、配置参数、查看数据</p>
          <p>• 异构数据接入：支持接入多种品牌的数据源，包括房产交易平台、政府公开数据、第三方估价机构数据等</p>
          <p>• 数据质量诊断：实时监测数据完整性、时效性与准确性，自动识别并提示数据质量问题</p>
          <p>• 负载压力分析：分析任务积压对系统资源与调度效率的压力影响</p>
          <p>• 智能体任务负载预测：基于机器学习模型预测未来任务负载变化趋势</p>
          <p>• 预警管理：自动识别智能体执行偏离、数据质量异常或系统健康问题</p>
          <p>• 任务工单流管理：将预警信息转化为可操作、可跟踪的运维动作</p>
          <p>• 系统高级功能：多维度数据融合分析、预测性维护决策支持、系统性能与可靠性保障</p>
          <p>• 行政区划数据来源：国家统计局《中国统计年鉴》</p>
          <p>• GDP数据来源：各省统计局年度公报（2020-2024年）</p>
          <p>• 房价指数来源：国家统计局《2026年1月70个大中城市住宅销售价格指数》</p>
        </div>
      </div>
    </div>
  );
};

export default DataCollectionPage;
