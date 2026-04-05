import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import {
  ArrowLeftIcon,
  BookOpenIcon,
  ClockIcon,
  UserIcon,
  ShareIcon,
  HandThumbUpIcon,
} from '@heroicons/react/24/outline';

interface Tutorial {
  id: string;
  title: string;
  description: string;
  content: string;
  author: string;
  readTime: number;
  category: string;
  createdAt: string;
  videoUrl?: string;
}

const tutorials: Tutorial[] = [
  {
    id: 'create-analysis-task',
    title: '如何创建房产分析任务',
    description: '学习如何创建新的房产分析任务，设置分析参数，选择AI模型，并生成专业的分析报告。',
    author: '房都督AI团队',
    readTime: 5,
    category: '入门指南',
    createdAt: '2024-01-15',
    content: `
# 如何创建房产分析任务

本教程将指导您如何使用房都督AI创建房产分析任务，并生成专业的分析报告。

## 步骤一：登录账号

首先，您需要登录房都督AI账号。如果您还没有账号，请先注册。

## 步骤二：进入分析页面

登录后，点击顶部导航栏的"房产分析"按钮，进入分析页面。

## 步骤三：输入房产信息

在分析页面，您可以：

1. **输入房产地址**：在搜索框中输入房产地址，系统会自动定位
2. **选择区域**：在地图上选择目标区域
3. **设置分析参数**：选择分析类型、AI模型等

## 步骤四：选择AI模型

房都督AI提供多种AI模型供您选择：

- **市场分析模型**：分析市场趋势和价格走势
- **投资建议模型**：提供投资建议和风险评估
- **综合分析模型**：综合多种因素进行全面分析

## 步骤五：生成报告

点击"开始分析"按钮，系统将自动生成分析报告。报告包含：

- 房产基本信息
- 市场价格评估
- 周边配套分析
- 投资建议

## 步骤六：查看和导出报告

分析完成后，您可以：

- 在线查看报告
- 导出PDF格式
- 分享给团队成员

## 注意事项

1. 确保输入的地址准确无误
2. 选择合适的AI模型以获得最佳结果
3. 专业版用户可以导出报告

## 常见问题

**Q: 分析需要多长时间？**
A: 通常需要1-3分钟，具体时间取决于分析复杂度。

**Q: 可以同时创建多个任务吗？**
A: 是的，您可以同时创建多个分析任务。

---

如果您有任何问题，请随时联系我们的客服团队。
    `,
    videoUrl: 'https://www.youtube.com/embed/dQw4w9WgXcQ',
  },
  {
    id: 'read-analysis-report',
    title: '如何解读分析报告',
    description: '了解报告中的各项指标含义，包括价格评估、市场趋势、投资建议等，帮助您做出更明智的决策。',
    author: '房都督AI团队',
    readTime: 8,
    category: '进阶教程',
    createdAt: '2024-01-20',
    content: `
# 如何解读分析报告

本教程将帮助您理解房都督AI生成的分析报告中的各项指标。

## 报告结构

分析报告通常包含以下几个部分：

### 1. 房产基本信息

包括房产地址、面积、户型、建筑年代等基本信息。

### 2. 价格评估

- **市场参考价**：基于市场数据的参考价格
- **价格区间**：价格的可能波动范围
- **价格趋势**：近期价格变化趋势

### 3. 市场分析

- **供需关系**：当前市场的供需状况
- **成交数据**：近期成交案例
- **价格走势**：历史价格变化

### 4. 周边配套

- **交通**：地铁、公交等交通设施
- **教育**：学校、幼儿园等教育资源
- **医疗**：医院、诊所等医疗设施
- **商业**：商场、超市等商业设施

### 5. 投资建议

- **投资评级**：综合投资价值评估
- **风险提示**：潜在风险因素
- **建议策略**：投资策略建议

## 指标解读

### 价格评估指标

| 指标 | 含义 | 参考范围 |
|------|------|----------|
| 市场参考价 | 基于市场数据的预估价格 | - |
| 价格偏离度 | 实际价格与参考价的偏差 | ±10% |
| 价格趋势 | 价格变化方向 | 上升/平稳/下降 |

### 市场分析指标

| 指标 | 含义 | 参考范围 |
|------|------|----------|
| 供需指数 | 市场供需平衡度 | 0.8-1.2 |
| 成交周期 | 平均成交时间 | 30-90天 |
| 价格波动率 | 价格波动程度 | <15% |

## 使用建议

1. 综合考虑各项指标，不要只看单一数据
2. 关注价格趋势和风险提示
3. 结合实地考察做出最终决策

---

如有疑问，请联系客服团队。
    `,
  },
  {
    id: 'data-visualization',
    title: '如何使用数据可视化',
    description: '掌握平台提供的各种图表和可视化工具，快速理解复杂数据，支持多种图表类型和交互式数据探索。',
    author: '房都督AI团队',
    readTime: 6,
    category: '进阶教程',
    createdAt: '2024-01-25',
    content: `
# 如何使用数据可视化

房都督AI提供丰富的数据可视化功能，帮助您直观理解复杂数据。

## 图表类型

### 1. 折线图

用于展示价格趋势、市场变化等时间序列数据。

**使用场景**：
- 价格走势分析
- 市场趋势预测
- 历史数据对比

### 2. 柱状图

用于展示分类数据对比。

**使用场景**：
- 区域价格对比
- 成交量分析
- 配套设施统计

### 3. 饼图

用于展示占比关系。

**使用场景**：
- 户型分布
- 价格区间占比
- 用户画像分析

### 4. 地图可视化

用于展示地理分布数据。

**使用场景**：
- 区域价格分布
- 周边配套展示
- 交通便利度分析

## 交互功能

### 缩放和拖拽

- 鼠标滚轮：缩放图表
- 拖拽：移动视图

### 数据筛选

- 点击图例：显示/隐藏数据系列
- 拖拽滑块：筛选时间范围

### 数据导出

- 右键菜单：导出图片
- 工具栏：导出数据

## 高级功能

### 自定义图表

1. 点击"自定义"按钮
2. 选择图表类型
3. 设置数据源
4. 调整样式

### 图表组合

1. 添加多个图表
2. 设置布局
3. 保存为模板

---

如有疑问，请联系客服团队。
    `,
  },
  {
    id: 'team-collaboration',
    title: '如何进行团队协作',
    description: '学习如何邀请团队成员，共享分析结果，管理权限，实现高效的团队协作工作流。',
    author: '房都督AI团队',
    readTime: 7,
    category: '团队功能',
    createdAt: '2024-02-01',
    content: `
# 如何进行团队协作

房都督AI支持团队协作功能，帮助您与团队成员高效协同工作。

## 创建团队

### 步骤一：进入团队管理

点击顶部导航栏的"团队"按钮，进入团队管理页面。

### 步骤二：创建新团队

1. 点击"创建团队"按钮
2. 输入团队名称和描述
3. 选择团队类型（个人/企业）
4. 点击"创建"完成

## 邀请成员

### 通过邮件邀请

1. 在团队页面点击"邀请成员"
2. 输入成员邮箱地址
3. 选择角色（管理员/成员/访客）
4. 发送邀请

### 通过链接邀请

1. 生成邀请链接
2. 分享链接给成员
3. 成员点击链接加入

## 权限管理

### 角色权限

| 角色 | 权限 |
|------|------|
| 管理员 | 全部权限 |
| 成员 | 查看、编辑、评论 |
| 访客 | 仅查看 |

### 设置权限

1. 进入团队设置
2. 点击"权限管理"
3. 选择成员
4. 调整权限

## 共享分析结果

### 共享报告

1. 打开分析报告
2. 点击"共享"按钮
3. 选择共享对象
4. 设置权限

### 共享任务

1. 在任务列表选择任务
2. 点击"共享"
3. 选择团队成员

## 协作功能

### 评论和标注

- 在报告中添加评论
- 标注重要信息
- @提及团队成员

### 版本历史

- 查看修改历史
- 恢复历史版本
- 对比版本差异

---

如有疑问，请联系客服团队。
    `,
  },
];

const TutorialDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [tutorial, setTutorial] = useState<Tutorial | null>(null);
  const [liked, setLiked] = useState(false);

  useEffect(() => {
    const found = tutorials.find(t => t.id === id);
    setTutorial(found || null);
  }, [id]);

  if (!tutorial) {
    return (
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <BookOpenIcon className="w-16 h-16 mx-auto text-gray-300 mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
            教程未找到
          </h2>
          <p className="text-gray-500 dark:text-gray-400 mb-4">
            该教程可能已被删除或不存在
          </p>
          <Link
            to="/help"
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
          >
            <ArrowLeftIcon className="w-4 h-4" />
            返回帮助中心
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12"
      >
        <Link
          to="/help"
          className="inline-flex items-center gap-2 text-gray-500 dark:text-gray-400 hover:text-primary-600 mb-8"
        >
          <ArrowLeftIcon className="w-4 h-4" />
          返回帮助中心
        </Link>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="bg-white dark:bg-gray-800 rounded-xl shadow-lg overflow-hidden">
            <div className="p-8 border-b border-gray-200 dark:border-gray-700">
              <div className="flex items-center gap-2 text-sm text-primary-600 dark:text-primary-400 mb-4">
                <span className="px-3 py-1 bg-primary-50 dark:bg-primary-900/20 rounded-full">
                  {tutorial.category}
                </span>
              </div>
              
              <h1 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                {tutorial.title}
              </h1>
              
              <p className="text-lg text-gray-600 dark:text-gray-400 mb-6">
                {tutorial.description}
              </p>
              
              <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                <div className="flex items-center gap-2">
                  <UserIcon className="w-4 h-4" />
                  <span>{tutorial.author}</span>
                </div>
                <div className="flex items-center gap-2">
                  <ClockIcon className="w-4 h-4" />
                  <span>{tutorial.readTime} 分钟阅读</span>
                </div>
                <div className="flex items-center gap-2">
                  <BookOpenIcon className="w-4 h-4" />
                  <span>{tutorial.createdAt}</span>
                </div>
              </div>
            </div>

            {tutorial.videoUrl && (
              <div className="p-8 border-b border-gray-200 dark:border-gray-700">
                <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
                  视频教程
                </h2>
                <div className="aspect-video rounded-lg overflow-hidden">
                  <iframe
                    src={tutorial.videoUrl}
                    title={tutorial.title}
                    className="w-full h-full"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                    allowFullScreen
                  />
                </div>
              </div>
            )}

            <div className="p-8 prose dark:prose-invert max-w-none">
              <ReactMarkdown>{tutorial.content}</ReactMarkdown>
            </div>

            <div className="p-8 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-700/50">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => setLiked(!liked)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                      liked
                        ? 'bg-primary-50 text-primary-600'
                        : 'bg-white dark:bg-gray-600 text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-500'
                    }`}
                  >
                    <ThumbUpIcon className="w-5 h-5" />
                    <span>{liked ? '已点赞' : '点赞'}</span>
                  </button>
                  <button className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-600 text-gray-600 dark:text-gray-300 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-500 transition-colors">
                    <ShareIcon className="w-5 h-5" />
                    <span>分享</span>
                  </button>
                </div>
                <Link
                  to="/feedback"
                  className="text-primary-600 hover:text-primary-700 font-medium"
                >
                  有问题？提交反馈
                </Link>
              </div>
            </div>
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.4 }}
          className="mt-8"
        >
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            相关教程
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {tutorials
              .filter(t => t.id !== tutorial.id && t.category === tutorial.category)
              .slice(0, 2)
              .map(related => (
                <Link
                  key={related.id}
                  to={`/help/tutorials/${related.id}`}
                  className="bg-white dark:bg-gray-800 rounded-xl shadow-md p-6 hover:shadow-lg transition-shadow"
                >
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                    {related.title}
                  </h3>
                  <p className="text-sm text-gray-500 dark:text-gray-400 line-clamp-2">
                    {related.description}
                  </p>
                  <div className="flex items-center gap-2 mt-4 text-sm text-gray-400">
                    <ClockIcon className="w-4 h-4" />
                    <span>{related.readTime} 分钟</span>
                  </div>
                </Link>
              ))}
          </div>
        </motion.div>
      </motion.div>
    </div>
  );
};

export default TutorialDetailPage;
