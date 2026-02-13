import os
import json
import time
import hashlib
from typing import List, Dict, Any, Optional
from collections import OrderedDict

class VectorMemory:
    """
    智能记忆系统
    
    特性:
    1. 短期记忆: 最近对话，快速访问
    2. 长期记忆: 重要信息，持久存储
    3. 语义检索: 基于关键词的相关性搜索
    4. 记忆压缩: 自动总结和精简
    """
    
    def __init__(self, root_dir: str = "./memory", max_short_term: int = 20):
        self.root_dir = root_dir
        self.max_short_term = max_short_term
        
        self.short_term_memory = OrderedDict()
        self.long_term_memory = {}
        self.memory_index = {}
        
        self.short_term_file = os.path.join(root_dir, "short_term.json")
        self.long_term_file = os.path.join(root_dir, "long_term.json")
        self.index_file = os.path.join(root_dir, "index.json")
        
        self._init_storage()
    
    def _init_storage(self):
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)
        
        self._load_from_disk()
    
    def _load_from_disk(self):
        try:
            if os.path.exists(self.short_term_file):
                with open(self.short_term_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.short_term_memory = OrderedDict(data)
        except:
            self.short_term_memory = OrderedDict()
        
        try:
            if os.path.exists(self.long_term_file):
                with open(self.long_term_file, "r", encoding="utf-8") as f:
                    self.long_term_memory = json.load(f)
        except:
            self.long_term_memory = {}
        
        try:
            if os.path.exists(self.index_file):
                with open(self.index_file, "r", encoding="utf-8") as f:
                    self.memory_index = json.load(f)
        except:
            self.memory_index = {}
    
    def _save_to_disk(self):
        with open(self.short_term_file, "w", encoding="utf-8") as f:
            json.dump(dict(self.short_term_memory), f, ensure_ascii=False, indent=2)
        
        with open(self.long_term_file, "w", encoding="utf-8") as f:
            json.dump(self.long_term_memory, f, ensure_ascii=False, indent=2)
        
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(self.memory_index, f, ensure_ascii=False, indent=2)
    
    def add(self, content: str, metadata: Dict = None, importance: float = 0.5) -> str:
        """
        添加记忆
        
        :param content: 记忆内容
        :param metadata: 元数据
        :param importance: 重要性 (0-1)
        :return: 记忆ID
        """
        memory_id = self._generate_id(content)
        
        memory_entry = {
            "id": memory_id,
            "content": content,
            "metadata": metadata or {},
            "importance": importance,
            "timestamp": time.time(),
            "access_count": 0
        }
        
        self.short_term_memory[memory_id] = memory_entry
        self._update_index(memory_id, content)
        
        if importance >= 0.7:
            self.long_term_memory[memory_id] = memory_entry
        
        if len(self.short_term_memory) > self.max_short_term:
            self._compress_short_term()
        
        self._save_to_disk()
        
        return memory_id
    
    def add_interaction(self, user_input: str, assistant_response: str, 
                        tool_calls: List = None, importance: float = None):
        """
        添加交互记录
        
        :param user_input: 用户输入
        :param assistant_response: 助手响应
        :param tool_calls: 工具调用记录
        :param importance: 重要性 (自动计算如果为None)
        """
        if importance is None:
            importance = self._calculate_importance(user_input, assistant_response, tool_calls)
        
        content = f"用户: {user_input}\n助手: {assistant_response}"
        if tool_calls:
            tools_str = ", ".join([t.get("name", "unknown") for t in tool_calls])
            content += f"\n工具: {tools_str}"
        
        metadata = {
            "type": "interaction",
            "tool_calls": tool_calls or []
        }
        
        self.add(content, metadata, importance)
    
    def retrieve_relevant(self, query: str, top_k: int = 5) -> List[str]:
        """
        检索相关记忆
        
        :param query: 查询
        :param top_k: 返回数量
        :return: 相关记忆列表
        """
        query_keywords = self._extract_keywords(query)
        
        scores = {}
        
        for memory_id, memory in self.short_term_memory.items():
            score = self._calculate_relevance(query_keywords, memory["content"])
            scores[memory_id] = score
        
        for memory_id, memory in self.long_term_memory.items():
            score = self._calculate_relevance(query_keywords, memory["content"])
            scores[memory_id] = score * 1.2
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)[:top_k]
        
        results = []
        for mid in sorted_ids:
            if mid in self.short_term_memory:
                results.append(self.short_term_memory[mid]["content"])
            elif mid in self.long_term_memory:
                results.append(self.long_term_memory[mid]["content"])
        
        return results
    
    def get_context_for_prompt(self, query: str, max_tokens: int = 1000) -> str:
        """
        获取用于 Prompt 的上下文
        
        :param query: 当前查询
        :param max_tokens: 最大 token 数 (估算)
        :return: 格式化的上下文字符串
        """
        relevant = self.retrieve_relevant(query, top_k=5)
        
        if not relevant:
            return ""
        
        context_parts = ["## 相关记忆"]
        current_length = 0
        
        for memory in relevant:
            estimated_tokens = len(memory) // 2
            if current_length + estimated_tokens > max_tokens:
                break
            context_parts.append(f"- {memory[:200]}...")
            current_length += estimated_tokens
        
        return "\n".join(context_parts)
    
    def compress(self, llm_client) -> str:
        """
        压缩记忆
        
        :param llm_client: LLM 客户端
        :return: 压缩摘要
        """
        if len(self.short_term_memory) < 5:
            return "记忆较少，无需压缩"
        
        memories = list(self.short_term_memory.values())
        memory_text = "\n\n".join([
            f"[{m['metadata'].get('type', 'unknown')}] {m['content']}" 
            for m in memories[-10:]
        ])
        
        prompt = f"""请总结以下对话记录，提取关键信息：

{memory_text}

请以简洁的要点形式输出重要信息，包括：
1. 用户偏好
2. 重要事实
3. 关键决策

只输出要点，每条一行。"""
        
        summary = llm_client.simple_chat(prompt)
        
        if summary:
            self.add(summary, {"type": "summary"}, importance=0.8)
            
            for memory_id in list(self.short_term_memory.keys())[:-5]:
                memory = self.short_term_memory[memory_id]
                if memory.get("importance", 0) < 0.6:
                    del self.short_term_memory[memory_id]
            
            self._save_to_disk()
        
        return summary or "压缩失败"
    
    def _generate_id(self, content: str) -> str:
        return hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
    
    def _update_index(self, memory_id: str, content: str):
        keywords = self._extract_keywords(content)
        for keyword in keywords:
            if keyword not in self.memory_index:
                self.memory_index[keyword] = []
            if memory_id not in self.memory_index[keyword]:
                self.memory_index[keyword].append(memory_id)
    
    def _extract_keywords(self, text: str) -> List[str]:
        stop_words = {"的", "是", "在", "了", "和", "与", "或", "有", "这", "那", "我", "你", "他", "她", "它"}
        
        words = []
        for word in text.split():
            clean_word = word.strip("，。！？、：""''()（）[]【】")
            if len(clean_word) > 1 and clean_word not in stop_words:
                words.append(clean_word.lower())
        
        return list(set(words))
    
    def _calculate_relevance(self, query_keywords: List[str], content: str) -> float:
        content_lower = content.lower()
        matches = sum(1 for kw in query_keywords if kw in content_lower)
        return matches / max(len(query_keywords), 1)
    
    def _calculate_importance(self, user_input: str, response: str, tool_calls: List) -> float:
        importance = 0.3
        
        if tool_calls and len(tool_calls) > 0:
            importance += 0.2
        
        important_keywords = ["重要", "记住", "保存", "记录", "偏好", "喜欢", "不喜欢"]
        for kw in important_keywords:
            if kw in user_input:
                importance += 0.15
        
        if len(user_input) > 100:
            importance += 0.1
        
        return min(importance, 1.0)
    
    def _compress_short_term(self):
        items = list(self.short_term_memory.items())
        
        items.sort(key=lambda x: x[1].get("importance", 0), reverse=True)
        
        self.short_term_memory = OrderedDict(items[:self.max_short_term])
    
    def get_stats(self) -> Dict:
        return {
            "short_term_count": len(self.short_term_memory),
            "long_term_count": len(self.long_term_memory),
            "index_keywords": len(self.memory_index)
        }
