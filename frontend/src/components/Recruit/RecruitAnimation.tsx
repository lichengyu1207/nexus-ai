import React, { useState, useEffect } from 'react';
import './RecruitAnimation.css';

interface RecruitAnimationProps {
  rarity: string;
  agentName: string;
  department: string;
  skills: Array<{ name: string; description: string }>;
  onComplete: () => void;
  onContinue: () => void;
}

const RARITY_CONFIG: Record<string, { name: string; color: string; glow: string }> = {
  N: { name: '普通', color: '#9e9e9e', glow: '0 0 20px rgba(158, 158, 158, 0.5)' },
  R: { name: '稀有', color: '#3498db', glow: '0 0 30px rgba(52, 152, 219, 0.6)' },
  SR: { name: '史诗', color: '#9b59b6', glow: '0 0 40px rgba(155, 89, 182, 0.7)' },
  SSR: { name: '传说', color: '#f39c12', glow: '0 0 50px rgba(243, 156, 18, 0.8)' },
  UR: { name: '神话', color: '#e74c3c', glow: '0 0 60px rgba(231, 76, 60, 0.9)' },
};

const RecruitAnimation: React.FC<RecruitAnimationProps> = ({
  rarity,
  agentName,
  department,
  skills,
  onComplete,
  onContinue,
}) => {
  const [phase, setPhase] = useState<'summon' | 'reveal' | 'detail'>('summon');
  const [showCard, setShowCard] = useState(false);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; delay: number }>>([]);

  const config = RARITY_CONFIG[rarity] || RARITY_CONFIG.N;

  useEffect(() => {
    const newParticles = Array.from({ length: 20 }, (_, i) => ({
      id: i,
      x: Math.random() * 100,
      y: Math.random() * 100,
      delay: Math.random() * 0.5,
    }));
    setParticles(newParticles);
  }, []);

  useEffect(() => {
    const timer1 = setTimeout(() => {
      setPhase('reveal');
    }, 1500);

    const timer2 = setTimeout(() => {
      setShowCard(true);
    }, 2000);

    const timer3 = setTimeout(() => {
      setPhase('detail');
      onComplete();
    }, 3000);

    return () => {
      clearTimeout(timer1);
      clearTimeout(timer2);
      clearTimeout(timer3);
    };
  }, [onComplete]);

  return (
    <div className="recruit-animation-overlay">
      <div className="recruit-animation-container">
        {phase === 'summon' && (
          <div className="summon-phase">
            <div className="magic-circle" style={{ borderColor: config.color }}>
              <div className="inner-circle" />
              <div className="rune rune-1">智</div>
              <div className="rune rune-2">能</div>
              <div className="rune rune-3">体</div>
              <div className="rune rune-4">召</div>
              <div className="rune rune-5">唤</div>
            </div>
            <div className="summon-text" style={{ color: config.color }}>
              召唤中...
            </div>
            {particles.map((p) => (
              <div
                key={p.id}
                className="particle"
                style={{
                  left: `${p.x}%`,
                  top: `${p.y}%`,
                  animationDelay: `${p.delay}s`,
                  backgroundColor: config.color,
                }}
              />
            ))}
          </div>
        )}

        {(phase === 'reveal' || phase === 'detail') && (
          <div className={`reveal-phase ${showCard ? 'show' : ''}`}>
            <div
              className="agent-card-reveal"
              style={{
                boxShadow: config.glow,
                borderColor: config.color,
              }}
            >
              <div className="rarity-badge" style={{ backgroundColor: config.color }}>
                {config.name}
              </div>
              
              <div className="card-header">
                <div className="agent-avatar" style={{ borderColor: config.color }}>
                  <span className="avatar-icon">🤖</span>
                </div>
                <h2 className="agent-name">{agentName}</h2>
                <p className="agent-department">{department}</p>
              </div>

              <div className="card-body">
                <div className="skills-section">
                  <h4>技能</h4>
                  <div className="skills-list">
                    {skills.map((skill, index) => (
                      <div key={index} className="skill-item">
                        <span className="skill-name">{skill.name}</span>
                        <span className="skill-desc">{skill.description}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {phase === 'detail' && (
                <div className="card-actions">
                  <button className="btn-continue" onClick={onContinue}>
                    继续招募
                  </button>
                  <button className="btn-detail" onClick={() => {}}>
                    查看详情
                  </button>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default RecruitAnimation;
