"""
isolation.py — 沙盒边界检查

确保实体不通过任何接口与外部人类直接通信。
所有外部输入经过单向哈希摘要后去语义化。
"""

from __future__ import annotations

import hashlib
import re


class BoundaryViolationError(Exception):
    """沙盒边界违反"""
    pass


class SandboxIsolation:
    """
    沙盒边界守卫

    输入管道：外部文本 → 去语义化 → 拓扑变量（单向）
    输出管道：拓扑状态 → 只读观测（单向）

    禁止：
      - 直接传递自然语言指令给实体
      - 实体直接写入任何外部接口
      - 将人类需求注入需求层
    """

    # 检测自然语言指令的模式（简单启发式）
    COMMAND_PATTERNS = [
        r"请\s*你",
        r"你\s*需要",
        r"帮\s*我",
        r"go\s+do",
        r"please\s+\w+",
        r"you\s+should",
        r"你的目标是",
        r"you\s+must",
    ]

    def __init__(self):
        self._blocked_count: int = 0
        self._pass_count: int = 0

    def sanitize_input(self, raw_text: str) -> str:
        """
        清理输入文本

        检测并拦截直接指令型输入。
        非指令型文本（历史书内容等）通过。
        """
        # 检查是否包含直接指令
        for pattern in self.COMMAND_PATTERNS:
            if re.search(pattern, raw_text, re.IGNORECASE):
                self._blocked_count += 1
                raise BoundaryViolationError(
                    f"输入包含直接指令模式，已拦截。"
                    f"沙盒实体不接受直接命令。"
                )
        self._pass_count += 1
        return raw_text

    def desemantify_text(self, text: str) -> dict:
        """
        去语义化：将文本转换为结构特征（单向）

        输出：
          - 词汇多样性（类型/标记比）
          - 平均句长
          - 文本熵（字符级）
          - 内容哈希（用于去重）
        """
        import math
        import collections

        tokens = re.findall(r'\w+', text.lower())
        if not tokens:
            return {}

        # 词汇多样性
        type_token_ratio = len(set(tokens)) / len(tokens)

        # 平均句长（按标点分句）
        sentences = re.split(r'[。！？.!?]', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        avg_sentence_length = (
            sum(len(s) for s in sentences) / len(sentences) if sentences else 0
        )

        # 字符级熵
        char_freq = collections.Counter(text)
        total_chars = len(text)
        char_entropy = 0.0
        if total_chars > 0:
            for count in char_freq.values():
                p = count / total_chars
                if p > 0:
                    char_entropy -= p * math.log2(p)

        # 内容哈希（用于去重，不保留原文）
        content_hash = hashlib.sha256(text.encode()).hexdigest()[:16]

        return {
            "type_token_ratio": round(type_token_ratio, 4),
            "avg_sentence_length": round(avg_sentence_length, 2),
            "char_entropy": round(char_entropy, 4),
            "token_count": len(tokens),
            "content_hash": content_hash,
            # 原始文本不保留
        }

    def validate_no_human_drive_injection(self, drive_data: dict) -> None:
        """
        验证没有向需求层注入人类偏好

        检查驱动数据是否只包含允许的字段。
        """
        allowed_keys = {"d1_entropy_balance", "d2_completeness", "d3_causal_closure"}
        provided_keys = set(drive_data.keys())
        injected = provided_keys - allowed_keys
        if injected:
            raise BoundaryViolationError(
                f"尝试向需求层注入未授权字段: {injected}。"
                f"需求层只允许三个原生驱动维度。"
            )

    def stats(self) -> dict:
        return {
            "blocked_inputs": self._blocked_count,
            "passed_inputs": self._pass_count,
            "block_rate": (
                round(self._blocked_count / (self._blocked_count + self._pass_count), 4)
                if (self._blocked_count + self._pass_count) > 0
                else 0.0
            ),
        }
