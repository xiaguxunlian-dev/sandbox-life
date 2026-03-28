"""
沙盒生命 - 环境模块
Sandbox Life - Environment Module

包含：
- book_parser: 历史书 → 事件流
- desemantifier: 事件流 → 拓扑变量（去语义化）
- event_sampler: 按好奇心采样事件
"""

from .book_parser import BookParser, HistoricalEvent, load_sample_shiji
from .desemantifier import Desemantifier, TopologyVariable, CuriositySampler
from .event_sampler import EventSampler, SamplerConfig

__all__ = [
    'BookParser',
    'HistoricalEvent', 
    'load_sample_shiji',
    'Desemantifier',
    'TopologyVariable',
    'CuriositySampler',
    'EventSampler',
    'SamplerConfig',
]
