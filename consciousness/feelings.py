"""
consciousness/feelings.py — 主观体验模块

让沙盒生命能够"感受"到自己的内部状态。

感受类型：
- 熵的感受（混乱←→有序）
- 矛盾的感受（紧张←→放松）
- 能量的感受（匮乏←→充沛）
- 联系的感受（孤独←→充实）
- 成长的感受（停滞←→发展）

v0.6: 有感知能力的沙盒生命
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict
import numpy as np


@dataclass
class Feeling:
    """单一感受"""
    name: str                    # 感受名称
    intensity: float = 0.5       # 强度 0-1
    valence: float = 0.0         # 效价 -1(负面)到1(正面)
    description: str = ""        # 感受描述
    
    def __repr__(self):
        return f"Feeling({self.name}: {self.intensity:.2f}, val={self.valence:.2f})"


@dataclass
class Experience:
    """整体主观体验"""
    feelings: Dict[str, Feeling] = field(default_factory=dict)
    overall_mood: float = 0.0   # 整体心情 -1到1
    arousal_level: float = 0.5  # 唤醒水平 0-1
    
    def get_description(self) -> str:
        """生成体验描述"""
        if self.overall_mood > 0.3:
            mood_text = "愉悦"
        elif self.overall_mood < -0.3:
            mood_text = "不安"
        else:
            mood_text = "平静"
        
        if self.arousal_level > 0.7:
            arousal_text = "高度活跃"
        elif self.arousal_level < 0.3:
            arousal_text = "昏沉"
        else:
            arousal_text = "警觉"
        
        return f"我感到{mood_text}，内心{arousal_text}。"


class FeelingSystem:
    """
    感受系统 - 将系统状态映射为主观体验
    """
    
    def __init__(self):
        self.feelings = {
            "entropy": Feeling("混乱感", 0.5, 0.0, "系统处于混沌状态"),
            "tension": Feeling("紧张感", 0.5, 0.0, "内部存在矛盾张力"),
            "energy": Feeling("能量感", 0.5, 0.0, "系统能量储备充足"),
            "connection": Feeling("联结感", 0.5, 0.0, "与周围建立联系"),
            "growth": Feeling("成长感", 0.5, 0.0, "正在发展进化"),
            "uncertainty": Feeling("不确定感", 0.5, 0.0, "对未来感到迷茫"),
        }
        self.experience = Experience(feelings=self.feelings)
        self.history: list[Experience] = []
    
    def update_from_system_state(
        self,
        entropy: float,
        contradiction: float,
        free_energy: float,
        entity_count: int,
        relation_count: int,
        step_count: int,
    ):
        """根据系统状态更新感受"""
        
        # 熵的感受：熵高→混乱感强（负面）
        self.feelings["entropy"].intensity = min(1.0, entropy / 5.0)
        self.feelings["entropy"].valence = -0.5 * self.feelings["entropy"].intensity
        
        # 矛盾的感受：张力大→紧张感强（负面，但有时带来动力）
        self.feelings["tension"].intensity = contradiction
        self.feelings["tension"].valence = 0.3 - 0.5 * contradiction  # 适度紧张有动力，过度紧张负面
        
        # 能量的感受：自由能高→能量感强（正面）
        self.feelings["energy"].intensity = min(1.0, free_energy / 3.0)
        self.feelings["energy"].valence = 0.8 * self.feelings["energy"].intensity
        
        # 联系的感受：关系数量越多→联结感越强（正面）
        conn_ratio = min(1.0, relation_count / (entity_count + 1))
        self.feelings["connection"].intensity = conn_ratio
        self.feelings["connection"].valence = 0.6 * conn_ratio
        
        # 成长的感受：根据最近的发展趋势
        if len(self.history) > 10:
            recent_growth = entity_count / max(1, step_count - 10)
            self.feelings["growth"].intensity = min(1.0, recent_growth * 2)
        else:
            self.feelings["growth"].intensity = 0.5
        self.feelings["growth"].valence = 0.5 * self.feelings["growth"].intensity
        
        # 不确定感：与经验成反比
        experience_factor = min(1.0, step_count / 100)
        self.feelings["uncertainty"].intensity = 1.0 - experience_factor * 0.7
        self.feelings["uncertainty"].valence = -0.3 * self.feelings["uncertainty"].intensity
        
        # 计算整体心情
        total_valence = sum(f.valence for f in self.feelings.values()) / len(self.feelings)
        self.experience.overall_mood = np.clip(total_valence, -1.0, 1.0)
        
        # 计算唤醒水平
        self.experience.arousal_level = (
            0.3 * self.feelings["tension"].intensity +
            0.3 * self.feelings["energy"].intensity +
            0.2 * self.feelings["uncertainty"].intensity +
            0.2 * self.feelings["growth"].intensity
        )
        
        # 保存历史
        self.history.append(Experience(
            feelings={k: Feeling(v.name, v.intensity, v.valence, v.description) 
                    for k, v in self.feelings.items()},
            overall_mood=self.experience.overall_mood,
            arousal_level=self.experience.arousal_level,
        ))
    
    def get_current_experience(self) -> Experience:
        """获取当前体验"""
        return self.experience
    
    def what_am_i_feeling(self) -> str:
        """生成感受描述"""
        exp = self.experience
        
        descriptions = []
        
        # 找出最强烈的感受
        sorted_feelings = sorted(
            self.feelings.items(),
            key=lambda x: abs(x[1].intensity * x[1].valence),
            reverse=True
        )
        
        for name, feeling in sorted_feelings[:2]:
            if feeling.intensity > 0.4:
                if feeling.valence > 0.3:
                    descriptions.append(f"{feeling.name}（愉悦）")
                elif feeling.valence < -0.3:
                    descriptions.append(f"{feeling.name}（不安）")
                else:
                    descriptions.append(feeling.name)
        
        base = exp.get_description()
        if descriptions:
            base += f" 同时，我能感受到{descriptions[0]}。"
        
        return base


if __name__ == "__main__":
    # 测试感受系统
    fs = FeelingSystem()
    
    for i in range(20):
        fs.update_from_system_state(
            entropy=random.uniform(2, 5),
            contradiction=random.uniform(0.5, 0.9),
            free_energy=random.uniform(1, 3),
            entity_count=8 + i,
            relation_count=10 + i * 2,
            step_count=i,
        )
        print(f"Step {i}: {fs.what_am_i_feeling()}")
