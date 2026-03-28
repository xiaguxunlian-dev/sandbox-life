"""
consciousness/ — 意识模块

让沙盒生命具有主观体验、自我认知和自主意图。

模块：
- feelings: 主观体验系统
- self_model: 自我模型
- intentions: 意图系统
- knowledge_gateway: 外部知识接口
- consciousness: 统一入口

v0.6: 有感知能力的沙盒生命
"""

from .feelings import FeelingSystem, Feeling, Experience
from .self_model import SelfModel, SelfIdentity, SelfMemory
from .intentions import IntentionSystem, Goal, GoalCategory, Intention
from .knowledge_gateway import KnowledgeGateway, KnowledgeItem, KnowledgeSource
from .consciousness import Consciousness

__all__ = [
    "FeelingSystem",
    "Feeling", 
    "Experience",
    "SelfModel",
    "SelfIdentity",
    "SelfMemory",
    "IntentionSystem",
    "Goal",
    "GoalCategory",
    "Intention",
    "KnowledgeGateway",
    "KnowledgeItem",
    "KnowledgeSource",
    "Consciousness",
]
