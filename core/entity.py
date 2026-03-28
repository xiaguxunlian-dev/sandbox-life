"""
entity.py — 事物节点

事物是实体感知世界的基本单位。
它不由外部定义，而是通过感知差异自发划定边界。

每个事物携带：
  - 特征向量（嵌入表示）
  - 不确定性权重
  - 激活历史
  - 生命状态
"""

from __future__ import annotations

import hashlib
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import numpy as np


class EntityState(Enum):
    """事物的生命状态"""
    ACTIVE = "active"       # 活跃：近期被激活
    DORMANT = "dormant"     # 休眠：长期未激活
    DYING = "dying"         # 消亡中：孤立且低活跃
    MERGED = "merged"       # 已合并入其他事物


@dataclass
class Entity:
    """
    事物节点

    不要手动创建，使用 Entity.create() 工厂方法。
    """

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    label: str = ""                          # 可选的人类可读标签（调试用，不参与推理）
    feature_vector: np.ndarray = field(default_factory=lambda: np.zeros(64))
    uncertainty: float = 0.5                 # 不确定性 ∈ [0,1]，越高越模糊
    activation_count: int = 0               # 历史激活次数
    last_activated: float = field(default_factory=time.time)
    created_at: float = field(default_factory=time.time)
    state: EntityState = EntityState.ACTIVE
    metadata: dict[str, Any] = field(default_factory=dict)

    # 用于反复制检测
    _structural_hash: str = field(default="", init=False, repr=False)

    def __post_init__(self):
        self._update_hash()

    @classmethod
    def create(
        cls,
        feature_vector: np.ndarray | None = None,
        label: str = "",
        uncertainty: float = 0.5,
        metadata: dict | None = None,
    ) -> "Entity":
        """工厂方法：创建新事物"""
        fv = feature_vector if feature_vector is not None else np.random.randn(64) * 0.1
        return cls(
            label=label,
            feature_vector=fv.astype(np.float32),
            uncertainty=float(np.clip(uncertainty, 0.0, 1.0)),
            metadata=metadata or {},
        )

    def activate(self) -> None:
        """激活事物（被感知/推理触碰）"""
        self.activation_count += 1
        self.last_activated = time.time()
        if self.state == EntityState.DORMANT:
            self.state = EntityState.ACTIVE

    def age(self) -> float:
        """返回自上次激活以来经过的时间（秒）"""
        return time.time() - self.last_activated

    def survival_probability(self, centrality: float = 0.0, alpha: float = 0.001) -> float:
        """
        计算生存概率（用于自然遗忘）

        P_survive = exp(-α * age) * (1 + centrality)
        高中心性的节点更不容易被遗忘。
        """
        import math
        return math.exp(-alpha * self.age()) * (1.0 + centrality)

    def similarity(self, other: "Entity") -> float:
        """余弦相似度"""
        a, b = self.feature_vector, other.feature_vector
        denom = (np.linalg.norm(a) * np.linalg.norm(b))
        if denom < 1e-8:
            return 0.0
        return float(np.dot(a, b) / denom)

    def _update_hash(self) -> None:
        """更新结构哈希（用于反复制检测）"""
        content = self.feature_vector.tobytes() + self.id.encode()
        self._structural_hash = hashlib.sha256(content).hexdigest()

    @property
    def structural_hash(self) -> str:
        return self._structural_hash

    def to_dict(self) -> dict:
        """序列化为字典（用于透明日志）"""
        return {
            "id": self.id,
            "label": self.label,
            "uncertainty": self.uncertainty,
            "activation_count": self.activation_count,
            "last_activated": self.last_activated,
            "created_at": self.created_at,
            "state": self.state.value,
            "feature_norm": float(np.linalg.norm(self.feature_vector)),
            "structural_hash": self._structural_hash,
        }

    def __repr__(self) -> str:
        label_str = f'"{self.label}"' if self.label else self.id[:8]
        return f"Entity({label_str}, σ={self.uncertainty:.2f}, state={self.state.value})"
