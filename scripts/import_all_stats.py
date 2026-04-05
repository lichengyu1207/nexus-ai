import asyncio
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "property-ai.db"

ADMIN_DIVISION_DATA = {
    "北京市": {"prefecture_count": 0, "county_count": 16, "prefecture_city": 0, "district": 16, "county_city": 0, "county": 0, "autonomous_county": 0},
    "天津市": {"prefecture_count": 0, "county_count": 16, "prefecture_city": 0, "district": 16, "county_city": 0, "county": 0, "autonomous_county": 0},
    "河北省": {"prefecture_count": 11, "county_count": 167, "prefecture_city": 11, "district": 49, "county_city": 21, "county": 91, "autonomous_county": 6},
    "山西省": {"prefecture_count": 11, "county_count": 117, "prefecture_city": 11, "district": 26, "county_city": 11, "county": 80, "autonomous_county": 0},
    "内蒙古自治区": {"prefecture_count": 12, "county_count": 103, "prefecture_city": 9, "district": 23, "county_city": 11, "county": 17, "autonomous_county": 0},
    "辽宁省": {"prefecture_count": 14, "county_count": 100, "prefecture_city": 14, "district": 59, "county_city": 16, "county": 17, "autonomous_county": 8},
    "吉林省": {"prefecture_count": 9, "county_count": 60, "prefecture_city": 8, "district": 21, "county_city": 20, "county": 16, "autonomous_county": 3},
    "黑龙江省": {"prefecture_count": 13, "county_count": 121, "prefecture_city": 12, "district": 54, "county_city": 21, "county": 45, "autonomous_county": 1},
    "上海市": {"prefecture_count": 0, "county_count": 16, "prefecture_city": 0, "district": 16, "county_city": 0, "county": 0, "autonomous_county": 0},
    "江苏省": {"prefecture_count": 13, "county_count": 95, "prefecture_city": 13, "district": 55, "county_city": 21, "county": 19, "autonomous_county": 0},
    "浙江省": {"prefecture_count": 11, "county_count": 90, "prefecture_city": 11, "district": 37, "county_city": 20, "county": 32, "autonomous_county": 1},
    "安徽省": {"prefecture_count": 16, "county_count": 104, "prefecture_city": 16, "district": 45, "county_city": 9, "county": 50, "autonomous_county": 0},
    "福建省": {"prefecture_count": 9, "county_count": 84, "prefecture_city": 9, "district": 31, "county_city": 11, "county": 42, "autonomous_county": 0},
    "江西省": {"prefecture_count": 11, "county_count": 100, "prefecture_city": 11, "district": 27, "county_city": 12, "county": 61, "autonomous_county": 0},
    "山东省": {"prefecture_count": 16, "county_count": 136, "prefecture_city": 16, "district": 58, "county_city": 26, "county": 52, "autonomous_county": 0},
    "河南省": {"prefecture_count": 17, "county_count": 157, "prefecture_city": 17, "district": 54, "county_city": 21, "county": 82, "autonomous_county": 0},
    "湖北省": {"prefecture_count": 13, "county_count": 103, "prefecture_city": 12, "district": 39, "county_city": 26, "county": 35, "autonomous_county": 2},
    "湖南省": {"prefecture_count": 14, "county_count": 122, "prefecture_city": 13, "district": 36, "county_city": 19, "county": 60, "autonomous_county": 7},
    "广东省": {"prefecture_count": 21, "county_count": 122, "prefecture_city": 21, "district": 65, "county_city": 20, "county": 34, "autonomous_county": 3},
    "广西壮族自治区": {"prefecture_count": 14, "county_count": 111, "prefecture_city": 14, "district": 41, "county_city": 10, "county": 48, "autonomous_county": 12},
    "海南省": {"prefecture_count": 4, "county_count": 25, "prefecture_city": 4, "district": 10, "county_city": 5, "county": 4, "autonomous_county": 6},
    "重庆市": {"prefecture_count": 0, "county_count": 38, "prefecture_city": 0, "district": 26, "county_city": 0, "county": 8, "autonomous_county": 4},
    "四川省": {"prefecture_count": 21, "county_count": 183, "prefecture_city": 18, "district": 55, "county_city": 19, "county": 105, "autonomous_county": 4},
    "贵州省": {"prefecture_count": 9, "county_count": 88, "prefecture_city": 6, "district": 16, "county_city": 10, "county": 50, "autonomous_county": 11},
    "云南省": {"prefecture_count": 16, "county_count": 129, "prefecture_city": 8, "district": 17, "county_city": 18, "county": 65, "autonomous_county": 29},
    "西藏自治区": {"prefecture_count": 7, "county_count": 74, "prefecture_city": 6, "district": 8, "county_city": 2, "county": 64, "autonomous_county": 0},
    "陕西省": {"prefecture_count": 10, "county_count": 107, "prefecture_city": 10, "district": 31, "county_city": 7, "county": 69, "autonomous_county": 0},
    "甘肃省": {"prefecture_count": 14, "county_count": 86, "prefecture_city": 12, "district": 17, "county_city": 5, "county": 57, "autonomous_county": 7},
    "青海省": {"prefecture_count": 8, "county_count": 44, "prefecture_city": 2, "district": 7, "county_city": 5, "county": 25, "autonomous_county": 7},
    "宁夏回族自治区": {"prefecture_count": 5, "county_count": 22, "prefecture_city": 5, "district": 9, "county_city": 2, "county": 11, "autonomous_county": 0},
    "新疆维吾尔自治区": {"prefecture_count": 14, "county_count": 108, "prefecture_city": 4, "district": 13, "county_city": 29, "county": 60, "autonomous_county": 6},
}

