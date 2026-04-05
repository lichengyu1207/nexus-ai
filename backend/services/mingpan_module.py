# -*- coding: utf-8 -*-
"""
命盘解析模块
基于八字理论的命盘分析和六维框架映射
"""
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class WuXing(str, Enum):
    """五行"""
    JIN = "金"
    MU = "木"
    SHUI = "水"
    HUO = "火"
    TU = "土"

class TianGan(str, Enum):
    """天干"""
    JIA = "甲"
    YI = "乙"
    BING = "丙"
    DING = "丁"
    WU = "戊"
    JI = "己"
    GENG = "庚"
    XIN = "辛"
    REN = "壬"
    GUI = "癸"

class DiZhi(str, Enum):
    """地支"""
    ZI = "子"
    CHOU = "丑"
    YIN = "寅"
    MAO = "卯"
    CHEN = "辰"
    SI = "巳"
    WU = "午"
    WEI = "未"
    SHEN = "申"
    YOU = "酉"
    XU = "戌"
    HAI = "亥"

@dataclass
class BaZi:
    """八字"""
    year_gan: str
    year_zhi: str
    month_gan: str
    month_zhi: str
    day_gan: str
    day_zhi: str
    hour_gan: str
    hour_zhi: str

@dataclass
class SixDimensionResult:
    """六维分析结果"""
    pattern: Dict[str, Any] = field(default_factory=dict)
    wealth: Dict[str, Any] = field(default_factory=dict)
    marriage: Dict[str, Any] = field(default_factory=dict)
    career: Dict[str, Any] = field(default_factory=dict)
    social: Dict[str, Any] = field(default_factory=dict)
    execution: Dict[str, Any] = field(default_factory=dict)

