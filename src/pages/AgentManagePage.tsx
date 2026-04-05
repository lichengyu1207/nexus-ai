import React, { useState } from 'react';
import { Card, Table, Tag, Button, Space, Avatar, Progress, Badge, Modal } from 'antd';
import {
  ReloadOutlined, SettingOutlined, ToolOutlined,
  RocketOutlined, CheckCircleOutlined, WarningOutlined
} from '@ant-design/icons';

const AgentManagePage: React.FC = () => {
  const [agents] = useState([
    { id: 1, name: '中书省', role: '任务拆解', status: '健康', health: 98, cpu: 45, memory: 62, tasks: 156, lastHeartbeat: '刚刚' },
    { id: 2, name: '门下省', role: '合规审核', status: '健康', health: 95, cpu: 38, memory: 45, tasks: 89, lastHeartbeat: '1分钟前' },
    { id: 3, name: '尚书省', role: '资源调度', status: '健康', health: 99, cpu: 62, memory: 78, tasks: 234, lastHeartbeat: '刚刚' },
    { id: 4, name: '礼部', role: '智能交互', status: '健康', health: 97, cpu: 35, memory: 52, tasks: 567, lastHeartbeat: '30秒前' },
    { id: 5, name: '户部', role: '数据采集', status: '健康', health: 96, cpu: 55, memory: 68, tasks: 445, lastHeartbeat: '刚刚' },
    { id: 6, name: '兵部', role: '风险预警', status: '降级', health: 78, cpu: 88, memory: 92, tasks: 34, lastHeartbeat: '5分钟前' },
    { id: 7, name: '刑部', role: '合规审计', status: '健康', health: 94, cpu: 25, memory: 38, tasks: 67, lastHeartbeat: '2分钟前' },
    { id: 8, name: '吏部', role: '智能体管理', status: '健康', health: 99, cpu: 20, memory: 32, tasks: 12, lastHeartbeat: '刚刚' },
    { id: 9, name: '工部', role: '报告生成', status: '健康', health: 96, cpu: 48, memory: 58, tasks: 312, lastHeartbeat: '1分钟前' }
  ]);

  const columns = [
    {
      title: '智能体', key: 'agent',
      render: (_: any, r: any) => (
        <Space>
          <Avatar size="small" style={{ background: r.health > 90 ? '#52c41a' : r.health > 70 ? '#faad14' : '#ff4d4f' }}>{r.name[0]}</Avatar>
          <div>
            <strong>{r.name}</strong><br /><span style={{ fontSize: 11, color: '#888' }}>{r.role}</span>
          </div>
        </Space>
      )
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Badge status={s === '健康' ? 'success' : 'warning'} text={s} />
    },
    { title: '健康度', dataIndex: 'health', key: 'health',
      render: (v: number) => <Progress percent={v} size="small" style={{ width: 80 }} />
    },
    { title: 'CPU(%)', dataIndex: 'cpu', key: 'cpu',
      render: (v: number) => <Progress percent={v} size="small" status={v > 70 ? 'exception' : 'active'} style={{ width: 60 }} />
    },
    { title: '内存(%)', dataIndex: 'memory', key: 'memory',
      render: (v: number) => <Progress percent={v} size="small" status={v > 80 ? 'exception' : 'active'} style={{ width: 60 }} />
    },
    { title: '任务数', dataIndex: 'tasks', key: 'tasks' },
    { title: '最后心跳', dataIndex: 'lastHeartbeat', key: 'lastHeartbeat' },
    {
      title: '操作', key: 'action',
      render: () => (
        <Space size="small">
          <Button size="small" icon={<ReloadOutlined />} />
          <Button size="small" icon={<SettingOutlined />} />
          <Button size="small" icon={<ToolOutlined />} />
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="三省六部智能体管理"
        extra={<Space><Button>工具权限配置</Button><Button type="primary">升级与羁绊</Button></Space>}
      >
        <p style={{ color: '#666', marginBottom: 16 }}>
          智能体通过完成任务自动积累经验值，达到阈值后自动升级；系统根据用户已拥有的智能体推荐可激活的羁绊，在任务调度时自动应用协同效果。
        </p>
        <Table dataSource={agents} rowKey="id" columns={columns} pagination={{ pageSize: 10 }} />
      </Card>

      <Card title="MCP工具库" style={{ marginTop: 16 }}>
        <Table
          dataSource={[
            { name: '房价数据查询API', calls: 12345, status: '正常' },
            { name: '地图地理编码服务', calls: 8765, status: '正常' },
            { name: '政策文件解析器', calls: 5432, status: '正常' },
            { name: 'LLM大模型接口', calls: 67890, status: '正常' },
            { name: '向量检索引擎', calls: 34567, status: '降级' }
          ]}
          pagination={false}
          size="small"
          columns={[
            { title: '工具名称', dataIndex: 'name', key: 'name' },
            { title: '调用次数', dataIndex: 'calls', key: 'calls' },
            { title: '状态', dataIndex: 'status', key: 'status',
              render: (s: string) => <Tag color={s === '正常' ? 'green' : 'orange'}>{s}</Tag>
            }
          ]}
        />
      </Card>
    </div>
  );
};

export default AgentManagePage;
