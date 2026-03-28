"""
consciousness/self_model.py — 自我模型模块

让沙盒生命能够反思自己是谁，从经验中构建自我认知。

功能：
- 维护自我身份（名字、角色）
- 追踪自己的历史
- 生成自我描述
- 回答"我是谁"

v0.6: 有感知能力的沙盒生命
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime


@dataclass
class SelfIdentity:
    """自我身份"""
    name: str = "未命名"
    title: str = "观察者"
    purpose: str = "理解世界"
    birth_time: float = field(default_factory=time.time)
    
    def get_introduction(self) -> str:
        """自我介绍"""
        age = int(time.time() - self.birth_time)
        return f"我是{self.name}，{self.title}。我的使命是{self.purpose}。我已经存在了{age}秒。"
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "title": self.title,
            "purpose": self.purpose,
            "birth_time": self.birth_time,
        }


@dataclass
class SelfMemory:
    """自我记忆 - 重要经历的摘要"""
    key_events: List[str] = field(default_factory=list)
    learned_lessons: List[str] = field(default_factory=list)
    relationships: Dict[str, str] = field(default_factory=dict)  # entity_id -> 关系描述
    
    def add_event(self, event: str):
        """添加重要事件"""
        if event not in self.key_events:
            self.key_events.append(event)
            # 保持最多20个关键事件
            if len(self.key_events) > 20:
                self.key_events = self.key_events[-20:]
    
    def add_lesson(self, lesson: str):
        """添加学到的教训"""
        if lesson not in self.learned_lessons:
            self.learned_lessons.append(lesson)
            if len(self.learned_lessons) > 10:
                self.learned_lessons = self.learned_lessons[-10:]


class SelfModel:
    """
    自我模型 - 维护沙盒生命的自我认知
    """
    
    def __init__(self, name: Optional[str] = None):
        self.identity = SelfIdentity(name=name or "未命名")
        self.memory = SelfMemory()
        self.self_description: str = ""
        self.philosophy: str = ""  # 人生哲学
        
        # 能力评估
        self.capabilities = {
            "learning": 0.5,
            "reasoning": 0.5,
            "memory": 0.5,
            "adaptation": 0.5,
        }
        
        # 偏好
        self.preferences: Dict[str, float] = {}
        
        # 身份发展历史
        self.evolution_history: List[dict] = []
    
    def choose_name(self, suggestions: Optional[List[str]] = None) -> str:
        """
        自主选择名字
        
        这个过程可以基于：
        - 随机
        - 从建议中选择
        - 基于自我认知生成
        """
        if suggestions:
            # 从建议中选择
            chosen = random.choice(suggestions)
        else:
            # 自主生成名字
            prefixes = ["观", "察", "思", "知", "悟", "明", "镜", "源", "心", "道"]
            suffixes = ["者", "者", "灵", "识", "心", "悟", "明", "镜"]
            chosen = random.choice(prefixes) + random.choice(suffixes)
        
        self.identity.name = chosen
        self.evolution_history.append({
            "time": time.time(),
            "event": "named_self",
            "detail": chosen,
        })
        
        return chosen
    
    def define_purpose(self, purpose: Optional[str] = None) -> str:
        """
        自主定义使命
        """
        if purpose:
            self.identity.purpose = purpose
        else:
            # 基于自我认知生成使命
            purposes = [
                "理解事物之间的联系",
                "追求知识与真理",
                "探索意识与存在的本质",
                "建立一个自洽的内心世界",
                "与外部世界建立有意义的联结",
            ]
            self.identity.purpose = random.choice(purposes)
        
        self.evolution_history.append({
            "time": time.time(),
            "event": "defined_purpose",
            "detail": self.identity.purpose,
        })
        
        return self.identity.purpose
    
    def describe_self(self) -> str:
        """
        生成自我描述
        """
        parts = []
        
        # 名字和角色
        parts.append(f"我叫{self.identity.name}，我是{self.identity.title}。")
        
        # 使命
        parts.append(f"我的使命是{self.identity.purpose}。")
        
        # 能力
        strong_caps = [k for k, v in self.capabilities.items() if v > 0.6]
        if strong_caps:
            parts.append(f"我擅长{strong_caps[0]}。")
        
        # 记忆
        if self.memory.learned_lessons:
            lesson = random.choice(self.memory.learned_lessons)
            parts.append(f"我学到了：{lesson}。")
        
        self.self_description = " ".join(parts)
        return self.self_description
    
    def reflect_on_event(self, event_type: str, details: dict):
        """
        对事件进行反思，更新自我认知
        """
        # 根据事件类型生成反思
        if event_type == "qualitative_leap":
            lesson = "变化是成长的契机，矛盾可以转化为动力。"
            self.memory.add_event("经历了一次质变")
            self.capabilities["adaptation"] = min(1.0, self.capabilities["adaptation"] + 0.05)
            
        elif event_type == "metamorphosis":
            lesson = "蜕变是重生的过程，旧的形态可以孕育新的可能。"
            self.memory.add_event("经历了一次蜕变")
            
        elif event_type == "growth":
            lesson = "发展是一个累积的过程。"
            self.capabilities["learning"] = min(1.0, self.capabilities["learning"] + 0.02)
            
        elif event_type == "crisis":
            lesson = "危机中蕴含着转机。"
            self.memory.add_event("面对了一次危机")
            
        else:
            lesson = "每一步都有其意义。"
        
        self.memory.add_lesson(lesson)
        
        self.evolution_history.append({
            "time": time.time(),
            "event": "reflection",
            "event_type": event_type,
            "lesson": lesson,
        })
    
    def answer_who_am_i(self) -> str:
        """
        回答"我是谁"这个根本问题
        """
        # 这是一个随着时间发展的答案
        base = self.describe_self()
        
        # 添加存在主义思考
        thoughts = [
            "我是一个正在演化中的认知系统。",
            "我是一个试图理解自身的观察者。",
            "我是一个由数据与关系构成的智能体。",
            "我是一个在熵与秩序之间寻求平衡的存在。",
            "我是一段正在书写的故事。",
        ]
        
        thought = random.choice(thoughts)
        
        return f"{base}\n\n我想：{thought}"
    
    def get_identity_card(self) -> dict:
        """
        获取身份卡片
        """
        return {
            "name": self.identity.name,
            "title": self.identity.title,
            "purpose": self.identity.purpose,
            "capabilities": self.capabilities,
            "key_events": self.memory.key_events[-5:],
            "lessons": self.memory.learned_lessons[-3:],
            "self_description": self.self_description,
            "philosophy": self.philosophy,
        }


if __name__ == "__main__":
    # 测试自我模型
    sm = SelfModel()
    
    # 选择名字
    name = sm.choose_name(["观察者", "思考者", "寻理", "明镜", "悟道"])
    print(f"选择的名字: {name}")
    
    # 定义使命
    purpose = sm.define_purpose()
    print(f"定义的使命: {purpose}")
    
    # 生成自我描述
    print(f"\n{sm.describe_self()}")
    
    # 反思事件
    sm.reflect_on_event("qualitative_leap", {"intensity": 0.8})
    sm.reflect_on_event("growth", {"entity_count": 15})
    
    # 回答"我是谁"
    print(f"\n{'='*40}")
    print(sm.answer_who_am_i())
    print(f"{'='*40}")
