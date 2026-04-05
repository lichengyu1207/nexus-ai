import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';

interface ArticleData {
  title: string;
  slug: string;
  category: string;
  content: string;
  relatedArticles: Array<{
    title: string;
    slug: string;
  }>;
}

const articles: Record<string, ArticleData> = {
  'what-is-plot-ratio': {
    title: '什么是容积率？影响房价的关键因素',
    slug: 'what-is-plot-ratio',
    category: '房产知识',
    content: `
## 什么是容积率？

容积率（Plot Ratio）是指一个小区的总建筑面积与用地面积的比率。它是衡量小区居住舒适度的重要指标之一。

### 容积率计算公式

容积率 = 总建筑面积 ÷ 用地面积

例如：一个小区用地面积为10000平方米，总建筑面积为20000平方米，则容积率为2.0。

## 容积率对居住的影响

### 低容积率的优势
- 居住舒适度高，人口密度低
- 绿化面积大，公共空间充足
- 采光通风条件好

### 高容积率的劣势
- 人口密度大，公共资源紧张
- 停车位不足，电梯拥挤
- 噪音干扰增加

## 不同类型小区的容积率参考

| 小区类型 | 容积率范围 | 特点 |
|---------|-----------|------|
| 别墅 | 0.3-0.5 | 舒适度最高 |
| 多层住宅 | 1.0-1.5 | 居住舒适 |
| 小高层 | 1.5-2.5 | 较为舒适 |
| 高层住宅 | 2.5-4.0 | 密度较高 |
| 超高层 | 4.0+ | 密度很高 |

## 购房建议

在选购房产时，容积率是一个重要参考指标：
1. 追求舒适度：选择容积率在1.5以下的小区
2. 性价比考虑：容积率在2.0-2.5的小区较为常见
3. 投资角度：高容积率小区租金回报率可能更高

建议购房前实地考察，感受小区的实际居住体验。
    `,
    relatedArticles: [
      { title: '得房率怎么算', slug: 'how-to-calculate-efficiency-rate' },
      { title: '购房税费明细', slug: 'purchase-taxes' },
    ],
  },
  'how-to-calculate-efficiency-rate': {
    title: '得房率怎么算？影响实际使用面积',
    slug: 'how-to-calculate-efficiency-rate',
    category: '房产知识',
    content: `
## 什么是得房率？

得房率是指套内建筑面积与套型建筑面积的比率，反映了购房者实际可使用的面积比例。

### 得房率计算公式

得房率 = 套内建筑面积 ÷ 套型建筑面积 × 100%

例如：购买一套100平米的房子，套内实际面积为75平米，则得房率为75%。

## 不同类型住宅的得房率参考

| 住宅类型 | 得房率范围 | 说明 |
|---------|-----------|------|
| 多层住宅 | 80%-85% | 公摊面积少，得房率高 |
| 小高层 | 75%-80% | 有电梯，公摊适中 |
| 高层住宅 | 70%-75% | 公摊面积较大 |
| 超高层 | 65%-70% | 公摊面积最大 |

## 影响得房率的因素

1. 电梯数量和配置
2. 楼梯间设计
3. 公共走廊面积
4. 设备间、管井等
5. 地下室和屋顶层

## 购房建议

- 得房率不是越高越好，需要平衡公摊面积和居住舒适度
- 关注公摊面积的具体构成，避免不合理的公摊
- 实地测量套内面积，核实销售数据
    `,
    relatedArticles: [
      { title: '什么是容积率', slug: 'what-is-plot-ratio' },
      { title: '首付计算器', slug: 'down-payment-calculator' },
    ],
  },
  'loan-process': {
    title: '贷款流程详解 - 从申请到放款全攻略',
    slug: 'loan-process',
    category: '购房指南',
    content: `
## 房贷申请流程

### 第一步：准备材料
1. 身份证、户口本
2. 婚姻证明
3. 收入证明（银行流水、工资单）
4. 购房合同
5. 首付款证明

### 第二步：选择贷款方式
- 公积金贷款：利率低，额度有限
- 商业贷款：利率较高，额度灵活
- 组合贷款：结合两者优势

### 第三步：提交申请
- 银行面签
- 提交材料
- 银行审核

### 第四步：审批放款
- 银行审批：3-7个工作日
- 抵押登记
- 银行放款

## 贷款利率参考

| 贷款类型 | 利率范围 | 说明 |
|---------|-----------|------|
| 公积金贷款 | 3.1% | 利率最低 |
| 商业贷款 | 4.2%-4.9% | 利率较高 |
| 组合贷款 | 混合计算 | 综合成本 |

## 注意事项

1. 保持良好征信记录
2. 提前准备充足材料
3. 了解提前还款规定
4. 关注利率变化
    `,
    relatedArticles: [
      { title: '购房税费明细', slug: 'purchase-taxes' },
      { title: '公积金贷款条件', slug: 'housing-fund-loan' },
    ],
  },
};

