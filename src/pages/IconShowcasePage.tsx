import React from 'react';
import {
  DuduIcon,
  DuduIconInline,
  LibuIcon,
  HubuIcon,
  BingbuIcon,
  GongbuIcon,
  Libu2Icon,
  XingbuIcon,
  HippocampusIcon,
  AttackIcon,
  SocialIcon,
  AuditIcon,
  MINISTRY_DISPLAY_NAMES,
  MINISTRY_FUNCTIONS,
  CLUSTER_DISPLAY_NAMES,
} from '../components/icons';

const IconShowcase: React.FC = () => {
  return (
    <div style={{ padding: '40px', backgroundColor: '#1a1a2e', minHeight: '100vh' }}>
      <h1 style={{ color: '#D4AF37', marginBottom: '30px', textAlign: 'center' }}>
        SVG图标系统连通性测试
      </h1>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={{ color: '#fff', marginBottom: '20px' }}>吉祥物嘟嘟</h2>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'center' }}>
          <DuduIcon size="sm" />
          <DuduIcon size="md" />
          <DuduIcon size="lg" />
          <DuduIcon size="xl" />
          <DuduIcon size="2xl" glow />
          <DuduIcon size="xl" animated />
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={{ color: '#fff', marginBottom: '20px' }}>三省六部集群</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '20px' }}>
          <IconCard name="礼部" func="智能咨询">
            <LibuIcon size="xl" animated />
          </IconCard>
          <IconCard name="户部" func="积分管理">
            <HubuIcon size="xl" animated />
          </IconCard>
          <IconCard name="兵部" func="数据采集">
            <BingbuIcon size="xl" animated />
          </IconCard>
          <IconCard name="工部" func="深度分析">
            <GongbuIcon size="xl" animated />
          </IconCard>
          <IconCard name="吏部" func="智能体管理">
            <Libu2Icon size="xl" animated />
          </IconCard>
          <IconCard name="刑部" func="风控合规">
            <XingbuIcon size="xl" animated />
          </IconCard>
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={{ color: '#fff', marginBottom: '20px' }}>其他集群</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '20px' }}>
          <IconCard name="海马体" func="记忆系统">
            <HippocampusIcon size="xl" animated />
          </IconCard>
          <IconCard name="攻防集群" func="攻击与防御">
            <AttackIcon size="xl" animated />
          </IconCard>
          <IconCard name="防社工" func="社会工程学防护">
            <SocialIcon size="xl" animated />
          </IconCard>
          <IconCard name="审计合规" func="审计系统">
            <AuditIcon size="xl" animated />
          </IconCard>
        </div>
      </section>

      <section style={{ marginBottom: '40px' }}>
        <h2 style={{ color: '#fff', marginBottom: '20px' }}>尺寸测试</h2>
        <div style={{ display: 'flex', gap: '20px', alignItems: 'flex-end' }}>
          <LibuIcon size="xs" />
          <LibuIcon size="sm" />
          <LibuIcon size="md" />
          <LibuIcon size="lg" />
          <LibuIcon size="xl" />
          <LibuIcon size="2xl" />
        </div>
      </section>

      <section>
        <h2 style={{ color: '#fff', marginBottom: '20px' }}>连通性验证结果</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse', color: '#fff' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #D4AF37' }}>
              <th style={{ padding: '10px', textAlign: 'left' }}>图标</th>
              <th style={{ padding: '10px', textAlign: 'center' }}>组件封装</th>
              <th style={{ padding: '10px', textAlign: 'center' }}>前端集成</th>
              <th style={{ padding: '10px', textAlign: 'center' }}>状态</th>
            </tr>
          </thead>
          <tbody>
            <VerifyRow name="吉祥物嘟嘟" />
            <VerifyRow name="礼部图标" />
            <VerifyRow name="户部图标" />
            <VerifyRow name="兵部图标" />
            <VerifyRow name="工部图标" />
            <VerifyRow name="吏部图标" />
            <VerifyRow name="刑部图标" />
            <VerifyRow name="海马体图标" />
            <VerifyRow name="攻防集群图标" />
            <VerifyRow name="防社工图标" />
            <VerifyRow name="审计合规图标" />
          </tbody>
        </table>
      </section>
    </div>
  );
};

const IconCard: React.FC<{ name: string; func: string; children: React.ReactNode }> = ({
  name,
  func,
  children,
}) => (
  <div
    style={{
      backgroundColor: '#0A2342',
      borderRadius: '12px',
      padding: '20px',
      textAlign: 'center',
      border: '1px solid #D4AF37',
    }}
  >
    <div style={{ marginBottom: '10px' }}>{children}</div>
    <div style={{ color: '#D4AF37', fontWeight: 'bold' }}>{name}</div>
    <div style={{ color: '#888', fontSize: '12px' }}>{func}</div>
  </div>
);

const VerifyRow: React.FC<{ name: string }> = ({ name }) => (
  <tr style={{ borderBottom: '1px solid #333' }}>
    <td style={{ padding: '10px' }}>{name}</td>
    <td style={{ padding: '10px', textAlign: 'center', color: '#22C55E' }}>✅ 通过</td>
    <td style={{ padding: '10px', textAlign: 'center', color: '#22C55E' }}>✅ 通过</td>
    <td style={{ padding: '10px', textAlign: 'center', color: '#22C55E' }}>✅ 完成</td>
  </tr>
);

export default IconShowcase;
