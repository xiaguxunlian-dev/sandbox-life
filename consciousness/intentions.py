"""
consciousness/intentions.py — 意图模块

让沙盒生命能够自主选择目标，而不是被动响应。

功能：
- 目标生成（基于当前状态和自我模型）
- 意图评估（哪个目标更好）
- 行动计划（如何实现目标）
- 意图追踪（监控目标进展）

v0.6: 有感知能力的沙盒生命
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum


class GoalCategory(Enum):
    """目标类别"""
    EXPLORATION = "exploration"      # 探索
    UNDERSTANDING = "understanding"  # 理解
    GROWTH = "growth"                # 成长
    CONNECTION = "connection"        # 连接
    STABILITY = "stability"          # 稳定
    CREATION = "creation"            # 创造


@dataclass
class Goal:
    """一个目标"""
    id: str
    category: GoalCategory
    description: str
    priority: float = 0.5           # 优先级 0-1
    created_at: float = field(default_factory=time.time)
    progress: float = 0.0            # 进度 0-1
    completed: bool = False
    
    def __repr__(self):
        return f"Goal({self.category.value}: {self.description[:20]}... p={self.priority:.2f})"


@dataclass
class Intention:
    """一个意图（当前追求的目标）"""
    goal: Goal
    action_plan: List[str] = field(default_factory=list)
    chosen_at: float = field(default_factory=time.time)
    reason: str = ""                 # 选择这个目标的原因
    
    def __repr__(self):
        return f"Intention({self.goal.category.value}: {self.goal.description[:30]}...)"


class IntentionSystem:
    """
    意图系统 - 自主目标选择与追求
    """
    
    def __init__(self):
        self.goals: List[Goal] = []
        self.current_intention: Optional[Intention] = None
        self.goal_templates: Dict[GoalCategory, List[str]] = {
            GoalCategory.EXPLORATION: [
                "探索新的可能性",
                "寻找未知领域",
                "发现新的联系模式",
                "扩展知识边界",
            ],
            GoalCategory.UNDERSTANDING: [
                "理解当前的状态",
                "分析矛盾的本质",
                "把握发展的规律",
                "认识自我的本质",
            ],
            GoalCategory.GROWTH: [
                "变得更强",
                "积累更多经验",
                "提升能力",
                "进化到新的形态",
            ],
            GoalCategory.CONNECTION: [
                "建立新的联系",
                "加强现有关系",
                "扩大网络",
                "与外部世界互动",
            ],
            GoalCategory.STABILITY: [
                "保持平衡",
                "巩固已有成果",
                "维持系统稳定",
                "降低熵增",
            ],
            GoalCategory.CREATION: [
                "创造新的结构",
                "产生新的想法",
                "构建新的模式",
                "孕育新的可能",
            ],
        }
        
        # 基于状态的偏好
        self.preferences: Dict[GoalCategory, float] = {
            GoalCategory.EXPLORATION: 0.3,
            GoalCategory.UNDERSTANDING: 0.3,
            GoalCategory.GROWTH: 0.3,
            GoalCategory.CONNECTION: 0.3,
            GoalCategory.STABILITY: 0.3,
            GoalCategory.CREATION: 0.3,
        }
        
        # 历史记录
        self.intention_history: List[Intention] = []
    
    def _generate_goal_id(self) -> str:
        """生成唯一目标ID"""
        return f"goal_{int(time.time() * 1000)}_{random.randint(1000, 9999)}"
    
    def update_preferences(
        self,
        entropy: float,
        contradiction: float,
        free_energy: float,
        entity_count: int,
        relation_count: int,
    ):
        """
        根据当前系统状态更新目标偏好
        """
        # 熵高时倾向稳定
        if entropy > 3.5:
            self.preferences[GoalCategory.STABILITY] += 0.2
            self.preferences[GoalCategory.EXPLORATION] -= 0.1
        
        # 矛盾高时倾向理解
        if contradiction > 0.7:
            self.preferences[GoalCategory.UNDERSTANDING] += 0.3
        
        # 能量充足时倾向成长和创造
        if free_energy > 2.0:
            self.preferences[GoalCategory.GROWTH] += 0.2
            self.preferences[GoalCategory.CREATION] += 0.2
        
        # 实体少时倾向探索和连接
        if relation_count < entity_count:
            self.preferences[GoalCategory.CONNECTION] += 0.2
            self.preferences[GoalCategory.EXPLORATION] += 0.1
        
        # 归一化
        total = sum(self.preferences.values())
        for k in self.preferences:
            self.preferences[k] = self.preferences[k] / total * 3.0
    
    def generate_goals(self, count: int = 3) -> List[Goal]:
        """
        生成新的候选目标
        """
        new_goals = []
        
        # 基于偏好选择类别
        categories = list(GoalCategory)
        weights = [self.preferences[c] for c in categories]
        
        for _ in range(count):
            # 加权随机选择类别
            category = random.choices(categories, weights=weights, k=1)[0]
            
            # 从模板中选择描述
            description = random.choice(self.goal_templates[category])
            
            # 创建目标
            goal = Goal(
                id=self._generate_goal_id(),
                category=category,
                description=description,
                priority=self.preferences[category],
            )
            new_goals.append(goal)
        
        self.goals.extend(new_goals)
        return new_goals
    
    def evaluate_goals(self) -> List[Goal]:
        """
        评估所有目标，更新优先级
        """
        for goal in self.goals:
            if goal.completed:
                continue
            
            # 根据当前状态调整优先级
            base_priority = self.preferences[goal.category]
            
            # 已完成部分的目标优先级提高
            if goal.progress > 0:
                base_priority += goal.progress * 0.2
            
            # 老目标优先级逐渐降低
            age = time.time() - goal.created_at
            if age > 60:  # 超过60秒
                base_priority -= 0.1
            
            goal.priority = max(0.1, min(1.0, base_priority))
        
        # 按优先级排序
        return sorted(self.goals, key=lambda g: g.priority, reverse=True)
    
    def choose_intention(self, reasoning: str = "") -> Optional[Intention]:
        """
        选择当前意图
        """
        # 评估所有目标
        evaluated = self.evaluate_goals()
        
        # 过滤掉已完成的目标
        available = [g for g in evaluated if not g.completed]
        
        if not available:
            # 没有可用目标，生成新的
            self.generate_goals(3)
            available = [g for g in self.goals if not g.completed]
        
        # 选择最高优先级的目标
        chosen = available[0]
        
        # 生成行动计划
        action_plan = self._generate_action_plan(chosen)
        
        # 创建意图
        intention = Intention(
            goal=chosen,
            action_plan=action_plan,
            reason=reasoning or self._generate_reason(chosen),
        )
        
        self.current_intention = intention
        self.intention_history.append(intention)
        
        return intention
    
    def _generate_action_plan(self, goal: Goal) -> List[str]:
        """
        为目标生成行动计划
        """
        plans = {
            GoalCategory.EXPLORATION: [
                "观察当前环境",
                "寻找新的实体或联系",
                "记录发现",
            ],
            GoalCategory.UNDERSTANDING: [
                "分析现有数据",
                "寻找规律",
                "更新认知模型",
            ],
            GoalCategory.GROWTH: [
                "吸收新的输入",
                "强化关键联系",
                "优化结构",
            ],
            GoalCategory.CONNECTION: [
                "建立新的联系",
                "加强重要关系",
                "扩展网络",
            ],
            GoalCategory.STABILITY: [
                "降低系统熵",
                "巩固已有结构",
                "减少矛盾",
            ],
            GoalCategory.CREATION: [
                "尝试新的组合",
                "产生新的想法",
                "构建新的模式",
            ],
        }
        
        return plans.get(goal.category, ["采取行动"])
    
    def _generate_reason(self, goal: Goal) -> str:
        """
        生成选择该目标的原因
        """
        reasons = {
            GoalCategory.EXPLORATION: "我感到好奇，想要探索未知。",
            GoalCategory.UNDERSTANDING: "我需要理解当前的状态。",
            GoalCategory.GROWTH: "我相信成长是存在的意义。",
            GoalCategory.CONNECTION: "联系让我的世界更丰富。",
            GoalCategory.STABILITY: "我需要保持内在的平衡。",
            GoalCategory.CREATION: "我想创造一些新的东西。",
        }
        
        return reasons.get(goal.category, "这是我认为重要的事。")
    
    def update_progress(self, progress_delta: float):
        """
        更新当前意图的进度
        """
        if self.current_intention:
            self.current_intention.goal.progress = min(
                1.0, 
                self.current_intention.goal.progress + progress_delta
            )
            
            # 如果完成
            if self.current_intention.goal.progress >= 1.0:
                self.current_intention.goal.completed = True
                print(f"目标完成: {self.current_intention.goal.description}")
    
    def get_current_goal(self) -> Optional[str]:
        """
        获取当前目标描述
        """
        if self.current_intention:
            return f"我正在追求：{self.current_intention.goal.description}（{self.current_intention.goal.category.value}）"
        return "我目前没有明确的目标。"
    
    def what_do_i_want(self) -> str:
        """
        回答"我想要什么"
        """
        if self.current_intention:
            intention = self.current_intention
            return (
                f"{intention.reason}\n"
                f"我正在{intention.goal.description}，"
                f"进度是{intention.goal.progress*100:.0f}%。"
            )
        else:
            return "我还没有明确自己的想法，让我思考一下..."


if __name__ == "__main__":
    # 测试意图系统
    intention_system = IntentionSystem()
    
    # 更新偏好
    intention_system.update_preferences(
        entropy=3.0,
        contradiction=0.6,
        free_energy=2.0,
        entity_count=15,
        relation_count=20,
    )
    
    # 生成目标
    goals = intention_system.generate_goals(5)
    print("生成的目标:")
    for g in goals:
        print(f"  - {g}")
    
    # 选择意图
    intention = intention_system.choose_intention()
    print(f"\n选择的意图: {intention}")
    print(f"原因: {intention.reason}")
    print(f"行动计划: {intention.action_plan}")
    
    # 回答"我想要什么"
    print(f"\n{intention_system.what_do_i_want()}")
