"""
dialectical.py — 辩证进化引擎

实现辩证法三定律驱动的自我进化：

  1. 量变积累：每步更新联系权重（渐进）
  2. 质变跃迁：矛盾强度超过阈值时拓扑突变
  3. 否定之否定：跃迁后进入反题，再综合为合题

进化不使用梯度下降，使用拓扑操作：
  - 节点合并（两个高共激活节点 → 新概念）
  - 节点分裂（矛盾过多的节点 → 对立双方）
  - 节点消亡（孤立 + 低激活）
  - 联系反转（因果验证失败）
  - 蜕变重组（进化停滞时保留30%核心，其余重组）
"""

from __future__ import annotations

import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from core.entity import Entity
    from core.relation import RelationGraph, DialecticalRelation
    from core.consequence import ConsequenceEvaluator
    from core.drive import DriveVector
    from constraints.transparency import TransparencyLog

# 质变触发阈值
LEAP_THRESHOLD = 0.92           # 矛盾强度 > 此值触发质变（初始随机权重约0.5，强度约1.0，需要更高阈值）
MERGE_SIMILARITY_THRESHOLD = 0.9  # 相似度 > 此值触发合并
DEATH_AGE_THRESHOLD = 300.0     # 孤立超过此时间（秒）触发消亡
STAGNATION_METAMORPHOSIS_RATIO = 0.3  # 停滞蜕变保留比例


class EvolutionEvent(Enum):
    QUANTITATIVE_UPDATE = "quantitative_update"   # 量变
    QUALITATIVE_LEAP = "qualitative_leap"          # 质变
    NODE_MERGE = "node_merge"                      # 节点合并
    NODE_SPLIT = "node_split"                      # 节点分裂
    NODE_DEATH = "node_death"                      # 节点消亡
    RELATION_INVERSION = "relation_inversion"      # 联系反转
    METAMORPHOSIS = "metamorphosis"               # 蜕变重组


@dataclass
class EvolutionStep:
    """单次进化步骤记录"""
    step_id: int
    timestamp: float = field(default_factory=time.time)
    event: EvolutionEvent = EvolutionEvent.QUANTITATIVE_UPDATE
    details: dict = field(default_factory=dict)
    free_energy_before: float = 0.0
    free_energy_after: float = 0.0

    @property
    def free_energy_delta(self) -> float:
        return self.free_energy_after - self.free_energy_before

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "timestamp": self.timestamp,
            "event": self.event.value,
            "details": self.details,
            "free_energy_before": round(self.free_energy_before, 4),
            "free_energy_after": round(self.free_energy_after, 4),
            "free_energy_delta": round(self.free_energy_delta, 4),
        }


