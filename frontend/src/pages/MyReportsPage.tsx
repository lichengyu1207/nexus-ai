import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';

interface Task {
  id: string;
  query: string;
  status: string;
  result: any;
  created_at: string;
  updated_at: string;
}

const MyReportsPage: React.FC = () => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');

  useEffect(() => {
    fetchTasks();
  }, [page, statusFilter]);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams({
        page: page.toString(),
        page_size: '10',
      });
      if (statusFilter) params.append('status', statusFilter);

      const response = await fetch(`http://localhost:8000/api/user/tasks?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
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

  const getStatusColor = (status: string): string => {
    const colors: Record<string, string> = {
      completed: 'bg-green-100 text-green-700',
      processing: 'bg-blue-100 text-blue-700',
      pending: 'bg-yellow-100 text-yellow-700',
      failed: 'bg-red-100 text-red-700',
    };
    return colors[status] || 'bg-gray-100 text-gray-700';
  };

  const getStatusName = (status: string): string => {
    const names: Record<string, string> = {
      completed: '已完成',
      processing: '处理中',
      pending: '等待中',
      failed: '失败',
    };
    return names[status] || status;
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">我的报告</h1>
        <Link
          to="/property-analysis"
          className="bg-primary text-white px-4 py-2 rounded-md hover:bg-primaryDark"
        >
          新建分析
        </Link>
      </div>

      <div className="mb-4">
        <select
          value={statusFilter}
          onChange={(e) => {
            setStatusFilter(e.target.value);
            setPage(1);
          }}
          className="border border-gray-300 rounded px-3 py-2"
        >
          <option value="">全部状态</option>
          <option value="completed">已完成</option>
          <option value="processing">处理中</option>
          <option value="pending">等待中</option>
          <option value="failed">失败</option>
        </select>
      </div>

      {loading ? (
        <div className="flex justify-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      ) : tasks.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500 mb-4">暂无报告记录</p>
          <Link
            to="/property-analysis"
            className="text-primary hover:underline"
          >
            开始第一次分析
          </Link>
        </div>
      ) : (
        <>
          <div className="space-y-4">
            {tasks.map((task) => (
              <div key={task.id} className="bg-white rounded-lg shadow p-4">
                <div className="flex justify-between items-start">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-medium text-lg truncate">
                      {task.query || '房产分析任务'}
                    </h3>
                    <div className="flex items-center gap-4 mt-2 text-sm text-gray-500">
                      <span>创建: {new Date(task.created_at).toLocaleString('zh-CN')}</span>
                      <span className={`px-2 py-0.5 rounded ${getStatusColor(task.status)}`}>
                        {getStatusName(task.status)}
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    {task.status === 'completed' && (
                      <Link
                        to={`/virtual-office/${task.id}`}
                        className="text-primary hover:underline text-sm"
                      >
                        查看详情
                      </Link>
                    )}
                    {task.status === 'processing' && (
                      <Link
                        to={`/virtual-office/${task.id}`}
                        className="text-blue-600 hover:underline text-sm"
                      >
                        查看进度
                      </Link>
                    )}
                    {task.status === 'failed' && (
                      <span className="text-red-600 text-sm">分析失败</span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {total > 10 && (
            <div className="flex justify-center mt-6 gap-2">
              <button
                onClick={() => setPage(Math.max(1, page - 1))}
                disabled={page === 1}
                className="px-4 py-2 border rounded disabled:opacity-50"
              >
                上一页
              </button>
              <span className="px-4 py-2">
                第 {page} / {Math.ceil(total / 10)} 页
              </span>
              <button
                onClick={() => setPage(page + 1)}
                disabled={page >= Math.ceil(total / 10)}
                className="px-4 py-2 border rounded disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MyReportsPage;
