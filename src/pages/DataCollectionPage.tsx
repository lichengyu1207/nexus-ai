import React, { useState } from 'react';
import { Card, Table, Button, Tag, Space, Modal, Form, Input, Select, message } from 'antd';
import { PlusOutlined, PlayCircleOutlined, PauseCircleOutlined, SettingOutlined, EyeOutlined } from '@ant-design/icons';

const DataCollectionPage: React.FC = () => {
  const [sources] = useState([
    { id: 1, name: '贝壳研究院', type: '房产平台', status: '采集中', lastUpdate: '2026-04-02 06:00', successRate: 99.2 },
    { id: 2, name: '房天下', type: '房产平台', status: '已暂停', lastUpdate: '2026-04-01 06:00', successRate: 98.5 },
    { id: 3, name: '安居客', type: '房产平台', status: '采集中', lastUpdate: '2026-04-02 06:05', successRate: 97.8 },
    { id: 4, name: '政府开放数据平台', type: '政府数据', status: '采集中', lastUpdate: '2026-04-02 03:00', successRate: 100 },
    { id: 5, name: '统计局公开数据', type: '政府数据', status: '异常', lastUpdate: '2026-03-30 03:00', successRate: 0 },
    { id: 6, name: '土地出让信息', type: '政府数据', status: '采集中', lastUpdate: '2026-04-01 18:00', successRate: 95.3 }
  ]);

  const columns = [
    { title: '数据源名称', dataIndex: 'name', key: 'name' },
    { title: '类型', dataIndex: 'type', key: 'type' },
    {
      title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === '采集中' ? 'green' : s === '已暂停' ? 'orange' : 'red'}>{s}</Tag>
    },
    { title: '最近更新', dataIndex: 'lastUpdate', key: 'lastUpdate' },
    { title: '成功率(%)', dataIndex: 'successRate', key: 'successRate',
      render: (v: number) => <span style={{ color: v > 90 ? '#52c41a' : v > 50 ? '#faad14' : '#ff4d4f' }}>{v}%</span>
    },
    {
      title: '操作', key: 'action',
      render: (_: any, r: any) => (
        <Space>
          <Button size="small" icon={r.status === '采集中' ? <PauseCircleOutlined /> : <PlayCircleOutlined />}
            onClick={() => message.info(`切换${r.name}采集状态`)} />
          <Button size="small" icon={<SettingOutlined />} onClick={() => message.info('配置参数')} />
          <Button size="small" icon={<EyeOutlined />} onClick={() => message.info('查看数据')} />
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="数据源采集任务管理"
        extra={<Button type="primary" icon={<PlusOutlined />}>添加数据源</Button>}
        style={{ marginBottom: 16 }}
      >
        <p style={{ color: '#666', marginBottom: 16 }}>
          平台已接入贝壳研究院、房天下、安居客、政府开放数据平台等主流数据源，覆盖全国337个地级市的房价、成交记录、政策文件、土地出让信息等。数据每日凌晨自动增量更新。
        </p>
        <Table dataSource={sources} rowKey="id" columns={columns} pagination={{ pageSize: 10 }} />
      </Card>

      <Card title="数据质量实时诊断" style={{ marginTop: 16 }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 16 }}>
          {['完整性', '时效性', '准确性'].map((item, i) => (
            <div key={i} style={{ padding: 20, background: '#fafafa', borderRadius: 8, textAlign: 'center' }}>
              <h4>{item}</h4>
              <div style={{ fontSize: 32, fontWeight: 'bold', color: i === 0 ? '#1890ff' : i === 1 ? '#52c41a' : '#faad14' }}>
                {[99.2, 97.5, 98.1][i]}%
              </div>
              <div style={{ fontSize: 12, color: '#888', marginTop: 4 }}>{i === 0 ? '字段缺失率 0.8%' : i === 1 ? '平均延迟 12min' : '异常值占比 1.9%'}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
};

export default DataCollectionPage;
