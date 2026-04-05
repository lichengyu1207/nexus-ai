"""
报告生成智能体
Report Generation Agent

根据估价过程和各智能体输出，生成可视化报告，包括估价结果、影响因素雷达图、对比分析表格，并以周瑜或陆逊的口吻向用户讲解。
"""

import logging
import json
import os
import base64
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from io import BytesIO

logger = logging.getLogger(__name__)


@dataclass
class ReportConfig:
    """报告配置"""
    persona: str  # 周瑜或陆逊
    include_visualizations: bool = True
    include_radar_chart: bool = True
    include_comparison_table: bool = True
    output_format: str = "html"  # html, text, markdown


@dataclass
class ReportData:
    """报告数据"""
    property_data: Dict[str, Any]
    feature_vector: np.ndarray
    location_result: Any
    layout_result: Any
    market_result: Any
    collaborative_result: Any
    metadata: Dict[str, Any] = None


@dataclass
class ReportResult:
    """报告结果"""
    report_content: str
    visualizations: Dict[str, str]  # 图表名称 -> base64编码的图片
    metadata: Dict[str, Any]


class ReportGenerator:
    """报告生成智能体"""
    
    def __init__(self):
        # 角色配置
        self.personas = {
            "zhouyu": {
                "name": "周瑜",
                "style": "儒雅从容，善用典故",
                "greeting": "主公",
                "phrases": [
                    "主公此事，且听瑜一言",
                    "谈笑间，房价走势了然于胸",
                    "瑜已有策",
                    "此城之势，可图也",
                    "东风已备，只欠主公一声令下"
                ],
                "keywords": ["瑜", "主公", "公瑾", "江东", "赤壁", "东风"]
            },
            "luxun": {
                "name": "陆逊",
                "style": "沉稳内敛，善用比喻",
                "greeting": "主公",
                "phrases": [
                    "主公且慢，听逊一言",
                    "静观其变，一击必中",
                    "此盘有诈，当慎之",
                    "逊以为，此事需从长计议",
                    "后发制人，方为上策"
                ],
                "keywords": ["逊", "主公", "夷陵", "忍耐", "后发制人"]
            }
        }
        
        # 报告模板
        self.report_templates = {
            "html": self._generate_html_report,
            "text": self._generate_text_report,
            "markdown": self._generate_markdown_report
        }
    
    def generate_report(self, report_data: ReportData, config: ReportConfig) -> ReportResult:
        """生成报告"""
        # 生成可视化内容
        visualizations = {}
        if config.include_visualizations:
            if config.include_radar_chart:
                radar_chart = self._generate_radar_chart(report_data)
                visualizations["radar_chart"] = radar_chart
            
            if config.include_comparison_table:
                comparison_table = self._generate_comparison_table(report_data)
                visualizations["comparison_table"] = comparison_table
        
        # 生成报告内容
        template = self.report_templates.get(config.output_format, self._generate_text_report)
        report_content = template(report_data, config, visualizations)
        
        # 生成元数据
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "persona": config.persona,
            "output_format": config.output_format,
            "visualizations": list(visualizations.keys()),
            "property_id": report_data.metadata.get("property_id", "unknown")
        }
        
        return ReportResult(
            report_content=report_content,
            visualizations=visualizations,
            metadata=metadata
        )
    
    def _generate_radar_chart(self, report_data: ReportData) -> str:
        """生成影响因素雷达图"""
        # 准备数据
        factors = {
            "location": {
                "subway_distance": report_data.location_result.factors.get("subway_distance", 0),
                "school_district": report_data.location_result.factors.get("school_district", 0),
                "greening_rate": report_data.location_result.factors.get("greening_rate", 0),
                "total_floors": report_data.location_result.factors.get("total_floors", 0),
                "is_elevator": report_data.location_result.factors.get("is_elevator", 0),
                "property_type": report_data.location_result.factors.get("property_type", 0)
            },
            "layout": {
                "room_count": report_data.layout_result.factors.get("room_count", 0),
                "bathroom_count": report_data.layout_result.factors.get("bathroom_count", 0),
                "total_area": report_data.layout_result.factors.get("total_area", 0),
                "floor": report_data.layout_result.factors.get("floor", 0),
                "building_age": report_data.layout_result.factors.get("building_age", 0),
                "is_elevator": report_data.layout_result.factors.get("is_elevator", 0)
            },
            "market": {
                "price_level": report_data.market_result.factors.get("price_level", 0),
                "market_trend": report_data.market_result.factors.get("market_trend", 0),
                "policy_impact": report_data.market_result.factors.get("policy_impact", 0),
                "supply_demand": report_data.market_result.factors.get("supply_demand", 0)
            }
        }
        
        # 创建雷达图
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), subplot_kw=dict(polar=True))
        
        # 绘制区位因素雷达图
        ax = axes[0]
        labels = list(factors["location"].keys())
        values = list(factors["location"].values())
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label="区位因素")
        ax.fill(angles, values, alpha=0.25)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_title("区位因素", size=15, y=1.1)
        
        # 绘制户型因素雷达图
        ax = axes[1]
        labels = list(factors["layout"].keys())
        values = list(factors["layout"].values())
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label="户型因素", color="green")
        ax.fill(angles, values, alpha=0.25, color="green")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_title("户型因素", size=15, y=1.1)
        
        # 绘制市场因素雷达图
        ax = axes[2]
        labels = list(factors["market"].keys())
        values = list(factors["market"].values())
        angles = np.linspace(0, 2 * np.pi, len(labels), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        ax.plot(angles, values, 'o-', linewidth=2, label="市场因素", color="blue")
        ax.fill(angles, values, alpha=0.25, color="blue")
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(labels)
        ax.set_title("市场因素", size=15, y=1.1)
        
        plt.tight_layout()
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def _generate_comparison_table(self, report_data: ReportData) -> str:
        """生成对比分析表格"""
        # 准备数据
        data = {
            "评估维度": ["区位评估", "户型评估", "市场评估", "综合评估"],
            "估价(元/㎡)": [
                report_data.location_result.p1,
                report_data.layout_result.p2,
                report_data.market_result.p3,
                report_data.collaborative_result.p
            ],
            "置信度": [
                report_data.location_result.confidence,
                report_data.layout_result.confidence,
                report_data.market_result.confidence,
                (report_data.location_result.confidence + report_data.layout_result.confidence + report_data.market_result.confidence) / 3
            ],
            "权重": [
                report_data.collaborative_result.weights.get("location", 0),
                report_data.collaborative_result.weights.get("layout", 0),
                report_data.collaborative_result.weights.get("market", 0),
                1.0
            ]
        }
        
        # 创建表格
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.axis('tight')
        ax.axis('off')
        
        # 构建表格
        table_data = []
        table_data.append(list(data.keys()))
        for i in range(len(data["评估维度"])):
            row = []
            for key in data:
                if key == "估价(元/㎡)":
                    row.append(f"{data[key][i]:.2f}")
                elif key == "置信度" or key == "权重":
                    row.append(f"{data[key][i]:.4f}")
                else:
                    row.append(data[key][i])
            table_data.append(row)
        
        table = ax.table(cellText=table_data, loc='center')
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 1.2)
        
        plt.tight_layout()
        
        # 转换为base64
        buffer = BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight')
        buffer.seek(0)
        image_base64 = base64.b64encode(buffer.read()).decode('utf-8')
        plt.close()
        
        return image_base64
    
    def _generate_html_report(self, report_data: ReportData, config: ReportConfig, visualizations: Dict[str, str]) -> str:
        """生成HTML格式报告"""
        persona = self.personas.get(config.persona, self.personas["zhouyu"])
        
        # 生成讲解文本
        explanation = self._generate_explanation(report_data, config.persona)
        
        # 构建HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>房产估价报告</title>
            <style>
                body {{
                    font-family: 'Microsoft YaHei', Arial, sans-serif;
                    line-height: 1.6;
                    margin: 20px;
                    background-color: #f5f5f5;
                }}
                .container {{
                    max-width: 1000px;
                    margin: 0 auto;
                    background-color: white;
                    padding: 30px;
                    border-radius: 10px;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                }}
                h1, h2, h3 {{
                    color: #333;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 30px;
                    padding-bottom: 20px;
                    border-bottom: 2px solid #e0e0e0;
                }}
                .section {{
                    margin-bottom: 30px;
                }}
                .explanation {{
                    background-color: #f9f9f9;
                    padding: 20px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                }}
                .visualization {{
                    margin: 20px 0;
                    text-align: center;
                }}
                .visualization img {{
                    max-width: 100%;
                    height: auto;
                    border: 1px solid #e0e0e0;
                    border-radius: 5px;
                }}
                .table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                .table th, .table td {{
                    padding: 10px;
                    text-align: left;
                    border-bottom: 1px solid #e0e0e0;
                }}
                .table th {{
                    background-color: #f2f2f2;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    padding-top: 20px;
                    border-top: 2px solid #e0e0e0;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>房产估价报告</h1>
                    <p>生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p>讲解人: {persona['name']}</p>
                </div>
                
                <div class="section">
                    <h2>一、房产基本信息</h2>
                    <table class="table">
                        <tr>
                            <th>属性</th>
                            <th>值</th>
                        </tr>
                        <tr>
                            <td>房龄</td>
                            <td>{report_data.property_data.get('building_age', '未知')}年</td>
                        </tr>
                        <tr>
                            <td>距地铁距离</td>
                            <td>{report_data.property_data.get('distance_to_subway', '未知')}米</td>
                        </tr>
                        <tr>
                            <td>学区等级</td>
                            <td>{report_data.property_data.get('school_district_level', '未知')}</td>
                        </tr>
                        <tr>
                            <td>绿化率</td>
                            <td>{report_data.property_data.get('greening_rate', '未知')}%</td>
                        </tr>
                        <tr>
                            <td>每平米价格</td>
                            <td>{report_data.property_data.get('price_per_sqm', '未知')}元/㎡</td>
                        </tr>
                        <tr>
                            <td>总面积</td>
                            <td>{report_data.property_data.get('total_area', '未知')}㎡</td>
                        </tr>
                        <tr>
                            <td>房间数量</td>
                            <td>{report_data.property_data.get('room_count', '未知')}室</td>
                        </tr>
                        <tr>
                            <td>卫生间数量</td>
                            <td>{report_data.property_data.get('bathroom_count', '未知')}卫</td>
                        </tr>
                        <tr>
                            <td>楼层</td>
                            <td>{report_data.property_data.get('floor', '未知')}层</td>
                        </tr>
                        <tr>
                            <td>总楼层</td>
                            <td>{report_data.property_data.get('total_floors', '未知')}层</td>
                        </tr>
                        <tr>
                            <td>是否有电梯</td>
                            <td>{'是' if report_data.property_data.get('is_elevator', False) else '否'}</td>
                        </tr>
                        <tr>
                            <td>物业类型</td>
                            <td>{report_data.property_data.get('property_type', '未知')}</td>
                        </tr>
                    </table>
                </div>
                
                <div class="section">
                    <h2>二、估价结果</h2>
                    <div class="explanation">
                        <h3>专家讲解</h3>
                        <p>{explanation}</p>
                    </div>
                    
                    <div class="visualization">
                        <h3>对比分析表格</h3>
                        <img src="data:image/png;base64,{visualizations.get('comparison_table', '')}" alt="对比分析表格">
                    </div>
                </div>
                
                <div class="section">
                    <h2>三、影响因素分析</h2>
                    <div class="visualization">
                        <h3>影响因素雷达图</h3>
                        <img src="data:image/png;base64,{visualizations.get('radar_chart', '')}" alt="影响因素雷达图">
                    </div>
                </div>
                
                <div class="section">
                    <h2>四、详细评估</h2>
                    
                    <h3>1. 区位评估</h3>
                    <p>估价: {report_data.location_result.p1:.2f} 元/㎡</p>
                    <p>置信度: {report_data.location_result.confidence:.4f}</p>
                    <p>影响因素: {json.dumps(report_data.location_result.factors, ensure_ascii=False)}</p>
                    
                    <h3>2. 户型评估</h3>
                    <p>估价: {report_data.layout_result.p2:.2f} 元/㎡</p>
                    <p>置信度: {report_data.layout_result.confidence:.4f}</p>
                    <p>影响因素: {json.dumps(report_data.layout_result.factors, ensure_ascii=False)}</p>
                    
                    <h3>3. 市场评估</h3>
                    <p>估价: {report_data.market_result.p3:.2f} 元/㎡</p>
                    <p>置信度: {report_data.market_result.confidence:.4f}</p>
                    <p>影响因素: {json.dumps(report_data.market_result.factors, ensure_ascii=False)}</p>
                    
                    <h3>4. 综合评估</h3>
                    <p>估价: {report_data.collaborative_result.p:.2f} 元/㎡</p>
                    <p>各智能体权重: {json.dumps(report_data.collaborative_result.weights, ensure_ascii=False)}</p>
                </div>
                
                <div class="footer">
                    <p>本报告由房都督智能估价系统生成</p>
                    <p>报告仅供参考，实际交易价格可能有所不同</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html
    
    def _generate_text_report(self, report_data: ReportData, config: ReportConfig, visualizations: Dict[str, str]) -> str:
        """生成文本格式报告"""
        persona = self.personas.get(config.persona, self.personas["zhouyu"])
        
        # 生成讲解文本
        explanation = self._generate_explanation(report_data, config.persona)
        
        # 构建文本报告
        report = f"""
        ===============================================
                    房产估价报告
        ===============================================
        生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        讲解人: {persona['name']}
        
        一、房产基本信息
        -----------------------------------------------
        房龄: {report_data.property_data.get('building_age', '未知')}年
        距地铁距离: {report_data.property_data.get('distance_to_subway', '未知')}米
        学区等级: {report_data.property_data.get('school_district_level', '未知')}
        绿化率: {report_data.property_data.get('greening_rate', '未知')}%
        每平米价格: {report_data.property_data.get('price_per_sqm', '未知')}元/㎡
        总面积: {report_data.property_data.get('total_area', '未知')}㎡
        房间数量: {report_data.property_data.get('room_count', '未知')}室
        卫生间数量: {report_data.property_data.get('bathroom_count', '未知')}卫
        楼层: {report_data.property_data.get('floor', '未知')}层
        总楼层: {report_data.property_data.get('total_floors', '未知')}层
        是否有电梯: {'是' if report_data.property_data.get('is_elevator', False) else '否'}
        物业类型: {report_data.property_data.get('property_type', '未知')}
        
        二、估价结果
        -----------------------------------------------
        专家讲解:
        {explanation}
        
        对比分析:
        评估维度    估价(元/㎡)    置信度    权重
        -----------------------------------
        区位评估    {report_data.location_result.p1:.2f}    {report_data.location_result.confidence:.4f}    {report_data.collaborative_result.weights.get('location', 0):.4f}
        户型评估    {report_data.layout_result.p2:.2f}    {report_data.layout_result.confidence:.4f}    {report_data.collaborative_result.weights.get('layout', 0):.4f}
        市场评估    {report_data.market_result.p3:.2f}    {report_data.market_result.confidence:.4f}    {report_data.collaborative_result.weights.get('market', 0):.4f}
        综合评估    {report_data.collaborative_result.p:.2f}    {(report_data.location_result.confidence + report_data.layout_result.confidence + report_data.market_result.confidence) / 3:.4f}    1.0000
        
        三、详细评估
        -----------------------------------------------
        1. 区位评估
        估价: {report_data.location_result.p1:.2f} 元/㎡
        置信度: {report_data.location_result.confidence:.4f}
        影响因素: {json.dumps(report_data.location_result.factors, ensure_ascii=False)}
        
        2. 户型评估
        估价: {report_data.layout_result.p2:.2f} 元/㎡
        置信度: {report_data.layout_result.confidence:.4f}
        影响因素: {json.dumps(report_data.layout_result.factors, ensure_ascii=False)}
        
        3. 市场评估
        估价: {report_data.market_result.p3:.2f} 元/㎡
        置信度: {report_data.market_result.confidence:.4f}
        影响因素: {json.dumps(report_data.market_result.factors, ensure_ascii=False)}
        
        4. 综合评估
        估价: {report_data.collaborative_result.p:.2f} 元/㎡
        各智能体权重: {json.dumps(report_data.collaborative_result.weights, ensure_ascii=False)}
        
        ===============================================
        本报告由房都督智能估价系统生成
        报告仅供参考，实际交易价格可能有所不同
        ===============================================
        """
        
        return report
    
    def _generate_markdown_report(self, report_data: ReportData, config: ReportConfig, visualizations: Dict[str, str]) -> str:
        """生成Markdown格式报告"""
        persona = self.personas.get(config.persona, self.personas["zhouyu"])
        
        # 生成讲解文本
        explanation = self._generate_explanation(report_data, config.persona)
        
        # 构建Markdown报告
        report = f"""
        # 房产估价报告
        
        **生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        **讲解人**: {persona['name']}
        
        ## 一、房产基本信息
        
        | 属性 | 值 |
        |------|------|
        | 房龄 | {report_data.property_data.get('building_age', '未知')}年 |
        | 距地铁距离 | {report_data.property_data.get('distance_to_subway', '未知')}米 |
        | 学区等级 | {report_data.property_data.get('school_district_level', '未知')} |
        | 绿化率 | {report_data.property_data.get('greening_rate', '未知')}% |
        | 每平米价格 | {report_data.property_data.get('price_per_sqm', '未知')}元/㎡ |
        | 总面积 | {report_data.property_data.get('total_area', '未知')}㎡ |
        | 房间数量 | {report_data.property_data.get('room_count', '未知')}室 |
        | 卫生间数量 | {report_data.property_data.get('bathroom_count', '未知')}卫 |
        | 楼层 | {report_data.property_data.get('floor', '未知')}层 |
        | 总楼层 | {report_data.property_data.get('total_floors', '未知')}层 |
        | 是否有电梯 | {'是' if report_data.property_data.get('is_elevator', False) else '否'} |
        | 物业类型 | {report_data.property_data.get('property_type', '未知')} |
        
        ## 二、估价结果
        
        ### 专家讲解
        {explanation}
        
        ### 对比分析
        
        | 评估维度 | 估价(元/㎡) | 置信度 | 权重 |
        |----------|------------|--------|------|
        | 区位评估 | {report_data.location_result.p1:.2f} | {report_data.location_result.confidence:.4f} | {report_data.collaborative_result.weights.get('location', 0):.4f} |
        | 户型评估 | {report_data.layout_result.p2:.2f} | {report_data.layout_result.confidence:.4f} | {report_data.collaborative_result.weights.get('layout', 0):.4f} |
        | 市场评估 | {report_data.market_result.p3:.2f} | {report_data.market_result.confidence:.4f} | {report_data.collaborative_result.weights.get('market', 0):.4f} |
        | 综合评估 | {report_data.collaborative_result.p:.2f} | {(report_data.location_result.confidence + report_data.layout_result.confidence + report_data.market_result.confidence) / 3:.4f} | 1.0000 |
        
        ## 三、影响因素分析
        
        ![影响因素雷达图](data:image/png;base64,{visualizations.get('radar_chart', '')})
        
        ## 四、详细评估
        
        ### 1. 区位评估
        - 估价: {report_data.location_result.p1:.2f} 元/㎡
        - 置信度: {report_data.location_result.confidence:.4f}
        - 影响因素: {json.dumps(report_data.location_result.factors, ensure_ascii=False)}
        
        ### 2. 户型评估
        - 估价: {report_data.layout_result.p2:.2f} 元/㎡
        - 置信度: {report_data.layout_result.confidence:.4f}
        - 影响因素: {json.dumps(report_data.layout_result.factors, ensure_ascii=False)}
        
        ### 3. 市场评估
        - 估价: {report_data.market_result.p3:.2f} 元/㎡
        - 置信度: {report_data.market_result.confidence:.4f}
        - 影响因素: {json.dumps(report_data.market_result.factors, ensure_ascii=False)}
        
        ### 4. 综合评估
        - 估价: {report_data.collaborative_result.p:.2f} 元/㎡
        - 各智能体权重: {json.dumps(report_data.collaborative_result.weights, ensure_ascii=False)}
        
        ---
        
        *本报告由房都督智能估价系统生成*
        *报告仅供参考，实际交易价格可能有所不同*
        """
        
        return report
    
    def _generate_explanation(self, report_data: ReportData, persona: str) -> str:
        """生成讲解文本"""
        persona_config = self.personas.get(persona, self.personas["zhouyu"])
        
        # 获取估价结果
        p1 = report_data.location_result.p1
        p2 = report_data.layout_result.p2
        p3 = report_data.market_result.p3
        p = report_data.collaborative_result.p
        
        # 获取权重
        weights = report_data.collaborative_result.weights
        location_weight = weights.get("location", 0)
        layout_weight = weights.get("layout", 0)
        market_weight = weights.get("market", 0)
        
        # 生成讲解文本
        if persona == "zhouyu":
            explanation = f"{persona_config['greeting']}，瑜已对该房产进行全面评估。此房产综合估价为每平米{p:.2f}元，其中区位因素权重占{location_weight:.2f}，户型因素占{layout_weight:.2f}，市场因素占{market_weight:.2f}。"
            explanation += " 谈笑间，瑜已分析完毕："
            
            if location_weight > 0.4:
                explanation += " 区位优势明显，地铁便利，学区优良，实乃宜居之选。"
            if layout_weight > 0.4:
                explanation += " 户型布局合理，空间利用率高，居住舒适度佳。"
            if market_weight > 0.4:
                explanation += " 市场趋势向好，政策环境有利，投资潜力可观。"
            
            explanation += " 主公若有意，瑜愿为您详陈利弊，助您做出明智决策。"
        else:  # 陆逊
            explanation = f"{persona_config['greeting']}，逊已仔细评估此房产。综合估价为每平米{p:.2f}元，其中区位因素权重{location_weight:.2f}，户型因素{layout_weight:.2f}，市场因素{market_weight:.2f}。"
            explanation += " 逊以为，此事需从长计议："
            
            if location_weight > 0.4:
                explanation += " 区位条件优越，交通便利，周边配套完善，为房产价值之基石。"
            if layout_weight > 0.4:
                explanation += " 户型设计合理，采光通风良好，居住体验上乘。"
            if market_weight > 0.4:
                explanation += " 市场环境稳定，政策支持，长期持有价值可期。"
            
            explanation += " 主公当静观其变，择机而动，方为上策。"
        
        return explanation


# 示例使用
if __name__ == "__main__":
    # 模拟数据
    class MockResult:
        def __init__(self, p, factors, confidence):
            self.p = p
            self.factors = factors
            self.confidence = confidence
    
    location_result = MockResult(
        p=60000.00,
        factors={"subway_distance": 1.0, "school_district": 0.0, "greening_rate": 0.0, "total_floors": 1.0, "is_elevator": 1.0, "property_type": 0.0},
        confidence=0.5
    )
    
    layout_result = MockResult(
        p=66000.00,
        factors={"room_count": 1.0, "bathroom_count": 1.0, "total_area": 1.0, "floor": 0.6, "building_age": 0, "is_elevator": 1.0},
        confidence=1.0
    )
    
    market_result = MockResult(
        p=55290.00,
        factors={"price_level": 1.0, "market_trend": 0.6386, "policy_impact": 0.5853, "supply_demand": 0.4871},
        confidence=0.56
    )
    
    collaborative_result = MockResult(
        p=60319.47,
        factors={},
        confidence=0.6867
    )
    collaborative_result.weights = {"location": 0.4322, "layout": 0.2795, "market": 0.2883}
    
    property_data = {
        "building_age": 10,
        "distance_to_subway": 500,
        "school_district_level": "A",
        "greening_rate": 35,
        "price_per_sqm": 85000,
        "total_area": 120,
        "room_count": 3,
        "bathroom_count": 2,
        "floor": 15,
        "total_floors": 30,
        "is_elevator": True,
        "property_type": "apartment"
    }
    
    feature_vector = np.array([0.3333, 0.3, 0.0, 0.5, 0.3636, 0.3333, 0.5, 0.5, 0.5, 0.6667, 1.0, 0.0])
    
    report_data = ReportData(
        property_data=property_data,
        feature_vector=feature_vector,
        location_result=location_result,
        layout_result=layout_result,
        market_result=market_result,
        collaborative_result=collaborative_result,
        metadata={"property_id": "12345"}
    )
    
    config = ReportConfig(
        persona="zhouyu",
        include_visualizations=True,
        include_radar_chart=True,
        include_comparison_table=True,
        output_format="html"
    )
    
    generator = ReportGenerator()
    result = generator.generate_report(report_data, config)
    
    # 保存报告
    with open("report.html", "w", encoding="utf-8") as f:
        f.write(result.report_content)
    
    print("报告生成成功，保存为 report.html")
