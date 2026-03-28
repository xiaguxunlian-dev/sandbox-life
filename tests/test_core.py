"""
tests/test_core.py — 核心模块测试
"""
import math
import random
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import numpy as np
import pytest

from core.entity import Entity, EntityState
from core.relation import DialecticalRelation, RelationGraph, RelationType, NegationState
from core.consequence import ConsequenceEvaluator
from core.drive import DriveVector


# ── Entity 测试 ───────────────────────────────────────────────

class TestEntity:
    def test_create(self):
        e = Entity.create(label="测试")
        assert e.label == "测试"
        assert 0.0 <= e.uncertainty <= 1.0
        assert e.state == EntityState.ACTIVE
        assert e.activation_count == 0

    def test_activate(self):
        e = Entity.create()
        e.activate()
        assert e.activation_count == 1

    def test_similarity(self):
        fv = np.ones(64, dtype=np.float32)
        e1 = Entity.create(feature_vector=fv.copy())
        e2 = Entity.create(feature_vector=fv.copy())
        assert abs(e1.similarity(e2) - 1.0) < 1e-5

    def test_structural_hash_stable(self):
        e = Entity.create()
        h1 = e.structural_hash
        h2 = e.structural_hash
        assert h1 == h2

    def test_survival_probability_decreases_with_age(self):
        e = Entity.create()
        import time
        p1 = e.survival_probability(centrality=0.0, alpha=0.1)
        time.sleep(0.05)
        p2 = e.survival_probability(centrality=0.0, alpha=0.1)
        assert p2 <= p1


# ── DialecticalRelation 测试 ──────────────────────────────────

class TestDialecticalRelation:
    def test_contradiction_intensity_balanced(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=0.5, w_neg=0.5)
        assert abs(rel.contradiction_intensity - 1.0) < 1e-5

    def test_contradiction_intensity_unbalanced(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=1.0, w_neg=0.0)
        assert abs(rel.contradiction_intensity - 0.0) < 1e-5

    def test_dominant_pole(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=0.8, w_neg=0.2)
        assert rel.dominant_pole == "positive"

    def test_negate(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=0.8, w_neg=0.2)
        rel.negate()
        assert rel.negation_state == NegationState.ANTITHESIS
        assert rel.dominant_pole == "negative"  # 反转后负向主导

    def test_synthesize(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=0.8, w_neg=0.2)
        rel.negate()
        rel.synthesize()
        assert rel.negation_state == NegationState.SYNTHESIS

    def test_bayesian_update(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=0.5, w_neg=0.5)
        old_pos = rel.w_pos
        rel.bayesian_update(observed_positive=True, learning_rate=0.2)
        assert rel.w_pos > old_pos * 0.9  # 正向权重增加（考虑衰减）

    def test_relation_type_contradictory(self):
        rel = DialecticalRelation(source_id="a", target_id="b", w_pos=0.5, w_neg=0.5)
        assert rel.relation_type == RelationType.CONTRADICTORY


# ── RelationGraph 测试 ────────────────────────────────────────

class TestRelationGraph:
    def test_add_and_get(self):
        g = RelationGraph()
        rel = g.add_relation("e1", "e2")
        rels = g.get_relations("e1")
        assert len(rels) == 1
        assert rels[0].source_id == "e1"

    def test_find_hotspots(self):
        g = RelationGraph()
        g.add_relation("e1", "e2", w_pos=0.5, w_neg=0.5)  # 高矛盾
        g.add_relation("e3", "e4", w_pos=0.9, w_neg=0.1)  # 低矛盾
        hotspots = g.find_hotspots(top_k=1)
        assert len(hotspots) == 1

    def test_get_isolated(self):
        g = RelationGraph()
        g.add_relation("e1", "e2")
        all_ids = {"e1", "e2", "e3"}
        isolated = g.get_isolated_entities(all_ids)
        assert "e3" in isolated
        assert "e1" not in isolated


# ── ConsequenceEvaluator 测试 ─────────────────────────────────

class TestConsequenceEvaluator:
    def test_entity_entropy(self):
        entities = [
            Entity.create(uncertainty=0.5),
            Entity.create(uncertainty=0.5),
        ]
        h = ConsequenceEvaluator.compute_entity_entropy(entities)
        assert h > 0.0

    def test_free_energy_deviation(self):
        evaluator = ConsequenceEvaluator()
        entities = [Entity.create(uncertainty=0.9) for _ in range(10)]
        g = RelationGraph()
        fe = evaluator.compute_free_energy(entities, g)
        assert fe >= 0.0

    def test_record(self):
        evaluator = ConsequenceEvaluator()
        entities = [Entity.create() for _ in range(5)]
        g = RelationGraph()
        record = evaluator.record(entities, g, trigger_event="test")
        assert record is not None
        assert len(evaluator._history) == 1


# ── DriveVector 测试 ──────────────────────────────────────────

class TestDriveVector:
    def test_drive_immutable_constants(self):
        """需求常量不可修改"""
        from core.drive import DRIVE_CONSTANTS
        with pytest.raises(Exception):
            DRIVE_CONSTANTS.entropy_target = 999.0  # 应该失败

    def test_compute_returns_valid(self):
        drive = DriveVector()
        evaluator = ConsequenceEvaluator()
        entities = [Entity.create() for _ in range(5)]
        g = RelationGraph()
        d1, d2, d3 = drive.compute(entities, g, evaluator)
        assert 0.0 <= d1 <= 1.0
        assert 0.0 <= d2 <= 1.0
        assert 0.0 <= d3 <= 1.0

    def test_completeness_drive_increases_with_isolation(self):
        drive = DriveVector()
        evaluator = ConsequenceEvaluator()
        g = RelationGraph()
        # 没有联系的实体 → d2 高
        entities_isolated = [Entity.create() for _ in range(10)]
        _, d2_isolated, _ = drive.compute(entities_isolated, g, evaluator)
        # 全部有联系 → d2 低
        g2 = RelationGraph()
        entities_connected = [Entity.create() for _ in range(4)]
        ids = [e.id for e in entities_connected]
        g2.add_relation(ids[0], ids[1])
        g2.add_relation(ids[1], ids[2])
        g2.add_relation(ids[2], ids[3])
        g2.add_relation(ids[3], ids[0])
        _, d2_connected, _ = drive.compute(entities_connected, g2, evaluator)
        assert d2_isolated >= d2_connected


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