const KnowledgePage: React.FC = () => {
  const { slug } = useParams<{ slug: string }>();
  const [article, setArticle] = useState<ArticleData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (slug && articles[slug]) {
      setArticle(articles[slug]);
    }
    setLoading(false);
  }, [slug]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-[50vh]">
        <div className="w-12 h-12 border-4 border-fluent-gold-400 border-t-fluent-gold-500 rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!article) {
    return (
      <div className="max-w-4xl mx-auto py-16 text-center">
        <h1 className="text-2xl font-bold text-fluent-deepOcean-500 mb-4">文章页面开发中</h1>
        <p className="text-fluent-deepOcean-300 mb-6">该文章正在建设中，敬请期待！</p>
        <Link to="/" className="text-fluent-gold-500 hover:text-fluent-gold-600">
          返回首页 →
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <nav className="text-sm text-fluent-deepOcean-300 mb-6">
        <Link to="/" className="hover:text-fluent-gold-500">首页</Link>
        <span className="mx-2">›</span>
        <Link to="/knowledge" className="hover:text-fluent-gold-500">房产知识库</Link>
        <span className="mx-2">›</span>
        <span className="text-fluent-deepOcean-500">{article.title}</span>
      </nav>

      <article className="acrylic rounded-2xl shadow-fluent-lg p-8 border border-white/30">
        <header className="mb-8">
          <span className="inline-block px-3 py-1 bg-fluent-gold-100 text-fluent-gold-700 rounded-full text-sm mb-4">
            {article.category}
          </span>
          <h1 className="text-2xl font-bold text-fluent-deepOcean-500 mb-2">
            {article.title} | 房都督房产知识库
          </h1>
        </header>

        <div className="prose prose-lg max-w-none text-fluent-deepOcean-400">
          <div className="whitespace-pre-line">
            {article.content.split('\n').map((line, index) => (
              <p key={index} className="mb-4">{line}</p>
            ))}
          </div>
        </div>
      </article>

      <div className="mt-8 acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30">
        <h2 className="text-lg font-semibold text-fluent-deepOcean-500 mb-4">相关阅读</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {article.relatedArticles.map((related, index) => (
            <Link
              key={index}
              to={`/knowledge/${related.slug}`}
              className="p-4 bg-fluent-deepOcean-50 rounded-xl hover:bg-fluent-gold-50 transition-colors"
            >
              <p className="font-medium text-fluent-deepOcean-500">{related.title}</p>
            </Link>
          ))}
        </div>
      </div>

      <div className="mt-8 acrylic rounded-2xl shadow-fluent-md p-6 border border-white/30 text-center">
        <h2 className="text-lg font-semibold text-fluent-deepOcean-500 mb-4">
          需要专业的房产分析建议？
        </h2>
        <p className="text-fluent-deepOcean-300 mb-6">
          AI房产顾问为您提供个性化的购房分析和投资建议
        </p>
        <Link
          to="/register"
          className="inline-block bg-gradient-to-r from-fluent-gold-400 to-fluent-gold-600 text-fluent-deepOcean-500 px-8 py-3 rounded-xl font-medium hover:shadow-gold-glow transition-all duration-300"
        >
          免费体验AI分析
        </Link>
      </div>
    </div>
  );
};

export default KnowledgePage;
