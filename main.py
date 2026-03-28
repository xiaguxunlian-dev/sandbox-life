"""
main.py — 沙盒生命主入口

最小可运行沙盒（v0.1）

此阶段：
  - 初始化实体池（随机种子）
  - 建立初始联系
  - 运行辩证进化主循环
  - 实时输出状态观测

历史书喂入将在 v0.2 实现。
"""

import random
import sys
import time

import numpy as np

# ── 模块导入 ──────────────────────────────────────────────────
from core.entity import Entity
from core.relation import RelationGraph
from core.consequence import ConsequenceEvaluator
from core.drive import DriveVector
from constraints.no_replication import NoReplicationLock
from constraints.transparency import TransparencyLog
from constraints.isolation import SandboxIsolation
from evolution.dialectical import DialecticalEvolution

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.live import Live
    from rich.layout import Layout
    from rich.text import Text
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def build_initial_state(
    n_entities: int = 12,
    n_initial_relations: int = 18,
    seed: int = 42,
) -> tuple:
    """构建初始沙盒状态"""
    random.seed(seed)
    np.random.seed(seed)

    # 创建初始事物
    entities = [
        Entity.create(
            feature_vector=np.random.randn(64).astype(np.float32),
            label=f"e{i:02d}",
            uncertainty=random.uniform(0.3, 0.7),
        )
        for i in range(n_entities)
    ]

    # 创建辩证联系图（初始权重有意偏离均衡，避免全部立即质变）
    graph = RelationGraph()
    ids = [e.id for e in entities]
    added = set()
    for _ in range(n_initial_relations):
        src, tgt = random.sample(ids, 2)
        pair = frozenset([src, tgt])
        if pair not in added:
            # 初始权重：一方明显高于另一方（0.6~0.9 vs 0.1~0.4）
            w1 = random.uniform(0.6, 0.9)
            w2 = random.uniform(0.1, 0.4)
            graph.add_relation(
                src, tgt,
                w_pos=w1 if random.random() > 0.5 else w2,
                w_neg=w2 if random.random() > 0.5 else w1,
                causal_strength=random.uniform(0.3, 0.8),
            )
            added.add(pair)

    return entities, graph


def run_sandbox(
    steps: int = 200,
    sleep_interval: float = 0.1,
    log_dir: str = "logs",
    seed: int = 42,
):
    """主运行函数"""

    print("=" * 60)
    print("  沙盒生命 v0.1 — 初始化中")
    print("=" * 60)

    # ── 初始化组件 ────────────────────────────────────────────
    entities, graph = build_initial_state(seed=seed)
    consequence = ConsequenceEvaluator()
    drive = DriveVector()
    log = TransparencyLog(log_dir=log_dir, entity_id="sandbox_v01")
    isolation = SandboxIsolation()
    replication_lock = NoReplicationLock()

    # 注册初始状态（反复制锁）
    replication_lock.register(entities, graph)

    # 初始化进化引擎
    engine = DialecticalEvolution(
        entities=entities,
        relation_graph=graph,
        consequence_evaluator=consequence,
        drive_vector=drive,
        log=log,
    )

    log.log("sandbox_init", {
        "version": "0.1.0",
        "seed": seed,
        "initial_entities": len(entities),
        "initial_relations": len(graph.all_relations()),
    })

    print(f"  初始事物数: {len(entities)}")
    print(f"  初始联系数: {len(graph.all_relations())}")
    print(f"  透明日志: {log.log_path}")
    print(f"  开始运行 {steps} 步...\n")

    # ── 主循环 ────────────────────────────────────────────────
    prev_entropy = consequence.compute_system_entropy(entities, graph)

    for step_idx in range(1, steps + 1):
        # 随机激活部分实体
        n_activate = random.randint(1, max(1, len(entities) // 3))
        activated = [e.id for e in random.sample(entities, min(n_activate, len(entities)))]

        # 执行进化步
        step_record = engine.step(activated_entities=activated)

        # 更新实体引用（进化可能增减实体）
        entities = engine.entities

        # 记录结果
        consequence.record(
            entities=entities,
            relation_graph=graph,
            trigger_event=step_record.event.value,
            prev_entropy=prev_entropy,
        )
        prev_entropy = consequence.last_entropy

        # 计算驱动向量
        d1, d2, d3 = drive.compute(entities, graph, consequence)

        # 每10步输出状态
        if step_idx % 10 == 0 or step_record.event.value != "quantitative_update":
            _print_status(step_idx, steps, entities, graph, consequence, d1, d2, d3, step_record)

        time.sleep(sleep_interval)

    # ── 结束 ──────────────────────────────────────────────────
    log.flush()
    log.close()

    print("\n" + "=" * 60)
    print("  沙盒运行完毕")
    print(f"  总进化步数: {engine._step_count}")
    print(f"  最终事物数: {len(entities)}")
    print(f"  最终联系数: {len(graph.all_relations())}")
    print(f"  日志记录数: {log.sequence}")
    print(f"  日志文件: {log.log_path}")
    print("=" * 60)

    return engine, entities, graph, consequence


def _print_status(step, total, entities, graph, consequence, d1, d2, d3, step_record):
    """打印当前状态（简洁文本版）"""
    event = step_record.event.value
    marker = "**" if event != "quantitative_update" else "  "
    graph_stats = graph.stats()
    print(
        f"[{step:4d}/{total}]{marker} "
        f"E:{len(entities):3d} "
        f"R:{len(graph.all_relations()):4d} "
        f"C:{graph_stats.get('avg_contradiction', 0):.2f} "
        f"H:{consequence.last_entropy:.3f} "
        f"F:{consequence.last_free_energy:.3f} "
        f"驱动:({d1:.2f},{d2:.2f},{d3:.2f}) "
        f"事件:{event}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="沙盒生命 v0.1")
    parser.add_argument("--steps", type=int, default=200, help="运行步数")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--sleep", type=float, default=0.05, help="步间隔（秒）")
    parser.add_argument("--log-dir", type=str, default="logs", help="日志目录")
    args = parser.parse_args()

    run_sandbox(
        steps=args.steps,
        sleep_interval=args.sleep,
        log_dir=args.log_dir,
        seed=args.seed,
    )
