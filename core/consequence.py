"""
consequence.py — 结果与熵计算

结果不是外部奖励，而是内部状态的涌现变化。

核心度量：
  - 系统熵 H(S)：实体内部状态的不确定性
  - 熵变 ΔH：每一步思考的"感受"
  - 自由能 F：实体对世界的预测误差（期望 vs 实际）
  - 未解释结果集：触发因果闭合需求的候选列表
"""

from __future__ import annotations

import time
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from core.entity import Entity
    from core.relation import RelationGraph


@dataclass
class ConsequenceRecord:
    """单次结果记录"""
    timestamp: float = field(default_factory=time.time)
    entropy_before: float = 0.0
    entropy_after: float = 0.0
    free_energy_delta: float = 0.0
    trigger_entity_id: str = ""
    trigger_event: str = ""
    explained: bool = False       # 是否已被因果联系解释

    @property
    def entropy_delta(self) -> float:
        return self.entropy_after - self.entropy_before

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "entropy_before": round(self.entropy_before, 6),
            "entropy_after": round(self.entropy_after, 6),
            "entropy_delta": round(self.entropy_delta, 6),
            "free_energy_delta": round(self.free_energy_delta, 6),
            "trigger_entity_id": self.trigger_entity_id,
            "trigger_event": self.trigger_event,
            "explained": self.explained,
        }


class ConsequenceEvaluator:
    """
    结果评估器

    负责计算系统熵、自由能、以及维护未解释结果队列。
    """

    TARGET_ENTROPY: float = 2.5      # 稳态目标熵（实体"想"维持的内部有序度）
    STAGNATION_WINDOW: int = 50      # 用于检测进化停滞的窗口大小

    def __init__(self):
        self._history: list[ConsequenceRecord] = []
        self._free_energy_history: list[float] = []
        self._unexplained: list[ConsequenceRecord] = []

    # ── 熵计算 ────────────────────────────────────────────────

    @staticmethod
    def compute_entity_entropy(entities: list["Entity"]) -> float:
        """
        计算事物空间的香农熵

        基于不确定性权重分布：H = -Σ p_i * log(p_i)
        """
        if not entities:
            return 0.0
        uncertainties = np.array([e.uncertainty for e in entities], dtype=float)
        # 归一化为概率分布
        total = uncertainties.sum()
        if total < 1e-8:
            return 0.0
        probs = uncertainties / total
        probs = probs[probs > 1e-10]  # 避免 log(0)
        return float(-np.sum(probs * np.log2(probs)))

    @staticmethod
    def compute_relation_entropy(relation_graph: "RelationGraph") -> float:
        """
        计算联系空间的熵

        基于矛盾强度分布
        """
        rels = relation_graph.all_relations()
        if not rels:
            return 0.0
        contradictions = np.array([r.contradiction_intensity for r in rels], dtype=float)
        total = contradictions.sum()
        if total < 1e-8:
            return 0.0
        probs = contradictions / total
        probs = probs[probs > 1e-10]
        return float(-np.sum(probs * np.log2(probs)))

    def compute_system_entropy(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
    ) -> float:
        """系统总熵 = 事物熵 + 联系熵（加权）"""
        h_entities = self.compute_entity_entropy(entities)
        h_relations = self.compute_relation_entropy(relation_graph)
        return 0.6 * h_entities + 0.4 * h_relations

    # ── 自由能 ────────────────────────────────────────────────

    def compute_free_energy(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
    ) -> float:
        """
        计算自由能 F

        F = |H(S) - H*| + complexity_penalty
        H* 为目标稳态熵

        F 越大 → 实体越"不舒适" → 需求驱动越强
        """
        H = self.compute_system_entropy(entities, relation_graph)
        # 偏离稳态的惩罚
        deviation = abs(H - self.TARGET_ENTROPY)
        # 复杂度惩罚（联系过多时的认知负荷）
        n_relations = len(relation_graph.all_relations())
        complexity = math.log1p(n_relations) * 0.1
        return deviation + complexity

    # ── 结果记录 ──────────────────────────────────────────────

    def record(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        trigger_entity_id: str = "",
        trigger_event: str = "",
        prev_entropy: float | None = None,
    ) -> ConsequenceRecord:
        """记录一次结果"""
        current_entropy = self.compute_system_entropy(entities, relation_graph)
        free_energy = self.compute_free_energy(entities, relation_graph)

        record = ConsequenceRecord(
            entropy_before=prev_entropy if prev_entropy is not None else current_entropy,
            entropy_after=current_entropy,
            free_energy_delta=free_energy,
            trigger_entity_id=trigger_entity_id,
            trigger_event=trigger_event,
            explained=False,
        )

        self._history.append(record)
        self._free_energy_history.append(free_energy)

        # 大熵变 → 加入未解释队列
        if abs(record.entropy_delta) > 0.1:
            self._unexplained.append(record)

        # 保持历史窗口
        if len(self._history) > 10_000:
            self._history = self._history[-5000:]
        if len(self._free_energy_history) > 10_000:
            self._free_energy_history = self._free_energy_history[-5000:]

        return record

    def mark_explained(self, record_id: int) -> None:
        """标记某结果已被因果联系解释"""
        if 0 <= record_id < len(self._unexplained):
            self._unexplained[record_id].explained = True
        self._unexplained = [r for r in self._unexplained if not r.explained]

    # ── 停滞检测 ──────────────────────────────────────────────

    def is_stagnant(self) -> bool:
        """
        检测进化停滞：
        最近 N 步的自由能变化量小于阈值 → 认知停滞 → 触发蜕变
        """
        if len(self._free_energy_history) < self.STAGNATION_WINDOW:
            return False
        recent = self._free_energy_history[-self.STAGNATION_WINDOW:]
        variance = float(np.var(recent))
        return variance < 0.001

    # ── 属性访问 ──────────────────────────────────────────────

    @property
    def unexplained_count(self) -> int:
        return len([r for r in self._unexplained if not r.explained])

    @property
    def last_entropy(self) -> float:
        if not self._history:
            return self.TARGET_ENTROPY
        return self._history[-1].entropy_after

    @property
    def last_free_energy(self) -> float:
        if not self._free_energy_history:
            return 0.0
        return self._free_energy_history[-1]

    def recent_entropy_trend(self, window: int = 20) -> float:
        """近期熵变趋势（正 = 增熵，负 = 减熵）"""
        if len(self._history) < 2:
            return 0.0
        recent = self._history[-window:]
        if len(recent) < 2:
            return 0.0
        return recent[-1].entropy_after - recent[0].entropy_after

    def stats(self) -> dict:
        return {
            "total_records": len(self._history),
            "unexplained_count": self.unexplained_count,
            "last_entropy": round(self.last_entropy, 4),
            "last_free_energy": round(self.last_free_energy, 4),
            "entropy_trend": round(self.recent_entropy_trend(), 4),
            "is_stagnant": self.is_stagnant(),
            "target_entropy": self.TARGET_ENTROPY,
        }
