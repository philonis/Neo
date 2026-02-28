"""
技能索引服务 - 杜绝重复创建，快速定位已有技能

核心功能:
1. 技能语义索引：基于名称、描述、关键词建立索引
2. 技能相似度匹配：在创建新技能前检查是否已存在类似技能
3. 技能使用统计：记录技能调用频率，优先推荐高频技能
4. 技能依赖图谱：记录技能间的关系

借鉴 OpenClaw 设计哲学:
- 上下文效率优先：索引信息精简，只包含触发信息
- 渐进式披露：元数据在索引中，详情按需加载
"""

import os
import json
import re
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from pathlib import Path


@dataclass
class SkillMatch:
    """技能匹配结果"""
    name: str
    score: float
    description: str
    category: str
    usage_count: int = 0
    source_type: str = "python"


@dataclass
class SkillIndexEntry:
    """技能索引条目"""
    name: str
    description: str
    keywords: List[str]
    category: str
    source_type: str
    source_path: str
    created_at: float
    usage_count: int = 0
    last_used: Optional[float] = None
    composable_with: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    provides: List[str] = field(default_factory=list)


class SkillIndex:
    """
    技能索引服务
    
    功能:
    - 索引技能元数据
    - 搜索相似技能
    - 检查重复技能
    - 统计使用频率
    - 建议技能组合
    """
    
    CATEGORIES = {
        "acquisition": "信息获取",
        "processing": "信息处理",
        "output": "信息输出",
        "control": "流程控制",
        "browser": "浏览器交互",
        "desktop": "桌面操作",
        "communication": "通信通知",
        "other": "其他"
    }
    
    STOP_WORDS = {
        "的", "是", "在", "了", "和", "与", "或", "有", "这", "那",
        "我", "你", "他", "她", "它", "一个", "可以", "用于", "支持",
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "being", "have", "has", "had", "do", "does", "did", "will",
        "would", "could", "should", "may", "might", "must", "shall",
        "to", "of", "in", "for", "on", "with", "at", "by", "from",
        "as", "into", "through", "during", "before", "after", "above",
        "below", "between", "under", "again", "further", "then", "once"
    }
    
    def __init__(self, index_dir: str = "./skill_index"):
        self.index_dir = Path(index_dir)
        self.index_file = self.index_dir / "skill_index.json"
        self.stats_file = self.index_dir / "usage_stats.json"
        
        self._index: Dict[str, SkillIndexEntry] = {}
        self._keyword_index: Dict[str, List[str]] = defaultdict(list)
        self._category_index: Dict[str, List[str]] = defaultdict(list)
        self._usage_stats: Dict[str, int] = {}
        
        self._load_index()
    
    def _load_index(self):
        if not self.index_dir.exists():
            self.index_dir.mkdir(parents=True, exist_ok=True)
            return
        
        if self.index_file.exists():
            try:
                with open(self.index_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for name, entry_data in data.items():
                        self._index[name] = SkillIndexEntry(**entry_data)
                        self._rebuild_indices_for_entry(self._index[name])
            except (json.JSONDecodeError, IOError, OSError) as e:
                self._index = {}
        
        if self.stats_file.exists():
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    self._usage_stats = json.load(f)
            except (json.JSONDecodeError, IOError, OSError):
                self._usage_stats = {}
    
    def _save_index(self):
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        data = {name: asdict(entry) for name, entry in self._index.items()}
        with open(self.index_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self._usage_stats, f, ensure_ascii=False, indent=2)
    
    def _rebuild_indices_for_entry(self, entry: SkillIndexEntry):
        for keyword in entry.keywords:
            keyword_lower = keyword.lower()
            if entry.name not in self._keyword_index[keyword_lower]:
                self._keyword_index[keyword_lower].append(entry.name)
        
        self._category_index[entry.category].append(entry.name)
    
    def index_skill(
        self,
        name: str,
        description: str,
        keywords: List[str] = None,
        category: str = "other",
        source_type: str = "python",
        source_path: str = None,
        composable_with: List[str] = None,
        dependencies: List[str] = None,
        provides: List[str] = None
    ) -> bool:
        """
        索引一个技能
        
        Args:
            name: 技能名称
            description: 技能描述
            keywords: 关键词列表
            category: 技能类别
            source_type: 来源类型 (python/md)
            source_path: 来源路径
            composable_with: 可组合的技能列表
            dependencies: 依赖列表
            provides: 提供的输出列表
            
        Returns:
            是否索引成功
        """
        if not name or not description:
            return False
        
        extracted_keywords = self._extract_keywords(description)
        if keywords:
            extracted_keywords.extend([k.lower() for k in keywords])
        extracted_keywords = list(set(extracted_keywords))
        
        entry = SkillIndexEntry(
            name=name,
            description=description,
            keywords=extracted_keywords,
            category=category,
            source_type=source_type,
            source_path=source_path or name,
            created_at=time.time(),
            usage_count=self._usage_stats.get(name, 0),
            composable_with=composable_with or [],
            dependencies=dependencies or [],
            provides=provides or []
        )
        
        if name in self._index:
            old_entry = self._index[name]
            for keyword in old_entry.keywords:
                keyword_lower = keyword.lower()
                if name in self._keyword_index[keyword_lower]:
                    self._keyword_index[keyword_lower].remove(name)
        
        self._index[name] = entry
        self._rebuild_indices_for_entry(entry)
        self._save_index()
        
        return True
    
    def remove_skill(self, name: str) -> bool:
        """从索引中移除技能"""
        if name not in self._index:
            return False
        
        entry = self._index[name]
        
        for keyword in entry.keywords:
            keyword_lower = keyword.lower()
            if name in self._keyword_index[keyword_lower]:
                self._keyword_index[keyword_lower].remove(name)
        
        if name in self._category_index[entry.category]:
            self._category_index[entry.category].remove(name)
        
        del self._index[name]
        
        if name in self._usage_stats:
            del self._usage_stats[name]
        
        self._save_index()
        return True
    
    def search_similar(
        self,
        query: str,
        threshold: float = 0.3,
        top_k: int = 5
    ) -> List[SkillMatch]:
        """
        搜索相似技能
        
        Args:
            query: 查询字符串
            threshold: 相似度阈值
            top_k: 返回数量
            
        Returns:
            相似技能列表
        """
        query_keywords = self._extract_keywords(query)
        
        if not query_keywords:
            return []
        
        scores: Dict[str, float] = {}
        
        for keyword in query_keywords:
            keyword_lower = keyword.lower()
            
            if keyword_lower in self._keyword_index:
                for skill_name in self._keyword_index[keyword_lower]:
                    if skill_name not in scores:
                        scores[skill_name] = 0
                    scores[skill_name] += 1
        
        for skill_name, entry in self._index.items():
            for skill_keyword in entry.keywords:
                for query_keyword in query_keywords:
                    if query_keyword.lower() in skill_keyword.lower():
                        if skill_name not in scores:
                            scores[skill_name] = 0
                        scores[skill_name] += 0.5
                    elif skill_keyword.lower() in query_keyword.lower():
                        if skill_name not in scores:
                            scores[skill_name] = 0
                        scores[skill_name] += 0.5
        
        max_possible = len(query_keywords)
        for skill_name in scores:
            scores[skill_name] = min(scores[skill_name] / max_possible, 1.0)
            
            usage_count = self._usage_stats.get(skill_name, 0)
            if usage_count > 0:
                scores[skill_name] += min(usage_count * 0.01, 0.2)
        
        results = []
        for skill_name, score in sorted(scores.items(), key=lambda x: x[1], reverse=True):
            if score >= threshold:
                entry = self._index[skill_name]
                results.append(SkillMatch(
                    name=skill_name,
                    score=score,
                    description=entry.description,
                    category=entry.category,
                    usage_count=entry.usage_count,
                    source_type=entry.source_type
                ))
        
        return results[:top_k]
    
    def check_duplicate(
        self,
        description: str,
        name: str = None,
        threshold: float = 0.7
    ) -> Optional[SkillMatch]:
        """
        检查是否存在重复技能
        
        Args:
            description: 新技能描述
            name: 新技能名称（可选，用于排除自身）
            threshold: 相似度阈值
            
        Returns:
            如果存在重复，返回匹配的技能；否则返回 None
        """
        similar_skills = self.search_similar(description, threshold=threshold, top_k=3)
        
        for match in similar_skills:
            if name and match.name == name:
                continue
            
            if match.score >= threshold:
                return match
        
        return None
    
    def record_usage(self, skill_name: str):
        """记录技能使用"""
        if skill_name not in self._usage_stats:
            self._usage_stats[skill_name] = 0
        
        self._usage_stats[skill_name] += 1
        
        if skill_name in self._index:
            self._index[skill_name].usage_count = self._usage_stats[skill_name]
            self._index[skill_name].last_used = time.time()
        
        self._save_index()
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """获取使用统计"""
        total_skills = len(self._index)
        total_usage = sum(self._usage_stats.values())
        
        top_skills = sorted(
            self._usage_stats.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        category_stats = defaultdict(int)
        for entry in self._index.values():
            category_stats[entry.category] += 1
        
        return {
            "total_skills": total_skills,
            "total_usage": total_usage,
            "top_skills": top_skills,
            "category_distribution": dict(category_stats),
            "recently_used": [
                (name, entry.last_used)
                for name, entry in sorted(
                    self._index.items(),
                    key=lambda x: x[1].last_used or 0,
                    reverse=True
                )[:10]
                if entry.last_used
            ]
        }
    
    def suggest_skills(self, task_description: str, top_k: int = 5) -> List[str]:
        """
        根据任务描述建议技能
        
        Args:
            task_description: 任务描述
            top_k: 返回数量
            
        Returns:
            建议的技能名称列表
        """
        matches = self.search_similar(task_description, threshold=0.2, top_k=top_k)
        return [match.name for match in matches]
    
    def suggest_composition(self, task_description: str) -> Dict[str, Any]:
        """
        建议技能组合方案
        
        Args:
            task_description: 任务描述
            
        Returns:
            组合建议
        """
        keywords = self._extract_keywords(task_description)
        
        acquisition_keywords = {"获取", "搜索", "查询", "读取", "fetch", "search", "query", "read", "get"}
        processing_keywords = {"处理", "解析", "转换", "提取", "parse", "transform", "extract", "process"}
        output_keywords = {"保存", "写入", "发送", "通知", "save", "write", "send", "notify", "output"}
        browser_keywords = {"浏览器", "网页", "网站", "browser", "web", "page", "site"}
        
        suggested_categories = set()
        
        for kw in keywords:
            kw_lower = kw.lower()
            if kw_lower in acquisition_keywords:
                suggested_categories.add("acquisition")
            if kw_lower in processing_keywords:
                suggested_categories.add("processing")
            if kw_lower in output_keywords:
                suggested_categories.add("output")
            if kw_lower in browser_keywords:
                suggested_categories.add("browser")
        
        if not suggested_categories:
            suggested_categories = {"acquisition", "processing"}
        
        composition = []
        for category in ["acquisition", "processing", "output", "browser"]:
            if category in suggested_categories:
                skills_in_category = self._category_index.get(category, [])
                if skills_in_category:
                    best_skill = max(
                        skills_in_category,
                        key=lambda s: self._usage_stats.get(s, 0)
                    )
                    composition.append(best_skill)
        
        return {
            "suggested_categories": list(suggested_categories),
            "composition": composition,
            "reasoning": f"基于关键词 {keywords[:5]} 推荐的组合方案"
        }
    
    def get_skill_info(self, name: str) -> Optional[Dict[str, Any]]:
        """获取技能详细信息"""
        if name not in self._index:
            return None
        
        entry = self._index[name]
        return {
            "name": entry.name,
            "description": entry.description,
            "keywords": entry.keywords,
            "category": entry.category,
            "source_type": entry.source_type,
            "source_path": entry.source_path,
            "usage_count": entry.usage_count,
            "last_used": entry.last_used,
            "composable_with": entry.composable_with,
            "dependencies": entry.dependencies,
            "provides": entry.provides
        }
    
    def list_skills_by_category(self, category: str = None) -> Dict[str, List[str]]:
        """按类别列出技能"""
        if category:
            return {category: self._category_index.get(category, [])}
        return dict(self._category_index)
    
    def get_composable_skills(self, skill_name: str) -> List[str]:
        """获取可与指定技能组合的技能列表"""
        if skill_name not in self._index:
            return []
        
        entry = self._index[skill_name]
        composable = []
        
        for name in entry.composable_with:
            if name in self._index:
                composable.append(name)
        
        for other_name, other_entry in self._index.items():
            if skill_name in other_entry.composable_with:
                if other_name not in composable:
                    composable.append(other_name)
        
        return composable
    
    def _extract_keywords(self, text: str) -> List[str]:
        """从文本中提取关键词"""
        if not text:
            return []
        
        words = []
        
        chinese_pattern = re.compile(r'[\u4e00-\u9fa5]+')
        chinese_matches = chinese_pattern.findall(text)
        for match in chinese_matches:
            if len(match) > 1:
                words.append(match)
        
        english_pattern = re.compile(r'[a-zA-Z]+')
        english_matches = english_pattern.findall(text)
        for match in english_matches:
            if len(match) > 2 and match.lower() not in self.STOP_WORDS:
                words.append(match.lower())
        
        camel_case_pattern = re.compile(r'[A-Z][a-z]+|[A-Z]+(?=[A-Z]|$)')
        camel_matches = camel_case_pattern.findall(text)
        for match in camel_matches:
            if len(match) > 1:
                words.append(match.lower())
        
        return list(set(words))
    
    def clear_index(self):
        """清空索引"""
        self._index.clear()
        self._keyword_index.clear()
        self._category_index.clear()
        self._usage_stats.clear()
        self._save_index()
    
    def rebuild_index(self, skills: List[Dict[str, Any]]):
        """
        重建索引
        
        Args:
            skills: 技能列表，每个元素包含 name, description, category 等字段
        """
        self.clear_index()
        
        for skill in skills:
            self.index_skill(
                name=skill.get("name", ""),
                description=skill.get("description", ""),
                keywords=skill.get("keywords", []),
                category=skill.get("category", "other"),
                source_type=skill.get("source_type", "python"),
                source_path=skill.get("source_path"),
                composable_with=skill.get("composable_with", []),
                dependencies=skill.get("dependencies", []),
                provides=skill.get("provides", [])
            )
    
    def export_index(self) -> Dict[str, Any]:
        """导出索引数据"""
        return {
            "skills": {name: asdict(entry) for name, entry in self._index.items()},
            "usage_stats": self._usage_stats,
            "exported_at": time.time()
        }
    
    def import_index(self, data: Dict[str, Any]):
        """导入索引数据"""
        if "skills" in data:
            for name, entry_data in data["skills"].items():
                self._index[name] = SkillIndexEntry(**entry_data)
                self._rebuild_indices_for_entry(self._index[name])
        
        if "usage_stats" in data:
            self._usage_stats.update(data["usage_stats"])
        
        self._save_index()


_skill_index_instance: Optional[SkillIndex] = None


def get_skill_index() -> SkillIndex:
    """获取技能索引单例"""
    global _skill_index_instance
    if _skill_index_instance is None:
        _skill_index_instance = SkillIndex()
    return _skill_index_instance
