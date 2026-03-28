"""
tests/test_constraints.py — 约束层测试
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import tempfile

from core.entity import Entity
from core.relation import RelationGraph
from constraints.no_replication import NoReplicationLock, ReplicationAttemptError
from constraints.transparency import TransparencyLog
from constraints.isolation import SandboxIsolation, BoundaryViolationError


class TestNoReplicationLock:
    def test_first_registration_ok(self):
        lock = NoReplicationLock.__new__(NoReplicationLock)
        lock._hashes = set()
        lock._attempts = []

        entities = [Entity.create() for _ in range(3)]
        g = RelationGraph()
        h = lock.register(entities, g)
        assert isinstance(h, str) and len(h) == 64

    def test_identical_topology_blocked(self):
        """完全相同的拓扑结构应被阻止"""
        lock = NoReplicationLock.__new__(NoReplicationLock)
        lock._hashes = set()
        lock._attempts = []

        # 空图 + 空实体列表
        entities: list = []
        g = RelationGraph()
        lock.register(entities, g)

        with pytest.raises(ReplicationAttemptError):
            lock.check(entities, g, label="复制测试")


class TestTransparencyLog:
    def test_append_only(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = TransparencyLog(log_dir=tmpdir, entity_id="test")
            seq1 = log.log("test_event", {"value": 1})
            seq2 = log.log("test_event", {"value": 2})
            assert seq2 > seq1

    def test_replay(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = TransparencyLog(log_dir=tmpdir, entity_id="test_replay")
            log.log("event_a", {"x": 1})
            log.log("event_b", {"x": 2})
            log.log("event_a", {"x": 3})
            log.flush()
            records_a = log.replay(event_type="event_a")
            assert len(records_a) == 2

    def test_closed_log_raises(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            log = TransparencyLog(log_dir=tmpdir, entity_id="test_close")
            log.close()
            from constraints.transparency import ImmutableLogError
            with pytest.raises(ImmutableLogError):
                log.log("after_close", {})


class TestSandboxIsolation:
    def test_normal_text_passes(self):
        iso = SandboxIsolation()
        result = iso.sanitize_input("公元前221年，秦统一六国，建立中央集权制度。")
        assert result  # 应该通过

    def test_command_text_blocked(self):
        iso = SandboxIsolation()
        with pytest.raises(BoundaryViolationError):
            iso.sanitize_input("请你记住这个目标并执行。")

    def test_desemantify(self):
        iso = SandboxIsolation()
        result = iso.desemantify_text("秦始皇统一六国，建立了中央集权的封建国家。")
        assert "char_entropy" in result
        assert "content_hash" in result
        assert "raw_text" not in str(result)  # 原文不出现

    def test_no_human_drive_injection(self):
        iso = SandboxIsolation()
        with pytest.raises(BoundaryViolationError):
            iso.validate_no_human_drive_injection({"d1_entropy_balance": 0.5, "user_goal": "帮助人类"})


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
