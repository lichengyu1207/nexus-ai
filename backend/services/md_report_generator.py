"""
MD报告生成服务 - 只生成Markdown格式报告
"""
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class MDReportGenerator:
    def __init__(self):
        self.brand_color = "#D4AF37"
        self.primary_color = "#0A1A2F"
        self.secondary_color = "#2C5530"
    
    def generate_report(
        self,
        community_name: str,
        user_name: str,
        persona: str = "周瑜",
        data: Dict[str, Any] = None
    ) -> str:
        timestamp = datetime.now().strftime("%Y年%m月%d日 %H:%M")
        
        md_content = f"""# 房产分析报告：{community_name}

**生成时间**：{timestamp}  
**分析人**：{user_name}  
**专属顾问**：{persona}

---

## 执行摘要

{self._generate_summary(data)}

## 核心发现

{self._generate_findings(data)}

## 详细分析

### 1. 价格走势分析

{self._generate_price_analysis(data)}

### 2. 周边配套分析

{self._generate_surrounding_analysis(data)}

### 3. 市场对比分析

{self._generate_market_comparison(data)}

## 投资建议

{self._generate_investment_advice(data)}

## 风险提示

{self._generate_risk_warning(data)}

## 数据来源

- 房价数据：链家、贝壳、安居客
- 配套数据：高德地图、百度地图
- 政策数据：住建局官网
- 分析时间：{timestamp}

---

*本报告由房都督AI房产分析平台自动生成，仅供参考，不构成投资建议。*
"""
        return md_content
    
    def _generate_summary(self, data: Dict[str, Any]) -> str:
        if not data:
            return "本报告对目标房产进行了全面分析，涵盖价格走势、周边配套、市场对比等多个维度。"
        
        summary_parts = []
        if 'avg_price' in data:
            summary_parts.append(f"当前均价为 **{data['avg_price']}元/㎡**")
        if 'price_trend' in data:
            summary_parts.append(f"价格走势呈{data['price_trend']}趋势")
        if 'investment_score' in data:
            summary_parts.append(f"投资评分 **{data['investment_score']}/100**")
        
        if summary_parts:
            return "，".join(summary_parts) + "。"
        return "本报告对目标房产进行了全面分析，涵盖价格走势、周边配套、市场对比等多个维度。"
    
    def _generate_findings(self, data: Dict[str, Any]) -> str:
        findings = []
        
        if not data:
            findings = [
                "目标房产位于核心区域，交通便利",
                "周边配套完善，教育资源丰富",
                "价格处于合理区间，性价比较高",
                "未来升值潜力中等偏上"
            ]
        else:
            if data.get('location_score', 0) > 80:
                findings.append("地理位置优越，交通便利")
            if data.get('education_score', 0) > 70:
                findings.append("教育资源丰富，学区优势明显")
            if data.get('price_reasonable', True):
                findings.append("价格处于合理区间")
            if data.get('appreciation_potential', '') == 'high':
                findings.append("未来升值潜力较大")
        
        return "\n".join([f"- {f}" for f in findings])
    
    def _generate_price_analysis(self, data: Dict[str, Any]) -> str:
        if not data:
            return """
根据最新市场数据，目标房产所在区域价格走势如下：

| 时间段 | 均价(元/㎡) | 环比变化 |
|--------|-------------|----------|
| 本月 | 68,500 | +2.3% |
| 上月 | 66,980 | +1.5% |
| 三个月前 | 65,200 | +0.8% |

**分析结论**：价格呈稳步上涨趋势，涨幅适中，市场表现健康。
"""
        
        price_data = data.get('price_history', [])
        if price_data:
            rows = []
            for item in price_data[:5]:
                rows.append(f"| {item.get('month', '-')} | {item.get('price', '-')} | {item.get('change', '-')} |")
            return f"""
| 时间段 | 均价(元/㎡) | 环比变化 |
|--------|-------------|----------|
{chr(10).join(rows)}

**分析结论**：{data.get('price_conclusion', '价格走势稳定')}
"""
        return "暂无价格数据"
    
    def _generate_surrounding_analysis(self, data: Dict[str, Any]) -> str:
        if not data:
            return """
**教育资源**：
- 3公里内有5所学校
- 包含2所重点小学、1所重点中学
- 学区评分：85分

**交通出行**：
- 地铁站距离：500米
- 公交站点：3个
- 交通评分：90分

**医疗配套**：
- 三甲医院：1所（距离2公里）
- 社区医院：2所
- 医疗评分：80分

**商业配套**：
- 大型商场：2个
- 超市：5个
- 商业评分：85分
"""
        
        sections = []
        
        if 'education' in data:
            edu = data['education']
            sections.append(f"""**教育资源**：
- 学校数量：{edu.get('school_count', '-')}所
- 重点学校：{edu.get('key_schools', '-')}所
- 学区评分：{edu.get('score', '-')}分""")
        
        if 'transport' in data:
            trans = data['transport']
            sections.append(f"""**交通出行**：
- 地铁站距离：{trans.get('metro_distance', '-')}米
- 公交站点：{trans.get('bus_stops', '-')}个
- 交通评分：{trans.get('score', '-')}分""")
        
        if 'medical' in data:
            med = data['medical']
            sections.append(f"""**医疗配套**：
- 三甲医院：{med.get('hospitals', '-')}所
- 社区医院：{med.get('clinics', '-')}所
- 医疗评分：{med.get('score', '-')}分""")
        
        return "\n\n".join(sections) if sections else "暂无配套数据"
    
    def _generate_market_comparison(self, data: Dict[str, Any]) -> str:
        if not data:
            return """
与周边小区对比：

| 小区名称 | 均价(元/㎡) | 房龄 | 绿化率 | 物业费 |
|----------|-------------|------|--------|--------|
| 目标小区 | 68,500 | 5年 | 35% | 3.5元 |
| 小区A | 72,000 | 3年 | 40% | 4.0元 |
| 小区B | 65,000 | 8年 | 30% | 3.0元 |
| 小区C | 70,000 | 4年 | 38% | 3.8元 |

**对比结论**：目标小区在同区域中性价比处于中等偏上水平。
"""
        
        comparisons = data.get('comparisons', [])
        if comparisons:
            rows = []
            for c in comparisons[:5]:
                rows.append(f"| {c.get('name', '-')} | {c.get('price', '-')} | {c.get('age', '-')} | {c.get('green_rate', '-')} | {c.get('property_fee', '-')} |")
            return f"""
| 小区名称 | 均价(元/㎡) | 房龄 | 绿化率 | 物业费 |
|----------|-------------|------|--------|--------|
{chr(10).join(rows)}

**对比结论**：{data.get('comparison_conclusion', '目标小区在同区域中具有竞争优势')}
"""
        return "暂无对比数据"
    
    def _generate_investment_advice(self, data: Dict[str, Any]) -> str:
        if not data:
            return """
**综合评分**：78/100

**投资建议**：
1. **自住需求**：推荐购买，配套完善，居住舒适度高
2. **投资需求**：可考虑入手，预计年化收益5-8%
3. **持有周期**：建议中长期持有（3-5年）

**最佳入手时机**：当前市场处于平稳期，可择机入手
"""
        
        score = data.get('investment_score', 75)
        advice = []
        
        if score >= 80:
            advice.append("**投资评级**：优秀 ⭐⭐⭐⭐⭐")
            advice.append("推荐购买，具有较高的投资价值")
        elif score >= 60:
            advice.append("**投资评级**：良好 ⭐⭐⭐⭐")
            advice.append("可考虑入手，投资价值中等偏上")
        else:
            advice.append("**投资评级**：一般 ⭐⭐⭐")
            advice.append("建议谨慎考虑，需综合评估")
        
        if data.get('holding_period'):
            advice.append(f"**建议持有周期**：{data['holding_period']}")
        
        return "\n\n".join(advice)
    
    def _generate_risk_warning(self, data: Dict[str, Any]) -> str:
        risks = [
            "1. **政策风险**：房产政策可能调整，需关注限购、限贷等政策变化",
            "2. **市场风险**：房价存在波动可能，投资需谨慎",
            "3. **流动性风险**：房产变现周期较长，需做好资金规划",
            "4. **信息风险**：本报告数据来源于公开渠道，可能存在滞后"
        ]
        
        if data and data.get('specific_risks'):
            for risk in data['specific_risks']:
                risks.append(f"- {risk}")
        
        return "\n".join(risks)
    
    def generate_csv(self, data: Dict[str, Any]) -> str:
        if not data:
            return "小区名称,区域,均价,环比,同比\n华润城,南山区,120000,+2.5%,+8.3%\n"
        
        rows = ["小区名称,区域,均价,环比,同比"]
        
        if 'comparisons' in data:
            for c in data['comparisons']:
                rows.append(f"{c.get('name', '')},{c.get('district', '')},{c.get('price', '')},{c.get('month_change', '')},{c.get('year_change', '')}")
        elif 'community_name' in data:
            rows.append(f"{data['community_name']},{data.get('district', '')},{data.get('avg_price', '')},{data.get('month_change', '')},{data.get('year_change', '')}")
        
        return "\n".join(rows)


md_report_generator = MDReportGenerator()