class MingpanParser:
    """
    命盘解析器
    
    基于出生时间解析八字命盘
    """
    
    def __init__(self):
        self.tian_gan = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
        self.di_zhi = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
        
        self.tian_gan_wuxing = {
            "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
            "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"
        }
        
        self.di_zhi_wuxing = {
            "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
            "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"
        }
        
        self.zodiac_map = {
            "子": "鼠", "丑": "牛", "寅": "虎", "卯": "兔", "辰": "龙", "巳": "蛇",
            "午": "马", "未": "羊", "申": "猴", "酉": "鸡", "戌": "狗", "亥": "猪"
        }
        
        self.wuxing_direction = {
            "金": "西", "木": "东", "水": "北", "火": "南", "土": "中"
        }
        
        self.san_he = {
            "申子辰": "水", "亥卯未": "木", "寅午戌": "火", "巳酉丑": "金"
        }
    
    def parse_birth(self, year: int, month: int, day: int, hour: int = 0) -> BaZi:
        """
        解析出生时间为八字
        
        Args:
            year: 出生年份
            month: 出生月份
            day: 出生日
            hour: 出生时辰（默认子时）
        
        Returns:
            BaZi: 八字
        """
        year_gan_idx = (year - 4) % 10
        year_zhi_idx = (year - 4) % 12
        
        year_gan = self.tian_gan[year_gan_idx]
        year_zhi = self.di_zhi[year_zhi_idx]
        
        month_gan_idx = (year_gan_idx * 2 + month) % 10
        month_zhi_idx = (month + 1) % 12
        month_gan = self.tian_gan[month_gan_idx]
        month_zhi = self.di_zhi[month_zhi_idx]
        
        base_date = datetime(1900, 1, 31)
        target_date = datetime(year, month, day)
        days_diff = (target_date - base_date).days
        day_gan_idx = (days_diff + 4) % 10
        day_zhi_idx = (days_diff + 4) % 12
        day_gan = self.tian_gan[day_gan_idx]
        day_zhi = self.di_zhi[day_zhi_idx]
        
        hour_zhi_idx = ((hour + 1) // 2) % 12
        hour_gan_idx = (day_gan_idx * 2 + hour_zhi_idx) % 10
        hour_gan = self.tian_gan[hour_gan_idx]
        hour_zhi = self.di_zhi[hour_zhi_idx]
        
        return BaZi(
            year_gan=year_gan,
            year_zhi=year_zhi,
            month_gan=month_gan,
            month_zhi=month_zhi,
            day_gan=day_gan,
            day_zhi=day_zhi,
            hour_gan=hour_gan,
            hour_zhi=hour_zhi
        )
    
    def get_zodiac(self, year_zhi: str) -> str:
        """获取生肖"""
        return self.zodiac_map.get(year_zhi, "未知")
    
    def get_day_master_wuxing(self, day_gan: str) -> str:
        """获取日主五行"""
        return self.tian_gan_wuxing.get(day_gan, "未知")
    
    def analyze_wuxing_strength(self, bazi: BaZi) -> Dict[str, int]:
        """
        分析五行强弱
        
        Args:
            bazi: 八字
        
        Returns:
            Dict: 五行强度
        """
        wuxing_count = {"金": 0, "木": 0, "水": 0, "火": 0, "土": 0}
        
        for gan in [bazi.year_gan, bazi.month_gan, bazi.day_gan, bazi.hour_gan]:
            wx = self.tian_gan_wuxing.get(gan)
            if wx:
                wuxing_count[wx] += 2
        
        for zhi in [bazi.year_zhi, bazi.month_zhi, bazi.day_zhi, bazi.hour_zhi]:
            wx = self.di_zhi_wuxing.get(zhi)
            if wx:
                wuxing_count[wx] += 1
        
        return wuxing_count
    
    def get_favorable_direction(self, wuxing_strength: Dict[str, int]) -> str:
        """
        获取有利方位
        
        Args:
            wuxing_strength: 五行强度
        
        Returns:
            有利方位
        """
        min_wuxing = min(wuxing_strength, key=wuxing_strength.get)
        return self.wuxing_direction.get(min_wuxing, "中")
    
    def check_san_he(self, zhi1: str, zhi2: str) -> Optional[str]:
        """
        检查三合
        
        Args:
            zhi1: 地支1
            zhi2: 地支2
        
        Returns:
            三合五行或None
        """
        for combo, wuxing in self.san_he.items():
            if zhi1 in combo and zhi2 in combo:
                return wuxing
        return None

class SixDimensionAnalyzer:
    """
    六维框架分析器
    
    将命盘映射到六维框架
    """
    
    def __init__(self):
        self.parser = MingpanParser()
        
        self.xing_yao_map = {
            "文昌": ["甲", "乙", "丙", "丁"],
            "文曲": ["壬", "癸"],
            "武曲": ["庚", "辛"],
            "天机": ["乙"],
            "紫微": ["己"],
            "天相": ["壬"],
        }
        
        self.cai_xing_map = {
            "正财": {"strong": ["戊", "己"], "weak": ["壬", "癸"]},
            "偏财": {"strong": ["庚", "辛"], "weak": ["甲", "乙"]}
        }
    
    def analyze(self, bazi: BaZi) -> SixDimensionResult:
        """
        执行六维分析
        
        Args:
            bazi: 八字
        
        Returns:
            SixDimensionResult: 六维分析结果
        """
        result = SixDimensionResult()
        
        wuxing_strength = self.parser.analyze_wuxing_strength(bazi)
        day_master_wuxing = self.parser.get_day_master_wuxing(bazi.day_gan)
        favorable_direction = self.parser.get_favorable_direction(wuxing_strength)
        
        result.pattern = self._analyze_pattern(bazi, day_master_wuxing)
        result.wealth = self._analyze_wealth(bazi, wuxing_strength)
        result.marriage = self._analyze_marriage(bazi)
        result.career = self._analyze_career(bazi, day_master_wuxing)
        result.social = self._analyze_social(bazi)
        result.execution = self._analyze_execution(bazi, wuxing_strength)
        
        return result
    
    def _analyze_pattern(self, bazi: BaZi, day_master_wuxing: str) -> Dict[str, Any]:
        """分析格局"""
        xing_yao = []
        for xing, gans in self.xing_yao_map.items():
            if bazi.day_gan in gans:
                xing_yao.append(xing)
        
        trait_map = {
            "文昌": "适合靠技术、专业吃饭，对知识敏感",
            "文曲": "有文艺气质，善于表达",
            "武曲": "有管理能力，适合金融、技术",
            "天机": "心思细腻，善于谋划",
            "紫微": "有领导气质，适合管理",
        }
        
        traits = [trait_map.get(x, "") for x in xing_yao]
        
        return {
            "summary": f"{bazi.day_gan}{bazi.day_zhi}日主，{day_master_wuxing}命",
            "xing_yao": xing_yao,
            "trait": "、".join(traits) if traits else "稳扎稳打型",
            "strength": "适合靠积累成长，不适合投机冒险"
        }
    
    def _analyze_wealth(self, bazi: BaZi, wuxing_strength: Dict[str, int]) -> Dict[str, Any]:
        """分析财运"""
        day_wuxing = self.parser.get_day_master_wuxing(bazi.day_gan)
        
        wuxing_ke = {
            "木": "土", "火": "金", "土": "水", "金": "木", "水": "火"
        }
        wuxing_wo = {
            "木": "水", "火": "木", "土": "火", "金": "土", "水": "金"
        }
        
        cai_wuxing = wuxing_ke.get(day_wuxing, "土")
        cai_strength = wuxing_strength.get(cai_wuxing, 0)
        
        if cai_strength >= 3:
            wealth_type = "财星旺"
            advice = "有财运，但要注意守财，避免冲动消费"
        elif cai_strength >= 1:
            wealth_type = "财星中等"
            advice = "财运平稳，适合稳健投资"
        else:
            wealth_type = "财星弱"
            advice = "财运需要培养，适合正财路线，不宜投机"
        
        return {
            "summary": wealth_type,
            "cai_wuxing": cai_wuxing,
            "strength": cai_strength,
            "trait": "正财型" if cai_strength < 3 else "偏财型",
            "advice": advice
        }
    
    def _analyze_marriage(self, bazi: BaZi) -> Dict[str, Any]:
        """分析姻缘"""
        day_zhi = bazi.day_zhi
        
        sha_xing = ["子", "午", "卯", "酉"]
        if day_zhi in sha_xing:
            marriage_note = "夫妻宫有桃花，感情丰富，但要注意专一"
        else:
            marriage_note = "夫妻宫稳定，适合建立长期关系"
        
        return {
            "summary": f"日支{day_zhi}，{marriage_note}",
            "day_zhi": day_zhi,
            "trait": "感情细腻，重视家庭",
            "advice": "适合找性格互补的伴侣"
        }
    
    def _analyze_career(self, bazi: BaZi, day_master_wuxing: str) -> Dict[str, Any]:
        """分析事业"""
        favorable_direction = self.parser.get_favorable_direction(
            self.parser.analyze_wuxing_strength(bazi)
        )
        
        direction_cities = {
            "东": ["杭州", "苏州", "上海", "南京"],
            "南": ["广州", "深圳", "厦门", "海口"],
            "西": ["成都", "重庆", "西安", "兰州"],
            "北": ["北京", "天津", "沈阳", "哈尔滨"],
            "中": ["武汉", "长沙", "郑州", "合肥"]
        }
        
        cities = direction_cities.get(favorable_direction, ["待定"])
        
        return {
            "summary": f"适合往{favorable_direction}方发展",
            "favorable_direction": favorable_direction,
            "recommended_cities": cities,
            "trait": "适合稳定发展，不宜频繁跳槽",
            "advice": "选择一个方向深耕，积累比跳槽更重要"
        }
    
    def _analyze_social(self, bazi: BaZi) -> Dict[str, Any]:
        """分析人际"""
        return {
            "summary": "人际关系稳定",
            "trait": "善于维护长期关系",
            "advice": "多结交滋养型朋友，远离消耗型关系"
        }
    
    def _analyze_execution(self, bazi: BaZi, wuxing_strength: Dict[str, int]) -> Dict[str, Any]:
        """分析执行力"""
        total = sum(wuxing_strength.values())
        
        if total > 12:
            level = "强"
            advice = "行动力强，但要注意方向，避免盲目行动"
        elif total > 8:
            level = "中等"
            advice = "行动力适中，需要明确目标后再行动"
        else:
            level = "需要培养"
            advice = "容易想得多做得少，建议把大目标拆成小步骤"
        
        return {
            "summary": f"执行力{level}",
            "level": level,
            "wuxing_balance": wuxing_strength,
            "advice": advice
        }

class MingpanModule:
    """
    命盘模块
    
    提供完整的命盘分析功能
    """
    
    def __init__(self):
        self.parser = MingpanParser()
        self.analyzer = SixDimensionAnalyzer()
    
    def analyze(self, birth_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行命盘分析
        
        Args:
            birth_info: 出生信息
                - year: 出生年份
                - month: 出生月份
                - day: 出生日
                - hour: 出生时辰（可选）
        
        Returns:
            Dict: 分析结果
        """
        year = birth_info.get("year", 1990)
        month = birth_info.get("month", 1)
        day = birth_info.get("day", 1)
        hour = birth_info.get("hour", 0)
        
        bazi = self.parser.parse_birth(year, month, day, hour)
        zodiac = self.parser.get_zodiac(bazi.year_zhi)
        day_master_wuxing = self.parser.get_day_master_wuxing(bazi.day_gan)
        wuxing_strength = self.parser.analyze_wuxing_strength(bazi)
        favorable_direction = self.parser.get_favorable_direction(wuxing_strength)
        six_dim = self.analyzer.analyze(bazi)
        
        return {
            "bazi": {
                "year": f"{bazi.year_gan}{bazi.year_zhi}",
                "month": f"{bazi.month_gan}{bazi.month_zhi}",
                "day": f"{bazi.day_gan}{bazi.day_zhi}",
                "hour": f"{bazi.hour_gan}{bazi.hour_zhi}"
            },
            "zodiac": zodiac,
            "day_master": bazi.day_gan,
            "day_master_wuxing": day_master_wuxing,
            "wuxing_strength": wuxing_strength,
            "favorable_direction": favorable_direction,
            "six_dimensions": {
                "pattern": six_dim.pattern,
                "wealth": six_dim.wealth,
                "marriage": six_dim.marriage,
                "career": six_dim.career,
                "social": six_dim.social,
                "execution": six_dim.execution
            }
        }
    
    def check_compatibility(self, birth1: Dict, birth2: Dict) -> Dict[str, Any]:
        """
        检查两人合盘
        
        Args:
            birth1: 第一人出生信息
            birth2: 第二人出生信息
        
        Returns:
            Dict: 合盘分析结果
        """
        bazi1 = self.parser.parse_birth(
            birth1.get("year", 1990),
            birth1.get("month", 1),
            birth1.get("day", 1),
            birth1.get("hour", 0)
        )
        bazi2 = self.parser.parse_birth(
            birth2.get("year", 1990),
            birth2.get("month", 1),
            birth2.get("day", 1),
            birth2.get("hour", 0)
        )
        
        zodiac1 = self.parser.get_zodiac(bazi1.year_zhi)
        zodiac2 = self.parser.get_zodiac(bazi2.year_zhi)
        
        san_he_result = self.parser.check_san_he(bazi1.year_zhi, bazi2.year_zhi)
        
        score = 60
        if san_he_result:
            score += 20
            compatibility = "生肖三合，非常相配"
        else:
            compatibility = "生肖普通，需要其他维度配合"
        
        day_wuxing1 = self.parser.get_day_master_wuxing(bazi1.day_gan)
        day_wuxing2 = self.parser.get_day_master_wuxing(bazi2.day_gan)
        
        wuxing_sheng = {
            "木": "火", "火": "土", "土": "金", "金": "水", "水": "木"
        }
        
        if wuxing_sheng.get(day_wuxing1) == day_wuxing2:
            score += 10
            compatibility += f"，{day_wuxing1}生{day_wuxing2}"
        elif wuxing_sheng.get(day_wuxing2) == day_wuxing1:
            score += 10
            compatibility += f"，{day_wuxing2}生{day_wuxing1}"
        
        return {
            "zodiac1": zodiac1,
            "zodiac2": zodiac2,
            "san_he": san_he_result,
            "compatibility": compatibility,
            "score": min(score, 100),
            "day_wuxing1": day_wuxing1,
            "day_wuxing2": day_wuxing2
        }

mingpan_module = MingpanModule()
