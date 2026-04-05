import React, { useState, useEffect } from 'react';
import governanceApi, { UserAgent, FinanceSummary } from '../../api/governance';
import { Card, Button, Badge, Loading, EmptyState } from '../ui';

interface CoreAgent {
  agent_id: string;
  name: string;
  department: string;
  level: number;
  current_salary: number;
  status: string;
}

const CabinetPage: React.FC = () => {
  const [coreAgents, setCoreAgents] = useState<CoreAgent[]>([]);
  const [recruitedAgents, setRecruitedAgents] = useState<UserAgent[]>([]);
  const [finance, setFinance] = useState<FinanceSummary>({
    total_integral: 0,
    total_spent: 0,
    total_earned: 0,
    active_agents: 0,
    daily_salary_cost: 0,
    monthly_salary_cost: 0,
  });
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState<string | null>(null);
  const [dismissing, setDismissing] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [agentsRes, financeRes] = await Promise.all([
        governanceApi.getGovernanceAgents(),
        governanceApi.getGovernanceFinance(),
      ]);
      
      if (agentsRes.success) {
        setCoreAgents(agentsRes.core_agents);
        setRecruitedAgents(agentsRes.recruited_agents);
      }
      if (financeRes.success) {
        setFinance(financeRes.summary);
      }
    } catch (error) {
      console.error('Failed to load cabinet data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = async (agent: UserAgent) => {
    if (!confirm(`确定升级 ${agent.name}？将消耗积分`)) {
      return;
    }

    setUpgrading(agent.id);
    try {
      const result = await governanceApi.upgradeAgent(agent.id);
      if (result.success) {
        alert(result.message);
        loadData();
      } else {
        alert(result.error || '升级失败');
      }
    } catch (error) {
      console.error('Upgrade failed:', error);
      alert('升级失败，请稍后重试');
    } finally {
      setUpgrading(null);
    }
  };

  const handleDismiss = async (agent: UserAgent) => {
    if (!confirm(`确定解雇 ${agent.name}？将返还部分积分`)) {
      return;
    }

    setDismissing(agent.id);
    try {
      const result = await governanceApi.dismissAgent(agent.id);
      if (result.success) {
        alert(result.message);
        loadData();
      } else {
        alert(result.error || '解雇失败');
      }
    } catch (error) {
      console.error('Dismiss failed:', error);
      alert('解雇失败，请稍后重试');
    } finally {
      setDismissing(null);
    }
  };

  const getDepartmentColor = (dept: string): string => {
    const colors: Record<string, string> = {
      '中书省': '#e74c3c',
      '门下省': '#3498db',
      '尚书省': '#2ecc71',
      '吏部': '#9b59b6',
      '户部': '#f39c12',
      '礼部': '#1abc9c',
      '兵部': '#e67e22',
      '刑部': '#34495e',
      '工部': '#95a5a6',
    };
    return colors[dept] || '#7f8c8d';
  };

  if (loading) {
    return <Loading text="加载内阁数据..." />;
  }

  return (
    <div className="cabinet-page">
      <div className="cabinet-header">
        <h1>👑 我的内阁</h1>
        <p>管理你的三省六部智能体团队</p>
      </div>

      <div className="finance-summary">
        <div className="summary-card">
          <div className="summary-icon">💰</div>
          <div className="summary-info">
            <span className="summary-label">积分余额</span>
            <span className="summary-value">{finance.total_integral.toLocaleString()}</span>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">📊</div>
          <div className="summary-info">
            <span className="summary-label">累计消耗</span>
            <span className="summary-value">{finance.total_spent.toLocaleString()}</span>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">👥</div>
          <div className="summary-info">
            <span className="summary-label">活跃智能体</span>
            <span className="summary-value">{finance.active_agents}</span>
          </div>
        </div>
        <div className="summary-card">
          <div className="summary-icon">📅</div>
          <div className="summary-info">
            <span className="summary-label">日均薪资</span>
            <span className="summary-value">{finance.daily_salary_cost}</span>
          </div>
        </div>
      </div>

      <div className="departments-section">
        <h2>🏛️ 三省核心</h2>
        <div className="agents-grid core">
          {coreAgents.map(agent => (
            <Card key={agent.agent_id} className="agent-card core-agent">
              <div 
                className="agent-header"
                style={{ borderColor: getDepartmentColor(agent.department) }}
              >
                <div className="agent-avatar">
                  {agent.name.charAt(0)}
                </div>
                <div className="agent-title">
                  <h3>{agent.name}</h3>
                  <Badge 
                    color={getDepartmentColor(agent.department)}
                    text={agent.department}
                  />
                </div>
                <div className="agent-level">
                  Lv.{agent.level}
                </div>
              </div>
              <div className="agent-info">
                <div className="info-row">
                  <span>当前薪资</span>
                  <strong>{agent.current_salary} 积分/次</strong>
                </div>
                <div className="info-row">
                  <span>状态</span>
                  <span className={`status-badge ${agent.status}`}>
                    {agent.status === 'idle' ? '空闲' : '忙碌'}
                  </span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      </div>

      <div className="departments-section">
        <h2>📋 六部官员</h2>
        {recruitedAgents.length === 0 ? (
          <EmptyState
            title="暂无招募的智能体"
            description="前往人才市场招募你的智能体团队"
          />
        ) : (
          <div className="agents-grid">
            {recruitedAgents.map(agent => (
              <Card key={agent.id} className="agent-card">
                <div 
                  className="agent-header"
                  style={{ borderColor: getDepartmentColor(agent.department) }}
                >
                  <div className="agent-avatar">
                    {agent.name.charAt(0)}
                  </div>
                  <div className="agent-title">
                    <h3>{agent.name}</h3>
                    <Badge 
                      color={getDepartmentColor(agent.department)}
                      text={agent.department}
                    />
                  </div>
                  <div className="agent-level">
                    Lv.{agent.level}
                  </div>
                </div>
                
                <div className="agent-info">
                  <div className="info-row">
                    <span>当前薪资</span>
                    <strong>{agent.salary} 积分/次</strong>
                  </div>
                  <div className="info-row">
                    <span>招募时间</span>
                    <span>{new Date(agent.recruited_at).toLocaleDateString()}</span>
                  </div>
                  <div className="info-row">
                    <span>状态</span>
                    <span className={`status-badge ${agent.status}`}>
                      {agent.status === 'active' ? '在职' : agent.status === 'busy' ? '忙碌' : '离职'}
                    </span>
                  </div>
                </div>

                <div className="agent-actions">
                  <Button
                    variant="outline"
                    size="small"
                    onClick={() => handleUpgrade(agent)}
                    disabled={upgrading === agent.id}
                  >
                    {upgrading === agent.id ? '升级中...' : '升级'}
                  </Button>
                  <Button
                    variant="danger"
                    size="small"
                    onClick={() => handleDismiss(agent)}
                    disabled={dismissing === agent.id}
                  >
                    {dismissing === agent.id ? '解雇中...' : '解雇'}
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </div>

      <style>{`
        .cabinet-page {
          padding: 24px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .cabinet-header {
          margin-bottom: 24px;
        }

        .cabinet-header h1 {
          margin: 0 0 8px 0;
          font-size: 28px;
          color: #1a1a2e;
        }

        .cabinet-header p {
          margin: 0;
          color: #666;
        }

        .finance-summary {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 16px;
          margin-bottom: 32px;
        }

        .summary-card {
          display: flex;
          align-items: center;
          gap: 16px;
          padding: 20px;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .summary-icon {
          font-size: 32px;
        }

        .summary-info {
          display: flex;
          flex-direction: column;
        }

        .summary-label {
          font-size: 12px;
          color: #999;
        }

        .summary-value {
          font-size: 24px;
          font-weight: bold;
          color: #333;
        }

        .departments-section {
          margin-bottom: 32px;
        }

        .departments-section h2 {
          margin: 0 0 16px 0;
          font-size: 20px;
          color: #333;
        }

        .agents-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
          gap: 16px;
        }

        .agents-grid.core {
          grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
        }

        .agent-card {
          padding: 0;
        }

        .agent-card.core-agent {
          border: 2px solid #ffd700;
        }

        .agent-header {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 16px;
          border-bottom: 3px solid;
          background: #f8f9fa;
        }

        .agent-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 20px;
          font-weight: bold;
        }

        .agent-title {
          flex: 1;
        }

        .agent-title h3 {
          margin: 0 0 4px 0;
          font-size: 16px;
        }

        .agent-level {
          font-size: 14px;
          font-weight: bold;
          color: #667eea;
        }

        .agent-info {
          padding: 12px 16px;
        }

        .info-row {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #f0f0f0;
        }

        .info-row:last-child {
          border-bottom: none;
        }

        .info-row span {
          color: #666;
        }

        .info-row strong {
          color: #333;
        }

        .status-badge {
          padding: 2px 8px;
          border-radius: 4px;
          font-size: 12px;
        }

        .status-badge.idle,
        .status-badge.active {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .status-badge.busy {
          background: #fff3e0;
          color: #ef6c00;
        }

        .status-badge.inactive,
        .status-badge.dismissed {
          background: #f8f9fa;
          color: #6c757d;
        }

        .agent-actions {
          display: flex;
          gap: 8px;
          padding: 12px 16px;
          border-top: 1px solid #eee;
        }

        .agent-actions button {
          flex: 1;
        }
      `}</style>
    </div>
  );
};

export default CabinetPage;
