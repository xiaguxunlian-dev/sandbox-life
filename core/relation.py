"""
relation.py — 辩证联系

联系不是静态的知识图谱边，而是带矛盾张力的双极动态关系。

核心概念：
  - 每条联系有正向权重（促进）和负向权重（矛盾/否定）
  - 矛盾强度 = 1 - |w⁺ - w⁻|，两极势均力敌时矛盾最激烈
  - 联系随"结果验证"动态更新（贝叶斯更新）
  - 联系有时间衰减（遗忘）

辩证法三定律在联系中的体现：
  1. 对立统一：每条联系同时携带正向和负向张力
  2. 量变质变：矛盾强度积累到阈值时触发拓扑跃迁
  3. 否定之否定：联系可以经历"反转-综合"的辩证运动
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity


class RelationType(Enum):
    """联系的主导性质（动态，随权重变化）"""
    POSITIVE_DOMINANT = "positive_dominant"   # 正向主导
    NEGATIVE_DOMINANT = "negative_dominant"   # 负向主导（矛盾/否定）
    CONTRADICTORY = "contradictory"           # 矛盾激烈（势均力敌）
    RESOLVED = "resolved"                     # 已综合（经历过否定之否定）


class NegationState(Enum):
    """否定状态（用于否定之否定追踪）"""
    THESIS = "thesis"           # 正题
    ANTITHESIS = "antithesis"   # 反题
    SYNTHESIS = "synthesis"     # 合题


@dataclass
class DialecticalRelation:
    """
    辩证联系

    核心公式：
      矛盾强度 = 1 - |w⁺ - w⁻|   ∈ [0, 1]
      联系强度 = (w⁺ + w⁻) / 2   ∈ [0, 1]
      主导极 = "positive" if w⁺ > w⁻ else "negative"
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""          # 源事物 ID
    target_id: str = ""          # 目标事物 ID

    # 双极权重（辩证核心）
    w_pos: float = 0.5           # 正向权重：促进/统一
    w_neg: float = 0.5           # 负向权重：矛盾/否定

    # 时间参数
    time_delay: float = 0.0      # 因果时延（秒或事件步）
    created_at: float = field(default_factory=time.time)
    last_updated: float = field(default_factory=time.time)
    update_count: int = 0

    # 辩证状态追踪
    negation_state: NegationState = NegationState.THESIS
    negation_history: list[dict] = field(default_factory=list)

    # 因果方向性（源→目标 的因果强度）
    causal_strength: float = 0.5  # ∈ [0,1]，0=相关，1=强因果

    def __post_init__(self):
        self.w_pos = float(_clamp(self.w_pos))
        self.w_neg = float(_clamp(self.w_neg))

    # ── 核心属性 ──────────────────────────────────────────────

    @property
    def contradiction_intensity(self) -> float:
        """
        矛盾强度 ∈ [0, 1]
        越接近 1 → 两极势均力敌 → 越不稳定 → 越可能质变
        """
        return 1.0 - abs(self.w_pos - self.w_neg)

    @property
    def relation_strength(self) -> float:
        """联系总强度（正负之和的均值）"""
        return (self.w_pos + self.w_neg) / 2.0

    @property
    def dominant_pole(self) -> str:
        """主导极"""
        if self.w_pos > self.w_neg + 0.05:
            return "positive"
        elif self.w_neg > self.w_pos + 0.05:
            return "negative"
        else:
            return "balanced"  # 矛盾区

    @property
    def relation_type(self) -> RelationType:
        if self.negation_state == NegationState.SYNTHESIS:
            return RelationType.RESOLVED
        if self.dominant_pole == "positive":
            return RelationType.POSITIVE_DOMINANT
        elif self.dominant_pole == "negative":
            return RelationType.NEGATIVE_DOMINANT
        else:
            return RelationType.CONTRADICTORY

    # ── 更新方法 ──────────────────────────────────────────────

    def bayesian_update(
        self,
        observed_positive: bool,
        learning_rate: float = 0.1,
        decay: float = 0.995,
    ) -> None:
        """
        贝叶斯风格权重更新 + 时间衰减

        observed_positive=True  → 正向证据（联系促进了结果）
        observed_positive=False → 负向证据（联系阻碍/矛盾了结果）
        """
        # 时间衰减
        self.w_pos *= decay
        self.w_neg *= decay

        # 贝叶斯更新
        if observed_positive:
            self.w_pos = _clamp(self.w_pos + learning_rate * (1 - self.w_pos))
        else:
            self.w_neg = _clamp(self.w_neg + learning_rate * (1 - self.w_neg))

        self.last_updated = time.time()
        self.update_count += 1

    def negate(self) -> None:
        """
        第一次否定：反转主导极

        正题 → 反题：w_pos 和 w_neg 互换
        """
        if self.negation_state == NegationState.THESIS:
            snapshot = {"w_pos": self.w_pos, "w_neg": self.w_neg, "time": time.time()}
            self.negation_history.append(snapshot)
            self.w_pos, self.w_neg = self.w_neg, self.w_pos
            self.negation_state = NegationState.ANTITHESIS

    def synthesize(self) -> None:
        """
        否定之否定：综合对立双方

        合题：取两次状态的加权综合，不是简单回到起点
        """
        if self.negation_state == NegationState.ANTITHESIS and self.negation_history:
            prev = self.negation_history[-1]
            # 综合 = 保留两者各自合理内核
            self.w_pos = _clamp((self.w_pos + prev["w_pos"]) / 2.0 + 0.05)
            self.w_neg = _clamp((self.w_neg + prev["w_neg"]) / 2.0 - 0.05)
            self.negation_state = NegationState.SYNTHESIS
            self.last_updated = time.time()

    def decay_spontaneous(self, alpha: float = 0.0005) -> None:
        """自然衰减（长期未更新的联系自动弱化）"""
        elapsed = time.time() - self.last_updated
        factor = (1.0 - alpha) ** elapsed
        self.w_pos *= factor
        self.w_neg *= factor

    # ── 序列化 ────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "w_pos": round(self.w_pos, 4),
            "w_neg": round(self.w_neg, 4),
            "contradiction_intensity": round(self.contradiction_intensity, 4),
            "relation_strength": round(self.relation_strength, 4),
            "dominant_pole": self.dominant_pole,
            "relation_type": self.relation_type.value,
            "negation_state": self.negation_state.value,
            "causal_strength": round(self.causal_strength, 4),
            "update_count": self.update_count,
            "last_updated": self.last_updated,
        }

    def __repr__(self) -> str:
        return (
            f"Relation({self.source_id[:6]}→{self.target_id[:6]}, "
            f"contradiction={self.contradiction_intensity:.2f}, "
            f"type={self.relation_type.value})"
        )


