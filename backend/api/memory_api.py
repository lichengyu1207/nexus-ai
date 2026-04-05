#!/usr/bin/env python3
"""
海马体记忆系统API接口
"""

import json
import time
import sys
import os

# 添加项目根目录到系统路径
current_dir = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
root_dir = os.path.dirname(grandparent_dir)
sys.path.append(root_dir)

from flask import Flask, request, jsonify
from backend.memory.hippocampus import Hippocampus

app = Flask(__name__)

# 初始化海马体记忆系统
hippocampus = Hippocampus()

@app.route('/api/memory/create', methods=['POST'])
def create_memory():
    """创建新的记忆"""
    try:
        data = request.json
        user_id = data.get('user_id')
        request_data = data.get('request')
        intermediate_data = data.get('intermediate_data', {})
        result = data.get('result')
        metadata = data.get('metadata', {})
        
        if not user_id or not request_data or not result:
            return jsonify({"error": "Missing required fields"}), 400
        
        memory_id = hippocampus.create_memory(user_id, request_data, intermediate_data, result, metadata)
        return jsonify({"memory_id": memory_id, "status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/get', methods=['GET'])
def get_memory():
    """获取记忆"""
    try:
        memory_id = request.args.get('memory_id')
        if not memory_id:
            return jsonify({"error": "Missing memory_id"}), 400
        
        memory = hippocampus.get_memory(memory_id)
        if not memory:
            return jsonify({"error": "Memory not found"}), 404
        
        return jsonify({
            "memory_id": memory.memory_id,
            "user_id": memory.user_id,
            "request": memory.request,
            "intermediate_data": memory.intermediate_data,
            "result": memory.result,
            "timestamp": memory.timestamp,
            "metadata": memory.metadata,
            "access_count": memory.access_count,
            "last_accessed": memory.last_accessed,
            "importance": memory.importance
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/retrieve', methods=['POST'])
def retrieve_memories():
    """检索记忆"""
    try:
        data = request.json
        user_id = data.get('user_id')
        query = data.get('query')
        top_k = data.get('top_k', 5)
        
        if not user_id or not query:
            return jsonify({"error": "Missing required fields"}), 400
        
        memories = hippocampus.retrieve_memories(user_id, query, top_k)
        results = []
        for memory in memories:
            results.append({
                "memory_id": memory.memory_id,
                "user_id": memory.user_id,
                "request": memory.request,
                "result": memory.result,
                "timestamp": memory.timestamp,
                "importance": memory.importance
            })
        
        return jsonify({"results": results, "count": len(results)}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/delete', methods=['DELETE'])
def delete_memory():
    """删除记忆"""
    try:
        memory_id = request.args.get('memory_id')
        if not memory_id:
            return jsonify({"error": "Missing memory_id"}), 400
        
        hippocampus.delete_memory(memory_id)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/clear', methods=['POST'])
def clear_user_memories():
    """清除用户的所有记忆"""
    try:
        data = request.json
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400
        
        hippocampus.clear_user_memories(user_id)
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/consolidate', methods=['POST'])
def consolidate_memories():
    """执行记忆固化"""
    try:
        hippocampus._consolidate_to_long_term_memory()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/activate', methods=['POST'])
def activate_memories():
    """执行记忆激活"""
    try:
        hippocampus._activate_related_memories()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/memory/forget', methods=['POST'])
def forget_memories():
    """执行主动遗忘"""
    try:
        hippocampus._active_forgetting()
        return jsonify({"status": "success"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