GDP_DATA = {
    "北京市": {"2024": 49670.2, "2023": 47353.7, "2022": 45222.4, "2021": 44350.7, "2020": 38503.6},
    "天津市": {"2024": 17931.3, "2023": 17211.8, "2022": 16588.5, "2021": 16093.2, "2020": 14230.8},
    "河北省": {"2024": 47448.1, "2023": 45660.0, "2022": 43198.3, "2021": 41205.4, "2020": 36821.5},
    "山西省": {"2024": 25353.5, "2023": 26050.8, "2022": 25653.2, "2021": 23087.8, "2020": 18202.7},
    "内蒙古自治区": {"2024": 26337.0, "2023": 25020.5, "2022": 23795.7, "2021": 21584.8, "2020": 17623.4},
    "辽宁省": {"2024": 32540.8, "2023": 31389.8, "2022": 29739.7, "2021": 28471.0, "2020": 25839.0},
    "吉林省": {"2024": 14305.0, "2023": 13942.7, "2022": 13121.4, "2021": 13431.1, "2020": 12499.5},
    "黑龙江省": {"2024": 16478.1, "2023": 16470.7, "2022": 16359.2, "2021": 15292.8, "2020": 14000.1},
    "上海市": {"2024": 53759.5, "2023": 51404.5, "2022": 48594.5, "2021": 47059.4, "2020": 41603.9},
    "江苏省": {"2024": 136696.9, "2023": 130924.3, "2022": 124564.2, "2021": 119853.2, "2020": 104566.6},
    "浙江省": {"2024": 90007.0, "2023": 85619.6, "2022": 80770.0, "2021": 76765.3, "2020": 67164.5},
    "安徽省": {"2024": 50646.7, "2023": 48227.5, "2022": 45525.1, "2021": 43102.8, "2020": 38628.8},
    "福建省": {"2024": 57476.6, "2023": 54801.7, "2022": 52099.6, "2021": 49602.6, "2020": 43682.0},
    "江西省": {"2024": 34227.9, "2023": 32677.1, "2022": 31568.1, "2021": 29838.2, "2020": 25825.4},
    "山东省": {"2024": 98406.9, "2023": 94206.4, "2022": 89519.4, "2021": 84838.0, "2020": 74355.9},
    "河南省": {"2024": 63557.1, "2023": 60627.7, "2022": 58807.4, "2021": 57806.9, "2020": 54160.6},
    "湖北省": {"2024": 59644.3, "2023": 56794.3, "2022": 53445.4, "2021": 50093.3, "2020": 43017.6},
    "湖南省": {"2024": 53084.7, "2023": 50667.5, "2022": 47957.9, "2021": 45751.9, "2020": 41693.7},
    "广东省": {"2024": 141488.9, "2023": 137905.4, "2022": 132547.1, "2021": 127577.4, "2020": 113708.9},
    "广西壮族自治区": {"2024": 28694.1, "2023": 27501.7, "2022": 26419.7, "2021": 25311.5, "2020": 22250.7},
    "海南省": {"2024": 7972.7, "2023": 7590.2, "2022": 6912.8, "2021": 6508.9, "2020": 5640.8},
    "重庆市": {"2024": 32046.7, "2023": 30614.3, "2022": 28771.8, "2021": 28092.5, "2020": 25158.1},
    "四川省": {"2024": 64537.9, "2023": 61353.4, "2022": 57609.4, "2021": 55131.3, "2020": 49445.1},
    "贵州省": {"2024": 22645.7, "2023": 21513.7, "2022": 20579.5, "2021": 19921.3, "2020": 18308.3},
    "云南省": {"2024": 31423.4, "2023": 30595.8, "2022": 29301.1, "2021": 27895.3, "2020": 25214.5},
    "西藏自治区": {"2024": 2789.1, "2023": 2532.9, "2022": 2235.4, "2021": 2145.1, "2020": 1956.5},
    "陕西省": {"2024": 35437.1, "2023": 33976.5, "2022": 33035.6, "2021": 30476.6, "2020": 26297.0},
    "甘肃省": {"2024": 13020.5, "2023": 12345.7, "2022": 11553.6, "2021": 10608.0, "2020": 9323.1},
    "青海省": {"2024": 3965.5, "2023": 3849.2, "2022": 3677.4, "2021": 3446.3, "2020": 3080.6},
    "宁夏回族自治区": {"2024": 5520.2, "2023": 5368.8, "2022": 5168.1, "2021": 4666.5, "2020": 4036.2},
    "新疆维吾尔自治区": {"2024": 20492.4, "2023": 19603.3, "2022": 18550.5, "2021": 16791.5, "2020": 14262.2},
}

