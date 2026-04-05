"""
初始化SEO文章数据
"""
import asyncio
import aiosqlite
import json
from pathlib import Path
from datetime import datetime
import uuid

DB_PATH = Path(__file__).parent.parent / "data" / "property-ai.db"

# SEO文章内容
ARTICLE_CONTENT = '''# 4+7 之后，房子的事该想明白

文/老骇

---

关于房子，我写过不少。

但今天想专门聊聊"4+7"这件事。因为这个概念被我提出来之后，传着传着就失真了，有人把它当投资口诀，有人把它当买房圣经。

其实都不是。

4+7，是对未来资源流向的一个观察，仅此而已。

---

## 一、什么是 4+7？

简单说，就是 11 座城市：

**4** 座一线：北京、上海、广州、深圳  
**7** 座核心二线：杭州、苏州、重庆、成都、武汉、合肥、南京

不是说其他城市不能住人，也不是说其他地方没有好房子。而是说，未来所有的核心资源——资金、产业、人才、政策红利——都会全方位地向这 11 座城市倾斜。

这是一个资源有限前提下的必然选择。

以现有盘面总量的极限，只能供这 11 座城市继续进行深度开发。其他的，能维持现状就不错。

---

## 二、为什么是这 11 座？

有人问：凭什么？我老家也很努力啊。

这话让我想起一个比喻：一场马拉松，跑到后半程，第一梯队和第二梯队的距离会越拉越大。不是第二梯队跑得慢，而是第一梯队的资源补给、医疗保障、教练团队都更优，形成了正向循环。

城市发展也是一样。

过去二十年，几乎所有城市都在往上走，差别只是走多快。但现在不一样了——增量放缓，存量博弈开始。资金总量就这么多，人才就这么多，好项目就这么多。往哪里投？

一定是往基础最好、回报最稳、预期最明确的地方投。

北上广深不用说，那是国运的基本盘。杭州有数字经济，苏州有工业园区，重庆成都成渝双圈，武汉九省通衢，合肥风投之城，南京科教重镇。每一座，都有自己不可替代的生态位。

这不是谁更努力的问题，是历史和现实共同筛选的结果。

---

## 三、房子背后，是"产"

很多人看房子，只看"房"——面积、户型、装修、楼层。

但真正决定价值的，是"产"——产业、产权、教育资源、医疗资源、圈层资源。

同样 100 平米的房子，放在鹤岗可能只值几万，放在上海可能值几百万。差的不是那 100 平米的钢筋水泥，是背后附着的一切。

北京海淀的一套老破小，为什么能卖出天价？因为它的"产"里，有全中国最顶级的教育资源。

上海徐汇的一套老公房，为什么一直有人接盘？因为它的"产"里，有三甲医院的床位、有跨国公司的工作机会、有下一代能接触到的人脉圈层。

这就是 4+7 的逻辑核心：**你买的不是房子，是你和你的家庭，能接入的资源配置网络。**

---

## 四、那其他城市怎么办？

客观说，也能活，而且能活得不错。

基础建设都不差，商场、医院、学校都有，生活成本还低。如果你能接受"质朴且简约地活着"，那没问题，日子可以过得很舒服。

但如果你想问的是资产价值——未来会不会涨？流通性好不好？能不能传给下一代？

答案就有点残酷了：**二三线城市的房子，正在不可逆转地失去金融属性。**

人口外流，资源外溢，年轻人都往核心城市跑。没有新增人口，就没有新增需求。没有新增需求，再好的房子也只是消费品，不是资产。

消费品的意思是：你买它，是因为你需要用，别指望它升值。

很多人不理解这一点，还在拿着过去二十年的经验，觉得"房子永远是涨的"。但过去二十年是城市化率从 30% 冲到 65% 的黄金时代，那个时代已经结束了。

---

## 五、那该怎么办？

如果你已经在这 11 座城市里，恭喜你，拿到了入场券。接下来要做的，是优化——把房子往更好的地段、更好的品质、更好的资源上换。

如果你不在，又想上车，那就得认真想想：要不要置换？

这个话题我不展开说，因为涉及太多个人选择。只想提醒一点：**城市会造就人，城市也会拖垮人。** 在一个不断失血的环境里，再努力也很难逆势而上。

当然，如果你能接受现状，觉得"我就想在老家安安稳稳过"，那也没问题。怕的是明明心里不甘，却下不了决心，一天天拖下去，最后连选择的机会都没了。

---

## 六、一些碎片

写完上面这些，再给你几条碎片的思考，可能不成体系，但都是真话：

**第一，关于周期。**

现在确实不太好，各种数据都在往下走。但周期这东西，有下就有上。问题是，你能不能活到上的那天。

**第二，关于杠杆。**

现在这个阶段，除非你现金流极其稳健，否则不要加杠杆。好资产，可以等，但不能赌。

**第三，关于信息。**

网上太多人在讨论房子，但大多数都是情绪，没有信息。真正有用的信息，往往不在公开渠道。

**第四，关于心态。**

我见过太多人，因为房子的事把自己搞得很焦虑。其实没必要。房子只是工具，不是目的。把日子过好，把身体养好，把该做的事做好，比什么都强。

---

最后，想跟你说一句：

不管你有没有房，在什么城市，都不用把自己逼得太紧。

人生很长，房子只是其中的一站。看得明白，走稳当，比什么都重要。

---

**本文首发于公众号「意骇有道」。**

**需要《城市白皮書》电子书的读者，后台回复【666】。
'''

