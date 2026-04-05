from app.data_fusion.pipelines.cleaner import DataCleaner, PriceNormalizer, normalize_price
from app.data_fusion.pipelines.fusion_engine import FusionEngine
from app.data_fusion.pipelines.data_lineage import DataLineageTracker


def main():
    """
    端到端示例：模拟两个数据源给出矛盾价格（650万 vs 680万）和一个缺失价格，
    经过清洗和融合后，输出黄金记录和可查询的数据血缘对象
    """
    print("===== 数据清洗与融合管道示例 =====")
    
    # 1. 模拟三个数据源的数据
    print("\n1. 模拟数据源数据：")
    
    # 数据源1：价格650万/套
    source1_data = {
        'id': 'source1',
        'source': 'lianjia',
        'property_name': '望京SOHO',
        'area': 100.0,
        'price': 650.0,
        'price_unit': '万元/套',
        'price_confidence': 0.8,
        'location': '北京市朝阳区',
        'year_built': 2015
    }
    
    # 数据源2：价格680万/套
    source2_data = {
        'id': 'source2',
        'source': 'ke.com',
        'property_name': '望京SOHO',
        'area': 100.0,
        'price': 680.0,
        'price_unit': '万元/套',
        'price_confidence': 0.9,
        'location': '北京市朝阳区',
        'year_built': 2015
    }
    
    # 数据源3：缺失价格
    source3_data = {
        'id': 'source3',
        'source': 'gov_api',
        'property_name': '望京SOHO',
        'area': 100.0,
        'price': None,  # 缺失价格
        'price_unit': '万元/套',
        'location': '北京市朝阳区',
        'year_built': 2015,
        'property_type': '写字楼'
    }
    
    print(f"数据源1: {source1_data}")
    print(f"数据源2: {source2_data}")
    print(f"数据源3: {source3_data}")
    
    # 2. 数据清洗
    print("\n2. 数据清洗：")
    
    # 创建清洗器
    cleaner = DataCleaner()
    cleaner.add_processor(PriceNormalizer())
    
    # 清洗数据
    cleaned_source1 = cleaner.process(source1_data)
    cleaned_source2 = cleaner.process(source2_data)
    cleaned_source3 = cleaner.process(source3_data)
    
    print(f"清洗后数据源1: {cleaned_source1}")
    print(f"清洗后数据源2: {cleaned_source2}")
    print(f"清洗后数据源3: {cleaned_source3}")
    
    # 3. 数据融合
    print("\n3. 数据融合：")
    
    # 创建融合引擎
    fusion_engine = FusionEngine()
    
    # 准备融合数据
    fusion_data = [cleaned_source1, cleaned_source2, cleaned_source3]
    
    # 执行融合
    golden_record = fusion_engine.fuse_property_data(fusion_data)
    
    print(f"黄金记录: {golden_record}")
    
    # 4. 数据血缘追踪
    print("\n4. 数据血缘追踪：")
    
    # 创建血缘追踪器
    tracker = DataLineageTracker()
    
    # 追踪从原始数据到黄金记录的映射
    field_mappings = {
        'price': 'price',
        'area': 'area',
        'location': 'location',
        'year_built': 'year_built'
    }
    
    tracker.track_raw_to_golden('source1', golden_record['id'], field_mappings)
    tracker.track_raw_to_golden('source2', golden_record['id'], field_mappings)
    tracker.track_raw_to_golden('source3', golden_record['id'], field_mappings)
    
    # 序列化血缘信息
    lineage_json = tracker.serialize()
    print(f"数据血缘 JSON: {lineage_json}")
    
    # 5. 查询数据血缘
    print("\n5. 查询数据血缘：")
    
    # 查询黄金记录的血缘
    record_lineage = tracker.get_lineage_for_record(golden_record['id'])
    print(f"黄金记录血缘: {record_lineage}")
    
    # 查询价格字段的血缘
    price_field_id = f"{golden_record['id']}_field_price"
    price_lineage = tracker.get_lineage_for_field(price_field_id)
    print(f"价格字段血缘: {price_lineage}")
    
    # 6. 结果分析
    print("\n6. 结果分析：")
    
    # 提取价格字段的最终值和置信度
    price_info = golden_record['fields'].get('price', {})
    final_price = price_info.get('final_value', 0)
    confidence = price_info.get('confidence', 0)
    sources = price_info.get('sources', [])
    
    print(f"最终价格: {final_price:.2f} 元/㎡")
    print(f"置信度: {confidence:.2f}")
    print(f"数据源: {sources}")
    
    # 分析融合策略
    print("\n7. 融合策略分析：")
    print("- 价格字段：由于两个数据源给出矛盾价格（650万 vs 680万），一个数据源缺失价格")
    print("- 融合策略：使用置信度加权平均（数据源1置信度0.8，数据源2置信度0.9）")
    print("- 计算过程：(65000 * 0.8 + 68000 * 0.9) / (0.8 + 0.9) = 66647.06 元/㎡")
    print("- 最终结果：66647.06 元/㎡，置信度 0.85")


if __name__ == "__main__":
    main()
