import React, { useState, useEffect } from 'react';
import governanceApi, { AgentTemplate, UserAgent } from '../../api/governance';
import { Card, Button, Badge, Loading, EmptyState, Modal } from '../ui';

interface AgentMarketPageProps {
  onRecruitSuccess?: () => void;
}

const AgentMarketPage: React.FC<AgentMarketPageProps> = ({ onRecruitSuccess }) => {
  const [availableAgents, setAvailableAgents] = useState<AgentTemplate[]>([]);
  const [userAgents, setUserAgents] = useState<UserAgent[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedAgent, setSelectedAgent] = useState<AgentTemplate | null>(null);
  const [recruiting, setRecruiting] = useState(false);
  const [filter, setFilter] = useState<string>('all');
  const [balance, setBalance] = useState(0);
  const [showDetailModal, setShowDetailModal] = useState(false);

  const departments = [
    { key: 'all', label: '全部' },
    { key: '中书省', label: '中书省' },
    { key: '门下省', label: '门下省' },
    { key: '尚书省', label: '尚书省' },
    { key: '吏部', label: '吏部' },
    { key: '户部', label: '户部' },
    { key: '礼部', label: '礼部' },
    { key: '兵部', label: '兵部' },
    { key: '刑部', label: '刑部' },
    { key: '工部', label: '工部' },
  ];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [agentsRes, userAgentsRes, balanceRes] = await Promise.all([
        governanceApi.getAvailableAgents(),
        governanceApi.getUserAgents(),
        governanceApi.checkBalance(),
      ]);
      
      if (agentsRes.success) {
        setAvailableAgents(agentsRes.agents);
      }
      if (userAgentsRes.success) {
        setUserAgents(userAgentsRes.agents);
      }
      if (balanceRes.success) {
        setBalance(balanceRes.balance);
      }
    } catch (error) {
      console.error('Failed to load market data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRecruit = async (agent: AgentTemplate) => {
    if (balance < agent.recruit_cost) {
      alert('积分不足，无法招募该智能体');
      return;
    }

    if (!confirm(`确定招募 ${agent.name}？将消耗 ${agent.recruit_cost} 积分`)) {
      return;
    }

    setRecruiting(true);
    try {
      const result = await governanceApi.recruitAgent(agent.id);
      if (result.success) {
        alert(result.message);
        loadData();
        onRecruitSuccess?.();
      } else {
        alert(result.error || '招募失败');
      }
    } catch (error) {
      console.error('Recruit failed:', error);
      alert('招募失败，请稍后重试');
    } finally {
      setRecruiting(false);
    }
  };

  const isRecruited = (agentId: string) => {
    return userAgents.some(ua => ua.agent_id === agentId);
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

  const filteredAgents = filter === 'all' 
    ? availableAgents 
    : availableAgents.filter(a => a.department === filter);

  if (loading) {
    return <Loading text="加载人才市场..." />;
  }

  return (
    <div className="agent-market-page">
      <div className="market-header">
        <div className="header-info">
          <h1>🏛️ 人才市场</h1>
          <p>招募智能体，组建你的内阁团队</p>
        </div>
        <div className="balance-info">
          <span className="balance-label">当前积分</span>
          <span className="balance-value">{balance.toLocaleString()}</span>
        </div>
      </div>

      <div className="filter-tabs">
        {departments.map(dept => (
          <button
            key={dept.key}
            className={`filter-tab ${filter === dept.key ? 'active' : ''}`}
            onClick={() => setFilter(dept.key)}
          >
            {dept.label}
          </button>
        ))}
      </div>

      {filteredAgents.length === 0 ? (
        <EmptyState
          title="暂无可招募智能体"
          description="请稍后再来查看"
        />
      ) : (
        <div className="agents-grid">
          {filteredAgents.map(agent => (
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

              <p className="agent-description">{agent.description}</p>

              <div className="agent-skills">
                {agent.skills.slice(0, 3).map((skill, idx) => (
                  <span key={idx} className="skill-tag">
                    {skill.name}
                  </span>
                ))}
              </div>

              <div className="agent-stats">
                <div className="stat">
                  <span className="stat-label">薪资</span>
                  <span className="stat-value">{agent.base_salary}/次</span>
                </div>
                <div className="stat">
                  <span className="stat-label">招募费用</span>
                  <span className="stat-value highlight">{agent.recruit_cost}</span>
                </div>
              </div>

              <div className="agent-actions">
                <Button
                  variant="outline"
                  size="small"
                  onClick={() => {
                    setSelectedAgent(agent);
                    setShowDetailModal(true);
                  }}
                >
                  详情
                </Button>
                <Button
                  variant={isRecruited(agent.id) ? 'secondary' : 'primary'}
                  size="small"
                  disabled={isRecruited(agent.id) || recruiting}
                  onClick={() => handleRecruit(agent)}
                >
                  {isRecruited(agent.id) ? '已招募' : '招募'}
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}

      <Modal
        isOpen={showDetailModal}
        onClose={() => setShowDetailModal(false)}
        title={selectedAgent?.name || '智能体详情'}
      >
        {selectedAgent && (
          <div className="agent-detail">
            <div className="detail-header">
              <Badge 
                color={getDepartmentColor(selectedAgent.department)}
                text={selectedAgent.department}
              />
              <span className="detail-level">Lv.{selectedAgent.level}</span>
            </div>

            <p className="detail-description">{selectedAgent.description}</p>

            <div className="detail-section">
              <h4>技能列表</h4>
              <div className="skills-list">
                {selectedAgent.skills.map((skill, idx) => (
                  <div key={idx} className="skill-item">
                    <div className="skill-header">
                      <span className="skill-name">{skill.name}</span>
                      <span className="skill-efficiency">
                        效率: {(skill.efficiency * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="skill-desc">{skill.description}</p>
                  </div>
                ))}
              </div>
            </div>

            <div className="detail-section">
              <h4>费用信息</h4>
              <div className="fee-info">
                <div className="fee-item">
                  <span>招募费用</span>
                  <strong className="highlight">{selectedAgent.recruit_cost} 积分</strong>
                </div>
                <div className="fee-item">
                  <span>基础薪资</span>
                  <strong>{selectedAgent.base_salary} 积分/次</strong>
                </div>
              </div>
            </div>

            <div className="detail-actions">
              <Button
                variant="outline"
                onClick={() => setShowDetailModal(false)}
              >
                关闭
              </Button>
              <Button
                variant="primary"
                disabled={isRecruited(selectedAgent.id) || recruiting}
                onClick={() => {
                  setShowDetailModal(false);
                  handleRecruit(selectedAgent);
                }}
              >
                {isRecruited(selectedAgent.id) ? '已招募' : '招募'}
              </Button>
            </div>
          </div>
        )}
      </Modal>

      <style>{`
        .agent-market-page {
          padding: 24px;
          max-width: 1400px;
          margin: 0 auto;
        }

        .market-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 24px;
        }

        .header-info h1 {
          margin: 0 0 8px 0;
          font-size: 28px;
          color: #1a1a2e;
        }

        .header-info p {
          margin: 0;
          color: #666;
        }

        .balance-info {
          display: flex;
          flex-direction: column;
          align-items: flex-end;
          padding: 16px 24px;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 12px;
          color: white;
        }

        .balance-label {
          font-size: 12px;
          opacity: 0.9;
        }

        .balance-value {
          font-size: 28px;
          font-weight: bold;
        }

        .filter-tabs {
          display: flex;
          gap: 8px;
          margin-bottom: 24px;
          flex-wrap: wrap;
        }

        .filter-tab {
          padding: 8px 16px;
          border: 1px solid #e0e0e0;
          border-radius: 20px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
        }

        .filter-tab:hover {
          border-color: #667eea;
        }

        .filter-tab.active {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }

        .agents-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
          gap: 20px;
        }

        .agent-card {
          padding: 0;
          overflow: hidden;
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

        .agent-description {
          padding: 12px 16px;
          margin: 0;
          font-size: 13px;
          color: #666;
          line-height: 1.5;
        }

        .agent-skills {
          padding: 0 16px;
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }

        .skill-tag {
          padding: 4px 8px;
          background: #f0f0f0;
          border-radius: 4px;
          font-size: 12px;
          color: #555;
        }

        .agent-stats {
          display: flex;
          padding: 12px 16px;
          margin-top: 12px;
          border-top: 1px solid #eee;
        }

        .stat {
          flex: 1;
          text-align: center;
        }

        .stat-label {
          display: block;
          font-size: 12px;
          color: #999;
        }

        .stat-value {
          font-weight: bold;
          color: #333;
        }

        .stat-value.highlight {
          color: #e74c3c;
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

        .agent-detail {
          padding: 16px;
        }

        .detail-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
        }

        .detail-level {
          font-size: 18px;
          font-weight: bold;
          color: #667eea;
        }

        .detail-description {
          color: #666;
          line-height: 1.6;
          margin-bottom: 20px;
        }

        .detail-section {
          margin-bottom: 20px;
        }

        .detail-section h4 {
          margin: 0 0 12px 0;
          font-size: 14px;
          color: #333;
        }

        .skills-list {
          display: flex;
          flex-direction: column;
          gap: 12px;
        }

        .skill-item {
          padding: 12px;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .skill-header {
          display: flex;
          justify-content: space-between;
          margin-bottom: 4px;
        }

        .skill-name {
          font-weight: 500;
        }

        .skill-efficiency {
          font-size: 12px;
          color: #667eea;
        }

        .skill-desc {
          margin: 0;
          font-size: 13px;
          color: #666;
        }

        .fee-info {
          display: flex;
          flex-direction: column;
          gap: 8px;
        }

        .fee-item {
          display: flex;
          justify-content: space-between;
          padding: 8px 0;
          border-bottom: 1px solid #eee;
        }

        .fee-item:last-child {
          border-bottom: none;
        }

        .fee-item strong.highlight {
          color: #e74c3c;
        }

        .detail-actions {
          display: flex;
          gap: 12px;
          margin-top: 24px;
        }

        .detail-actions button {
          flex: 1;
        }
      `}</style>
    </div>
  );
};

export default AgentMarketPage;
