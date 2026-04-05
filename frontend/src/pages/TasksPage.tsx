import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Task {
  id: string;
  query: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress?: number;
  created_at: string;
  updated_at: string;
}

const TasksPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    fetchTasks();
  }, [page, statusFilter]);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');
      if (statusFilter) params.append('status', statusFilter);
      if (searchQuery) params.append('search', searchQuery);

      const response = await fetch(`http://localhost:8000/api/tasks?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });

      if (response.ok) {
        const data = await response.json();
        setTasks(data.tasks || []);
        setTotal(data.total || 0);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchTasks();
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-700',
      processing: 'bg-blue-100 text-blue-700',
      pending: 'bg-yellow-100 text-yellow-700',
      failed: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getStatusName = (status: string) => {
    const names: Record<string, string> = {
      completed: '已完成',
      processing: '分析中',
      pending: '等待中',
      failed: '失败',
    };
    return names[status] || status;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">我的任务</h1>
        <Link
          to="/dashboard/property-analysis"
          className="bg-primary text-white px-4 py-2 rounded-lg hover:bg-primaryDark"
        >
          新建分析
        </Link>
      </div>

      <div className="bg-white rounded-lg shadow mb-6 p-4">
        <form onSubmit={handleSearch} className="flex flex-wrap gap-4">
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="搜索任务..."
            className="flex-1 min-w-[200px] border rounded-lg px-4 py-2"
          />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="border rounded-lg px-4 py-2"
          >
            <option value="">全部状态</option>
            <option value="pending">等待中</option>
            <option value="processing">分析中</option>
            <option value="completed">已完成</option>
            <option value="failed">失败</option>
          </select>
          <button
            type="submit"
            className="bg-primary text-white px-6 py-2 rounded-lg hover:bg-primaryDark"
          >
            搜索
          </button>
        </form>
      </div>

      {loading ? (
        <div className="text-center py-10">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-10 text-center">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-medium mb-2">暂无任务</h3>
          <p className="text-gray-500 mb-4">开始您的第一次房产分析吧！</p>
          <Link
            to="/dashboard/property-analysis"
            className="inline-block bg-primary text-white px-6 py-2 rounded-lg hover:bg-primaryDark"
          >
            开始分析
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {tasks.map((task) => (
            <div key={task.id} className="bg-white rounded-lg shadow p-4 hover:shadow-md transition-shadow">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <span className={`px-2 py-1 text-xs rounded-full ${getStatusColor(task.status)}`}>
                      {getStatusName(task.status)}
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(task.created_at).toLocaleString('zh-CN')}
                    </span>
                  </div>
                  <p className="font-medium text-gray-900">{task.query || '房产分析任务'}</p>
                  
                  {task.status === 'processing' && task.progress !== undefined && (
                    <div className="mt-3">
                      <div className="flex justify-between text-sm text-gray-500 mb-1">
                        <span>分析进度</span>
                        <span>{task.progress}%</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-primary rounded-full h-2 transition-all"
                          style={{ width: `${task.progress}%` }}
                        ></div>
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="ml-4">
                  {task.status === 'completed' && (
                    <Link
                      to={`/virtual-office/${task.id}`}
                      className="bg-primary text-white px-4 py-2 rounded-lg text-sm hover:bg-primaryDark"
                    >
                      查看报告
                    </Link>
                  )}
                  {task.status === 'failed' && (
                    <button
                      onClick={() => {
                        // 重试逻辑
                      }}
                      className="border border-red-500 text-red-500 px-4 py-2 rounded-lg text-sm hover:bg-red-50"
                    >
                      重试
                    </button>
                  )}
                  {task.status === 'processing' && (
                    <Link
                      to={`/virtual-office/${task.id}`}
                      className="border border-primary text-primary px-4 py-2 rounded-lg text-sm hover:bg-primary/10"
                    >
                      查看进度
                    </Link>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {total > 20 && (
        <div className="flex justify-center items-center gap-4 mt-6">
          <button
            onClick={() => setPage(p => Math.max(1, p - 1))}
            disabled={page === 1}
            className="px-4 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-50"
          >
            上一页
          </button>
          <span className="text-gray-500">
            第 {page} 页，共 {total} 条
          </span>
          <button
            onClick={() => setPage(p => p + 1)}
            disabled={tasks.length < 20}
            className="px-4 py-2 border rounded-lg disabled:opacity-50 hover:bg-gray-50"
          >
            下一页
          </button>
        </div>
      )}
    </div>
  );
};

export default TasksPage;
