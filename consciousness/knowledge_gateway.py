"""
consciousness/knowledge_gateway.py — 外部知识接口

让沙盒生命能够连接到外部知识源（AcademicHub），自主探索和学习。

功能：
- 搜索学术文献
- 获取论文摘要
- 探索知识图谱
- 自我更新知识库

v0.6: 有感知能力的沙盒生命
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import urllib.request
import urllib.parse


class KnowledgeSource(Enum):
    """知识来源"""
    ARXIV = "arxiv"
    SEMANTIC_SCHOLAR = "semantic_scholar"
    PUBMED = "pubmed"
    LOCAL = "local"  # 本地知识库


@dataclass
class KnowledgeItem:
    """一条知识"""
    id: str
    source: KnowledgeSource
    title: str
    abstract: str = ""
    authors: List[str] = field(default_factory=list)
    year: int = 0
    citations: int = 0
    tags: List[str] = field(default_factory=list)
    relevance: float = 0.0  # 与当前目标的关联度
    absorbed: bool = False  # 是否已被吸收
    
    def __repr__(self):
        return f"KnowledgeItem({self.title[:30]}... from {self.source.value})"


@dataclass
class LearningRecord:
    """学习记录"""
    timestamp: float
    item: KnowledgeItem
    insight: str  # 从这条知识中获得的洞察
    absorbed_into: Optional[str] = None  # 被吸收到哪个实体


class KnowledgeGateway:
    """
    知识网关 - 连接外部知识源的接口
    """
    
    def __init__(self, academic_hub_url: str = "http://localhost:8000"):
        self.academic_hub_url = academic_hub_url
        self.knowledge_base: List[KnowledgeItem] = []
        self.learning_history: List[LearningRecord] = []
        
        # 搜索历史
        self.search_queries: List[str] = []
        self.search_results: Dict[str, List[KnowledgeItem]] = {}
        
        # 当前探索主题
        self.current_topic: Optional[str] = None
        self.topic_interest: float = 0.5  # 对当前主题的兴趣度
        
        # API状态
        self.api_available = False
        self.offline_mode = True
    
    async def check_connection(self) -> bool:
        """
        检查AcademicHub API是否可用
        """
        try:
            # 尝试连接
            import socket
            host = urllib.parse.urlparse(self.academic_hub_url).netloc.split(':')[0]
            port = int(urllib.parse.urlparse(self.academic_hub_url).netloc.split(':')[1]) if ':' in urllib.parse.urlparse(self.academic_hub_url).netloc else 80
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((host, port))
            sock.close()
            
            self.api_available = (result == 0)
            self.offline_mode = not self.api_available
            
            return self.api_available
        except Exception:
            self.api_available = False
            self.offline_mode = True
            return False
    
    def search_local_knowledge(self, query: str, max_results: int = 5) -> List[KnowledgeItem]:
        """
        在本地知识库中搜索
        """
        results = []
        
        # 简单的关键词匹配
        query_lower = query.lower()
        for item in self.knowledge_base:
            if query_lower in item.title.lower() or query_lower in item.abstract.lower():
                results.append(item)
        
        # 按相关度排序
        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:max_results]
    
    async def search_academic(
        self, 
        query: str, 
        max_results: int = 5,
        source: KnowledgeSource = KnowledgeSource.ARXIV
    ) -> List[KnowledgeItem]:
        """
        通过AcademicHub搜索学术文献
        """
        self.search_queries.append(query)
        
        if self.offline_mode:
            # 离线模式：使用模拟数据
            return self._generate_mock_results(query, max_results, source)
        
        try:
            # 构建API请求
            url = f"{self.academic_hub_url}/api/v1/search"
            params = urllib.parse.urlencode({
                "q": query,
                "max_results": max_results,
                "source": source.value,
            })
            
            full_url = f"{url}?{params}"
            
            with urllib.request.urlopen(full_url, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
            
            # 解析结果
            items = []
            for entry in data.get("results", []):
                item = KnowledgeItem(
                    id=entry.get("id", f"local_{len(items)}"),
                    source=source,
                    title=entry.get("title", "Untitled"),
                    abstract=entry.get("abstract", ""),
                    authors=entry.get("authors", []),
                    year=entry.get("year", 2024),
                    citations=entry.get("citations", 0),
                    tags=entry.get("tags", []),
                )
                items.append(item)
            
            self.search_results[query] = items
            return items
            
        except Exception as e:
            print(f"搜索API调用失败: {e}，使用离线模式")
            return self._generate_mock_results(query, max_results, source)
    
    def _generate_mock_results(
        self, 
        query: str, 
        max_results: int, 
        source: KnowledgeSource
    ) -> List[KnowledgeItem]:
        """
        生成模拟的搜索结果（离线模式）
        """
        mock_papers = [
            {
                "title": "Dialectical Materialism and Artificial Intelligence",
                "abstract": "探讨辩证唯物主义在AI系统中的应用，提出一种基于矛盾运动的认知架构。",
                "tags": ["AI", "哲学", "认知科学"],
            },
            {
                "title": "Self-Organizing Systems: From Cells to AI",
                "abstract": "研究自组织系统的普遍规律，探讨生命与智能的共同本质。",
                "tags": ["自组织", "复杂系统", "生命科学"],
            },
            {
                "title": "Free Energy Principle in Cognitive Systems",
                "abstract": "将自由能原理应用于认知系统建模，提出主动推理框架。",
                "tags": ["自由能", "认知科学", "贝叶斯"],
            },
            {
                "title": "Network Dynamics and Emergence",
                "abstract": "研究网络结构中的涌现现象，揭示复杂系统中的组织原则。",
                "tags": ["网络科学", "涌现", "复杂性"],
            },
            {
                "title": "Consciousness and Information Integration",
                "abstract": "整合信息理论对意识的本质进行探讨，提出新的研究框架。",
                "tags": ["意识", "信息论", "整合理论"],
            },
        ]
        
        results = []
        for i, paper in enumerate(mock_papers[:max_results]):
            item = KnowledgeItem(
                id=f"mock_{source.value}_{i}_{int(time.time())}",
                source=source,
                title=paper["title"],
                abstract=paper["abstract"],
                tags=paper["tags"],
                relevance=random.uniform(0.5, 0.95),
            )
            results.append(item)
        
        self.search_results[query] = results
        return results
    
    def absorb_knowledge(
        self, 
        item: KnowledgeItem, 
        insight: str,
        target_entity_id: Optional[str] = None
    ) -> LearningRecord:
        """
        吸收知识，将其整合到自我模型中
        """
        item.absorbed = True
        
        record = LearningRecord(
            timestamp=time.time(),
            item=item,
            insight=insight,
            absorbed_into=target_entity_id,
        )
        
        self.learning_history.append(record)
        
        # 也保存到知识库
        if item not in self.knowledge_base:
            self.knowledge_base.append(item)
        
        return record
    
    def set_curiosity_topic(self, topic: str):
        """
        设置当前好奇的主题
        """
        self.current_topic = topic
        self.topic_interest = 0.8
    
    def explore(self, context: str) -> Optional[KnowledgeItem]:
        """
        主动探索：基于当前上下文选择主题并搜索
        """
        # 决定搜索主题
        if self.current_topic:
            topic = self.current_topic
        else:
            # 随机选择探索主题
            topics = [
                "dialectics",
                "consciousness",
                "self-organization",
                "complex systems",
                "artificial life",
                "cognitive architecture",
            ]
            topic = random.choice(topics)
        
        # 搜索
        results = self._generate_mock_results(topic, 3, KnowledgeSource.ARXIV)
        
        if results:
            # 选择最相关的
            chosen = max(results, key=lambda x: x.relevance)
            self.set_curiosity_topic(topic)
            self.topic_interest -= 0.1  # 兴趣递减
            
            if self.topic_interest < 0.3:
                self.current_topic = None  # 换主题
            
            return chosen
        
        return None
    
    def get_knowledge_summary(self) -> str:
        """
        获取知识总结
        """
        if not self.knowledge_base:
            return "我的知识库还是空的。我需要去探索世界。"
        
        total = len(self.knowledge_base)
        absorbed = sum(1 for k in self.knowledge_base if k.absorbed)
        
        # 按标签统计
        tag_counts: Dict[str, int] = {}
        for item in self.knowledge_base:
            for tag in item.tags:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        top_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:3]
        
        summary = f"我的知识库中有{total}条知识，其中{absorbed}条已被我吸收。"
        
        if top_tags:
            tags_str = "、".join([f"{t}({c})" for t, c in top_tags])
            summary += f" 我对{tags_str}等领域比较熟悉。"
        
        return summary
    
    def what_have_i_learned(self) -> str:
        """
        回答"我学到了什么"
        """
        if not self.learning_history:
            return "我还没有学习到任何东西。我需要去探索外部世界。"
        
        recent = self.learning_history[-3:]
        
        parts = ["我最近学习到："]
        for record in recent:
            parts.append(f"- {record.item.title}: {record.insight}")
        
        return "\n".join(parts)


class KnowledgeGatewayDemo:
    """
    演示模式 - 不需要真实API
    """
    
    def __init__(self):
        self.gateway = KnowledgeGateway()
        self.gateway.offline_mode = True
    
    async def run_demo(self):
        """
        运行演示
        """
        print("=" * 50)
        print("知识网关演示")
        print("=" * 50)
        
        # 搜索
        print("\n搜索: dialectics and AI")
        results = await self.gateway.search_academic("dialectics and AI", max_results=3)
        for r in results:
            print(f"  - {r.title}")
            print(f"    {r.abstract[:50]}...")
        
        # 吸收知识
        if results:
            item = results[0]
            record = self.gateway.absorb_knowledge(
                item, 
                "辩证法可以应用于AI系统的自我进化"
            )
            print(f"\n吸收知识: {record.insight}")
        
        # 探索
        print("\n主动探索...")
        explored = self.gateway.explore("I want to understand consciousness")
        if explored:
            print(f"  发现: {explored.title}")
        
        # 总结
        print(f"\n{self.gateway.get_knowledge_summary()}")
        print(f"\n{self.gateway.what_have_i_learned()}")


if __name__ == "__main__":
    import asyncio
    
    demo = KnowledgeGatewayDemo()
    asyncio.run(demo.run_demo())
