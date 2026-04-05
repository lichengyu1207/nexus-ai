# -*- coding: utf-8 -*-
"""
Terminology Translation Library
Bilingual mapping for destiny and property terms
"""
from typing import Dict, Optional

TERMS: Dict[str, Dict[str, str]] = {
    "mingpan": {
        "正财": {"en": "Regular Wealth", "zh": "正财"},
        "偏财": {"en": "Partial Wealth", "zh": "偏财"},
        "正官": {"en": "Regular Officer", "zh": "正官"},
        "偏官": {"en": "Partial Officer", "zh": "偏官"},
        "正印": {"en": "Regular Seal", "zh": "正印"},
        "偏印": {"en": "Partial Seal", "zh": "偏印"},
        "食神": {"en": "Eating God", "zh": "食神"},
        "伤官": {"en": "Hurting Officer", "zh": "伤官"},
        "比肩": {"en": "Friend", "zh": "比肩"},
        "劫财": {"en": "Rob Wealth", "zh": "劫财"},
        
        "文昌": {"en": "Wenchang (Literary Star)", "zh": "文昌"},
        "文曲": {"en": "Wenqu (Artistic Star)", "zh": "文曲"},
        "武曲": {"en": "Wuqu (Military Star)", "zh": "武曲"},
        "天机": {"en": "Tianji (Strategist Star)", "zh": "天机"},
        "紫微": {"en": "Ziwei (Emperor Star)", "zh": "紫微"},
        "天相": {"en": "Tianxiang (Minister Star)", "zh": "天相"},
        "天梁": {"en": "Tianliang (Shade Star)", "zh": "天梁"},
        "七杀": {"en": "Seven Killings", "zh": "七杀"},
        "破军": {"en": "Po Jun (Army Breaker)", "zh": "破军"},
        "贪狼": {"en": "Tan Lang (Greedy Wolf)", "zh": "贪狼"},
        
        "日主": {"en": "Day Master", "zh": "日主"},
        "五行": {"en": "Five Elements", "zh": "五行"},
        "金": {"en": "Metal", "zh": "金"},
        "木": {"en": "Wood", "zh": "木"},
        "水": {"en": "Water", "zh": "水"},
        "火": {"en": "Fire", "zh": "火"},
        "土": {"en": "Earth", "zh": "土"},
        
        "生肖": {"en": "Zodiac", "zh": "生肖"},
        "鼠": {"en": "Rat", "zh": "鼠"},
        "牛": {"en": "Ox", "zh": "牛"},
        "虎": {"en": "Tiger", "zh": "虎"},
        "兔": {"en": "Rabbit", "zh": "兔"},
        "龙": {"en": "Dragon", "zh": "龙"},
        "蛇": {"en": "Snake", "zh": "蛇"},
        "马": {"en": "Horse", "zh": "马"},
        "羊": {"en": "Goat", "zh": "羊"},
        "猴": {"en": "Monkey", "zh": "猴"},
        "鸡": {"en": "Rooster", "zh": "鸡"},
        "狗": {"en": "Dog", "zh": "狗"},
        "猪": {"en": "Pig", "zh": "猪"},
        
        "三合": {"en": "Three Harmony", "zh": "三合"},
        "六合": {"en": "Six Harmony", "zh": "六合"},
        "相冲": {"en": "Clash", "zh": "相冲"},
        "相害": {"en": "Harm", "zh": "相害"},
        "相刑": {"en": "Punishment", "zh": "相刑"},
        
        "财运": {"en": "Wealth Fortune", "zh": "财运"},
        "事业": {"en": "Career", "zh": "事业"},
        "姻缘": {"en": "Marriage Fate", "zh": "姻缘"},
        "人际": {"en": "Social Relations", "zh": "人际"},
        "执行力": {"en": "Execution Power", "zh": "执行力"},
        
        "流年": {"en": "Annual Fortune", "zh": "流年"},
        "大运": {"en": "Major Fortune Cycle", "zh": "大运"},
        "命盘": {"en": "Destiny Chart", "zh": "命盘"},
        "八字": {"en": "Eight Characters (Ba Zi)", "zh": "八字"},
    },
    
    "property": {
        "房价": {"en": "Property Price", "zh": "房价"},
        "均价": {"en": "Average Price", "zh": "均价"},
        "总价": {"en": "Total Price", "zh": "总价"},
        "单价": {"en": "Price per Unit", "zh": "单价"},
        "首付": {"en": "Down Payment", "zh": "首付"},
        "月供": {"en": "Monthly Payment", "zh": "月供"},
        "贷款": {"en": "Loan", "zh": "贷款"},
        "公积金": {"en": "Housing Provident Fund", "zh": "公积金"},
        "商贷": {"en": "Commercial Loan", "zh": "商贷"},
        
        "学区房": {"en": "School District Housing", "zh": "学区房"},
        "地铁房": {"en": "Metro-Adjacent Housing", "zh": "地铁房"},
        "新房": {"en": "New House", "zh": "新房"},
        "二手房": {"en": "Second-hand House", "zh": "二手房"},
        "期房": {"en": "Pre-sale Property", "zh": "期房"},
        "现房": {"en": "Completed Property", "zh": "现房"},
        
        "板块": {"en": "District", "zh": "板块"},
        "小区": {"en": "Residential Community", "zh": "小区"},
        "楼盘": {"en": "Property Development", "zh": "楼盘"},
        "户型": {"en": "Floor Plan", "zh": "户型"},
        "面积": {"en": "Area", "zh": "面积"},
        "容积率": {"en": "Plot Ratio", "zh": "容积率"},
        "绿化率": {"en": "Greening Rate", "zh": "绿化率"},
        
        "自住": {"en": "Self-use", "zh": "自住"},
        "投资": {"en": "Investment", "zh": "投资"},
        "刚需": {"en": "First-time Buyer", "zh": "刚需"},
        "改善": {"en": "Upgrading", "zh": "改善"},
        
        "挂牌量": {"en": "Listing Volume", "zh": "挂牌量"},
        "成交量": {"en": "Transaction Volume", "zh": "成交量"},
        "库存周期": {"en": "Inventory Cycle", "zh": "库存周期"},
        "环比": {"en": "Month-over-Month", "zh": "环比"},
        "同比": {"en": "Year-over-Year", "zh": "同比"},
    },
    
    "common": {
        "预算": {"en": "Budget", "zh": "预算"},
        "城市": {"en": "City", "zh": "城市"},
        "报告": {"en": "Report", "zh": "报告"},
        "分析": {"en": "Analysis", "zh": "分析"},
        "建议": {"en": "Recommendation", "zh": "建议"},
        "风险": {"en": "Risk", "zh": "风险"},
        "机会": {"en": "Opportunity", "zh": "机会"},
        "趋势": {"en": "Trend", "zh": "趋势"},
        "预测": {"en": "Forecast", "zh": "预测"},
        "策略": {"en": "Strategy", "zh": "策略"},
        
        "高": {"en": "High", "zh": "高"},
        "中": {"en": "Medium", "zh": "中"},
        "低": {"en": "Low", "zh": "低"},
        "强": {"en": "Strong", "zh": "强"},
        "弱": {"en": "Weak", "zh": "弱"},
    }
}

