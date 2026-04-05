import React, { useState, useEffect } from 'react';
import './AutoWorkPanel.css';

interface AgentAutoWorkInfo {
  id: string;
  name: string;
  level: number;
  rarity: string;
  department: string;
  auto_work_enabled: boolean;
  daily_work_seconds: number;
  daily_limit: number;
  total_reward: number;
  efficiency_bonus: number;
}

interface AutoWorkPanelProps {
  agentId: string;
  agentName: string;
  onClose?: () => void;
}

const AutoWorkPanel: React.FC<AutoWorkPanelProps> = ({ agentId, agentName, onClose }) => {
  const [agentInfo, setAgentInfo] = useState<AgentAutoWorkInfo | null>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    fetchData();
  }, [agentId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [statsRes, logsRes] = await Promise.all([
        fetch('/api/auto-work/stats', { headers }),
        fetch(`/api/auto-work/logs?agent_id=${agentId}&limit=10`, { headers }),
      ]);

      const statsData = await statsRes.json();
      const logsData = await logsRes.json();

      if (statsData.success) {
        const agent = statsData.agents.find((a: any) => a.id === agentId);
        if (agent) {
          setAgentInfo(agent);
        }
      }

      if (logsData.success) {
        setLogs(logsData.logs);
      }
    } catch (error) {
      console.error('Failed to fetch auto work data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggle = async (enabled: boolean) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/auto-work/toggle', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ agent_id: agentId, enabled }),
      });

      const data = await response.json();
      if (data.success) {
        setAgentInfo((prev) => prev ? { ...prev, auto_work_enabled: enabled } : null);
      }
    } catch (error) {
      console.error('Failed to toggle auto work:', error);
    } finally {
      setSaving(false);
    }
  };

  const handleSetLimit = async (limitMinutes: number) => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const limitSeconds = limitMinutes * 60;
      const response = await fetch('/api/auto-work/set-limit', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ agent_id: agentId, limit_seconds: limitSeconds }),
      });

      const data = await response.json();
      if (data.success) {
        setAgentInfo((prev) => prev ? { ...prev, daily_limit: limitSeconds } : null);
      }
    } catch (error) {
      console.error('Failed to set limit:', error);
    } finally {
      setSaving(false);
    }
  };

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}小时${minutes}分钟`;
    }
    return `${minutes}分钟`;
  };

  const progressPercent = agentInfo
    ? Math.min((agentInfo.daily_work_seconds / agentInfo.daily_limit) * 100, 100)
    : 0;

  return (
    <div className="auto-work-panel">
      <div className="panel-header">
        <h3>🤖 自主工作设置</h3>
        <span className="agent-name">{agentName}</span>
      </div>

      {loading ? (
        <div className="loading-state">加载中...</div>
      ) : agentInfo ? (
        <>
          <div className="toggle-section">
            <div className="toggle-row">
              <span className="toggle-label">启用自主工作</span>
              <label className="toggle-switch">
                <input
                  type="checkbox"
                  checked={agentInfo.auto_work_enabled}
                  onChange={(e) => handleToggle(e.target.checked)}
                  disabled={saving}
                />
                <span className="toggle-slider"></span>
              </label>
            </div>
            <p className="toggle-hint">
              开启后，智能体空闲时将自动执行任务赚取积分
            </p>
          </div>

          <div className="limit-section">
            <h4>每日工作限额</h4>
            <div className="limit-options">
              {[30, 60, 120, 180, 360].map((mins) => (
                <button
                  key={mins}
                  className={`limit-btn ${agentInfo.daily_limit === mins * 60 ? 'active' : ''}`}
                  onClick={() => handleSetLimit(mins)}
                  disabled={saving}
                >
                  {mins >= 60 ? `${mins / 60}小时` : `${mins}分钟`}
                </button>
              ))}
            </div>
          </div>

          <div className="progress-section">
            <h4>今日工作进度</h4>
            <div className="progress-bar">
              <div
                className="progress-fill"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="progress-info">
              <span>已工作: {formatDuration(agentInfo.daily_work_seconds)}</span>
              <span>限额: {formatDuration(agentInfo.daily_limit)}</span>
            </div>
          </div>

          <div className="stats-section">
            <div className="stat-item">
              <span className="stat-label">累计收益</span>
              <span className="stat-value reward">{agentInfo.total_reward} 积分</span>
            </div>
            <div className="stat-item">
              <span className="stat-label">效率加成</span>
              <span className="stat-value">{(agentInfo.efficiency_bonus * 100).toFixed(0)}%</span>
            </div>
          </div>

          <div className="logs-section">
            <h4>最近工作记录</h4>
            {logs.length === 0 ? (
              <p className="no-logs">暂无工作记录</p>
            ) : (
              <div className="logs-list">
                {logs.map((log) => (
                  <div key={log.id} className="log-item">
                    <div className="log-header">
                      <span className="task-type">{log.task_type}</span>
                      <span className="log-time">
                        {new Date(log.created_at).toLocaleString()}
                      </span>
                    </div>
                    <div className="log-details">
                      <span>耗时: {log.duration_seconds}秒</span>
                      <span className="reward">+{log.reward_earned}积分</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </>
      ) : (
        <div className="error-state">无法加载智能体信息</div>
      )}
    </div>
  );
};

export default AutoWorkPanel;
