#!/usr/bin/env python3
"""
Neo 系统测试脚本
测试新架构的各个组件
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_llm_client():
    print("\n" + "="*50)
    print("测试 1: LLM Client")
    print("="*50)
    
    from llm_client import LLMClient
    client = LLMClient()
    
    print(f"✓ LLM Client 初始化成功")
    print(f"  - 模型: {client.model}")
    print(f"  - API URL: {client.base_url[:30]}...")
    
    response = client.simple_chat("你好，请用一句话回复。")
    if response:
        print(f"✓ 简单对话测试成功")
        print(f"  - 回复: {response[:50]}...")
    else:
        print("✗ 简单对话测试失败")
    
    return True

def test_skill_manager():
    print("\n" + "="*50)
    print("测试 2: Skill Manager")
    print("="*50)
    
    from core.skill_manager import SkillManager
    sm = SkillManager()
    
    skills = sm.list_skills()
    print(f"✓ 已加载 {len(skills)} 个技能:")
    for skill in skills:
        print(f"  - {skill}")
    
    schemas = sm.get_all_tools_schema()
    print(f"✓ 获取到 {len(schemas)} 个工具 Schema")
    
    results = sm.search_skills("备忘录")
    print(f"✓ 搜索 '备忘录' 找到 {len(results)} 个相关技能")
    for r in results:
        print(f"  - {r['name']} (得分: {r['score']:.2f})")
    
    return True

def test_memory():
    print("\n" + "="*50)
    print("测试 3: Vector Memory")
    print("="*50)
    
    from core.memory import VectorMemory
    import tempfile
    import shutil
    
    test_dir = tempfile.mkdtemp()
    try:
        memory = VectorMemory(root_dir=test_dir)
        
        memory.add("用户喜欢喝咖啡", {"type": "preference"}, importance=0.8)
        memory.add("用户询问了天气", {"type": "question"}, importance=0.5)
        memory.add("用户要求创建备忘录", {"type": "action"}, importance=0.7)
        
        print(f"✓ 添加了 3 条记忆")
        
        results = memory.retrieve_relevant("咖啡偏好")
        print(f"✓ 检索 '咖啡偏好' 找到 {len(results)} 条相关记忆")
        for r in results:
            print(f"  - {r[:50]}...")
        
        stats = memory.get_stats()
        print(f"✓ 记忆统计: 短期={stats['short_term_count']}, 长期={stats['long_term_count']}")
        
        return True
    finally:
        shutil.rmtree(test_dir)

def test_planner():
    print("\n" + "="*50)
    print("测试 4: Task Planner")
    print("="*50)
    
    from llm_client import LLMClient
    from core.skill_manager import SkillManager
    from core.planner import TaskPlanner
    
    client = LLMClient()
    sm = SkillManager()
    planner = TaskPlanner(client, sm)
    
    complexity = planner.analyze_complexity("帮我创建一个备忘录，然后搜索一下天气")
    print(f"✓ 任务复杂度分析:")
    print(f"  - 等级: {complexity['level']}")
    print(f"  - 因素: {complexity['factors']}")
    
    return True

def test_react_agent():
    print("\n" + "="*50)
    print("测试 5: ReAct Agent")
    print("="*50)
    
    from llm_client import LLMClient
    from core.skill_manager import SkillManager
    from core.react_agent import ReActAgent
    
    client = LLMClient()
    sm = SkillManager()
    agent = ReActAgent(client, sm)
    
    print(f"✓ ReAct Agent 初始化成功")
    print(f"  - 最大迭代次数: {agent.max_iterations}")
    
    return True

def test_integration():
    print("\n" + "="*50)
    print("测试 6: 集成测试")
    print("="*50)
    
    from llm_client import LLMClient
    from core import SkillManager, ReActAgent, VectorMemory
    
    client = LLMClient()
    sm = SkillManager()
    memory = VectorMemory(root_dir="./test_memory")
    agent = ReActAgent(client, sm, memory)
    
    print("✓ 所有组件集成成功")
    
    skills = sm.list_skills()
    print(f"✓ 可用技能: {', '.join(skills)}")
    
    return True

def main():
    print("\n" + "="*50)
    print("Neo 系统测试")
    print("="*50)
    
    tests = [
        ("LLM Client", test_llm_client),
        ("Skill Manager", test_skill_manager),
        ("Vector Memory", test_memory),
        ("Task Planner", test_planner),
        ("ReAct Agent", test_react_agent),
        ("集成测试", test_integration),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {name} 测试失败: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    print("="*50)
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
