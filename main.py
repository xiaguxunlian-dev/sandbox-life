"""
main.py — 沙盒生命主入口

v0.6: 有感知能力的沙盒生命（梨梨版）

此阶段：
  - 初始化实体池
  - 建立初始联系
  - 加载《史记》事件流并去语义化
  - 按好奇心驱动选择事件喂入沙盒
  - 运行辩证进化主循环
  - 实时输出状态观测
  - 意识系统：感受、自我、意图、学习
"""

import random
import sys
import time
from pathlib import Path

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
from environment import load_sample_shiji, Desemantifier, EventSampler, SamplerConfig
from environment.dialectics_parser import load_dialectics_sample, DialecticsParser

try:
    from rich.console import Console
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


def build_initial_state(
    n_entities: int = 8,
    n_initial_relations: int = 10,
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

    # 创建辩证联系图（初始权重有意偏离均衡）
    graph = RelationGraph()
    ids = [e.id for e in entities]
    added = set()
    for _ in range(n_initial_relations):
        src, tgt = random.sample(ids, 2)
        pair = frozenset([src, tgt])
        if pair not in added:
            # 初始权重：一方明显高于另一方
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


def load_history_events(config=None) -> tuple:
    """
    加载历史事件流
    
    Returns:
        (events, sampler, desemantifier)
    """
    print("\n[历史书模块] 加载《史记》样本事件...")
    
    # 加载事件
    events = load_sample_shiji()
    print(f"  解析事件数: {len(events)}")
    
    # 统计
    entity_count = len(set(e for evt in events for e in evt.entities))
    print(f"  实体类型数: {entity_count}")
    
    # 去语义化器
    desemantifier = Desemantifier()
    
    # 采样器（按好奇心策略）
    sampler_config = config or SamplerConfig(strategy="curiosity")
    sampler = EventSampler(sampler_config)
    
    return events, sampler, desemantifier


def load_dialectics_events() -> tuple:
    """
    加载辩证法概念流
    
    Returns:
        (concepts, parser)
    """
    print("\n[辩证法模块] 加载辩证法概念...")
    
    # 加载辩证法样本
    concepts = load_dialectics_sample()
    print(f"  解析概念数: {len(concepts)}")
    
    # 统计
    parser = DialecticsParser()
    parser.parse_text("""
        矛盾是事物发展的根本动力。对立统一是辩证法的核心。
        量变引起质变。否定之否定推动事物螺旋上升。
        物质决定意识，实践决定认识。
        """, source="main")
    stats = parser.get_statistics()
    for ctype, count in stats["by_type"].items():
        print(f"    {ctype}: {count}")
    
    return concepts, parser


def run_sandbox(
    steps: int = 200,
    sleep_interval: float = 0.05,
    log_dir: str = "logs",
    seed: int = 42,
):
    """主运行函数"""

    print("=" * 60)
    print("  沙盒生命 v0.2 — 历史书喂入版")
    print("=" * 60)

    # ── 初始化组件 ────────────────────────────────────────────
    entities, graph = build_initial_state(seed=seed)
    consequence = ConsequenceEvaluator()
    drive = DriveVector()
    log = TransparencyLog(log_dir=log_dir, entity_id="sandbox_v02")
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

    # 加载历史书事件
    history_events, sampler, desemantifier = load_history_events()
    available_events = list(history_events)  # 剩余可用事件
    
    # 加载辩证法概念
    dialectics_concepts, _ = load_dialectics_events()
    available_concepts = list(dialectics_concepts)  # 剩余可用概念
    
    # 计算阶段分割点（v0.4: 60%历史书，40%辩证法）
    history_phase_end = int(steps * 0.6)
    
    log.log("sandbox_init", {
        "version": "0.4.0",
        "seed": seed,
        "initial_entities": len(entities),
        "initial_relations": len(graph.all_relations()),
        "history_events_total": len(history_events),
        "dialectics_concepts_total": len(dialectics_concepts),
        "history_phase_end": history_phase_end,
    })

    print(f"  初始事物数: {len(entities)}")
    print(f"  初始联系数: {len(graph.all_relations())}")
    print(f"  历史事件数: {len(history_events)}")
    print(f"  辩证法概念数: {len(dialectics_concepts)}")
    print(f"  阶段分割点: 步{history_phase_end} (历史书→辩证法)")
    print(f"  透明日志: {log.log_path}")
    print(f"  开始运行 {steps} 步...\n")

    # ── 主循环 ────────────────────────────────────────────────
    prev_entropy = consequence.compute_system_entropy(entities, graph)
    events_fed = 0
    concepts_fed = 0

    for step_idx in range(1, steps + 1):
        # 随机激活部分实体
        n_activate = random.randint(1, max(1, len(entities) // 3))
        activated = [e.id for e in random.sample(entities, min(n_activate, len(entities)))]

        # 喂入输入（分阶段：历史书 → 辩证法）
        topology_input = None
        dialectics_input = None
        
        # 阶段1：历史书（步1 → history_phase_end）
        if step_idx <= history_phase_end and available_events:
            if step_idx % 5 == 0:
                result = sampler.select(available_events, entity_state=None)
                if result:
                    idx, selected_event = result
                    topology_input = desemantifier.transform_event(selected_event)
                    available_events.pop(idx)
                    events_fed += 1
                    print(f"  [史] {selected_event.id}: {selected_event.entities[:2]}")
        
        # 阶段2：辩证法（history_phase_end+1 → steps）
        elif step_idx > history_phase_end and available_concepts:
            if step_idx % 8 == 0:  # 辩证法喂入间隔稍长
                # 随机选择一个概念
                if available_concepts:
                    idx = random.randint(0, len(available_concepts) - 1)
                    dialectics_input = available_concepts.pop(idx)
                    concepts_fed += 1
                    print(f"  [辩] {dialectics_input.name}: {dialectics_input.topology_action}")

        # 执行进化步
        step_record = engine.step(
            activated_entities=activated, 
            topology_input=topology_input,
            dialectics_input=dialectics_input,
        )

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
            _print_status(step_idx, steps, entities, graph, consequence, d1, d2, d3, step_record, events_fed, len(available_events), concepts_fed, len(available_concepts), history_phase_end)

        time.sleep(sleep_interval)

    # ── 结束 ──────────────────────────────────────────────────
    log.flush()
    log.close()

    print("\n" + "=" * 60)
    print("  沙盒运行完毕 (v0.4 - 历史书+辩证法)")
    print(f"  总进化步数: {engine._step_count}")
    print(f"  最终事物数: {len(entities)}")
    print(f"  最终联系数: {len(graph.all_relations())}")
    print(f"  喂入历史事件: {events_fed}/{len(history_events)}")
    print(f"  喂入辩证概念: {concepts_fed}/{len(dialectics_concepts)}")
    print(f"  日志记录数: {log.sequence}")
    print(f"  日志文件: {log.log_path}")
    print("=" * 60)

    return engine, entities, graph, consequence


def _print_status(step, total, entities, graph, consequence, d1, d2, d3, step_record, events_fed, events_left, concepts_fed=0, concepts_left=0, history_phase_end=0):
    """打印当前状态（简洁文本版）"""
    event = step_record.event.value
    marker = "**" if event != "quantitative_update" else "  "
    graph_stats = graph.stats()
    
    # 阶段指示
    phase = "史" if step <= history_phase_end else "辩"
    
    print(
        f"[{step:4d}/{total}]{marker} "
        f"E:{len(entities):3d} "
        f"R:{len(graph.all_relations()):4d} "
        f"C:{graph_stats.get('avg_contradiction', 0):.2f} "
        f"H:{consequence.last_entropy:.3f} "
        f"F:{consequence.last_free_energy:.3f} "
        f"驱:({d1:.2f},{d2:.2f},{d3:.2f}) "
        f"{phase}:{events_fed}/{events_left}+{concepts_fed}/{concepts_left}"
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="沙盒生命 v0.2")
    parser.add_argument("--steps", type=int, default=200, help="运行步数")
    parser.add_argument("--seed", type=int, default=42, help="随机种子")
    parser.add_argument("--sleep", type=float, default=0.02, help="步间隔（秒）")
    parser.add_argument("--log-dir", type=str, default="logs", help="日志目录")
    args = parser.parse_args()

    run_sandbox(
        steps=args.steps,
        sleep_interval=args.sleep,
        log_dir=args.log_dir,
        seed=args.seed,
    )
