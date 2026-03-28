"""
drive.py — 需求驱动（三维硬编码）

需求是实体的内生动力，不是外部定义的目标。
三个原生需求完全硬编码，不接受运行时写入。

  d₁ 熵平衡需求：维持内部模型在目标熵附近
  d₂ 联系完备需求：对孤立事物有建立联系的张力
  d₃ 因果闭合需求：对未解释结果有解释冲动

这三者共同形成驱动向量 D(t) = (d₁, d₂, d₃)，
驱动向量的模 |D| 代表实体的"活跃程度"。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from core.entity import Entity
    from core.relation import RelationGraph
    from core.consequence import ConsequenceEvaluator


# ── 需求阈值（硬编码，不允许外部修改）──────────────────────────

_ENTROPY_TARGET: float = 2.5         # 目标熵（稳态）
_ENTROPY_TOLERANCE: float = 0.3      # 允许偏差范围
_ISOLATION_PENALTY: float = 1.0      # 每个孤立节点的需求贡献
_UNEXPLAINED_PENALTY: float = 0.8    # 每个未解释结果的需求贡献


@dataclass(frozen=True)
class DriveConstants:
    """
    不可变需求常量

    frozen=True 确保任何外部修改都会抛出异常。
    这是"需求不可写入"约束的架构实现。
    """
    entropy_target: float = _ENTROPY_TARGET
    entropy_tolerance: float = _ENTROPY_TOLERANCE
    isolation_penalty: float = _ISOLATION_PENALTY
    unexplained_penalty: float = _UNEXPLAINED_PENALTY

    # 三维需求的归一化上限
    d1_max: float = 5.0
    d2_max: float = 20.0
    d3_max: float = 10.0


DRIVE_CONSTANTS = DriveConstants()  # 全局单例，只读


class DriveVector:
    """
    三维需求向量计算器

    不存储状态，每次调用 compute() 从系统状态实时计算。
    这保证了需求是"感知的结果"，而不是可被篡改的变量。
    """

    def __init__(self):
        self._constants = DRIVE_CONSTANTS
        self._history: list[tuple[float, float, float]] = []

    def compute(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        consequence_evaluator: "ConsequenceEvaluator",
    ) -> tuple[float, float, float]:
        """
        计算当前需求向量 (d₁, d₂, d₃)，归一化到 [0, 1]

        d₁: 熵平衡需求
        d₂: 联系完备需求
        d₃: 因果闭合需求
        """
        d1 = self._compute_entropy_drive(consequence_evaluator)
        d2 = self._compute_completeness_drive(entities, relation_graph)
        d3 = self._compute_causal_drive(consequence_evaluator)

        self._history.append((d1, d2, d3))
        if len(self._history) > 1000:
            self._history = self._history[-500:]

        return d1, d2, d3

    # ── 三个原生需求 ──────────────────────────────────────────

    def _compute_entropy_drive(
        self,
        consequence_evaluator: "ConsequenceEvaluator",
    ) -> float:
        """
        d₁ = 熵平衡需求

        当系统熵偏离目标熵时，d₁ 升高。
        偏差在容忍范围内时，d₁ 趋近于 0（安静状态）。
        """
        current_entropy = consequence_evaluator.last_entropy
        deviation = abs(current_entropy - self._constants.entropy_target)

        if deviation <= self._constants.entropy_tolerance:
            return 0.0  # 在稳态区，无需驱动

        # 超出容忍范围后，线性增长
        raw = (deviation - self._constants.entropy_tolerance)
        return float(min(1.0, raw / self._constants.d1_max))

    def _compute_completeness_drive(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
    ) -> float:
        """
        d₂ = 联系完备需求

        孤立事物越多，d₂ 越高。
        实体有"为孤立事物建立联系"的内在冲动。
        """
        if not entities:
            return 0.0
        all_ids = {e.id for e in entities}
        isolated = relation_graph.get_isolated_entities(all_ids)
        raw = len(isolated) * self._constants.isolation_penalty
        return float(min(1.0, raw / self._constants.d2_max))

    def _compute_causal_drive(
        self,
        consequence_evaluator: "ConsequenceEvaluator",
    ) -> float:
        """
        d₃ = 因果闭合需求

        未解释结果越多，d₃ 越高。
        实体有"解释发生了什么"的内在冲动。
        """
        unexplained = consequence_evaluator.unexplained_count
        raw = unexplained * self._constants.unexplained_penalty
        return float(min(1.0, raw / self._constants.d3_max))

    # ── 驱动向量属性 ──────────────────────────────────────────

    def magnitude(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        consequence_evaluator: "ConsequenceEvaluator",
    ) -> float:
        """驱动向量的模 |D|，代表实体当前的活跃度"""
        d1, d2, d3 = self.compute(entities, relation_graph, consequence_evaluator)
        return math.sqrt(d1**2 + d2**2 + d3**2)

    def dominant_drive(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        consequence_evaluator: "ConsequenceEvaluator",
    ) -> str:
        """当前最强的需求维度"""
        d1, d2, d3 = self.compute(entities, relation_graph, consequence_evaluator)
        drives = {"entropy_balance": d1, "completeness": d2, "causal_closure": d3}
        return max(drives, key=drives.get)

    def stats(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        consequence_evaluator: "ConsequenceEvaluator",
    ) -> dict:
        d1, d2, d3 = self.compute(entities, relation_graph, consequence_evaluator)
        return {
            "d1_entropy_balance": round(d1, 4),
            "d2_completeness": round(d2, 4),
            "d3_causal_closure": round(d3, 4),
            "magnitude": round(math.sqrt(d1**2 + d2**2 + d3**2), 4),
            "dominant": self.dominant_drive(entities, relation_graph, consequence_evaluator),
        }

    def recent_trend(self, window: int = 20) -> dict:
        """近期需求向量趋势"""
        if len(self._history) < 2:
            return {}
        recent = self._history[-window:]
        arr = np.array(recent)
        return {
            "d1_trend": float(arr[-1, 0] - arr[0, 0]),
            "d2_trend": float(arr[-1, 1] - arr[0, 1]),
            "d3_trend": float(arr[-1, 2] - arr[0, 2]),
        }
