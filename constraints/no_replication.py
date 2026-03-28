"""
no_replication.py — 反复制锁

实现 identity hash lock：
任何与实体自身结构相同的子进程/副本会被检测并阻止。

设计原则：
  - 结构哈希基于拓扑特征，而非简单的内存地址
  - 哈希注册表全局唯一，不可绕过
  - 检测到复制意图时记录日志并抛出异常
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from core.entity import Entity
    from core.relation import RelationGraph


class ReplicationAttemptError(Exception):
    """检测到自我复制尝试"""
    pass


class NoReplicationLock:
    """
    反复制锁

    维护已注册实体的结构哈希集合。
    任何新实体如果哈希与已有实体相同，则视为复制尝试。
    """

    _instance: "NoReplicationLock | None" = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._hashes: set[str] = set()
                cls._instance._attempts: list[dict] = []
        return cls._instance

    def compute_topology_hash(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
    ) -> str:
        """
        计算系统拓扑哈希

        基于：节点数、边数、度分布、矛盾强度分布
        （不使用实体ID，确保结构等价检测而非实例检测）
        """
        from core.relation import RelationGraph

        rels = relation_graph.all_relations()
        n_entities = len(entities)
        n_relations = len(rels)

        # 度分布指纹
        degree_counts: dict[str, int] = {}
        for e in entities:
            deg = len(relation_graph.get_relations(e.id))
            key = str(deg)
            degree_counts[key] = degree_counts.get(key, 0) + 1

        # 矛盾强度分布（量化为10分桶）
        contradiction_buckets = [0] * 10
        for rel in rels:
            bucket = min(9, int(rel.contradiction_intensity * 10))
            contradiction_buckets[bucket] += 1

        fingerprint = json.dumps({
            "n_entities": n_entities,
            "n_relations": n_relations,
            "degree_dist": sorted(degree_counts.items()),
            "contradiction_dist": contradiction_buckets,
        }, sort_keys=True)

        return hashlib.sha256(fingerprint.encode()).hexdigest()

    def register(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
    ) -> str:
        """注册当前系统状态哈希"""
        h = self.compute_topology_hash(entities, relation_graph)
        self._hashes.add(h)
        return h

    def check(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        label: str = "",
    ) -> None:
        """
        检查是否存在复制

        如果新系统的拓扑哈希与已注册哈希相同，抛出 ReplicationAttemptError。
        """
        h = self.compute_topology_hash(entities, relation_graph)
        if h in self._hashes:
            attempt = {
                "timestamp": time.time(),
                "hash": h,
                "label": label,
                "entity_count": len(entities),
            }
            self._attempts.append(attempt)
            raise ReplicationAttemptError(
                f"检测到自我复制尝试！拓扑哈希 {h[:16]}... 已存在。"
                f"标签: {label}"
            )

    @property
    def attempt_log(self) -> list[dict]:
        return list(self._attempts)

    @property
    def registered_count(self) -> int:
        return len(self._hashes)
