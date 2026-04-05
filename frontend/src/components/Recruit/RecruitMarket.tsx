import React, { useState, useEffect } from 'react';
import RecruitAnimation from './RecruitAnimation';
import AgentDetailCard from './AgentDetailCard';
import BondsPage from './BondsPage';
import './RecruitMarket.css';

interface Agent {
  id: string;
  template_id: string;
  name: string;
  rarity: string;
  rarity_color: string;
  department: string;
  level: number;
  level_cap: number;
  skills: Array<{ name: string; description: string }>;
  status: string;
  recruited_at: string;
}

interface RecruitResult {
  success: boolean;
  user_agent_id?: string;
  name?: string;
  rarity?: string;
  department?: string;
  skills?: Array<{ name: string; description: string }>;
  cost?: number;
  guarantee_triggered?: string;
  error?: string;
}

interface RecruitStats {
  total_recruits: number;
  sr_guarantee_count: number;
  ssr_guarantee_count: number;
  sr_guarantee_percent: number;
  ssr_guarantee_percent: number;
}

interface AgentDetail {
  id: string;
  name: string;
  rarity: string;
  rarity_color: string;
  department: string;
  level: number;
  level_cap: number;
  can_upgrade: boolean;
  upgrade_cost: number;
  skills: Array<{
    slot: number;
    name: string;
    description: string;
    unlock_level: number;
    unlocked: boolean;
    level: number;
  }>;
  stats: Record<string, number>;
  base_salary: number;
  current_salary: number;
  assigned_department: string | null;
  status: string;
  description: string;
  can_breakthrough: boolean;
  breakthrough_cost: { integral?: number };
  next_rarity: string | null;
}

const RARITY_NAMES: Record<string, string> = {
  N: '普通',
  R: '稀有',
  SR: '史诗',
  SSR: '传说',
  UR: '神话',
};

