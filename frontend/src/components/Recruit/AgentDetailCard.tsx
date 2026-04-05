import React, { useState } from 'react';
import './AgentDetailCard.css';

interface Skill {
  slot: number;
  name: string;
  description: string;
  effect: Record<string, unknown>;
  unlock_level: number;
  unlocked: boolean;
  level: number;
}

interface AgentDetail {
  id: string;
  name: string;
  rarity: string;
  rarity_color: string;
  department: string;
  level: number;
  exp: number;
  level_cap: number;
  can_upgrade: boolean;
  upgrade_cost: number;
  skills: Skill[];
  stats: Record<string, number>;
  base_salary: number;
  current_salary: number;
  assigned_department: string | null;
  status: string;
  description: string;
  can_breakthrough: boolean;
  breakthrough_cost: { integral?: number; material?: string };
  next_rarity: string | null;
}

interface AgentDetailCardProps {
  agent: AgentDetail;
  onUpgrade: () => Promise<void>;
  onLearnSkill: (skillSlot: number) => Promise<void>;
  onBreakthrough: () => Promise<void>;
  onAssignDepartment: (department: string) => Promise<void>;
  onClose: () => void;
  loading?: boolean;
}

const RARITY_NAMES: Record<string, string> = {
  N: '普通',
  R: '稀有',
  SR: '史诗',
  SSR: '传说',
  UR: '神话',
};

const DEPARTMENTS = ['吏部', '户部', '礼部', '兵部', '刑部', '工部'];

const AgentDetailCard: React.FC<AgentDetailCardProps> = ({
  agent,
  onUpgrade,
  onLearnSkill,
  onBreakthrough,
  onAssignDepartment,
  onClose,
  loading = false,
}) => {
  const [activeTab, setActiveTab] = useState<'info' | 'skills' | 'actions'>('info');
  const [selectedDepartment, setSelectedDepartment] = useState(agent.assigned_department || '');

  const handleAssign = async () => {
    if (selectedDepartment) {
      await onAssignDepartment(selectedDepartment);
    }
  };

  const expPercent = (agent.exp / (agent.level * 100)) * 100;

  return (
    <div className="agent-detail-overlay" onClick={onClose}>
      <div className="agent-detail-card" onClick={(e) => e.stopPropagation()}>
        <button className="close-btn" onClick={onClose}>×</button>
        
        <div className="card-banner" style={{ background: `linear-gradient(135deg, ${agent.rarity_color}22, ${agent.rarity_color}44)` }}>
          <div className="rarity-tag" style={{ backgroundColor: agent.rarity_color }}>
            {RARITY_NAMES[agent.rarity]}
          </div>
          <div className="agent-avatar-large">
            <span>🤖</span>
          </div>
          <h2 className="agent-title">{agent.name}</h2>
          <p className="agent-dept">{agent.department}</p>
        </div>

        <div className="level-section">
          <div className="level-info">
            <span className="level-label">等级</span>
            <span className="level-value">{agent.level} / {agent.level_cap}</span>
          </div>
          <div className="exp-bar">
            <div className="exp-fill" style={{ width: `${expPercent}%` }} />
          </div>
          <div className="salary-info">
            <span>时薪: {agent.current_salary} 积分</span>
            <span className="status-badge" data-status={agent.status}>
              {agent.status === 'working' ? '工作中' : '闲置'}
            </span>
          </div>
        </div>

        <div className="tabs">
          <button
            className={`tab ${activeTab === 'info' ? 'active' : ''}`}
            onClick={() => setActiveTab('info')}
          >
            信息
          </button>
          <button
            className={`tab ${activeTab === 'skills' ? 'active' : ''}`}
            onClick={() => setActiveTab('skills')}
          >
            技能
          </button>
          <button
            className={`tab ${activeTab === 'actions' ? 'active' : ''}`}
            onClick={() => setActiveTab('actions')}
          >
            操作
          </button>
        </div>

        <div className="tab-content">
          {activeTab === 'info' && (
            <div className="info-tab">
              <p className="description">{agent.description}</p>
              
              <div className="stats-grid">
                {Object.entries(agent.stats).map(([key, value]) => (
                  <div key={key} className="stat-item">
                    <span className="stat-name">{key}</span>
                    <div className="stat-bar">
                      <div className="stat-fill" style={{ width: `${value}%` }} />
                    </div>
                    <span className="stat-value">{value}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {activeTab === 'skills' && (
            <div className="skills-tab">
              {agent.skills.map((skill) => (
                <div
                  key={skill.slot}
                  className={`skill-card ${skill.unlocked ? 'unlocked' : 'locked'}`}
                >
                  <div className="skill-header">
                    <span className="skill-name">{skill.name}</span>
                    {skill.unlocked && (
                      <span className="skill-level">Lv.{skill.level}</span>
                    )}
                  </div>
                  <p className="skill-desc">{skill.description}</p>
                  {!skill.unlocked ? (
                    <span className="unlock-hint">
                      🔒 {skill.unlock_level}级解锁
                    </span>
                  ) : skill.level < 10 ? (
                    <button
                      className="upgrade-skill-btn"
                      onClick={() => onLearnSkill(skill.slot)}
                      disabled={loading}
                    >
                      升级技能 ({(skill.level + 1) * 100} 积分)
                    </button>
                  ) : (
                    <span className="max-level">已满级</span>
                  )}
                </div>
              ))}
            </div>
          )}

          {activeTab === 'actions' && (
            <div className="actions-tab">
              <div className="action-group">
                <h4>升级</h4>
                {agent.can_upgrade ? (
                  <button
                    className="action-btn upgrade"
                    onClick={onUpgrade}
                    disabled={loading}
                  >
                    升级 ({agent.upgrade_cost} 积分)
                  </button>
                ) : (
                  <p className="action-hint">
                    {agent.level >= agent.level_cap ? '已达等级上限' : '无法升级'}
                  </p>
                )}
              </div>

              <div className="action-group">
                <h4>突破</h4>
                {agent.can_breakthrough ? (
                  <button
                    className="action-btn breakthrough"
                    onClick={onBreakthrough}
                    disabled={loading}
                  >
                    突破为 {agent.next_rarity} ({agent.breakthrough_cost?.integral?.toLocaleString()} 积分)
                  </button>
                ) : (
                  <p className="action-hint">
                    {agent.rarity === 'UR' ? '已达最高稀有度' : `需达到 ${agent.level_cap} 级`}
                  </p>
                )}
              </div>

              <div className="action-group">
                <h4>分配部门</h4>
                <div className="department-select">
                  <select
                    value={selectedDepartment}
                    onChange={(e) => setSelectedDepartment(e.target.value)}
                  >
                    <option value="">选择部门</option>
                    {DEPARTMENTS.map((dept) => (
                      <option key={dept} value={dept}>{dept}</option>
                    ))}
                  </select>
                  <button
                    className="action-btn assign"
                    onClick={handleAssign}
                    disabled={loading || !selectedDepartment}
                  >
                    分配
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default AgentDetailCard;
