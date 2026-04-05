import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

interface Task {
  id: string;
  city_name: string;
  province_name: string;
  task_type: string;
  status: string;
  progress: number;
  total_items: number;
  processed_items: number;
  message: string;
  error_message: string;
  started_at: string;
  completed_at: string;
  created_at: string;
}

interface Dashboard {
  total_tasks: number;
  pending_tasks: number;
  processing_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  cities: CityProgress[];
}

interface CityProgress {
  city_name: string;
  province_name: string;
  community_progress: number;
  community_status: string;
  price_progress: number;
  price_status: string;
  poi_progress: number;
  poi_status: string;
}

const fetchDashboard = async (): Promise<Dashboard> => {
  const res = await fetch('/api/admin/data-collection/dashboard', {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  });
  if (!res.ok) throw new Error('Failed to fetch dashboard');
  return res.json();
};

const fetchTasks = async (city?: string, status?: string): Promise<Task[]> => {
  const params = new URLSearchParams();
  if (city) params.append('city', city);
  if (status) params.append('status', status);
  
  const res = await fetch(`/api/admin/data-collection/tasks?${params}`, {
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  });
  if (!res.ok) throw new Error('Failed to fetch tasks');
  return res.json();
};

const createTask = async (data: { city_name: string; task_type: string }): Promise<Task> => {
  const res = await fetch('/api/admin/data-collection/tasks', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${localStorage.getItem('token')}`
    },
    body: JSON.stringify(data)
  });
  if (!res.ok) throw new Error('Failed to create task');
  return res.json();
};

const cancelTask = async (taskId: string): Promise<void> => {
  const res = await fetch(`/api/admin/data-collection/tasks/${taskId}/cancel`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  });
  if (!res.ok) throw new Error('Failed to cancel task');
};

const retryTask = async (taskId: string): Promise<{ new_task_id: string }> => {
  const res = await fetch(`/api/admin/data-collection/tasks/${taskId}/retry`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
  });
  if (!res.ok) throw new Error('Failed to retry task');
  return res.json();
};

const ProgressBar: React.FC<{ progress: number; status: string }> = ({ progress, status }) => {
  const getColor = () => {
    switch (status) {
      case 'completed': return 'bg-green-500';
      case 'processing': return 'bg-blue-500';
      case 'failed': return 'bg-red-500';
      case 'cancelled': return 'bg-gray-500';
      default: return 'bg-yellow-500';
    }
  };

  return (
    <div className="w-full bg-gray-200 rounded-full h-2.5">
      <div
        className={`${getColor()} h-2.5 rounded-full transition-all duration-300`}
        style={{ width: `${Math.min(progress, 100)}%` }}
      />
    </div>
  );
};

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const getStyle = () => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800';
      case 'processing': return 'bg-blue-100 text-blue-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'cancelled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-yellow-100 text-yellow-800';
    }
  };

  const labels: Record<string, string> = {
    pending: '待处理',
    processing: '进行中',
    completed: '已完成',
    failed: '失败',
    cancelled: '已取消'
  };

  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStyle()}`}>
      {labels[status] || status}
    </span>
  );
};