# ── 辩证联系图 ────────────────────────────────────────────────

class RelationGraph:
    """
    辩证联系图

    基于 dict 实现（不依赖 networkx 以保持可控性），
    同时提供 networkx 导出接口用于可视化。
    """

    def __init__(self):
        self._relations: dict[str, DialecticalRelation] = {}  # id → relation
        self._adjacency: dict[str, set[str]] = {}              # entity_id → {relation_id}

    def add_relation(
        self,
        source_id: str,
        target_id: str,
        w_pos: float = 0.5,
        w_neg: float = 0.5,
        causal_strength: float = 0.5,
    ) -> DialecticalRelation:
        """添加新联系"""
        rel = DialecticalRelation(
            source_id=source_id,
            target_id=target_id,
            w_pos=w_pos,
            w_neg=w_neg,
            causal_strength=causal_strength,
        )
        self._relations[rel.id] = rel
        self._adjacency.setdefault(source_id, set()).add(rel.id)
        self._adjacency.setdefault(target_id, set()).add(rel.id)
        return rel

    def get_relations(self, entity_id: str) -> list[DialecticalRelation]:
        """获取与某事物相关的所有联系"""
        rel_ids = self._adjacency.get(entity_id, set())
        return [self._relations[rid] for rid in rel_ids if rid in self._relations]

    def find_hotspots(self, top_k: int = 5) -> list[tuple[str, float]]:
        """
        找到矛盾最激烈的联系（质变候选）

        返回 [(relation_id, contradiction_intensity), ...]
        """
        scored = [
            (rel.id, rel.contradiction_intensity)
            for rel in self._relations.values()
        ]
        return sorted(scored, key=lambda x: x[1], reverse=True)[:top_k]

    def get_isolated_entities(self, all_entity_ids: set[str]) -> set[str]:
        """找到没有任何联系的孤立事物（触发联系完备需求）"""
        connected = set(self._adjacency.keys())
        return all_entity_ids - connected

    def contradiction_load(self, entity_id: str) -> float:
        """计算某事物的矛盾负荷（其所有联系矛盾强度之和）"""
        rels = self.get_relations(entity_id)
        if not rels:
            return 0.0
        return sum(r.contradiction_intensity for r in rels) / len(rels)

    def remove_relation(self, relation_id: str) -> None:
        """删除联系"""
        rel = self._relations.pop(relation_id, None)
        if rel:
            self._adjacency.get(rel.source_id, set()).discard(relation_id)
            self._adjacency.get(rel.target_id, set()).discard(relation_id)

    def all_relations(self) -> list[DialecticalRelation]:
        return list(self._relations.values())

    def to_networkx(self):
        """导出为 networkx 图（用于可视化）"""
        try:
            import networkx as nx
            G = nx.DiGraph()
            for rel in self._relations.values():
                G.add_edge(
                    rel.source_id,
                    rel.target_id,
                    **rel.to_dict(),
                )
            return G
        except ImportError:
            raise ImportError("networkx 未安装，请运行 pip install networkx")

    def stats(self) -> dict:
        rels = list(self._relations.values())
        if not rels:
            return {"total_relations": 0}
        contradictions = [r.contradiction_intensity for r in rels]
        return {
            "total_relations": len(rels),
            "avg_contradiction": round(sum(contradictions) / len(contradictions), 4),
            "max_contradiction": round(max(contradictions), 4),
            "contradictory_count": sum(1 for c in contradictions if c > 0.8),
        }


def _clamp(v: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, v))