CITY_NAMES: Dict[str, Dict[str, str]] = {
    "suzhou": {"en": "Suzhou", "zh": "苏州"},
    "hangzhou": {"en": "Hangzhou", "zh": "杭州"},
    "nanjing": {"en": "Nanjing", "zh": "南京"},
    "shanghai": {"en": "Shanghai", "zh": "上海"},
    "beijing": {"en": "Beijing", "zh": "北京"},
    "shenzhen": {"en": "Shenzhen", "zh": "深圳"},
    "guangzhou": {"en": "Guangzhou", "zh": "广州"},
    "chengdu": {"en": "Chengdu", "zh": "成都"},
    "wuhan": {"en": "Wuhan", "zh": "武汉"},
    "changsha": {"en": "Changsha", "zh": "长沙"},
    "xian": {"en": "Xi'an", "zh": "西安"},
    "chongqing": {"en": "Chongqing", "zh": "重庆"},
    "tianjin": {"en": "Tianjin", "zh": "天津"},
    "suzhou": {"en": "Suzhou", "zh": "苏州"},
    "wuxi": {"en": "Wuxi", "zh": "无锡"},
    "ningbo": {"en": "Ningbo", "zh": "宁波"},
    "qingdao": {"en": "Qingdao", "zh": "青岛"},
    "dalian": {"en": "Dalian", "zh": "大连"},
    "xiamen": {"en": "Xiamen", "zh": "厦门"},
    "kunming": {"en": "Kunming", "zh": "昆明"},
    
    "new_york": {"en": "New York", "zh": "纽约"},
    "london": {"en": "London", "zh": "伦敦"},
    "tokyo": {"en": "Tokyo", "zh": "东京"},
    "singapore": {"en": "Singapore", "zh": "新加坡"},
    "sydney": {"en": "Sydney", "zh": "悉尼"},
    "toronto": {"en": "Toronto", "zh": "多伦多"},
    "vancouver": {"en": "Vancouver", "zh": "温哥华"},
    "melbourne": {"en": "Melbourne", "zh": "墨尔本"},
    "los_angeles": {"en": "Los Angeles", "zh": "洛杉矶"},
    "san_francisco": {"en": "San Francisco", "zh": "旧金山"},
}


