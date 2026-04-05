"""
报告生成模块
基于模板生成烦恼分析报告
"""

import json
import uuid
import random
from typing import List, Dict, Optional


def generate_report(user_message: str, memories: List[Dict]) -> Dict:
    """
    生成烦恼分析报告
    
    Args:
        user_message: 用户最新消息
        memories: 历史记忆列表
    
    Returns:
        报告字典
    """
    # 提取关键词
    keywords = _extract_keywords(user_message)
    
    # 分析情绪趋势
    emotion_trend = _analyze_emotion_trend(memories)
    
    # 生成建议
    suggestions = _generate_suggestions(keywords)
    
    # 生成图表数据
    chart_data = _generate_chart_data(memories)
    
    report = {
        "report_id": str(uuid.uuid4()),
        "title": "烦恼分析报告",
        "summary": _generate_summary(keywords, memories),
        "emotion_trend": emotion_trend,
        "suggestions": suggestions,
        "chart_data": chart_data,
        "generated_at": "2026-03-21"
    }
    
    return report


def _extract_keywords(text: str) -> List[str]:
    """
    提取关键词
    
    Args:
        text: 文本
    
    Returns:
        关键词列表
    """
    keywords = [
        "压力", "烦恼", "焦虑", "工作", "学习", "生活", "家庭",
        "朋友", "健康", "未来", "困难", "问题", "挫折", "迷茫"
    ]
    
    extracted = []
    for keyword in keywords:
        if keyword in text:
            extracted.append(keyword)
    
    return extracted


def _analyze_emotion_trend(memories: List[Dict]) -> str:
    """
    分析情绪趋势
    
    Args:
        memories: 历史记忆列表
    
    Returns:
        情绪趋势描述
    """
    if not memories:
        return "暂无历史记录"
    
    # 简单分析
    if len(memories) == 1:
        return "这是您的第一次倾诉，希望我们能帮到您"
    elif len(memories) <= 3:
        return "从记录看，情绪波动较大，但整体向稳"
    else:
        return "通过多次交流，您的情绪逐渐平稳，烦恼有所缓解"


def _generate_suggestions(keywords: List[str]) -> List[str]:
    """
    生成建议
    
    Args:
        keywords: 关键词列表
    
    Returns:
        建议列表
    """
    # 预设建议模板
    suggestion_templates = {
        "工作": [
            "尝试深呼吸5分钟，缓解工作压力",
            "与同事或上级沟通，寻求支持",
            "设定小目标，逐步完成工作任务"
        ],
        "学习": [
            "制定合理的学习计划，避免压力过大",
            "适当休息，保持良好的学习状态",
            "寻求老师或同学的帮助"
        ],
        "生活": [
            "多参加户外活动，放松心情",
            "与朋友分享，减轻心理负担",
            "培养兴趣爱好，丰富生活"
        ],
        "家庭": [
            "与家人坦诚沟通，表达自己的感受",
            "尝试理解家人的立场",
            "寻求家庭咨询师的帮助"
        ],
        "健康": [
            "保持规律的作息时间",
            "适当运动，增强体质",
            "如症状严重，及时就医"
        ],
        "其他": [
            "尝试冥想，放松身心",
            "写日记，记录心情变化",
            "寻求专业心理咨询"
        ]
    }
    
    # 根据关键词选择建议
    category = "其他"
    if "工作" in keywords:
        category = "工作"
    elif "学习" in keywords:
        category = "学习"
    elif "生活" in keywords or "朋友" in keywords:
        category = "生活"
    elif "家庭" in keywords:
        category = "家庭"
    elif "健康" in keywords:
        category = "健康"
    
    return suggestion_templates.get(category, suggestion_templates["其他"])


def _generate_chart_data(memories: List[Dict]) -> Dict:
    """
    生成图表数据
    
    Args:
        memories: 历史记忆列表
    
    Returns:
        图表数据字典
    """
    # 生成模拟数据
    days = min(len(memories), 7)
    labels = [f"Day{i+1}" for i in range(days)]
    
    # 模拟情绪值（1-5，5表示情绪最好）
    values = []
    for i in range(days):
        # 简单的波动模拟
        if i == 0:
            values.append(3)
        else:
            # 略有波动，但整体向好
            change = random.randint(-1, 1)
            new_value = min(5, max(1, values[-1] + change))
            values.append(new_value)
    
    return {
        "labels": labels,
        "values": values
    }


def _generate_summary(keywords: List[str], memories: List[Dict]) -> str:
    """
    生成报告摘要
    
    Args:
        keywords: 关键词列表
        memories: 历史记忆列表
    
    Returns:
        摘要文本
    """
    if not keywords:
        return "您的烦恼较为复杂，需要进一步了解"
    
    main_keyword = keywords[0]
    
    if len(memories) == 1:
        return f"您提到了关于{main_keyword}的烦恼，这是您第一次向我们倾诉"
    else:
        return f"您最近多次提及{main_keyword}相关的烦恼，我们一直在关注"


def save_report(report: Dict) -> str:
    """
    保存报告到数据库
    
    Args:
        report: 报告字典
    
    Returns:
        报告ID
    """
    import sqlite3
    
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO reports (report_id, user_message, content, created_at) VALUES (?, ?, ?, ?)",
        (report["report_id"], "用户消息", json.dumps(report), "2026-03-21")
    )
    
    conn.commit()
    conn.close()
    
    return report["report_id"]


def get_report(report_id: str) -> Optional[Dict]:
    """
    获取报告
    
    Args:
        report_id: 报告ID
    
    Returns:
        报告字典
    """
    import sqlite3
    
    conn = sqlite3.connect("data.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT content FROM reports WHERE report_id = ?",
        (report_id,)
    )
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return json.loads(row["content"])
    return None