const CreateTaskModal: React.FC<{ onClose: () => void; onSuccess: () => void }> = ({ onClose, onSuccess }) => {
  const [cityName, setCityName] = useState('');
  const [taskType, setTaskType] = useState('community');
  const mutation = useMutation({ mutationFn: createTask });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await mutation.mutateAsync({ city_name: cityName, task_type: taskType });
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-md">
        <h3 className="text-lg font-semibold mb-4">新建数据采集任务</h3>
        
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">城市名称</label>
            <input
              type="text"
              value={cityName}
              onChange={(e) => setCityName(e.target.value)}
              className="w-full border rounded-md px-3 py-2"
              placeholder="如：深圳"
              required
            />
          </div>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">任务类型</label>
            <select
              value={taskType}
              onChange={(e) => setTaskType(e.target.value)}
              className="w-full border rounded-md px-3 py-2"
            >
              <option value="community">小区数据采集</option>
              <option value="poi">POI数据采集</option>
              <option value="price">价格数据采集</option>
            </select>
          </div>
          
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:bg-gray-100 rounded-md"
            >
              取消
            </button>
            <button
              type="submit"
              disabled={mutation.isPending}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
            >
              {mutation.isPending ? '创建中...' : '创建任务'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

const CityProgressTable: React.FC<{ cities: CityProgress[]; onCityClick: (city: string) => void }> = ({ cities, onCityClick }) => {
  return (
    <div className="overflow-x-auto">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">城市</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">小区采集</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">价格采集</th>
            <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">POI采集</th>
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {cities.map((city) => (
            <tr
              key={city.city_name}
              className="hover:bg-gray-50 cursor-pointer"
              onClick={() => onCityClick(city.city_name)}
            >
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="text-sm font-medium text-gray-900">{city.city_name}</div>
                <div className="text-sm text-gray-500">{city.province_name}</div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <div className="w-24">
                    <ProgressBar progress={city.community_progress} status={city.community_status || 'pending'} />
                  </div>
                  <span className="text-sm text-gray-500">{city.community_progress}%</span>
                  {city.community_status && <StatusBadge status={city.community_status} />}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <div className="w-24">
                    <ProgressBar progress={city.price_progress} status={city.price_status || 'pending'} />
                  </div>
                  <span className="text-sm text-gray-500">{city.price_progress}%</span>
                  {city.price_status && <StatusBadge status={city.price_status} />}
                </div>
              </td>
              <td className="px-6 py-4 whitespace-nowrap">
                <div className="flex items-center gap-2">
                  <div className="w-24">
                    <ProgressBar progress={city.poi_progress} status={city.poi_status || 'pending'} />
                  </div>
                  <span className="text-sm text-gray-500">{city.poi_progress}%</span>
                  {city.poi_status && <StatusBadge status={city.poi_status} />}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

const TaskList: React.FC<{ tasks: Task[]; onCancel: (id: string) => void; onRetry: (id: string) => void }> = ({ tasks, onCancel, onRetry }) => {
  const taskTypeLabels: Record<string, string> = {
    community: '小区采集',
    poi: 'POI采集',
    price: '价格采集'
  };

  return (
    <div className="space-y-3">
      {tasks.map((task) => (
        <div key={task.id} className="border rounded-lg p-4">
          <div className="flex justify-between items-start mb-2">
            <div>
              <span className="font-medium">{task.city_name}</span>
              <span className="text-gray-500 ml-2">({taskTypeLabels[task.task_type] || task.task_type})</span>
              <StatusBadge status={task.status} />
            </div>
            <div className="flex gap-2">
              {task.status === 'processing' && (
                <button
                  onClick={() => onCancel(task.id)}
                  className="px-3 py-1 text-sm text-red-600 hover:bg-red-50 rounded"
                >
                  取消
                </button>
              )}
              {task.status === 'failed' && (
                <button
                  onClick={() => onRetry(task.id)}
                  className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded"
                >
                  重试
                </button>
              )}
            </div>
          </div>
          
          <div className="mb-2">
            <ProgressBar progress={task.progress} status={task.status} />
          </div>
          
          <div className="flex justify-between text-sm text-gray-500">
            <span>{task.message || '等待执行...'}</span>
            <span>{task.processed_items}/{task.total_items || '?'}</span>
          </div>
          
          {task.error_message && (
            <div className="mt-2 text-sm text-red-600 bg-red-50 p-2 rounded">
              {task.error_message}
            </div>
          )}
        </div>
      ))}
    </div>
  );
};

export const DataCollectionPage: React.FC = () => {
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedCity, setSelectedCity] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const { data: dashboard, isLoading: dashboardLoading } = useQuery({
    queryKey: ['data-collection-dashboard'],
    queryFn: fetchDashboard,
    refetchInterval: 5000
  });

  const { data: tasks, isLoading: tasksLoading } = useQuery({
    queryKey: ['data-collection-tasks', selectedCity],
    queryFn: () => fetchTasks(selectedCity || undefined),
    enabled: !!selectedCity
  });

  const cancelMutation = useMutation({
    mutationFn: cancelTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['data-collection'] })
  });

  const retryMutation = useMutation({
    mutationFn: retryTask,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['data-collection'] })
  });

  return (
      <div className="p-6">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold">数据采集监控</h1>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            + 新建任务
          </button>
        </div>

        {dashboardLoading ? (
          <div className="text-center py-10">加载中...</div>
        ) : (
          <>
            <div className="grid grid-cols-5 gap-4 mb-6">
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-2xl font-bold">{dashboard?.total_tasks || 0}</div>
                <div className="text-gray-500 text-sm">总任务数</div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-2xl font-bold text-yellow-500">{dashboard?.pending_tasks || 0}</div>
                <div className="text-gray-500 text-sm">待处理</div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-2xl font-bold text-blue-500">{dashboard?.processing_tasks || 0}</div>
                <div className="text-gray-500 text-sm">进行中</div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-2xl font-bold text-green-500">{dashboard?.completed_tasks || 0}</div>
                <div className="text-gray-500 text-sm">已完成</div>
              </div>
              <div className="bg-white rounded-lg p-4 shadow">
                <div className="text-2xl font-bold text-red-500">{dashboard?.failed_tasks || 0}</div>
                <div className="text-gray-500 text-sm">失败</div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow">
              <div className="p-4 border-b">
                <h2 className="text-lg font-semibold">城市采集进度</h2>
              </div>
              <CityProgressTable
                cities={dashboard?.cities || []}
                onCityClick={(city) => setSelectedCity(city)}
              />
            </div>

            {selectedCity && (
              <div className="mt-6 bg-white rounded-lg shadow">
                <div className="p-4 border-b flex justify-between items-center">
                  <h2 className="text-lg font-semibold">{selectedCity} 任务详情</h2>
                  <button
                    onClick={() => setSelectedCity(null)}
                    className="text-gray-500 hover:text-gray-700"
                  >
                    关闭
                  </button>
                </div>
                <div className="p-4">
                  {tasksLoading ? (
                    <div className="text-center py-4">加载中...</div>
                  ) : (
                    <TaskList
                      tasks={tasks || []}
                      onCancel={(id) => cancelMutation.mutate(id)}
                      onRetry={(id) => retryMutation.mutate(id)}
                    />
                  )}
                </div>
              </div>
            )}
          </>
        )}

        {showCreateModal && (
          <CreateTaskModal
            onClose={() => setShowCreateModal(false)}
            onSuccess={() => queryClient.invalidateQueries({ queryKey: ['data-collection'] })}
          />
        )}
      </div>
  );
};

export default DataCollectionPage;
