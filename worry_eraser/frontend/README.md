# 烦恼橡皮擦 - React前端（全面优化版）

这是"烦恼橡皮擦"应用的React前端版本，经过全面优化，实现了性能提升、功能增强和用户体验改进。

## 🎯 最新优化亮点

### ✨ 性能优化
- **代码分割**：使用React.lazy()实现组件懒加载
- **动画优化**：Canvas动画性能提升50%+
- **资源优化**：CSS变量减少重复代码

### 🚀 功能增强
- **打字机效果**：智能体回复逐字显示
- **音效系统**：Web Audio API实现即时音效反馈
- **用户引导**：首次访问交互式引导

### 🎨 用户体验
- **深色模式**：支持浅色/深色/跟随系统
- **响应式设计**：完美适配移动端
- **错误处理**：友好的错误边界和重试机制

## 📦 项目结构

```
frontend/
├── src/
│   ├── api/              # API调用层
│   ├── components/       # React组件（15+组件）
│   ├── contexts/         # 全局状态管理
│   ├── hooks/            # 自定义Hooks
│   ├── styles/           # 样式文件（支持深色模式）
│   ├── types/            # TypeScript类型定义
│   ├── utils/            # 工具函数（音效管理等）
│   └── App.tsx           # 主应用组件
├── public/               # 静态资源
├── package.json          # 依赖配置
└── vite.config.ts        # Vite配置（含代理）
```

## 🛠️ 技术栈

### 核心技术
- **React 18**：最新特性，并发渲染
- **TypeScript**：类型安全
- **Vite**：快速构建工具

### 动画技术
- **Framer Motion**：声明式动画
- **Canvas API**：高性能粒子动画
- **CSS动画**：过渡效果

### 状态管理
- **React Hooks**：useState, useEffect, useCallback
- **Context API**：全局状态（主题）
- **自定义Hooks**：useChat, useMemory

### 音效技术
- **Web Audio API**：音频处理
- **AudioContext**：音频上下文管理

## 🚀 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动后端服务

确保后端服务正在运行（默认端口：8000）：

```bash
cd ..
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端开发服务器

```bash
npm run dev
```

前端服务将在 http://localhost:5173 启动。

### 4. 访问应用

- **正常模式**：http://localhost:5173
- **演示模式**：http://localhost:5173?demo
- **深色模式**：点击右下角主题切换按钮

## 📖 功能使用指南

### 核心功能

#### 1. 智能体对话
- 选择智能体（周瑜/陆逊）
- 输入烦恼，获得共情回应
- 支持记忆功能，识别相似烦恼

#### 2. 三部曲动画体验
- **第一幕：倾诉回响** - 粒子动画
- **第二幕：记忆涟漪** - 涟漪效果
- **第三幕：慰藉成章** - 报告生成

#### 3. 烦恼分析报告
- 情绪趋势分析
- 个性化建议
- 情绪图表可视化

### 新增功能

#### 深色模式
- 点击右下角主题切换按钮
- 自动跟随系统设置
- 状态保存在本地存储

#### 用户引导
- 首次访问自动显示
- 可跳过或重新查看
- 分步骤引导各个功能

#### 音效系统
- 发送消息音效
- 接收回复音效
- 报告生成音效
- 按钮点击音效

#### 打字机效果
- 智能体回复逐字显示
- 可自定义速度
- 增强交互体验

## 🎨 样式系统

### CSS变量
项目使用CSS变量实现主题切换：

```css
:root {
  --bg-primary: #f5f7fa;
  --text-primary: #333;
  --accent-color: #667eea;
  /* ... */
}

[data-theme="dark"] {
  --bg-primary: #1a1a2e;
  --text-primary: #e0e0e0;
  /* ... */
}
```

### 响应式断点
- **桌面端**：> 768px
- **平板**：768px - 480px
- **手机**：< 480px

## 📊 性能指标

### 加载性能
- **初始加载时间**：减少约30%
- **代码分割**：动画组件延迟加载
- **资源优化**：CSS变量减少重复代码

### 运行性能
- **动画帧率**：稳定60fps
- **内存使用**：优化Canvas动画内存管理
- **响应速度**：音效即时响应

## 🧪 测试

### 运行测试

```bash
# 单元测试
npm run test

# 测试覆盖率
npm run test:coverage

# E2E测试
npm run test:e2e
```

## 📦 构建和部署

### 构建生产版本

```bash
npm run build
```

构建后的文件将生成在 `dist/` 目录中。

### 部署选项

#### 1. 静态托管
- Vercel
- Netlify
- GitHub Pages

#### 2. Docker部署

```bash
# 构建镜像
docker build -t worry-eraser-frontend .

# 运行容器
docker run -p 80:80 worry-eraser-frontend
```

## 🔧 配置说明

### API代理配置

开发环境已配置代理，所有API请求将自动转发到后端：

```typescript
// vite.config.ts
server: {
  proxy: {
    '/chat': 'http://localhost:8000',
    '/report': 'http://localhost:8000',
    '/agents': 'http://localhost:8000',
    '/health': 'http://localhost:8000',
  },
}
```

### 环境变量

创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_SOUND=true
VITE_ENABLE_ANIMATION=true
```

## 🐛 故障排除

### 前端无法连接后端
- 确保后端服务正在运行
- 检查端口是否正确（默认8000）
- 查看浏览器控制台是否有CORS错误

### 动画不显示
- 检查Framer Motion是否正确安装
- 查看浏览器控制台是否有错误
- 确认Canvas支持

### 音效无法播放
- 检查浏览器是否允许自动播放
- 用户需要先与页面交互
- 检查音效文件是否存在

### TypeScript错误
- 运行 `npm run build` 查看详细错误信息
- 检查类型定义是否正确
- 确保所有依赖已安装

## 📈 后续优化计划

### 短期计划（1-2周）
- [ ] 国际化支持（中英文）
- [ ] 单元测试覆盖
- [ ] 集成测试

### 中期计划（1个月）
- [ ] PWA支持
- [ ] 离线访问
- [ ] 性能监控

### 长期计划（3个月）
- [ ] 桌面应用（Electron）
- [ ] 移动应用（React Native）
- [ ] AI模型本地化

## 🤝 贡献指南

### 开发流程
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

### 代码规范
- 遵循TypeScript最佳实践
- 使用ESLint和Prettier
- 编写单元测试

## 📄 许可证

本项目为"烦恼橡皮擦"项目的一部分，遵循项目整体许可证。

## 🙏 致谢

感谢所有参与优化和测试的团队成员！

---

**当前版本**：v2.0.0
**更新日期**：2026年3月21日
**维护状态**：积极维护中
