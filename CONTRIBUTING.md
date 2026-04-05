# 贡献指南

感谢您考虑为房都督AI项目做出贡献！

## 目录

- [行为准则](#行为准则)
- [如何贡献](#如何贡献)
- [开发环境设置](#开发环境设置)
- [代码规范](#代码规范)
- [提交规范](#提交规范)
- [Pull Request 流程](#pull-request-流程)

---

## 行为准则

### 我们的承诺

为了营造开放和友好的环境，我们承诺：

- 尊重不同的观点和经验
- 优雅地接受建设性批评
- 关注对社区最有利的事情
- 对其他社区成员表示同理心

### 不可接受的行为

- 使用性化的语言或图像
- 捣乱、侮辱/贬损评论
- 公开或私下的骚扰
- 未经许可发布他人的私人信息
- 其他不道德或不专业的行为

---

## 如何贡献

### 报告Bug

如果您发现了bug，请创建Issue并包含：

1. **描述**: 清晰描述问题
2. **复现步骤**: 如何复现该问题
3. **预期行为**: 您期望发生什么
4. **实际行为**: 实际发生了什么
5. **环境**: 操作系统、浏览器版本等
6. **截图**: 如果适用，添加截图

### 建议新功能

我们欢迎新功能建议！请创建Issue并包含：

1. **功能描述**: 详细描述您想要的功能
2. **使用场景**: 这个功能解决什么问题
3. **替代方案**: 您考虑过的其他解决方案

### 提交代码

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'feat: add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建 Pull Request

---

## 开发环境设置

### 前置要求

- Python 3.10+
- Node.js 18+
- SQLite 3

### 后端设置

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
.\venv\Scripts\activate  # Windows

# 安装依赖
cd backend
pip install -r requirements.txt

# 运行开发服务器
uvicorn main:app --reload --port 8000
```

### 前端设置

```bash
# 安装依赖
npm install

# 运行开发服务器
npm run dev
```

### 环境变量

创建 `.env` 文件：

```env
# 后端
SECRET_KEY=your-secret-key
DATABASE_URL=sqlite:///./data/app.db

# 前端
VITE_API_URL=http://localhost:8000
```

---

## 代码规范

### Python 代码规范

- 遵循 PEP 8 规范
- 使用 `black` 格式化代码
- 使用 `isort` 排序导入
- 使用类型注解
- 编写 docstring

```python
def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """
    通过ID获取用户
    
    Args:
        user_id: 用户ID
        
    Returns:
        用户信息字典，如果不存在返回None
    """
    # 实现...
```

### TypeScript 代码规范

- 遵循 ESLint 规则
- 使用 Prettier 格式化
- 使用函数组件和 Hooks
- 使用 TypeScript 类型

```typescript
interface User {
  id: string;
  email: string;
  full_name: string | null;
}

const UserProfile: React.FC<{ user: User }> = ({ user }) => {
  // 实现...
};
```

### 文件命名

- Python: `snake_case.py`
- React组件: `PascalCase.tsx`
- 工具函数: `camelCase.ts`
- 样式文件: `kebab-case.css`

---

## 提交规范

我们使用 [Conventional Commits](https://www.conventionalcommits.org/) 规范：

### 提交格式

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 类型 (type)

| 类型 | 描述 |
|------|------|
| feat | 新功能 |
| fix | Bug修复 |
| docs | 文档更新 |
| style | 代码格式（不影响功能） |
| refactor | 重构 |
| perf | 性能优化 |
| test | 测试相关 |
| chore | 构建/工具相关 |

### 示例

```
feat(tasks): add task export feature

- Add PDF export for reports
- Add CSV export for task data
- Add export progress indicator

Closes #123
```

---

## Pull Request 流程

### PR 检查清单

- [ ] 代码遵循项目规范
- [ ] 已添加必要的测试
- [ ] 文档已更新
- [ ] 提交信息符合规范
- [ ] 所有测试通过

### PR 标题格式

使用与提交信息相同的格式：

```
feat(tasks): add task export feature
```

### PR 描述模板

```markdown
## 变更类型
- [ ] Bug修复
- [ ] 新功能
- [ ] 重构
- [ ] 文档更新

## 描述
简要描述您的更改

## 相关Issue
Closes #

## 测试
描述如何测试这些更改

## 截图
如有UI更改，添加截图
```

### 代码审查

所有PR需要至少一位维护者审查后才能合并。我们会尽快处理您的PR。

---

## 开发提示

### 调试

**后端调试**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

**前端调试**:
使用 React DevTools 和浏览器开发者工具

### 测试

**后端测试**:
```bash
pytest tests/ -v
```

**前端测试**:
```bash
npm run test
```

### 常见问题

**Q: 数据库迁移失败？**
A: 删除 `data/app.db` 并重新启动服务器

**Q: 前端无法连接后端？**
A: 检查后端是否运行在 8000 端口

---

## 获取帮助

- 创建 Issue
- 发送邮件至 dev@example.com
- 加入开发者群组

感谢您的贡献！
