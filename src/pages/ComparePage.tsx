import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { taskApi, Task } from '@/services/api';
import Mascot from '@/components/mascot/Mascot';
import {
  ArrowsRightLeftIcon,
  ChartBarIcon,
  MapPinIcon,
  AcademicCapIcon,
  TruckIcon,
  CurrencyDollarIcon,
  HomeIcon,
  ArrowUpIcon,
  ArrowDownIcon,
  XMarkIcon,
  DocumentArrowDownIcon,
  SparklesIcon,
} from '@heroicons/react/24/outline';

interface CompareMetrics {
  id: string;
  query: string;
  price: number;
  area: number;
  pricePerSqm: number;
  schoolScore: number;
  transportScore: number;
  hospitalScore: number;
  mallScore: number;
  overallScore: number;
  status: string;
}

const ComparePage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [selectedTasks, setSelectedTasks] = useState<Task[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortKey, setSortKey] = useState<keyof CompareMetrics>('overallScore');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');
  
  const navigate = useNavigate();

  useEffect(() => {
    loadCompletedTasks();
  }, []);

  const loadCompletedTasks = async () => {
    setIsLoading(true);
    try {
      const response = await taskApi.list({ limit: 20, status: 'completed' });
      setTasks(response.tasks);
    } catch (error) {
      console.error('Failed to load tasks:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleTaskSelection = (task: Task) => {
    if (selectedTasks.find(t => t.id === task.id)) {
      setSelectedTasks(selectedTasks.filter(t => t.id !== task.id));
    } else if (selectedTasks.length < 5) {
      setSelectedTasks([...selectedTasks, task]);
    }
  };

  const removeFromSelection = (taskId: string) => {
    setSelectedTasks(selectedTasks.filter(t => t.id !== taskId));
  };

  const generateMockMetrics = (task: Task): CompareMetrics => {
    const basePrice = 300 + Math.random() * 700;
    const area = 60 + Math.random() * 100;
    
    return {
      id: task.id,
      query: task.query,
      price: Math.round(basePrice),
      area: Math.round(area),
      pricePerSqm: Math.round((basePrice * 10000) / area),
      schoolScore: Math.round(60 + Math.random() * 40),
      transportScore: Math.round(60 + Math.random() * 40),
      hospitalScore: Math.round(60 + Math.random() * 40),
      mallScore: Math.round(60 + Math.random() * 40),
      overallScore: Math.round(70 + Math.random() * 30),
      status: task.status,
    };
  };

  const compareData = selectedTasks.map(generateMockMetrics);

  const sortedData = [...compareData].sort((a, b) => {
    const aValue = a[sortKey];
    const bValue = b[sortKey];
    if (typeof aValue === 'number' && typeof bValue === 'number') {
      return sortOrder === 'asc' ? aValue - bValue : bValue - aValue;
    }
    return 0;
  });

  const handleSort = (key: keyof CompareMetrics) => {
    if (sortKey === key) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortKey(key);
      setSortOrder('desc');
    }
  };

  const getBestInCategory = (key: keyof CompareMetrics): string | null => {
    if (sortedData.length === 0) return null;
    const isHigherBetter = !['price', 'pricePerSqm'].includes(key);
    const values = sortedData.map(d => d[key] as number);
    const bestValue = isHigherBetter ? Math.max(...values) : Math.min(...values);
    const best = sortedData.find(d => d[key] === bestValue);
    return best?.id || null;
  };

  const generateMascotSuggestion = (): string => {
    if (sortedData.length < 2) return '请选择至少2个房源进行对比';
    
    const bestOverall = sortedData[0];
    const bestPrice = sortedData.reduce((a, b) => a.price < b.price ? a : b);
    const bestSchool = sortedData.reduce((a, b) => a.schoolScore > b.schoolScore ? a : b);
    
    return `${bestOverall.query.slice(0, 10)}...综合评分最高，${bestSchool.query.slice(0, 10)}...学区最好！`;
  };

  const SortIcon = ({ columnKey }: { columnKey: keyof CompareMetrics }) => {
    if (sortKey !== columnKey) return null;
    return sortOrder === 'asc' 
      ? <ArrowUpIcon className="w-4 h-4" />
      : <ArrowDownIcon className="w-4 h-4" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-primary-200 border-t-primary-600 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">房源对比</h1>
          <p className="text-gray-600 mt-1">选择多个已完成的房源分析进行对比</p>
        </div>
        {selectedTasks.length >= 2 && (
          <button
            onClick={() => navigate(`/tasks/${selectedTasks[0].id}`)}
            className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <DocumentArrowDownIcon className="w-5 h-5" />
            导出对比报告
          </button>
        )}
      </div>

      {selectedTasks.length > 0 && (
        <div className="bg-primary-50 rounded-xl p-4">
          <div className="flex items-center gap-2 mb-3">
            <SparklesIcon className="w-5 h-5 text-primary-600" />
            <span className="font-medium text-primary-900">已选择 {selectedTasks.length} 个房源</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {selectedTasks.map(task => (
              <div
                key={task.id}
                className="flex items-center gap-2 bg-white px-3 py-1.5 rounded-full border border-primary-200"
              >
                <span className="text-sm text-gray-700 max-w-[150px] truncate">
                  {task.query}
                </span>
                <button
                  onClick={() => removeFromSelection(task.id)}
                  className="p-0.5 hover:bg-gray-100 rounded-full"
                >
                  <XMarkIcon className="w-4 h-4 text-gray-400" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {selectedTasks.length >= 2 && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">对比分析</h2>
            <div className="flex items-center gap-3">
              <Mascot emotion="thinking" size="sm" />
              <p className="text-sm text-gray-600 max-w-md">
                {generateMascotSuggestion()}
              </p>
            </div>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">
                    房源
                  </th>
                  <th 
                    className="px-4 py-3 text-center text-sm font-medium text-gray-500 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('price')}
                  >
                    <div className="flex items-center justify-center gap-1">
                      <CurrencyDollarIcon className="w-4 h-4" />
                      总价(万)
                      <SortIcon columnKey="price" />
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-center text-sm font-medium text-gray-500 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('area')}
                  >
                    <div className="flex items-center justify-center gap-1">
                      <HomeIcon className="w-4 h-4" />
                      面积(㎡)
                      <SortIcon columnKey="area" />
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-center text-sm font-medium text-gray-500 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('pricePerSqm')}
                  >
                    <div className="flex items-center justify-center gap-1">
                      单价(元/㎡)
                      <SortIcon columnKey="pricePerSqm" />
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-center text-sm font-medium text-gray-500 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('schoolScore')}
                  >
                    <div className="flex items-center justify-center gap-1">
                      <AcademicCapIcon className="w-4 h-4" />
                      学区
                      <SortIcon columnKey="schoolScore" />
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-center text-sm font-medium text-gray-500 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('transportScore')}
                  >
                    <div className="flex items-center justify-center gap-1">
                      <TruckIcon className="w-4 h-4" />
                      交通
                      <SortIcon columnKey="transportScore" />
                    </div>
                  </th>
                  <th 
                    className="px-4 py-3 text-center text-sm font-medium text-gray-500 cursor-pointer hover:bg-gray-100"
                    onClick={() => handleSort('overallScore')}
                  >
                    <div className="flex items-center justify-center gap-1">
                      <ChartBarIcon className="w-4 h-4" />
                      综合评分
                      <SortIcon columnKey="overallScore" />
                    </div>
                  </th>
                  <th className="px-4 py-3 text-center text-sm font-medium text-gray-500">
                    操作
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {sortedData.map((item, index) => {
                  const bestPrice = getBestInCategory('price');
                  const bestSchool = getBestInCategory('schoolScore');
                  const bestOverall = getBestInCategory('overallScore');
                  
                  return (
                    <tr key={item.id} className="hover:bg-gray-50">
                      <td className="px-4 py-4">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center text-primary-600 font-bold">
                            {index + 1}
                          </div>
                          <div className="max-w-[200px]">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {item.query}
                            </p>
                          </div>
                        </div>
                      </td>
                      <td className={`px-4 py-4 text-center ${item.id === bestPrice ? 'text-green-600 font-bold' : ''}`}>
                        {item.price}万
                        {item.id === bestPrice && (
                          <span className="ml-1 text-xs bg-green-100 text-green-700 px-1.5 py-0.5 rounded">最低</span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-center text-gray-900">
                        {item.area}㎡
                      </td>
                      <td className="px-4 py-4 text-center text-gray-900">
                        {item.pricePerSqm}
                      </td>
                      <td className={`px-4 py-4 text-center ${item.id === bestSchool ? 'text-green-600 font-bold' : ''}`}>
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-primary-500 h-2 rounded-full"
                              style={{ width: `${item.schoolScore}%` }}
                            />
                          </div>
                          <span className="text-sm">{item.schoolScore}</span>
                        </div>
                      </td>
                      <td className="px-4 py-4 text-center text-gray-900">
                        <div className="flex items-center justify-center gap-2">
                          <div className="w-16 bg-gray-200 rounded-full h-2">
                            <div 
                              className="bg-blue-500 h-2 rounded-full"
                              style={{ width: `${item.transportScore}%` }}
                            />
                          </div>
                          <span className="text-sm">{item.transportScore}</span>
                        </div>
                      </td>
                      <td className={`px-4 py-4 text-center ${item.id === bestOverall ? 'text-green-600 font-bold' : ''}`}>
                        <span className={`text-lg font-bold ${item.overallScore >= 90 ? 'text-green-600' : item.overallScore >= 80 ? 'text-blue-600' : 'text-gray-900'}`}>
                          {item.overallScore}
                        </span>
                        {item.id === bestOverall && (
                          <span className="ml-1 text-xs bg-yellow-100 text-yellow-700 px-1.5 py-0.5 rounded">最佳</span>
                        )}
                      </td>
                      <td className="px-4 py-4 text-center">
                        <Link
                          to={`/tasks/${item.id}`}
                          className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                        >
                          查看详情
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">选择房源进行对比</h2>
          <p className="text-sm text-gray-500 mt-1">点击房源卡片添加到对比列表（最多5个）</p>
        </div>
        
        {tasks.length === 0 ? (
          <div className="p-8 text-center">
            <Mascot emotion="thinking" size="lg" />
            <p className="text-gray-500 mt-4">暂无可对比的房源分析</p>
            <p className="text-sm text-gray-400 mt-1">请先完成一些房源分析任务</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
            {tasks.map(task => {
              const isSelected = selectedTasks.find(t => t.id === task.id);
              
              return (
                <div
                  key={task.id}
                  onClick={() => toggleTaskSelection(task)}
                  className={`p-4 rounded-xl border-2 cursor-pointer transition-all ${
                    isSelected
                      ? 'border-primary-500 bg-primary-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-gray-900 truncate">{task.query}</p>
                      <p className="text-sm text-gray-500 mt-1">
                        {new Date(task.created_at || '').toLocaleDateString()}
                      </p>
                    </div>
                    {isSelected && (
                      <div className="w-6 h-6 bg-primary-500 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default ComparePage;
