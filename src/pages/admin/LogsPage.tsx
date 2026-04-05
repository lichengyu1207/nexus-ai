import React, { useState, useEffect } from 'react';
import {
  Search, Filter, RefreshCw, Download, Trash2, AlertCircle,
  Info, AlertTriangle, XCircle, Clock, FileText, ChevronDown,
} from 'lucide-react';

interface LogEntry {
  timestamp: string;
  level: string;
  logger: string;
  message: string;
  module?: string;
  function?: string;
  line?: number;
  request_id?: string;
  user_id?: string;
  exception?: string;
}

interface LogStats {
  total: number;
  by_level: Record<string, number>;
  by_logger: Record<string, number>;
  error_rate: number;
}

interface LogFile {
  name: string;
  size: number;
  size_human: string;
  modified: string;
}

const LEVEL_COLORS: Record<string, string> = {
  DEBUG: 'text-gray-500 bg-gray-100',
  INFO: 'text-blue-600 bg-blue-100',
  WARNING: 'text-yellow-600 bg-yellow-100',
  ERROR: 'text-red-600 bg-red-100',
  CRITICAL: 'text-purple-600 bg-purple-100',
};

const LEVEL_ICONS: Record<string, React.ReactNode> = {
  DEBUG: <Info className="w-4 h-4" />,
  INFO: <Info className="w-4 h-4" />,
  WARNING: <AlertTriangle className="w-4 h-4" />,
  ERROR: <AlertCircle className="w-4 h-4" />,
  CRITICAL: <XCircle className="w-4 h-4" />,
};

