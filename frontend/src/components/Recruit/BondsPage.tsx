import React, { useState, useEffect } from 'react';
import './BondsPage.css';

interface Bond {
  id: string;
  name: string;
  description: string;
  required_agents: string[];
  required_count: number;
  owned_count: number;
  is_activated: boolean;
  progress: string;
  effect: string;
  bonus: Record<string, number>;
}

interface BondsPageProps {
  onClose?: () => void;
}

const BondsPage: React.FC<BondsPageProps> = ({ onClose }) => {
  const [bonds, setBonds] = useState<Bond[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'activated' | 'locked'>('all');

  useEffect(() => {
    fetchBonds();
  }, []);

  const fetchBonds = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/recruit/all-bonds', {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });
      const data = await response.json();
      if (data.success) {
        setBonds(data.bonds);
      }
    } catch (error) {
      console.error('Failed to fetch bonds:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredBonds = bonds.filter((bond) => {
    if (filter === 'activated') return bond.is_activated;
    if (filter === 'locked') return !bond.is_activated;
    return true;
  });

  const activatedCount = bonds.filter((b) => b.is_activated).length;

  const getBonusText = (bonus: Record<string, number>) => {
    const texts: string[] = [];
    if (bonus.work_speed) texts.push(`工作效率 +${(bonus.work_speed * 100).toFixed(0)}%`);
    if (bonus.income_bonus) texts.push(`积分收入 +${(bonus.income_bonus * 100).toFixed(0)}%`);
    if (bonus.global_efficiency) texts.push(`全局效率 +${(bonus.global_efficiency * 100).toFixed(0)}%`);
    if (bonus.predict_accuracy) texts.push(`预测准确率 +${(bonus.predict_accuracy * 100).toFixed(0)}%`);
    if (bonus.risk_accuracy) texts.push(`风险准确率 +${(bonus.risk_accuracy * 100).toFixed(0)}%`);
    if (bonus.data_speed) texts.push(`数据速度 +${(bonus.data_speed * 100).toFixed(0)}%`);
    if (Object.keys(bonus).length === 0 || texts.length === 0) {
      return bonus.toString ? bonus.toString() : '特殊效果';
    }
    return texts.join(', ');
  };

  return (
    <div className="bonds-page">
      <div className="bonds-header">
        <h2>羁绊图鉴</h2>
        <div className="bonds-stats">
          <span className="stat">
            <span className="stat-value">{activatedCount}</span>
            <span className="stat-label">已激活</span>
          </span>
          <span className="stat">
            <span className="stat-value">{bonds.length}</span>
            <span className="stat-label">总羁绊</span>
          </span>
        </div>
        {onClose && (
          <button className="close-btn" onClick={onClose}>×</button>
        )}
      </div>

      <div className="filter-tabs">
        <button
          className={`filter-tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          全部
        </button>
        <button
          className={`filter-tab ${filter === 'activated' ? 'active' : ''}`}
          onClick={() => setFilter('activated')}
        >
          已激活
        </button>
        <button
          className={`filter-tab ${filter === 'locked' ? 'active' : ''}`}
          onClick={() => setFilter('locked')}
        >
          未激活
        </button>
      </div>

      {loading ? (
        <div className="loading-state">
          <div className="spinner" />
          <p>加载中...</p>
        </div>
      ) : (
        <div className="bonds-grid">
          {filteredBonds.map((bond) => (
            <div
              key={bond.id}
              className={`bond-card ${bond.is_activated ? 'activated' : 'locked'}`}
            >
              <div className="bond-icon">
                {bond.is_activated ? '🔗' : '🔓'}
              </div>
              <div className="bond-content">
                <h3 className="bond-name">{bond.name}</h3>
                <p className="bond-desc">{bond.description}</p>
                
                <div className="bond-progress">
                  <div className="progress-bar">
                    <div
                      className="progress-fill"
                      style={{ width: `${(bond.owned_count / bond.required_count) * 100}%` }}
                    />
                  </div>
                  <span className="progress-text">{bond.progress}</span>
                </div>

                <div className="bond-effect">
                  <span className="effect-label">效果:</span>
                  <span className="effect-value">{bond.effect}</span>
                </div>

                <div className="bond-bonus">
                  <span className="bonus-label">加成:</span>
                  <span className="bonus-value">{getBonusText(bond.bonus)}</span>
                </div>

                <div className="required-agents">
                  <span className="required-label">所需智能体:</span>
                  <div className="agent-icons">
                    {Array.from({ length: bond.required_count }).map((_, i) => (
                      <div
                        key={i}
                        className={`agent-icon ${i < bond.owned_count ? 'owned' : ''}`}
                      >
                        🤖
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {bond.is_activated && (
                <div className="activated-badge">已激活</div>
              )}
            </div>
          ))}
        </div>
      )}

      {!loading && filteredBonds.length === 0 && (
        <div className="empty-state">
          <p>暂无{filter === 'activated' ? '已激活' : filter === 'locked' ? '未激活' : ''}羁绊</p>
        </div>
      )}
    </div>
  );
};

export default BondsPage;
