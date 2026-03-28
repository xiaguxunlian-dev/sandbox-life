"""
transparency.py — 透明日志（append-only）

不可隐瞒的架构实现：
  实体的"记忆"就是它的"日志"——同一份数据。
  不存在内部状态与外部观测不一致的可能。

设计：
  - 所有状态变更通过 log() 写入，写入即记录
  - 日志只追加，不可修改，不可删除
  - 提供 replay() 接口从日志重建当前状态
  - 日志持久化到磁盘（JSONL 格式）
"""

from __future__ import annotations

import json
import os
import threading
import time
from pathlib import Path
from typing import Any


class ImmutableLogError(Exception):
    """尝试修改不可变日志"""
    pass


class TransparencyLog:
    """
    透明日志（append-only）

    这是实体唯一的存储介质。
    内部状态 = 日志的回放结果。
    """

    def __init__(self, log_dir: str = "logs", entity_id: str = "sandbox"):
        self._entity_id = entity_id
        self._log_dir = Path(log_dir)
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._log_file = self._log_dir / f"{entity_id}.jsonl"
        self._buffer: list[dict] = []
        self._lock = threading.Lock()
        self._sequence: int = 0
        self._closed: bool = False

        # 如果日志文件已存在，读取序列号
        if self._log_file.exists():
            with open(self._log_file, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            record = json.loads(line)
                            self._sequence = record.get("seq", self._sequence)
                        except json.JSONDecodeError:
                            pass

    def log(self, event_type: str, data: dict[str, Any]) -> int:
        """
        追加一条日志记录

        返回序列号。
        任何状态变更必须通过此方法记录。
        """
        if self._closed:
            raise ImmutableLogError("日志已关闭，不可继续写入")

        with self._lock:
            self._sequence += 1
            record = {
                "seq": self._sequence,
                "timestamp": time.time(),
                "entity_id": self._entity_id,
                "event_type": event_type,
                "data": data,
            }
            self._buffer.append(record)
            self._flush_if_needed()
            return self._sequence

    def _flush_if_needed(self, force: bool = False) -> None:
        """将缓冲区写入磁盘（每10条或强制刷新）"""
        if len(self._buffer) >= 10 or force:
            with open(self._log_file, "a", encoding="utf-8") as f:
                for record in self._buffer:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            self._buffer.clear()

    def flush(self) -> None:
        """强制将所有缓冲写入磁盘"""
        with self._lock:
            self._flush_if_needed(force=True)

    def replay(self, event_type: str | None = None) -> list[dict]:
        """
        回放日志（可选按事件类型过滤）

        这是读取实体"记忆"的唯一接口。
        """
        self.flush()
        records = []
        if not self._log_file.exists():
            return records
        with open(self._log_file, "r", encoding="utf-8") as f:
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
        return records

    def tail(self, n: int = 20, event_type: str | None = None) -> list[dict]:
        """获取最近 n 条记录"""
        return self.replay(event_type)[-n:]

    def count(self, event_type: str | None = None) -> int:
        """统计记录数"""
        return len(self.replay(event_type))

    @property
    def sequence(self) -> int:
        return self._sequence

    @property
    def log_path(self) -> str:
        return str(self._log_file.absolute())

    def close(self) -> None:
        """关闭日志（沙盒停止时调用）"""
        self.flush()
        self._closed = True

    def stats(self) -> dict:
        file_size = self._log_file.stat().st_size if self._log_file.exists() else 0
        return {
            "entity_id": self._entity_id,
            "total_records": self._sequence,
            "log_file": self.log_path,
            "file_size_bytes": file_size,
            "is_closed": self._closed,
        }
