import React, { useState, useEffect, useCallback } from 'react';
import './UnifiedAdminPage.css';

interface DashboardStats {
  total_users: number;
  new_users_today: number;
  new_users_week: number;
  total_agents: number;
  total_tasks: number;
  completed_tasks: number;
  auto_tasks: number;
  total_memories: number;
  total_integral: number;
  integral_logs_today: number;
  user_growth: Array<{ date: string; count: number }>;
  task_trend: Array<{ date: string; count: number }>;
  agents_by_department: Record<string, number>;
  memories_by_type: Record<string, number>;
}

interface User {
  id: string;
  email: string;
  username: string;
  full_name: string;
  role: string;
  is_admin: boolean;
  is_active: boolean;
  integral: number;
  created_at: string;
  last_login: string;
}

interface Agent {
  id: string;
  user_id: string;
  name: string;
  department: string;
  level: number;
  status: string;
  created_at: string;
  user_email: string;
}

interface Task {
  id: string;
  user_id: string;
  type: string;
  status: string;
  created_at: string;
  completed_at: string;
}

interface IntegralLog {
  id: string;
  user_id: string;
  type: string;
  amount: number;
  balance: number;
  description: string;
  created_at: string;
  user_email: string;
}

interface Memory {
  id: string;
  user_id: string;
  type: string;
  summary: string;
  importance: number;
  source: string;
  created_at: string;
  user_email: string;
}

interface AuditLog {
  id: string;
  admin_id: string;
  operation_type: string;
  target_type: string;
  target_id: string;
  before_data: string;
  after_data: string;
  ip_address: string;
  created_at: string;
  admin_email: string;
}

type TabType = 'dashboard' | 'users' | 'agents' | 'tasks' | 'integral' | 'memories' | 'configs' | 'audit';

const UnifiedAdminPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('dashboard');
  const [loading, setLoading] = useState(false);
  
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [users, setUsers] = useState<{ users: User[]; total: number }>({ users: [], total: 0 });
  const [agents, setAgents] = useState<{ agents: Agent[]; total: number }>({ agents: [], total: 0 });
  const [tasks, setTasks] = useState<{ tasks: Task[]; total: number }>({ tasks: [], total: 0 });
  const [integralLogs, setIntegralLogs] = useState<{ logs: IntegralLog[]; total: number }>({ logs: [], total: 0 });
  const [memories, setMemories] = useState<{ memories: Memory[]; total: number }>({ memories: [], total: 0 });
  const [auditLogs, setAuditLogs] = useState<{ logs: AuditLog[]; total: number }>({ logs: [], total: 0 });
  const [configs, setConfigs] = useState<Record<string, any>>({});
  
  const [searchQuery, setSearchQuery] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [showUserDetail, setShowUserDetail] = useState(false);
  const [showIntegralAdjust, setShowIntegralAdjust] = useState(false);
  const [adjustAmount, setAdjustAmount] = useState(0);
  const [adjustReason, setAdjustReason] = useState('');

  const token = localStorage.getItem('token');

  const fetchDashboardStats = useCallback(async () => {
    try {
      const response = await fetch('/api/admin/unified/dashboard/stats', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
    }
  }, [token]);

  const fetchUsers = useCallback(async (page = 1, search = '') => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');
      if (search) params.append('search', search);

      const response = await fetch(`/api/admin/unified/users?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setUsers(data);
      }
    } catch (error) {
      console.error('Failed to fetch users:', error);
    }
    setLoading(false);
  }, [token]);

  const fetchAgents = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');

      const response = await fetch(`/api/admin/unified/agents?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setAgents(data);
      }
    } catch (error) {
      console.error('Failed to fetch agents:', error);
    }
    setLoading(false);
  }, [token]);

  const fetchTasks = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');

      const response = await fetch(`/api/admin/unified/tasks?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    }
    setLoading(false);
  }, [token]);

  const fetchIntegralLogs = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');

      const response = await fetch(`/api/admin/unified/integral/logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setIntegralLogs(data);
      }
    } catch (error) {
      console.error('Failed to fetch integral logs:', error);
    }
    setLoading(false);
  }, [token]);

  const fetchMemories = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');

      const response = await fetch(`/api/admin/unified/memories?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setMemories(data);
      }
    } catch (error) {
      console.error('Failed to fetch memories:', error);
    }
    setLoading(false);
  }, [token]);

  const fetchAuditLogs = useCallback(async (page = 1) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      params.append('page', String(page));
      params.append('page_size', '20');

      const response = await fetch(`/api/admin/unified/audit-logs?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setAuditLogs(data);
      }
    } catch (error) {
      console.error('Failed to fetch audit logs:', error);
    }
    setLoading(false);
  }, [token]);

  const fetchConfigs = useCallback(async () => {
    try {
      const response = await fetch('/api/admin/unified/configs', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setConfigs(data.configs || {});
      }
    } catch (error) {
      console.error('Failed to fetch configs:', error);
    }
  }, [token]);

  useEffect(() => {
    switch (activeTab) {
      case 'dashboard':
        fetchDashboardStats();
        break;
      case 'users':
        fetchUsers(currentPage, searchQuery);
        break;
      case 'agents':
        fetchAgents(currentPage);
        break;
      case 'tasks':
        fetchTasks(currentPage);
        break;
      case 'integral':
        fetchIntegralLogs(currentPage);
        break;
      case 'memories':
        fetchMemories(currentPage);
        break;
      case 'configs':
        fetchConfigs();
        break;
      case 'audit':
        fetchAuditLogs(currentPage);
        break;
    }
  }, [activeTab, currentPage, searchQuery, fetchDashboardStats, fetchUsers, fetchAgents, fetchTasks, fetchIntegralLogs, fetchMemories, fetchConfigs, fetchAuditLogs]);

  const handleUserClick = async (userId: string) => {
    try {
      const response = await fetch(`/api/admin/unified/users/${userId}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (response.ok) {
        const data = await response.json();
        setSelectedUser(data);
        setShowUserDetail(true);
      }
    } catch (error) {
      console.error('Failed to fetch user detail:', error);
    }
  };

  const handleAdjustIntegral = async () => {
    if (!selectedUser || !adjustReason) return;
    
    try {
      const response = await fetch(
        `/api/admin/unified/users/${selectedUser.user.id}/adjust-integral?amount=${adjustAmount}&reason=${encodeURIComponent(adjustReason)}`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      );
      
      if (response.ok) {
        alert('积分调整成功！');
        setShowIntegralAdjust(false);
        handleUserClick(selectedUser.user.id);
        fetchUsers(currentPage, searchQuery);
      }
    } catch (error) {
      console.error('Failed to adjust integral:', error);
    }
  };

  const handleDeleteMemory = async (memoryId: string) => {
    if (!window.confirm('确定要删除这条记忆吗？')) return;
    
    try {
      const response = await fetch(`/api/admin/unified/memories/${memoryId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` },
      });
      
      if (response.ok) {
        fetchMemories(currentPage);
      }
    } catch (error) {
      console.error('Failed to delete memory:', error);
    }
  };

  const formatDate = (dateStr: string) => {
    if (!dateStr) return '-';
    return new Date(dateStr).toLocaleString('zh-CN');
  };

  const renderDashboard = () => (
    <div className="dashboard-content">
      {stats && (
        <>
          <div className="stats-grid">
            <div className="stat-card">
              <div className="stat-icon">👥</div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_users}</div>
                <div className="stat-label">总用户数</div>
                <div className="stat-sub">今日新增: {stats.new_users_today}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🤖</div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_agents}</div>
                <div className="stat-label">总智能体</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">📋</div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_tasks}</div>
                <div className="stat-label">总任务数</div>
                <div className="stat-sub">完成: {stats.completed_tasks}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">🧠</div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_memories}</div>
                <div className="stat-label">总记忆数</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">💰</div>
              <div className="stat-info">
                <div className="stat-value">{stats.total_integral.toLocaleString()}</div>
                <div className="stat-label">总积分</div>
                <div className="stat-sub">今日变动: {stats.integral_logs_today}</div>
              </div>
            </div>
            <div className="stat-card">
              <div className="stat-icon">⚡</div>
              <div className="stat-info">
                <div className="stat-value">{stats.auto_tasks}</div>
                <div className="stat-label">自主任务</div>
              </div>
            </div>
          </div>

          <div className="charts-grid">
            <div className="chart-card">
              <h3>用户增长趋势</h3>
              <div className="chart-placeholder">
                {stats.user_growth.slice(-7).map((item, i) => (
                  <div key={i} className="chart-bar" style={{ height: `${Math.min(item.count * 5, 100)}px` }}>
                    <span className="bar-label">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="chart-card">
              <h3>任务趋势</h3>
              <div className="chart-placeholder">
                {stats.task_trend.slice(-7).map((item, i) => (
                  <div key={i} className="chart-bar blue" style={{ height: `${Math.min(item.count * 5, 100)}px` }}>
                    <span className="bar-label">{item.count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="chart-card">
              <h3>智能体部门分布</h3>
              <div className="pie-chart">
                {Object.entries(stats.agents_by_department).map(([dept, count], i) => (
                  <div key={dept} className="pie-item">
                    <span className="pie-label">{dept}</span>
                    <span className="pie-value">{count}</span>
                  </div>
                ))}
              </div>
            </div>
            <div className="chart-card">
              <h3>记忆类型分布</h3>
              <div className="pie-chart">
                {Object.entries(stats.memories_by_type).map(([type, count], i) => (
                  <div key={type} className="pie-item">
                    <span className="pie-label">{type}</span>
                    <span className="pie-value">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );

  const renderUsers = () => (
    <div className="table-container">
      <div className="table-header">
        <input
          type="text"
          placeholder="搜索用户..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="search-input"
        />
      </div>
      <table className="data-table">
        <thead>
          <tr>
            <th>邮箱</th>
            <th>用户名</th>
            <th>角色</th>
            <th>积分</th>
            <th>状态</th>
            <th>注册时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {users.users.map((user) => (
            <tr key={user.id}>
              <td>{user.email}</td>
              <td>{user.username || '-'}</td>
              <td>
                <span className={`role-badge ${user.role}`}>
                  {user.is_admin ? '管理员' : user.role}
                </span>
              </td>
              <td>{user.integral}</td>
              <td>
                <span className={`status-badge ${user.is_active ? 'active' : 'inactive'}`}>
                  {user.is_active ? '正常' : '禁用'}
                </span>
              </td>
              <td>{formatDate(user.created_at)}</td>
              <td>
                <button className="action-btn" onClick={() => handleUserClick(user.id)}>
                  详情
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>共 {users.total} 条</span>
      </div>
    </div>
  );

  const renderAgents = () => (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>名称</th>
            <th>所属用户</th>
            <th>部门</th>
            <th>等级</th>
            <th>状态</th>
            <th>创建时间</th>
          </tr>
        </thead>
        <tbody>
          {agents.agents.map((agent) => (
            <tr key={agent.id}>
              <td>{agent.name}</td>
              <td>{agent.user_email}</td>
              <td>{agent.department}</td>
              <td>Lv.{agent.level}</td>
              <td>
                <span className={`status-badge ${agent.status}`}>
                  {agent.status}
                </span>
              </td>
              <td>{formatDate(agent.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>共 {agents.total} 条</span>
      </div>
    </div>
  );

  const renderTasks = () => (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>任务ID</th>
            <th>用户ID</th>
            <th>类型</th>
            <th>状态</th>
            <th>创建时间</th>
            <th>完成时间</th>
          </tr>
        </thead>
        <tbody>
          {tasks.tasks.map((task) => (
            <tr key={task.id}>
              <td>{task.id.substring(0, 8)}...</td>
              <td>{task.user_id.substring(0, 8)}...</td>
              <td>{task.type}</td>
              <td>
                <span className={`status-badge ${task.status}`}>
                  {task.status}
                </span>
              </td>
              <td>{formatDate(task.created_at)}</td>
              <td>{formatDate(task.completed_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>共 {tasks.total} 条</span>
      </div>
    </div>
  );

  const renderIntegral = () => (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>类型</th>
            <th>变动</th>
            <th>余额</th>
            <th>描述</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          {integralLogs.logs.map((log) => (
            <tr key={log.id}>
              <td>{log.user_email}</td>
              <td>{log.type}</td>
              <td className={log.amount > 0 ? 'positive' : 'negative'}>
                {log.amount > 0 ? '+' : ''}{log.amount}
              </td>
              <td>{log.balance}</td>
              <td>{log.description}</td>
              <td>{formatDate(log.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>共 {integralLogs.total} 条</span>
      </div>
    </div>
  );

  const renderMemories = () => (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>用户</th>
            <th>类型</th>
            <th>摘要</th>
            <th>重要性</th>
            <th>来源</th>
            <th>时间</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          {memories.memories.map((memory) => (
            <tr key={memory.id}>
              <td>{memory.user_email}</td>
              <td>{memory.type}</td>
              <td className="memory-summary">{memory.summary?.substring(0, 50)}...</td>
              <td>{(memory.importance * 100).toFixed(0)}%</td>
              <td>{memory.source}</td>
              <td>{formatDate(memory.created_at)}</td>
              <td>
                <button 
                  className="action-btn danger" 
                  onClick={() => handleDeleteMemory(memory.id)}
                >
                  删除
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>共 {memories.total} 条</span>
      </div>
    </div>
  );

  const renderConfigs = () => (
    <div className="configs-container">
      {Object.entries(configs).map(([key, config]: [string, any]) => (
        <div key={key} className="config-card">
          <h4>{key}</h4>
          <p className="config-desc">{config.description}</p>
          <pre className="config-value">
            {JSON.stringify(config.value, null, 2)}
          </pre>
          <p className="config-time">更新时间: {formatDate(config.updated_at)}</p>
        </div>
      ))}
    </div>
  );

  const renderAudit = () => (
    <div className="table-container">
      <table className="data-table">
        <thead>
          <tr>
            <th>操作人</th>
            <th>操作类型</th>
            <th>目标类型</th>
            <th>目标ID</th>
            <th>IP地址</th>
            <th>时间</th>
          </tr>
        </thead>
        <tbody>
          {auditLogs.logs.map((log) => (
            <tr key={log.id}>
              <td>{log.admin_email}</td>
              <td>{log.operation_type}</td>
              <td>{log.target_type}</td>
              <td>{log.target_id?.substring(0, 8)}...</td>
              <td>{log.ip_address}</td>
              <td>{formatDate(log.created_at)}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="pagination">
        <span>共 {auditLogs.total} 条</span>
      </div>
    </div>
  );

  return (
    <div className="unified-admin-page">
      <header className="admin-header">
        <h1>🎛️ 统一管理面板</h1>
        <div className="header-info">
          <span>管理员后台</span>
        </div>
      </header>

      <div className="admin-body">
        <nav className="admin-sidebar">
          <button
            className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            📊 仪表盘
          </button>
          <button
            className={`nav-item ${activeTab === 'users' ? 'active' : ''}`}
            onClick={() => setActiveTab('users')}
          >
            👥 用户管理
          </button>
          <button
            className={`nav-item ${activeTab === 'agents' ? 'active' : ''}`}
            onClick={() => setActiveTab('agents')}
          >
            🤖 智能体管理
          </button>
          <button
            className={`nav-item ${activeTab === 'tasks' ? 'active' : ''}`}
            onClick={() => setActiveTab('tasks')}
          >
            📋 任务管理
          </button>
          <button
            className={`nav-item ${activeTab === 'integral' ? 'active' : ''}`}
            onClick={() => setActiveTab('integral')}
          >
            💰 积分管理
          </button>
          <button
            className={`nav-item ${activeTab === 'memories' ? 'active' : ''}`}
            onClick={() => setActiveTab('memories')}
          >
            🧠 记忆管理
          </button>
          <button
            className={`nav-item ${activeTab === 'configs' ? 'active' : ''}`}
            onClick={() => setActiveTab('configs')}
          >
            ⚙️ 系统配置
          </button>
          <button
            className={`nav-item ${activeTab === 'audit' ? 'active' : ''}`}
            onClick={() => setActiveTab('audit')}
          >
            📝 审计日志
          </button>
        </nav>

        <main className="admin-content">
          {loading && <div className="loading-overlay">加载中...</div>}
          
          {activeTab === 'dashboard' && renderDashboard()}
          {activeTab === 'users' && renderUsers()}
          {activeTab === 'agents' && renderAgents()}
          {activeTab === 'tasks' && renderTasks()}
          {activeTab === 'integral' && renderIntegral()}
          {activeTab === 'memories' && renderMemories()}
          {activeTab === 'configs' && renderConfigs()}
          {activeTab === 'audit' && renderAudit()}
        </main>
      </div>

      {showUserDetail && selectedUser && (
        <div className="modal-overlay" onClick={() => setShowUserDetail(false)}>
          <div className="modal-content user-detail-modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>用户详情</h3>
              <button className="close-btn" onClick={() => setShowUserDetail(false)}>✕</button>
            </div>
            <div className="modal-body">
              <div className="user-info-section">
                <h4>基本信息</h4>
                <div className="info-grid">
                  <div><span>邮箱:</span> {selectedUser.user.email}</div>
                  <div><span>用户名:</span> {selectedUser.user.username}</div>
                  <div><span>积分:</span> {selectedUser.user.integral}</div>
                  <div><span>注册时间:</span> {formatDate(selectedUser.user.created_at)}</div>
                </div>
                <button 
                  className="action-btn" 
                  onClick={() => setShowIntegralAdjust(true)}
                >
                  调整积分
                </button>
              </div>
              
              <div className="user-info-section">
                <h4>智能体 ({selectedUser.agents?.length || 0})</h4>
                <div className="sub-list">
                  {selectedUser.agents?.map((a: any) => (
                    <div key={a.id} className="sub-item">
                      {a.name} - {a.department} Lv.{a.level}
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="user-info-section">
                <h4>最近任务</h4>
                <div className="sub-list">
                  {selectedUser.tasks?.slice(0, 5).map((t: any) => (
                    <div key={t.id} className="sub-item">
                      {t.type} - {t.status}
                    </div>
                  ))}
                </div>
              </div>
              
              <div className="user-info-section">
                <h4>最近记忆</h4>
                <div className="sub-list">
                  {selectedUser.memories?.slice(0, 5).map((m: any) => (
                    <div key={m.id} className="sub-item">
                      {m.summary?.substring(0, 30)}...
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {showIntegralAdjust && (
        <div className="modal-overlay" onClick={() => setShowIntegralAdjust(false)}>
          <div className="modal-content small" onClick={(e) => e.stopPropagation()}>
            <h3>调整积分</h3>
            <div className="form-group">
              <label>当前积分: {selectedUser?.user?.integral}</label>
            </div>
            <div className="form-group">
              <label>变动量（正数增加，负数减少）</label>
              <input
                type="number"
                value={adjustAmount}
                onChange={(e) => setAdjustAmount(parseInt(e.target.value) || 0)}
              />
            </div>
            <div className="form-group">
              <label>原因</label>
              <input
                type="text"
                value={adjustReason}
                onChange={(e) => setAdjustReason(e.target.value)}
                placeholder="请输入调整原因"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-secondary" onClick={() => setShowIntegralAdjust(false)}>
                取消
              </button>
              <button className="btn-primary" onClick={handleAdjustIntegral}>
                确认
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UnifiedAdminPage;