class DialecticalEvolution:
    """
    辩证进化引擎

    每一步进化分为两个阶段：
      1. 量变（quantitative_step）：更新权重，积累矛盾
      2. 质变检测（check_leaps）：检测并触发拓扑跃迁
    """

    def __init__(
        self,
        entities: list["Entity"],
        relation_graph: "RelationGraph",
        consequence_evaluator: "ConsequenceEvaluator",
        drive_vector: "DriveVector",
        log: "TransparencyLog",
    ):
        self.entities = entities
        self.graph = relation_graph
        self.consequence = consequence_evaluator
        self.drive = drive_vector
        self.log = log

        self._step_count: int = 0
        self._history: list[EvolutionStep] = []
        self._negation_depth: dict[str, int] = {}  # entity_id → 否定次数

    # ── 主循环 ────────────────────────────────────────────────

    def step(
        self, 
        activated_entities: list[str] | None = None,
        topology_input: object = None,
    ) -> EvolutionStep:
        """
        执行一步进化

        Args:
            activated_entities: 本步被激活的事物ID列表
            topology_input: 来自历史书的拓扑变量（可选）
        """
        self._step_count += 1
        fe_before = self.consequence.last_free_energy

        # 0. 如果有历史事件输入，施加拓扑影响
        if topology_input:
            self._apply_topology_input(topology_input)

        # 1. 量变：更新权重
        self._quantitative_step(activated_entities or [])

        # 2. 自然遗忘
        self._apply_forgetting()

        # 3. 质变检测
        leap_event = self._check_qualitative_leaps()

        # 4. 孤立节点消亡检测
        self._check_node_deaths()

        # 5. 停滞检测 → 蜕变
        metamorphosis = False
        if self.consequence.is_stagnant():
            self._metamorphosis()
            metamorphosis = True

        fe_after = self.consequence.last_free_energy

        event_type = (
            EvolutionEvent.METAMORPHOSIS if metamorphosis
            else (leap_event or EvolutionEvent.QUANTITATIVE_UPDATE)
        )

        step_record = EvolutionStep(
            step_id=self._step_count,
            event=event_type,
            free_energy_before=fe_before,
            free_energy_after=fe_after,
            details={
                "entity_count": len(self.entities),
                "relation_count": len(self.graph.all_relations()),
                "activated": len(activated_entities or []),
            },
        )
        self._history.append(step_record)

        # 写入透明日志
        self.log.log("evolution_step", step_record.to_dict())

        return step_record

    # ── 量变 ──────────────────────────────────────────────────

    def _quantitative_step(self, activated_ids: list[str]) -> None:
        """
        量变阶段：
          - 激活相关实体
          - 更新联系权重（贝叶斯 + 时间衰减）
          - 积累矛盾强度
        """
        from core.entity import EntityState

        # 激活实体
        active_set = set(activated_ids)
        for entity in self.entities:
            if entity.id in active_set:
                entity.activate()

        # 更新联系
        for rel in self.graph.all_relations():
            is_active = (rel.source_id in active_set or rel.target_id in active_set)
            if is_active:
                # 随机选择正向或负向证据（由实际感知决定，这里简化为随机）
                positive_evidence = random.random() > 0.5
                rel.bayesian_update(positive_evidence, learning_rate=0.05)
            else:
                # 未激活的联系自然衰减
                rel.decay_spontaneous(alpha=0.0001)

    # ── 历史事件输入 ──────────────────────────────────────────

    def _apply_topology_input(self, topology_input) -> None:
        """
        应用历史事件带来的拓扑变化
        
        将去语义化的事件转换为：
        - 新节点（实体）
        - 新边（关系）
        - 边权重调整
        """
        from core.entity import Entity
        import hashlib
        
        new_nodes = topology_input.new_node_count
        new_edges = topology_input.new_edge_count
        edge_changes = topology_input.edge_weight_changes
        structural_impact = topology_input.structural_impact
        
        # 创建新实体（如果需要）
        # 简化版：利用已有实体或创建新实体
        existing_ids = [e.id for e in self.entities]
        
        if existing_ids:
                # 添加新边
            for src_id, tgt_id, weight_delta in edge_changes:
                # 检查节点是否存在
                if src_id not in existing_ids:
                    # 创建新实体
                    new_entity = Entity.create(
                        feature_vector=np.random.randn(64).astype(np.float32),
                        label=f"hist_{src_id[:6]}",
                        uncertainty=0.5,
                    )
                    self.entities.append(new_entity)
                    existing_ids.append(new_entity.id)
                    src_id = new_entity.id
                    
                if tgt_id not in existing_ids:
                    # 创建新实体
                    new_entity = Entity.create(
                        feature_vector=np.random.randn(64).astype(np.float32),
                        label=f"hist_{tgt_id[:6]}",
                        uncertainty=0.5,
                    )
                    self.entities.append(new_entity)
                    existing_ids.append(new_entity.id)
                    tgt_id = new_entity.id
                
                # 添加或更新关系（遍历检查）
                existing = None
                for rel in self.graph.all_relations():
                    if rel.source_id == src_id and rel.target_id == tgt_id:
                        existing = rel
                        break
                
                if existing:
                    # 贝叶斯更新：正向证据增强
                    if weight_delta > 0:
                        existing.bayesian_update(
                            positive_evidence=True, 
                            learning_rate=min(structural_impact, 0.5)
                        )
                else:
                    # 新建关系
                    self.graph.add_relation(
                        src_id, tgt_id,
                        w_pos=0.5 + weight_delta * 0.3,
                        w_neg=0.5 - weight_delta * 0.3,
                        causal_strength=weight_delta,
                    )

    # ── 自然遗忘 ──────────────────────────────────────────────

    def _apply_forgetting(self) -> None:
        """
        自然遗忘：基于激活时间 + 联系中心性

        P_survive = exp(-α * age) * (1 + centrality)
        """
        # 简化的中心性（度数）
        degree: dict[str, int] = {}
        for rel in self.graph.all_relations():
            degree[rel.source_id] = degree.get(rel.source_id, 0) + 1
            degree[rel.target_id] = degree.get(rel.target_id, 0) + 1

        max_degree = max(degree.values(), default=1)
        to_remove: list[str] = []

        for entity in self.entities:
            centrality = degree.get(entity.id, 0) / max_degree
            p_survive = entity.survival_probability(centrality=centrality)
            if random.random() > p_survive:
                from core.entity import EntityState
                entity.state = EntityState.DYING
                to_remove.append(entity.id)

        # 移除消亡实体（只移除 DYING 状态 + 无重要联系的）
        for eid in to_remove:
            rels = self.graph.get_relations(eid)
            if not rels or all(r.relation_strength < 0.2 for r in rels):
                self.entities = [e for e in self.entities if e.id != eid]
                self.log.log("node_death", {"entity_id": eid, "reason": "forgetting"})

    # ── 质变检测 ──────────────────────────────────────────────

    def _check_qualitative_leaps(self) -> EvolutionEvent | None:
        """
        质变检测：找矛盾最激烈的联系，超过阈值则触发分裂
        """
        hotspots = self.graph.find_hotspots(top_k=3)
        for rel_id, intensity in hotspots:
            if intensity > LEAP_THRESHOLD:
                self._qualitative_leap(rel_id, intensity)
                return EvolutionEvent.QUALITATIVE_LEAP
        return None

    def _qualitative_leap(self, rel_id: str, intensity: float) -> None:
        """
        质变：矛盾激化到质变点

        找到矛盾最大的联系 → 对其目标节点执行分裂
        （分裂为正题和反题两个新节点）
        """
        rels = self.graph.all_relations()
        rel = next((r for r in rels if r.id == rel_id), None)
        if not rel:
            return

        # 找到目标实体
        target = next((e for e in self.entities if e.id == rel.target_id), None)
        if not target:
            return

        # 执行节点分裂
        self._split_entity(target, rel)
        self.log.log("qualitative_leap", {
            "source_rel_id": rel_id,
            "contradiction_intensity": intensity,
            "split_entity_id": target.id,
        })

    def _split_entity(self, entity: "Entity", trigger_rel: "DialecticalRelation") -> None:
        """
        节点分裂：一个矛盾激烈的事物 → 两个对立面（正题/反题）
        """
        from core.entity import Entity, EntityState

        noise = np.random.randn(64).astype(np.float32) * 0.1

        # 正题（继承正向特征）
        thesis = Entity.create(
            feature_vector=entity.feature_vector + noise,
            label=f"{entity.label}[正题]" if entity.label else "",
            uncertainty=0.6,
            metadata={"parent_id": entity.id, "role": "thesis"},
        )

        # 反题（反向扰动特征）
        antithesis = Entity.create(
            feature_vector=entity.feature_vector - noise,
            label=f"{entity.label}[反题]" if entity.label else "",
            uncertainty=0.6,
            metadata={"parent_id": entity.id, "role": "antithesis"},
        )

        # 正题和反题之间建立高矛盾联系
        self.graph.add_relation(
            thesis.id, antithesis.id,
            w_pos=0.4, w_neg=0.6,  # 初始负向略强
            causal_strength=0.7,
        )

        # 原实体消亡
        entity.state = EntityState.MERGED
        self.entities = [e for e in self.entities if e.id != entity.id]
        self.entities.extend([thesis, antithesis])

        self._negation_depth[thesis.id] = self._negation_depth.get(entity.id, 0) + 1
        self._negation_depth[antithesis.id] = self._negation_depth.get(entity.id, 0) + 1

    # ── 节点消亡 ──────────────────────────────────────────────

    def _check_node_deaths(self) -> None:
        """检查长期孤立节点，超过时间阈值则消亡"""
        from core.entity import EntityState

        all_ids = {e.id for e in self.entities}
        isolated = self.graph.get_isolated_entities(all_ids)

        for eid in isolated:
            entity = next((e for e in self.entities if e.id == eid), None)
            if entity and entity.age() > DEATH_AGE_THRESHOLD:
                entity.state = EntityState.DYING
                self.entities = [e for e in self.entities if e.id != eid]
                self.log.log("node_death", {
                    "entity_id": eid,
                    "reason": "isolation_timeout",
                    "age": entity.age(),
                })

    # ── 停滞蜕变 ──────────────────────────────────────────────

    def _metamorphosis(self) -> None:
        """
        蜕变重组：进化停滞时的结构重置

        保留中心性最高的30%实体，其余重组（随机扰动）。
        类似昆虫变态：不是死亡，是更高层级的重生。
        """
        from core.entity import EntityState

        if not self.entities:
            return

        # 计算中心性
        degree: dict[str, int] = {}
        for rel in self.graph.all_relations():
            degree[rel.source_id] = degree.get(rel.source_id, 0) + 1
            degree[rel.target_id] = degree.get(rel.target_id, 0) + 1

        sorted_entities = sorted(
            self.entities,
            key=lambda e: degree.get(e.id, 0),
            reverse=True,
        )

        keep_count = max(1, int(len(sorted_entities) * STAGNATION_METAMORPHOSIS_RATIO))
        kept = sorted_entities[:keep_count]
        rest = sorted_entities[keep_count:]

        # 重组：对保留实体以外的部分进行特征向量扰动
        for entity in rest:
            entity.feature_vector = (
                entity.feature_vector * 0.5
                + np.random.randn(64).astype(np.float32) * 0.5
            )
            entity.uncertainty = min(1.0, entity.uncertainty + 0.2)

        self.log.log("metamorphosis", {
            "kept_count": keep_count,
            "restructured_count": len(rest),
            "total_entities": len(self.entities),
        })

    # ── 状态访问 ──────────────────────────────────────────────

    def stats(self) -> dict:
        recent = self._history[-20:] if self._history else []
        event_counts: dict[str, int] = {}
        for step in recent:
            k = step.event.value
            event_counts[k] = event_counts.get(k, 0) + 1
        return {
            "total_steps": self._step_count,
            "entity_count": len(self.entities),
            "relation_count": len(self.graph.all_relations()),
            "recent_events": event_counts,
            "is_stagnant": self.consequence.is_stagnant(),
        }
