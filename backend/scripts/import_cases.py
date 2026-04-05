# -*- coding: utf-8 -*-
"""
案例导入脚本
将情感咨询.md中的案例导入到案例库系统
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.case_library import (
    CaseLibrary, CaseRecord, CaseType, CaseStatus,
    UserProfile, SixDimensionAnalysis
)
from datetime import datetime
import uuid

def create_emotion_case():
    """创建情感咨询案例"""
    case = CaseRecord(
        id=f"case_{uuid.uuid4().hex[:8]}",
        case_type=CaseType.EMOTION,
        status=CaseStatus.PUBLISHED,
        
        user_profile=UserProfile(
            birth_year=1999,
            zodiac="兔",
            birth_month=12,
            birth_day=17,
            gender="男",
            city="苏州",
            profession="医美医生"
        ),
        
        question="我始终难过情关，这个女生和我在一起半年多，她是苏南我是苏北，比我大，收入比我好。我习惯多付出，她强调等价交换，我走进了死胡同。",
        question_category="感情",
        question_subcategory="付出模式冲突",
        
        analysis=SixDimensionAnalysis(
            pattern={
                "summary": "文昌在命，天机坐守，适合靠技术、专业吃饭",
                "trait": "保护者心态，习惯多付出、少计较",
                "strength": "责任感强，喜欢把身边人护在身后"
            },
            wealth={
                "summary": "正财星旺，偏财星弱",
                "trait": "钱是养出来的，不是赌出来的",
                "advice": "适合用时间换空间"
            },
            marriage={
                "summary": "生肖三合（卯亥），非常相配",
                "issue": "付出模式对不上：你习惯多给，她习惯等价交换",
                "advice": "别问算不算正缘，先把手里的关系处明白"
            },
            career={
                "summary": "25岁，流年丙午（火旺），点火之年",
                "choice": "苏州是根，南京是场",
                "advice": "稳中求进，半年铺路"
            },
            social={
                "summary": "苏州有信任的同事老师、亲人，是滋养型关系",
                "advice": "南京朋友是机会型关系，不是靠山"
            },
            execution={
                "summary": "执行力中上，心态容易波动",
                "issue": "太想一次把路走对，反复纠结",
                "advice": "先走一步，别想太多做太少"
            }
        ),
        
        dialogue_history=[
            {"role": "user", "content": "老师 我有个困惑 我最近内心出问题了 我始终难过情关..."},
            {"role": "assistant", "content": "我感受到了您话里的重量。内心困住自己，是最难受的..."},
            {"role": "user", "content": "99 12 17 她95 03 25"},
            {"role": "assistant", "content": "您出生于1999年12月17日，属兔..."},
            {"role": "user", "content": "老师 这个应该不算自己的正缘对不对"},
            {"role": "assistant", "content": "您先别急着下'算不算正缘'这个结论..."},
            {"role": "user", "content": "老师 我觉得可以 时间问题 我对自己有信心"},
            {"role": "assistant", "content": "好！您这句话，让我听出了决心..."}
        ],
        
        recommendations=[
            {
                "dimension": "感情",
                "recommendation": "把'我应该多付出'换成'我乐意付出多少'",
                "reason": "付出不该由对方条件决定，而应该由自己意愿决定"
            },
            {
                "dimension": "沟通",
                "recommendation": "跟她聊一次'我们各自对公平的理解'",
                "script": "我知道你很看重关系里的平等，这一点我很尊重..."
            },
            {
                "dimension": "心态",
                "recommendation": "放下'她和她前男友的画面'",
                "reason": "那些画面是自己画的，不是她给的"
            }
        ],
        
        action_steps=[
            {"step": 1, "action": "本周每天睡前问自己：今天我为自己做了一件什么事？", "timeline": "本周"},
            {"step": 2, "action": "找个平静的时候，跟她聊聊对公平的理解", "timeline": "两周内"},
            {"step": 3, "action": "观察自己的付出模式，记录每次付出时的心态", "timeline": "持续"}
        ],
        
        final_decision="稳中求进，先调整付出模式",
        outcome="持续跟踪中",
        
        tags=["感情", "付出模式", "生肖三合", "兔猪", "医美医生", "苏州", "南京"],
        rating=5,
        feedback="用户表示对自己有信心，愿意尝试调整"
    )
    
    return case

def create_career_case():
    """创建职业选择案例"""
    case = CaseRecord(
        id=f"case_{uuid.uuid4().hex[:8]}",
        case_type=CaseType.CAREER,
        status=CaseStatus.PUBLISHED,
        
        user_profile=UserProfile(
            birth_year=1999,
            zodiac="兔",
            birth_month=12,
            birth_day=17,
            gender="男",
            city="苏州",
            profession="医美医生"
        ),
        
        question="我这一年工作适不适合变动？现在在苏州做仪器，想去南京学打针，但南京那边不稳定。",
        question_category="事业",
        question_subcategory="职业变动",
        
        analysis=SixDimensionAnalysis(
            pattern={
                "summary": "文昌在命，天生适合靠技术、专业吃饭",
                "trait": "内心有股不甘平庸的劲，总想突破上限"
            },
            wealth={
                "summary": "正财旺，适合稳扎稳打",
                "current": "月入一万多，有上限",
                "potential": "学打针后收入可翻倍"
            },
            marriage={
                "summary": "感情稳定，但需要调整付出模式"
            },
            career={
                "summary": "25岁，流年丙午，点火之年",
                "choice_suzhou": "行业头部，稳定，有信任的同事和亲人",
                "choice_nanjing": "学打针机会，但项目不稳定",
                "advice": "稳中求进：保住苏州，用业余时间去南京练手"
            },
            social={
                "suzhou": "滋养型关系：信任的同事、亲人",
                "nanjing": "机会型关系：94年女老总，朋友但交情不深"
            },
            execution={
                "summary": "有决心，说'稳中求进'",
                "goal": "48w目标",
                "advice": "把大目标拆成小步骤"
            }
        ),
        
        dialogue_history=[
            {"role": "user", "content": "老师 能不能帮我看一下 我这一年工作适不适合变动..."},
            {"role": "assistant", "content": "您这个问题问得实在——是守着安稳但有上限的现在..."},
            {"role": "user", "content": "对的 但是老师我迟早要去做针剂的，我25周岁..."},
            {"role": "assistant", "content": "一个月没见，您还在琢磨这件事..."},
            {"role": "user", "content": "当时大师说我要向南方的城市发展..."},
            {"role": "assistant", "content": "大师说您适合向南发展，没错..."},
            {"role": "user", "content": "好 老师我懂了 我要完成老师你给我的48w约定，稳中求进"},
            {"role": "assistant", "content": "好！您这句话，让我听出了决心..."}
        ],
        
        recommendations=[
            {
                "dimension": "事业",
                "recommendation": "三明治方案：保苏州+去南京练手+设时间窗口",
                "reason": "既不丢安全感，又抓住机会"
            },
            {
                "dimension": "技术",
                "recommendation": "利用周末、调休去南京学习打针",
                "timeline": "半年内"
            },
            {
                "dimension": "人脉",
                "recommendation": "把南京老总当贵人，不当靠山",
                "reason": "利用机会学技术，职业规划以自己为主"
            }
        ],
        
        action_steps=[
            {"step": 1, "action": "继续在苏州工作，不辞职", "timeline": "现在"},
            {"step": 2, "action": "利用周末去南京学打针技术", "timeline": "每月1-2次"},
            {"step": 3, "action": "观察南京项目落地情况", "timeline": "半年内"},
            {"step": 4, "action": "技术学成后，评估是否全职转南京", "timeline": "半年后"}
        ],
        
        final_decision="稳中求进，48w目标",
        outcome="持续跟踪中",
        
        tags=["事业", "职业变动", "医美", "苏州", "南京", "稳中求进", "25岁"],
        rating=5,
        feedback="用户明确表示'稳中求进'，有决心完成48w目标"
    )
    
    return case

def import_cases():
    """导入所有案例"""
    library = CaseLibrary()
    
    # 创建情感案例
    emotion_case = create_emotion_case()
    library.add_case(emotion_case)
    print(f"导入情感案例: {emotion_case.id}")
    
    # 创建职业案例
    career_case = create_career_case()
    library.add_case(career_case)
    print(f"导入职业案例: {career_case.id}")
    
    # 打印统计信息
    stats = library.get_statistics()
    print(f"\n案例库统计:")
    print(f"  总案例数: {stats['total_cases']}")
    print(f"  按类型: {stats['by_type']}")
    print(f"  平均评分: {stats['avg_rating']:.1f}")

if __name__ == "__main__":
    import_cases()
