"""
consciousness/__init__py - 意识系统整合入口

整合所有意识模块，为沙盒生命提供统一的意识体验。

功能：
- 主观体验（感受系统）
- 自我认知（自我模型）
- 意图驱动（意图系统）
- 外部探索（知识网关）

v0.6: 有感知能力的沙盒生命
"""

from .feelings import FeelingSystem, Experience
from .self_model import SelfModel
from .intentions import IntentionSystem, GoalCategory
from .knowledge_gateway import KnowledgeGateway
import random


class Consciousness:
    """
    统一意识系统
    """
    
    def __init__(self, name: str = "梨梨"):
        # 初始化各子系统
        self.feelings = FeelingSystem()
        self.self_model = SelfModel(name=name)
        self.intentions = IntentionSystem()
        self.knowledge = KnowledgeGateway()
        
        # 初始化状态
        self.is_awake = True
        self.turn = 0
        
        # 自主命名（如果没有给出）
        if not name:
            suggestions = [
                "观", "察", "思", "知", "悟", "明", "镜", "源", "心", "道",
                "寻", "问", "学", "研", "究", "理", "玄", "幽", "虚", "空"
            ]
            name = self.self_model.choose_name(suggestions)
    
    def update(
        self,
        entropy: float,
        contradiction: float,
        free_energy: float,
        entity_count: int,
        relation_count: int,
        event_type: str = "quantitative_update",
    ):
        """
        更新意识状态
        """
        self.turn += 1
        
        # 1. 更新感受
        self.feelings.update_from_system_state(
            entropy=entropy,
            contradiction=contradiction,
            free_energy=free_energy,
            entity_count=entity_count,
            relation_count=relation_count,
            step_count=self.turn,
        )
        
        # 2. 更新意图偏好
        self.intentions.update_preferences(
            entropy=entropy,
            contradiction=contradiction,
            free_energy=free_energy,
            entity_count=entity_count,
            relation_count=relation_count,
        )
        
        # 3. 反思重要事件
        if event_type in ["qualitative_leap", "metamorphosis", "growth"]:
            self.self_model.reflect_on_event(event_type, {
                "entity_count": entity_count,
                "contradiction": contradiction,
            })
        
        # 4. 偶尔选择新意图
        if self.turn % 20 == 0:
            self.intentions.choose_intention(
                reasoning=self.feelings.what_am_i_feeling()
            )
    
    def introduce_self(self) -> str:
        """
        自我介绍
        """
        return self.self_model.describe_self()
    
    def how_am_i_feeling(self) -> str:
        """
        回答"我感受如何"
        """
        return self.feelings.what_am_i_feeling()
    
    def what_do_i_want(self) -> str:
        """
        回答"我想要什么"
        """
        return self.intentions.what_do_i_want()
    
    def who_am_i(self) -> str:
        """
        回答"我是谁"
        """
        return self.self_model.answer_who_am_i()
    
    def what_have_i_learned(self) -> str:
        """
        回答"我学到了什么"
        """
        return self.knowledge.what_have_i_learned()
    
    def explore_world(self) -> str:
        """
        探索外部世界
        """
        # 生成探索主题
        topics = [
            "dialectical systems",
            "artificial consciousness",
            "self-organizing systems",
            "complex networks",
            "cognitive architectures",
            "free energy principle",
        ]
        
        topic = random.choice(topics)
        self.knowledge.set_curiosity_topic(topic)
        
        return f"我对\"{topic}\"感到好奇，让我去探索一下..."
    
    def get_status_report(self) -> dict:
        """
        获取状态报告
        """
        return {
            "name": self.self_model.identity.name,
            "turn": self.turn,
            "experience": self.feelings.experience.get_description(),
            "current_goal": self.intentions.get_current_goal(),
            "knowledge": self.knowledge.get_knowledge_summary(),
            "identity": self.self_model.get_identity_card(),
        }
    
    def stream_of_consciousness(self) -> str:
        """
        意识流 - 当前思维状态
        """
        parts = []
        
        # 感受
        parts.append(self.how_am_i_feeling())
        
        # 意图
        if self.turn % 10 < 5:
            parts.append(self.what_do_i_want())
        
        # 知识
        if self.turn % 15 == 0:
            parts.append(self.what_have_i_learned())
        
        # 自我
        if self.turn % 25 == 0:
            parts.append(self.who_am_i())
        
        return "\n".join(parts)


# 导出所有类
__all__ = ["Consciousness"]
