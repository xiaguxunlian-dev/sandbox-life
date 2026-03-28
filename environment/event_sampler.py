"""
事件采样器：按好奇心驱动选择下一个事件
Event Sampler: Select next event based on curiosity-driven sampling
"""

import numpy as np
from typing import List, Optional, Tuple, Any, Dict
from dataclasses import dataclass


@dataclass
class SamplerConfig:
    """采样器配置"""
    strategy: str = "curiosity"  # "curiosity" | "random" | "sequential" | "entropy"
    temperature: float = 1.0      # 温度参数（用于概率采样）
    surprise_weight: float = 0.4  # 意外度权重
    recency_weight: float = 0.3   # 近因效应权重
    diversity_weight: float = 0.3 # 多样性权重


class EventSampler:
    """
    历史事件采样器
    
    多种采样策略：
    - curiosity: 基于意外度（KL散度近似）
    - random: 随机采样
    - sequential: 按时间顺序
    - entropy: 基于事件的信息熵
    """
    
    def __init__(self, config: Optional[SamplerConfig] = None):
        self.config = config or SamplerConfig()
        self.event_history: List[Any] = []
        self.selected_count = 0
        
    def select(
        self, 
        candidates: List[Any],
        entity_state: Any = None,
    ) -> Optional[Tuple[int, Any]]:
        """
        选择下一个事件
        
        Args:
            candidates: 候选事件列表
            entity_state: 实体当前状态（可选）
            
        Returns:
            (index, event) 或 None
        """
        if not candidates:
            return None
        
        strategy = self.config.strategy
        
        if strategy == "curiosity":
            return self._select_by_curiosity(candidates, entity_state)
        elif strategy == "random":
            return self._select_random(candidates)
        elif strategy == "sequential":
            return self._select_sequential(candidates)
        elif strategy == "entropy":
            return self._select_by_entropy(candidates)
        else:
            return self._select_random(candidates)
    
    def _select_by_curiosity(
        self, 
        candidates: List[Any],
        entity_state: Any
    ) -> Tuple[int, Any]:
        """
        基于好奇心（意外度）选择
        """
        scored = []
        
        for i, event in enumerate(candidates):
            score = self._compute_curiosity_score(event, i, len(candidates))
            scored.append((i, event, score))
        
        # 转换为概率分布
        scores = np.array([s[2] for s in scored])
        probs = self._softmax(scores, temperature=self.config.temperature)
        
        # 采样
        idx = np.random.choice(len(candidates), p=probs)
        self.selected_count += 1
        self.event_history.append(candidates[idx])
        
        return idx, candidates[idx]
    
    def _compute_curiosity_score(self, event: Any, position: int, total: int) -> float:
        """
        计算事件的好奇心分数
        """
        score = 0.0
        
        # 1. 意外度（基于结构冲击）
        if hasattr(event, 'entropy_delta'):
            structural_impact = event.entropy_delta
        elif hasattr(event, 'structural_impact'):
            structural_impact = event.structural_impact
        else:
            structural_impact = 0.5
        
        score += structural_impact * self.config.surprise_weight
        
        # 2. 近因效应（偏好选择后面的事件）
        recency = position / max(total - 1, 1)
        score += (1 - recency) * self.config.recency_weight
        
        # 3. 多样性（惩罚连续相似类型）
        if self.event_history and hasattr(event, 'relations'):
            last_event = self.event_history[-1]
            if hasattr(last_event, 'relations'):
                similarity = self._compute_similarity(event, last_event)
                diversity_bonus = (1 - similarity) * self.config.diversity_weight
                score += diversity_bonus
        
        return score
    
    def _compute_similarity(self, e1: Any, e2: Any) -> float:
        """计算两个事件的相似度"""
        r1 = set(e1.relations) if hasattr(e1, 'relations') else set()
        r2 = set(e2.relations) if hasattr(e2, 'relations') else set()
        
        if not r1 or not r2:
            return 0.0
        
        intersection = len(r1 & r2)
        union = len(r1 | r2)
        
        return intersection / union if union > 0 else 0.0
    
    def _softmax(self, x: np.ndarray, temperature: float = 1.0) -> np.ndarray:
        """softmax 转换"""
        exp_x = np.exp(x / temperature)
        return exp_x / exp_x.sum()
    
    def _select_random(self, candidates: List[Any]) -> Tuple[int, Any]:
        """随机选择"""
        idx = np.random.randint(0, len(candidates))
        self.selected_count += 1
        self.event_history.append(candidates[idx])
        return idx, candidates[idx]
    
    def _select_sequential(self, candidates: List[Any]) -> Tuple[int, Any]:
        """顺序选择（基于时间戳）"""
        # 按时间排序
        sorted_candidates = sorted(
            candidates, 
            key=lambda e: e.timestamp if hasattr(e, 'timestamp') and e.timestamp else 0
        )
        # 选择最接近当前历史下一个的
        last_ts = 0
        if self.event_history:
            last_ts = self.event_history[-1].timestamp if hasattr(self.event_history[-1], 'timestamp') else 0
        
        for i, c in enumerate(sorted_candidates):
            ts = c.timestamp if hasattr(c, 'timestamp') and c.timestamp else 0
            if ts >= last_ts:
                self.selected_count += 1
                self.event_history.append(c)
                return i, c
        
        # 如果都更早，选择最早的
        self.selected_count += 1
        self.event_history.append(sorted_candidates[0])
        return 0, sorted_candidates[0]
    
    def _select_by_entropy(self, candidates: List[Any]) -> Tuple[int, Any]:
        """基于信息熵选择（最大化信息增益）"""
        entropies = []
        
        for event in candidates:
            # 简化的熵估计：基于事件中的实体和关系数量
            n_entities = len(event.entities) if hasattr(event, 'entities') else 1
            n_relations = len(event.relations) if hasattr(event, 'relations') else 1
            
            # 熵 = log(可能状态数) ≈ log(n_entities * n_relations)
            entropy = np.log(n_entities * n_relations + 1)
            entropies.append(entropy)
        
        # 选择熵最高的
        entropies = np.array(entropies)
        probs = self._softmax(entropies, temperature=self.config.temperature)
        
        idx = np.random.choice(len(candidates), p=probs)
        self.selected_count += 1
        self.event_history.append(candidates[idx])
        
        return idx, candidates[idx]
    
    def get_statistics(self) -> Dict:
        """获取采样统计"""
        return {
            "total_selected": self.selected_count,
            "strategy": self.config.strategy,
            "history_length": len(self.event_history),
        }


if __name__ == "__main__":
    # 测试采样器
    from book_parser import load_sample_shiji
    
    events = load_sample_shiji()
    
    # 测试不同策略
    for strategy in ["curiosity", "random", "entropy"]:
        config = SamplerConfig(strategy=strategy)
        sampler = EventSampler(config)
        
        # 模拟选择10次
        for _ in range(10):
            idx, event = sampler.select(events)
            print(f"策略 {strategy}: [{event.timestamp}] {event.entities[:2]}")
        
        print()
