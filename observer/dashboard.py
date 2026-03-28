"""
observer/dashboard.py — 外部只读观测仪表盘

提供对沙盒实体内部状态的只读可视化。
不提供任何写入接口。

v0.1: 终端文本仪表盘
v0.5: 将升级为完整图形界面
"""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass


def read_log(log_path: str, event_type: str | None = None, tail_n: int = 50) -> list[dict]:
    """从透明日志读取记录（只读）"""
    path = Path(log_path)
    if not path.exists():
        return []
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
                if event_type is None or record.get("event_type") == event_type:
                    records.append(record)
            except json.JSONDecodeError:
                pass
    return records[-tail_n:]


def print_dashboard(log_path: str):
    """打印文本仪表盘"""
    records = read_log(log_path)
    if not records:
        print("没有找到日志记录。请先运行 main.py")
        return

    # 统计事件类型
    event_counts: dict[str, int] = {}
    last_evolution = None
    last_entropy = None
    last_free_energy = None

    for r in records:
        et = r.get("event_type", "unknown")
        event_counts[et] = event_counts.get(et, 0) + 1
        if et == "evolution_step":
            last_evolution = r.get("data", {})
            last_entropy = last_evolution.get("free_energy_after")
        elif et == "sandbox_init":
            pass

    print("\n" + "=" * 65)
    print("  沙盒生命观测仪表盘 (只读)")
    print("=" * 65)
    print(f"  日志文件: {log_path}")
    print(f"  总记录数: {len(records)}")
    print()

    print("  ── 事件统计 ──")
    for k, v in sorted(event_counts.items(), key=lambda x: -x[1]):
        bar = "█" * min(40, v)
        print(f"  {k:<30s} {v:5d} {bar}")

    if last_evolution:
        print()
        print("  ── 最近进化状态 ──")
        for k, v in last_evolution.items():
            print(f"  {k:<30s} {v}")

    # 质变事件列表
    leap_records = read_log(log_path, event_type="qualitative_leap")
    if leap_records:
        print()
        print(f"  ── 质变事件 ({len(leap_records)} 次) ──")
        for r in leap_records[-5:]:
            d = r.get("data", {})
            ts = time.strftime("%H:%M:%S", time.localtime(r.get("timestamp", 0)))
            print(f"  [{ts}] 矛盾强度={d.get('contradiction_intensity', '?'):.3f} "
                  f"节点={d.get('split_entity_id', '?')[:8]}")

    # 蜕变事件
    meta_records = read_log(log_path, event_type="metamorphosis")
    if meta_records:
        print()
        print(f"  ── 蜕变事件 ({len(meta_records)} 次) ──")
        for r in meta_records[-3:]:
            d = r.get("data", {})
            ts = time.strftime("%H:%M:%S", time.localtime(r.get("timestamp", 0)))
            print(f"  [{ts}] 保留={d.get('kept_count')} 重组={d.get('restructured_count')}")

    print("=" * 65)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="沙盒生命观测仪表盘")
    parser.add_argument(
        "--log", type=str,
        default="logs/sandbox_v01.jsonl",
        help="日志文件路径",
    )
    parser.add_argument(
        "--watch", action="store_true",
        help="持续监控模式（每5秒刷新）",
    )
    args = parser.parse_args()

    if args.watch:
        while True:
            os.system("cls" if sys.platform == "win32" else "clear")
            print_dashboard(args.log)
            print("\n  [监控模式] 5秒后刷新... (Ctrl+C 退出)")
            time.sleep(5)
    else:
        print_dashboard(args.log)