const LogsPage: React.FC = () => {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [stats, setStats] = useState<LogStats | null>(null);
  const [files, setFiles] = useState<LogFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [query, setQuery] = useState('');
  const [level, setLevel] = useState('');
  const [loggerName, setLoggerName] = useState('');
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState('');
  const [activeTab, setActiveTab] = useState<'logs' | 'files'>('logs');

  useEffect(() => {
    fetchLogs();
    fetchStats();
    fetchFiles();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      if (query) params.append('query', query);
      if (level) params.append('level', level);
      if (loggerName) params.append('logger_name', loggerName);
      params.append('limit', '100');

      const response = await fetch(`/api/admin/logs/search?${params}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch logs');
      const data = await response.json();
      setLogs(data.logs || []);
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/logs/stats', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Failed to fetch stats:', error);
    }
  };

  const fetchFiles = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/admin/logs/files', {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch files');
      const data = await response.json();
      setFiles(data.files || []);
    } catch (error) {
      console.error('Failed to fetch files:', error);
    }
  };

  const fetchFileContent = async (filename: string) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/admin/logs/files/${filename}?lines=200`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (!response.ok) throw new Error('Failed to fetch file content');
      const data = await response.json();
      setFileContent(data.content);
      setSelectedFile(filename);
    } catch (error) {
      console.error('Failed to fetch file content:', error);
    }
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    fetchLogs();
  };

  const formatTimestamp = (ts: string) => {
    try {
      return new Date(ts).toLocaleString();
    } catch {
      return ts;
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">日志管理</h1>
        <button
          onClick={() => {
            fetchLogs();
            fetchStats();
            fetchFiles();
          }}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
        >
          <RefreshCw className="w-4 h-4" />
          刷新
        </button>
      </div>

      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">总日志数 (24h)</p>
            <p className="text-2xl font-bold">{stats.total.toLocaleString()}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">错误率</p>
            <p className={`text-2xl font-bold ${stats.error_rate > 0.05 ? 'text-red-600' : 'text-green-600'}`}>
              {(stats.error_rate * 100).toFixed(2)}%
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">错误数</p>
            <p className="text-2xl font-bold text-red-600">
              {stats.by_level.ERROR || 0}
            </p>
          </div>
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-500">警告数</p>
            <p className="text-2xl font-bold text-yellow-600">
              {stats.by_level.WARNING || 0}
            </p>
          </div>
        </div>
      )}

      <div className="flex gap-4 border-b">
        <button
          onClick={() => setActiveTab('logs')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'logs'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500'
          }`}
        >
          日志搜索
        </button>
        <button
          onClick={() => setActiveTab('files')}
          className={`px-4 py-2 font-medium ${
            activeTab === 'files'
              ? 'text-blue-600 border-b-2 border-blue-600'
              : 'text-gray-500'
          }`}
        >
          日志文件
        </button>
      </div>

      {activeTab === 'logs' && (
        <div className="bg-white rounded-lg shadow">
          <form onSubmit={handleSearch} className="p-4 border-b">
            <div className="flex gap-4">
              <div className="flex-1">
                <input
                  type="text"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="搜索日志内容..."
                  className="w-full px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <select
                value={level}
                onChange={(e) => setLevel(e.target.value)}
                className="px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="">所有级别</option>
                <option value="DEBUG">DEBUG</option>
                <option value="INFO">INFO</option>
                <option value="WARNING">WARNING</option>
                <option value="ERROR">ERROR</option>
                <option value="CRITICAL">CRITICAL</option>
              </select>
              <button
                type="submit"
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                搜索
              </button>
            </div>
          </form>

          <div className="divide-y max-h-[600px] overflow-y-auto">
            {loading ? (
              <div className="p-8 text-center text-gray-500">加载中...</div>
            ) : logs.length === 0 ? (
              <div className="p-8 text-center text-gray-500">暂无日志</div>
            ) : (
              logs.map((log, index) => (
                <div key={index} className="p-4 hover:bg-gray-50">
                  <div className="flex items-start gap-3">
                    <span
                      className={`flex items-center gap-1 px-2 py-1 rounded text-xs font-medium ${
                        LEVEL_COLORS[log.level] || LEVEL_COLORS.INFO
                      }`}
                    >
                      {LEVEL_ICONS[log.level]}
                      {log.level}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 text-sm text-gray-500">
                        <Clock className="w-3 h-3" />
                        {formatTimestamp(log.timestamp)}
                        <span className="text-gray-300">|</span>
                        <span>{log.logger}</span>
                        {log.request_id && (
                          <>
                            <span className="text-gray-300">|</span>
                            <span className="text-xs">req:{log.request_id}</span>
                          </>
                        )}
                      </div>
                      <p className="mt-1 text-gray-900 font-mono text-sm break-all">
                        {log.message}
                      </p>
                      {log.exception && (
                        <pre className="mt-2 p-2 bg-red-50 rounded text-xs text-red-600 overflow-x-auto">
                          {log.exception}
                        </pre>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      )}

      {activeTab === 'files' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="bg-white rounded-lg shadow">
            <div className="p-4 border-b">
              <h3 className="font-semibold">日志文件</h3>
            </div>
            <div className="divide-y">
              {files.map((file) => (
                <div
                  key={file.name}
                  onClick={() => fetchFileContent(file.name)}
                  className={`p-4 hover:bg-gray-50 cursor-pointer ${
                    selectedFile === file.name ? 'bg-blue-50' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    <FileText className="w-5 h-5 text-gray-400" />
                    <span className="font-medium">{file.name}</span>
                  </div>
                  <div className="mt-1 text-sm text-gray-500">
                    {file.size_human} · {new Date(file.modified).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="lg:col-span-2 bg-white rounded-lg shadow">
            <div className="p-4 border-b flex justify-between items-center">
              <h3 className="font-semibold">
                {selectedFile || '选择文件查看内容'}
              </h3>
              {selectedFile && (
                <button
                  onClick={() => navigator.clipboard.writeText(fileContent)}
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  复制内容
                </button>
              )}
            </div>
            <div className="p-4 max-h-[500px] overflow-auto">
              {fileContent ? (
                <pre className="text-xs font-mono text-gray-700 whitespace-pre-wrap">
                  {fileContent}
                </pre>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  选择左侧文件查看内容
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default LogsPage;
