import React, { useState, useEffect } from 'react';
import './DashboardPage.css';

interface Agent {
  id: string;
  name: string;
  department: string;
  level: number;
  rarity: string;
  rarity_color: string;
  level_cap: number;
  status: string;
  current_task_description: string;
  efficiency: number;
  daily_work_seconds: number;
  total_reward: number;
}

interface Task {
  id: string;
  type: string;
  task_type: string;
  description: string;
  status: string;
  progress: number;
  start_time: string;
  assigned_agents: Array<{ id: string; name: string }>;
}

interface Stats {
  total_agents: number;
  online_agents: number;
  busy_agents: number;
  auto_work_agents: number;
  idle_agents: number;
  total_reward: number;
  today_work_seconds: number;
  pending_tasks: number;
}

interface Log {
  id: string;
  agent_name: string;
  task_type: string;
  duration_seconds: number;
  reward_earned: number;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  idle: '#2ecc71',
  busy: '#f39c12',
  working: '#3498db',
  offline: '#95a5a6',
};

const STATUS_NAMES: Record<string, string> = {
  idle: '空闲',
  busy: '忙碌',
  working: '自主工作',
  offline: '离线',
};

const DashboardPage: React.FC = () => {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [logs, setLogs] = useState<Log[]>([]);
  const [loading, setLoading] = useState(true);
  const [showTaskPanel, setShowTaskPanel] = useState(false);

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 30000);
    return () => clearInterval(interval);
  }, []);

  const fetchAllData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [agentsRes, tasksRes, statsRes, logsRes] = await Promise.all([
        fetch('/api/dashboard/agents-status', { headers }),
        fetch('/api/dashboard/current-tasks', { headers }),
        fetch('/api/dashboard/stats', { headers }),
        fetch('/api/dashboard/logs?limit=10', { headers }),
      ]);

      const agentsData = await agentsRes.json();
      const tasksData = await tasksRes.json();
      const statsData = await statsRes.json();
      const logsData = await logsRes.json();

      if (agentsData.success) setAgents(agentsData.agents);
      if (tasksData.success) setTasks(tasksData.tasks);
      if (statsData.success) setStats(statsData.stats);
      if (logsData.success) setLogs(logsData.logs);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) return `${hours}h ${minutes}m`;
    return `${minutes}m`;
  };

  if (loading) {
    return <div className="dashboard-loading">加载中...</div>;
  }

  return (
    <div className="dashboard-page">
      <div className="dashboard-header">
        <h1>智能体监控中心</h1>
        <button className="new-task-btn" onClick={() => setShowTaskPanel(true)}>
          + 新建任务
        </button>
      </div>

      <div className="stats-row">
        <div className="stat-card">
          <div className="stat-icon">🤖</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.total_agents || 0}</span>
            <span className="stat-label">智能体总数</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🟢</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.online_agents || 0}</span>
            <span className="stat-label">在线</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">🔄</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.busy_agents || 0}</span>
            <span className="stat-label">忙碌</span>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <span className="stat-value">{stats?.total_reward || 0}</span>
            <span className="stat-label">总收益</span>
          </div>
        </div>
      </div>

      <div className="main-content">
        <div className="agents-section">
          <h2>智能体状态</h2>
          <div className="agents-grid">
            {agents.map((agent) => (
              <div key={agent.id} className="agent-card">
                <div className="agent-header">
                  <div className="agent-avatar" style={{ borderColor: agent.rarity_color }}>
                    🤖
                  </div>
                  <div className="agent-info">
                    <h3>{agent.name}</h3>
                    <span className="agent-dept">{agent.department}</span>
                  </div>
                  <div
                    className="status-indicator"
                    style={{ backgroundColor: STATUS_COLORS[agent.status] || '#95a5a6' }}
                    title={STATUS_NAMES[agent.status] || agent.status}
                  />
                </div>
                <div className="agent-body">
                  <div className="agent-level">
                    <span>Lv.{agent.level}/{agent.level_cap}</span>
                    <div className="level-bar">
                      <div
                        className="level-fill"
                        style={{ width: `${(agent.level / agent.level_cap) * 100}%` }}
                      />
                    </div>
                  </div>
                  <p className="current-task">{agent.current_task_description}</p>
                  <div className="agent-stats">
                    <span>效率: {(agent.efficiency * 100).toFixed(0)}%</span>
                    <span>今日: {formatDuration(agent.daily_work_seconds)}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="right-panel">
          <div className="tasks-section">
            <h2>进行中的任务</h2>
            {tasks.length === 0 ? (
              <div className="no-tasks">暂无进行中的任务</div>
            ) : (
              <div className="tasks-list">
                {tasks.map((task) => (
                  <div key={task.id} className="task-card">
                    <div className="task-header">
                      <span className="task-type">{task.task_type}</span>
                      <span className="task-status">{task.status}</span>
                    </div>
                    <p className="task-desc">{task.description}</p>
                    <div className="task-progress">
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${task.progress}%` }} />
                      </div>
                      <span className="progress-text">{task.progress}%</span>
                    </div>
                    <div className="task-agents">
                      {task.assigned_agents.map((a) => (
                        <span key={a.id} className="agent-tag">{a.name}</span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="logs-section">
            <h2>实时日志</h2>
            <div className="logs-list">
              {logs.map((log) => (
                <div key={log.id} className="log-item">
                  <span className="log-time">
                    {new Date(log.created_at).toLocaleTimeString()}
                  </span>
                  <span className="log-agent">{log.agent_name}</span>
                  <span className="log-action">完成 {log.task_type}</span>
                  <span className="log-reward">+{log.reward_earned}积分</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {showTaskPanel && (
        <TaskAssignmentPanel
          onClose={() => setShowTaskPanel(false)}
          onSuccess={() => {
            setShowTaskPanel(false);
            fetchAllData();
          }}
        />
      )}
    </div>
  );
};

const TaskAssignmentPanel: React.FC<{
  onClose: () => void;
  onSuccess: () => void;
}> = ({ onClose, onSuccess }) => {
  const [taskType, setTaskType] = useState('analysis');
  const [input, setInput] = useState('');
  const [options, setOptions] = useState<any[]>([]);
  const [selectedAgents, setSelectedAgents] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchOptions();
  }, [taskType]);

  const fetchOptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`/api/dashboard/task-assignment-options?task_type=${taskType}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.success) {
        setOptions(data.options);
        const available = data.options.filter((o: any) => o.is_available);
        if (available.length > 0) {
          setSelectedAgents([available[0].id]);
        }
      }
    } catch (error) {
      console.error('Failed to fetch options:', error);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch('/api/dashboard/start-task', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          task_type: taskType,
          input,
          agent_ids: selectedAgents,
          auto_assign: selectedAgents.length === 0,
        }),
      });
      const data = await res.json();
      if (data.success) {
        onSuccess();
      } else {
        alert(data.error || '启动失败');
      }
    } catch (error) {
      console.error('Failed to start task:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="task-panel" onClick={(e) => e.stopPropagation()}>
        <div className="panel-header">
          <h3>新建任务</h3>
          <button className="close-btn" onClick={onClose}>×</button>
        </div>

        <div className="panel-body">
          <div className="form-group">
            <label>任务类型</label>
            <select value={taskType} onChange={(e) => setTaskType(e.target.value)}>
              <option value="analysis">任务分析</option>
              <option value="consult">智能咨询</option>
              <option value="auto_work">自主工作</option>
            </select>
          </div>

          <div className="form-group">
            <label>任务描述</label>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="请输入任务描述..."
            />
          </div>

          <div className="form-group">
            <label>选择智能体</label>
            <div className="agent-options">
              {options.map((opt) => (
                <label
                  key={opt.id}
                  className={`agent-option ${!opt.is_available ? 'disabled' : ''}`}
                >
                  <input
                    type="checkbox"
                    checked={selectedAgents.includes(opt.id)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedAgents([...selectedAgents, opt.id]);
                      } else {
                        setSelectedAgents(selectedAgents.filter((id) => id !== opt.id));
                      }
                    }}
                    disabled={!opt.is_available}
                  />
                  <span className="agent-name">{opt.name}</span>
                  <span className="agent-dept">{opt.department}</span>
                  <span className="agent-score">推荐: {opt.recommendation_score.toFixed(0)}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        <div className="panel-footer">
          <button
            className="submit-btn"
            onClick={handleSubmit}
            disabled={loading}
          >
            {loading ? '启动中...' : '开始任务'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;