ARTICLE_SUMMARY = "关于房子，我写过不少。但今天想专门聊聊4+7这件事。因为这个概念被我提出来之后，传着传着就失真了，有人把它当投资口诀，有人把它当买房圣经。其实都不是。4+7，是对未来资源流向的一个观察，仅此而已。"

async def init_articles():
    """初始化文章数据"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = await aiosqlite.connect(str(DB_PATH))
    conn.row_factory = aiosqlite.Row
    
    try:
        # 创建文章表（如果不存在）
        await conn.executescript("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                content TEXT,
                summary TEXT,
                cover_image TEXT,
                category TEXT DEFAULT 'news',
                tags TEXT DEFAULT '[]',
                author_id TEXT,
                status TEXT DEFAULT 'draft',
                is_featured INTEGER DEFAULT 0,
                view_count INTEGER DEFAULT 0,
                like_count INTEGER DEFAULT 0,
                comment_count INTEGER DEFAULT 0,
                published_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            
            CREATE INDEX IF NOT EXISTS idx_articles_slug ON articles(slug);
            CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category);
            CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status);
            
            CREATE TABLE IF NOT EXISTS article_comments (
                id TEXT PRIMARY KEY,
                article_id TEXT NOT NULL,
                user_id TEXT,
                parent_id TEXT,
                content TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                ip_address TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            );
        """)
        
        # 检查文章是否已存在
        cursor = await conn.execute(
            "SELECT id FROM articles WHERE slug = ?", 
            ("4-7-zhihou-fangzi-de-shi-gai-xiang-mingbai",)
        )
        existing = await cursor.fetchone()
        
        if existing:
            print("文章已存在，跳过创建")
            return
        
        # 创建文章
        article_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()
        
        await conn.execute("""
            INSERT INTO articles 
            (id, title, slug, content, summary, category, tags, 
             author_id, status, is_featured, published_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            article_id,
            "4+7 之后，房子的事该想明白",
            "4-7-zhihou-fangzi-de-shi-gai-xiang-mingbai",
            ARTICLE_CONTENT,
            ARTICLE_SUMMARY,
            "analysis",
            json.dumps(["房产投资", "4+7城市", "市场分析", "老骇"], ensure_ascii=False),
            "system",
            "published",
            1,  # is_featured
            now
        ))
        
        await conn.commit()
        print(f"✅ 文章创建成功: {article_id}")
        
    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(init_articles())
