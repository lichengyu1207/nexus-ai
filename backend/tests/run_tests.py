#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""测试意图识别模块"""
import sys
import os
import importlib.util

backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def load_module(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

intent_parser = load_module('intent_parser', os.path.join(backend_path, 'services', 'intent_parser.py'))
param_extractor = load_module('param_extractor', os.path.join(backend_path, 'services', 'param_extractor.py'))

parse_intent = intent_parser.parse_intent
TaskType = intent_parser.TaskType
extract_params = param_extractor.extract_params
generate_questions = param_extractor.generate_questions

def test_intent_parser():
    print("=" * 60)
    print("意图识别测试")
    print("=" * 60)
    
    # 测试用例 1: 多任务解析
    text1 = "帮我分析深圳南山区的房价，还有杭州的政策"
    result1 = parse_intent(text1)
    print(f"\n测试1: {text1}")
    print(f"  识别任务数: {len(result1.tasks)}")
    for t in result1.tasks:
        print(f"    - {t.type.value}: {t.span} (置信度: {t.confidence:.2f})")
    
    # 测试用例 2: 命理和房产任务
    text2 = "我想看看我的命盘，顺便查一下上海的学区房"
    result2 = parse_intent(text2)
    print(f"\n测试2: {text2}")
    print(f"  识别任务数: {len(result2.tasks)}")
    for t in result2.tasks:
        print(f"    - {t.type.value}: {t.span} (置信度: {t.confidence:.2f})")
    
    # 测试用例 3: 缺失参数追问
    text3 = "分析房价"
    result3 = parse_intent(text3)
    print(f"\n测试3: {text3}")
    print(f"  识别任务数: {len(result3.tasks)}")
    for t in result3.tasks:
        print(f"    - {t.type.value}: {t.span} (置信度: {t.confidence:.2f})")
    
    # 测试用例 4: 分号分隔
    text4 = "分析北京房价；查上海政策；算一下我的命盘"
    result4 = parse_intent(text4)
    print(f"\n测试4: {text4}")
    print(f"  识别任务数: {len(result4.tasks)}")
    for t in result4.tasks:
        print(f"    - {t.type.value}: {t.span} (置信度: {t.confidence:.2f})")
    
    print("\n" + "=" * 60)
    print("所有意图识别测试通过!")
    print("=" * 60)

def test_param_extractor():
    print("\n" + "=" * 60)
    print("参数提取测试")
    print("=" * 60)
    
    # 测试用例 1: 提取城市
    text1 = "深圳南山区的房价"
    result1 = extract_params(TaskType.PROPERTY_ANALYSIS, text1)
    print(f"\n测试1: {text1}")
    print(f"  提取结果: city={result1.get('city')}")
    
    # 测试用例 2: 缺失参数
    text2 = "分析房价"
    result2 = extract_params(TaskType.PROPERTY_ANALYSIS, text2)
    print(f"\n测试2: {text2}")
    missing = [k for k, v in result2.items() if hasattr(v, 'status') and v.status.value == 'missing']
    print(f"  缺失参数: {missing}")
    
    # 测试用例 3: 生成追问
    question = generate_questions(["city", "price_range"], TaskType.PROPERTY_ANALYSIS)
    print(f"\n测试3: 生成追问")
    print(f"  追问: {question}")
    
    print("\n" + "=" * 60)
    print("所有参数提取测试通过!")
    print("=" * 60)

if __name__ == "__main__":
    test_intent_parser()
    test_param_extractor()
    print("\n所有测试完成!")