NATIONAL_STATS = {
    "2024": {"prefecture_count": 333, "prefecture_city": 293, "county_count": 2846, "district": 977, "county_city": 397, "county": 1301, "autonomous_county": 117},
    "2023": {"prefecture_count": 333, "prefecture_city": 293, "county_count": 2844, "district": 977, "county_city": 397, "county": 1299, "autonomous_county": 117},
    "2022": {"prefecture_count": 333, "prefecture_city": 293, "county_count": 2843, "district": 977, "county_city": 394, "county": 1301, "autonomous_county": 117},
    "2021": {"prefecture_count": 333, "prefecture_city": 293, "county_count": 2843, "district": 977, "county_city": 394, "county": 1301, "autonomous_county": 117},
    "2020": {"prefecture_count": 333, "prefecture_city": 293, "county_count": 2844, "district": 973, "county_city": 388, "county": 1312, "autonomous_county": 117},
}

def create_tables(conn):
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin_divisions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT UNIQUE NOT NULL,
            prefecture_count INTEGER DEFAULT 0,
            county_count INTEGER DEFAULT 0,
            prefecture_city INTEGER DEFAULT 0,
            district INTEGER DEFAULT 0,
            county_city INTEGER DEFAULT 0,
            county INTEGER DEFAULT 0,
            autonomous_county INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gdp_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            region_name TEXT NOT NULL,
            year INTEGER NOT NULL,
            gdp_value REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(region_name, year)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS national_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER UNIQUE NOT NULL,
            prefecture_count INTEGER DEFAULT 0,
            prefecture_city INTEGER DEFAULT 0,
            county_count INTEGER DEFAULT 0,
            district INTEGER DEFAULT 0,
            county_city INTEGER DEFAULT 0,
            county INTEGER DEFAULT 0,
            autonomous_county INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    print("✓ 数据表创建完成")

def import_admin_divisions(conn):
    cursor = conn.cursor()
    
    for region, data in ADMIN_DIVISION_DATA.items():
        cursor.execute('''
            INSERT OR REPLACE INTO admin_divisions 
            (region_name, prefecture_count, county_count, prefecture_city, district, county_city, county, autonomous_county)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (region, data["prefecture_count"], data["county_count"], data["prefecture_city"], 
              data["district"], data["county_city"], data["county"], data["autonomous_county"]))
    
    conn.commit()
    print(f"✓ 导入行政区划数据: {len(ADMIN_DIVISION_DATA)} 条")

def import_gdp_data(conn):
    cursor = conn.cursor()
    
    count = 0
    for region, years_data in GDP_DATA.items():
        for year, gdp in years_data.items():
            cursor.execute('''
                INSERT OR REPLACE INTO gdp_data (region_name, year, gdp_value)
                VALUES (?, ?, ?)
            ''', (region, int(year), gdp))
            count += 1
    
    conn.commit()
    print(f"✓ 导入GDP数据: {count} 条")

def import_national_stats(conn):
    cursor = conn.cursor()
    
    for year, data in NATIONAL_STATS.items():
        cursor.execute('''
            INSERT OR REPLACE INTO national_stats 
            (year, prefecture_count, prefecture_city, county_count, district, county_city, county, autonomous_county)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (int(year), data["prefecture_count"], data["prefecture_city"], data["county_count"],
              data["district"], data["county_city"], data["county"], data["autonomous_county"]))
    
    conn.commit()
    print(f"✓ 导入全国统计数据: {len(NATIONAL_STATS)} 条")

def main():
    print("=" * 60)
    print("导入行政区划和GDP数据")
    print("=" * 60)
    
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    
    try:
        create_tables(conn)
        import_admin_divisions(conn)
        import_gdp_data(conn)
        import_national_stats(conn)
        
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM admin_divisions")
        admin_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM gdp_data")
        gdp_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM national_stats")
        stats_count = cursor.fetchone()[0]
        
        print("\n" + "=" * 60)
        print("导入完成!")
        print(f"  行政区划: {admin_count} 条")
        print(f"  GDP数据: {gdp_count} 条")
        print(f"  全国统计: {stats_count} 条")
        print("=" * 60)
        
    finally:
        conn.close()

if __name__ == "__main__":
    main()
