import React, { useState } from 'react';
import { Card, Table, Tag, Button, Space, Input, Select, Modal, Timeline, Progress } from 'antd';
import { PlusOutlined, EyeOutlined, PauseOutlined, PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';

const TaskCenterPage: React.FC = () => {
  const [tasks] = useState([
    { id: 1, title: '深圳南山区100平学区房分析', type: '房产分析', status: '已完成', progress: 100, user: '张三', time: '10分钟前', duration: '2分34秒' },
    { id: 2, title: '北京朝阳区投资价值评估', type: '投资评估', status: '执行中', progress: 65, user: '李四', time: '进行中', duration: '1分12秒' },
    { id: 3, title: '上海浦东新区趋势预测', type: '趋势预测', status: '排队中', progress: 0, user: '王五', time: '排队中', duration: '-' },
    { id: 4, title: '广州天河区政策解读', type: '政策解读', status: '已完成', progress: 100, user: '赵六', time: '15分钟前', duration: '1分45秒' },
    { id: 5, title: '杭州西湖区房价深度分析', type: '房产分析', status: '失败', progress: 45, user: '孙七', time: '20分钟前', duration: '3分21秒' },
    { id: 6, title: '成都高新区综合评估报告', type: '综合评估', status: '已完成', progress: 100, user: '周八', time: '25分钟前', duration: '4分56秒' }
  ]);

  const columns = [
    { title: '任务名称', dataIndex: 'title', key: 'title', ellipsis: true },
    { title: '类型', dataIndex: 'type', key: 'type',
      render: (t: string) => <Tag>{t}</Tag>
    },
    { title: '状态', dataIndex: 'status', key: 'status',
      render: (s: string) => <Tag color={s === '已完成' ? 'green' : s === '执行中' ? 'blue' : s === '排队中' ? 'orange' : s === '失败' ? 'red' : 'default'}>{s}</Tag>
    },
    { title: '进度', dataIndex: 'progress', key: 'progress',
      render: (v: number) => <Progress percent={v} size="small" style={{ width: 80 }} />
    },
    { title: '用户', dataIndex: 'user', key: 'user' },
    { title: '耗时', dataIndex: 'duration', key: 'duration' },
    {
      title: '操作', key: 'action',
      render: (_: any, r: any) => (
        <Space size="small">
          <Button size="small" icon={<EyeOutlined />} />
          {r.status === '执行中' && <Button size="small" icon={<PauseOutlined />} />}
          {r.status === '排队中' && <Button size="small" icon={<PlayCircleOutlined />} />}
          {r.status === '已完成' && <Button size="small" icon={<DownloadOutlined />} />}
        </Space>
      )
    }
  ];

  return (
    <div style={{ padding: 24 }}>
      <Card
        title="任务中心"
        extra={
          <Space>
            <Select defaultValue="all" style={{ width: 120 }} options={[
              { value: 'all', label: '全部状态' }, { value: 'running', label: '执行中' },
              { value: 'completed', label: '已完成' }, { value: 'queued', label: '排队中' }
            ]} />
            <Input.Search placeholder="搜索任务..." style={{ width: 200 }} enterButton />
            <Button type="primary" icon={<PlusOutlined />}>新建任务</Button>
            <Button>批量导入</Button>
          </Space>
        }
      >
        <Table dataSource={tasks} rowKey="id" columns={columns} pagination={{ pageSize: 8 }} />

        <div style={{ marginTop: 16, padding: 16, background: '#f6ffed', borderRadius: 8, border: '1px solid #b7eb8f' }}>
          <strong>DAG任务依赖说明：</strong>
          系统以DAG图（有向无环图）形式展示子任务之间的依赖关系及执行状态，节点颜色表示状态（灰色等待、蓝色执行中、绿色完成、红色失败）。
          鼠标悬停节点可查看任务详情（输入参数、输出结果、耗时）。支持暂停、取消、重试等操作。
        </div>
      </Card>
    </div>
  );
};

export default TaskCenterPage;