def translate_term(term: str, lang: str = 'en', category: str = None) -> str:
    """
    Translate a term to the target language
    
    Args:
        term: The term to translate (Chinese or English)
        lang: Target language ('en' or 'zh')
        category: Optional category to search in
    
    Returns:
        Translated term or original if not found
    """
    if lang not in ['en', 'zh']:
        return term
    
    source_lang = 'zh' if '\u4e00' <= term[0] <= '\u9fff' else 'en'
    
    if source_lang == lang:
        return term
    
    categories = [category] if category else TERMS.keys()
    
    for cat in categories:
        if cat in TERMS:
            for key, translations in TERMS[cat].items():
                if translations.get(source_lang) == term:
                    return translations.get(lang, term)
    
    return term


def get_city_name(city_code: str, lang: str = 'en') -> str:
    """
    Get city name in the target language
    
    Args:
        city_code: City code (lowercase, underscore format)
        lang: Target language ('en' or 'zh')
    
    Returns:
        City name in target language
    """
    city_code_lower = city_code.lower().replace(' ', '_')
    
    if city_code_lower in CITY_NAMES:
        return CITY_NAMES[city_code_lower].get(lang, city_code)
    
    return city_code


def get_city_code(city_name: str) -> Optional[str]:
    """
    Get city code from city name (Chinese or English)
    
    Args:
        city_name: City name in Chinese or English
    
    Returns:
        City code or None if not found
    """
    for code, names in CITY_NAMES.items():
        if city_name in names.values():
            return code
    
    city_name_lower = city_name.lower().replace(' ', '_')
    if city_name_lower in CITY_NAMES:
        return city_name_lower
    
    return None


def format_number(value: float, lang: str = 'en') -> str:
    """
    Format number according to language
    
    Args:
        value: Number to format
        lang: Target language
    
    Returns:
        Formatted number string
    """
    if lang == 'en':
        return f"{value:,.0f}"
    else:
        return f"{value:,.0f}".replace(',', ',').replace('.', '.')


def format_currency(value: float, lang: str = 'en', currency: str = 'CNY') -> str:
    """
    Format currency according to language
    
    Args:
        value: Amount to format
        lang: Target language
        currency: Currency code
    
    Returns:
        Formatted currency string
    """
    if lang == 'en':
        if currency == 'CNY':
            return f"CNY {value:,.0f}"
        else:
            return f"${value:,.0f}"
    else:
        if currency == 'CNY':
            return f"{value:,.0f}元"
        else:
            return f"{value:,.0f}美元"


def format_area(value: float, lang: str = 'en') -> str:
    """
    Format area according to language
    
    Args:
        value: Area in square meters
        lang: Target language
    
    Returns:
        Formatted area string
    """
    if lang == 'en':
        return f"{value:,.0f} sqm"
    else:
        return f"{value:,.0f}平方米"


translation_service = {
    'translate_term': translate_term,
    'get_city_name': get_city_name,
    'get_city_code': get_city_code,
    'format_number': format_number,
    'format_currency': format_currency,
    'format_area': format_area,
}