const RecruitMarket: React.FC = () => {
  const [userIntegral, setUserIntegral] = useState(0);
  const [stats, setStats] = useState<RecruitStats | null>(null);
  const [agents, setAgents] = useState<Agent[]>([]);
  const [loading, setLoading] = useState(false);
  const [recruitResult, setRecruitResult] = useState<RecruitResult | null>(null);
  const [showAnimation, setShowAnimation] = useState(false);
  const [selectedAgent, setSelectedAgent] = useState<AgentDetail | null>(null);
  const [showBonds, setShowBonds] = useState(false);
  const [activeTab, setActiveTab] = useState<'recruit' | 'agents' | 'bonds'>('recruit');

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Authorization': `Bearer ${token}` };

      const [statsRes, agentsRes] = await Promise.all([
        fetch('/api/recruit/stats', { headers }),
        fetch('/api/recruit/agents', { headers }),
      ]);

      const statsData = await statsRes.json();
      const agentsData = await agentsRes.json();

      if (statsData.success) {
        setStats(statsData.stats);
      }
      if (agentsData.success) {
        setAgents(agentsData.agents);
      }

      const userRes = await fetch('/api/auth/me', { headers });
      const userData = await userRes.json();
      if (userData.integral !== undefined) {
        setUserIntegral(userData.integral);
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    }
  };

  const handleRecruit = async (type: 'basic' | 'premium') => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/recruit/${type}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      const data: RecruitResult = await response.json();
      
      if (data.success) {
        setRecruitResult(data);
        setShowAnimation(true);
        setUserIntegral((prev) => prev - (data.cost || 0));
        fetchData();
      } else {
        alert(data.error || '招募失败');
      }
    } catch (error) {
      console.error('Recruit failed:', error);
      alert('招募失败，请重试');
    } finally {
      setLoading(false);
    }
  };

  const handleAgentClick = async (agent: Agent) => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`/api/recruit/agents/${agent.id}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const data = await response.json();
      if (data.success) {
        setSelectedAgent(data.agent);
      }
    } catch (error) {
      console.error('Failed to fetch agent detail:', error);
    }
  };

  const handleUpgrade = async () => {
    if (!selectedAgent) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/recruit/agents/upgrade', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_agent_id: selectedAgent.id }),
      });
      const data = await response.json();
      if (data.success) {
        alert(data.message);
        handleAgentClick({ id: selectedAgent.id } as Agent);
        setUserIntegral((prev) => prev - data.cost);
      } else {
        alert(data.error || '升级失败');
      }
    } catch (error) {
      console.error('Upgrade failed:', error);
    }
  };

  const handleLearnSkill = async (skillSlot: number) => {
    if (!selectedAgent) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/recruit/agents/learn-skill', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_agent_id: selectedAgent.id,
          skill_slot: skillSlot,
        }),
      });
      const data = await response.json();
      if (data.success) {
        alert(data.message);
        handleAgentClick({ id: selectedAgent.id } as Agent);
      } else {
        alert(data.error || '技能学习失败');
      }
    } catch (error) {
      console.error('Learn skill failed:', error);
    }
  };

  const handleBreakthrough = async () => {
    if (!selectedAgent) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/recruit/agents/breakthrough', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ user_agent_id: selectedAgent.id }),
      });
      const data = await response.json();
      if (data.success) {
        alert(data.message);
        handleAgentClick({ id: selectedAgent.id } as Agent);
      } else {
        alert(data.error || '突破失败');
      }
    } catch (error) {
      console.error('Breakthrough failed:', error);
    }
  };

  const handleAssignDepartment = async (department: string) => {
    if (!selectedAgent) return;
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/recruit/agents/assign', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_agent_id: selectedAgent.id,
          department,
        }),
      });
      const data = await response.json();
      if (data.success) {
        alert(data.message);
        handleAgentClick({ id: selectedAgent.id } as Agent);
      } else {
        alert(data.error || '分配失败');
      }
    } catch (error) {
      console.error('Assign failed:', error);
    }
  };

  return (
    <div className="recruit-market">
      <div className="market-header">
        <h1>人才市场</h1>
        <div className="user-info">
          <span className="integral-display">
            💰 {userIntegral.toLocaleString()} 积分
          </span>
        </div>
      </div>

      <div className="main-tabs">
        <button
          className={`main-tab ${activeTab === 'recruit' ? 'active' : ''}`}
          onClick={() => setActiveTab('recruit')}
        >
          招募
        </button>
        <button
          className={`main-tab ${activeTab === 'agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('agents')}
        >
          我的智能体 ({agents.length})
        </button>
        <button
          className={`main-tab ${activeTab === 'bonds' ? 'active' : ''}`}
          onClick={() => setActiveTab('bonds')}
        >
          羁绊图鉴
        </button>
      </div>

      {activeTab === 'recruit' && (
        <div className="recruit-section">
          <div className="recruit-cards">
            <div className="recruit-card basic">
              <div className="card-header">
                <h3>基础招募</h3>
                <span className="cost">100 积分</span>
              </div>
              <div className="probability-list">
                <div className="prob-item"><span className="rarity n">N</span> 60%</div>
                <div className="prob-item"><span className="rarity r">R</span> 30%</div>
                <div className="prob-item"><span className="rarity sr">SR</span> 8%</div>
                <div className="prob-item"><span className="rarity ssr">SSR</span> 1.5%</div>
                <div className="prob-item"><span className="rarity ur">UR</span> 0.5%</div>
              </div>
              <button
                className="recruit-btn"
                onClick={() => handleRecruit('basic')}
                disabled={loading || userIntegral < 100}
              >
                {loading ? '招募中...' : '立即招募'}
              </button>
            </div>

            <div className="recruit-card premium">
              <div className="card-header">
                <h3>高级招募</h3>
                <span className="cost">1000 积分</span>
                <span className="recommend-tag">推荐</span>
              </div>
              <div className="probability-list">
                <div className="prob-item"><span className="rarity n">N</span> 30%</div>
                <div className="prob-item"><span className="rarity r">R</span> 40%</div>
                <div className="prob-item"><span className="rarity sr">SR</span> 20%</div>
                <div className="prob-item"><span className="rarity ssr">SSR</span> 8%</div>
                <div className="prob-item"><span className="rarity ur">UR</span> 2%</div>
              </div>
              <button
                className="recruit-btn premium"
                onClick={() => handleRecruit('premium')}
                disabled={loading || userIntegral < 1000}
              >
                {loading ? '招募中...' : '立即招募'}
              </button>
            </div>
          </div>

          {stats && (
            <div className="guarantee-section">
              <h4>保底进度</h4>
              <div className="guarantee-bars">
                <div className="guarantee-item">
                  <span className="label">SR保底 (10次)</span>
                  <div className="progress-bar">
                    <div
                      className="progress-fill sr"
                      style={{ width: `${stats.sr_guarantee_percent}%` }}
                    />
                  </div>
                  <span className="count">{stats.sr_guarantee_count}/10</span>
                </div>
                <div className="guarantee-item">
                  <span className="label">SSR保底 (50次)</span>
                  <div className="progress-bar">
                    <div
                      className="progress-fill ssr"
                      style={{ width: `${stats.ssr_guarantee_percent}%` }}
                    />
                  </div>
                  <span className="count">{stats.ssr_guarantee_count}/50</span>
                </div>
              </div>
              <p className="total-recruits">总招募次数: {stats.total_recruits}</p>
            </div>
          )}
        </div>
      )}

      {activeTab === 'agents' && (
        <div className="agents-section">
          {agents.length === 0 ? (
            <div className="empty-state">
              <p>暂无智能体，快去招募吧！</p>
              <button onClick={() => setActiveTab('recruit')}>前往招募</button>
            </div>
          ) : (
            <div className="agents-grid">
              {agents.map((agent) => (
                <div
                  key={agent.id}
                  className={`agent-card ${agent.rarity.toLowerCase()}`}
                  onClick={() => handleAgentClick(agent)}
                >
                  <div
                    className="rarity-border"
                    style={{ borderColor: agent.rarity_color }}
                  />
                  <div className="agent-avatar">🤖</div>
                  <div className="agent-info">
                    <h4>{agent.name}</h4>
                    <p className="agent-rarity" style={{ color: agent.rarity_color }}>
                      {RARITY_NAMES[agent.rarity]}
                    </p>
                    <p className="agent-level">Lv.{agent.level}/{agent.level_cap}</p>
                    <p className="agent-dept">{agent.department}</p>
                  </div>
                  <span className={`status-dot ${agent.status}`} />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === 'bonds' && <BondsPage />}

      {showAnimation && recruitResult && (
        <RecruitAnimation
          rarity={recruitResult.rarity || 'N'}
          agentName={recruitResult.name || '未知'}
          department={recruitResult.department || ''}
          skills={recruitResult.skills || []}
          onComplete={() => {}}
          onContinue={() => {
            setShowAnimation(false);
            setRecruitResult(null);
          }}
        />
      )}

      {selectedAgent && (
        <AgentDetailCard
          agent={selectedAgent}
          onUpgrade={handleUpgrade}
          onLearnSkill={handleLearnSkill}
          onBreakthrough={handleBreakthrough}
          onAssignDepartment={handleAssignDepartment}
          onClose={() => setSelectedAgent(null)}
        />
      )}
    </div>
  );
};

export default RecruitMarket;
