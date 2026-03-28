"""
辩证法解析器：将辩证法文本转换为结构化概念流
Dialectics Parser: Transform dialectics text into structured concept streams

核心目标：
- 将辩证法的抽象概念映射为拓扑操作
- 不只是"告诉"实体辩证法，而是让它"体验"辩证逻辑

设计思路：
- 对立统一 → 激活矛盾关系（双极性增强）
- 量变质变 → 触发拓扑跃迁（质变阈值降低）
- 否定之否定 → 激活综合机制（合成新节点）
"""

import re
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional


@dataclass
class DialecticalConcept:
    """
    辩证法概念结构
    """
    id: str
    name: str                    # 概念名称
    concept_type: str            # "对立统一" | "量变质变" | "否定之否定" | "物质" | "意识" | ...
    description: str             # 原始描述
    activation_strength: float   # [0,1] 激活强度
    topology_action: str        # 触发的拓扑操作
    related_concepts: List[str]  # 相关概念
    
    def to_topology_action_params(self) -> Dict:
        """转换为拓扑参数"""
        return {
            "action": self.topology_action,
            "strength": self.activation_strength,
            "contradiction_boost": 0.3 if self.concept_type == "对立统一" else 0.0,
            "leap_threshold_mod": -0.1 if self.concept_type == "量变质变" else 0.0,
            "synthesis_chance": 0.3 if self.concept_type == "否定之否定" else 0.0,
        }


class DialecticsParser:
    """
    辩证法文本解析器
    
    输入：辩证法/马克思主义文本
    输出：DialecticalConcept 列表
    """
    
    # 核心概念定义
    CORE_CONCEPTS = {
        # 对立统一律
        "矛盾": {
            "type": "对立统一",
            "description": "对立统一的双方既相互依存又相互斗争",
            "action": "contradiction_boost",
            "related": ["统一", "斗争", "依存"],
        },
        "对立": {
            "type": "对立统一",
            "description": "双方处于相互排斥、相互斗争的状态",
            "action": "contradiction_boost",
            "related": ["统一", "斗争"],
        },
        "统一": {
            "type": "对立统一",
            "description": "对立双方的相互依存和相互转化",
            "action": "balance_maintain",
            "related": ["矛盾", "依存"],
        },
        "斗争": {
            "type": "对立统一",
            "description": "矛盾双方的相互排斥和相互冲突",
            "action": "contradiction_intensify",
            "related": ["矛盾", "依存"],
        },
        
        # 量变质变律
        "量变": {
            "type": "量变质变",
            "description": "数量的增减、场所的变更",
            "action": "quantitative_accumulation",
            "related": ["质变", "积累"],
        },
        "质变": {
            "type": "量变质变",
            "description": "事物根本性质的改变",
            "action": "qualitative_leap",
            "related": ["量变", "飞跃"],
        },
        "飞跃": {
            "type": "量变质变",
            "description": "突发的、根本性的变化",
            "action": "qualitative_leap",
            "related": ["质变"],
        },
        "积累": {
            "type": "量变质变",
            "description": "量的逐渐增加",
            "action": "quantitative_accumulation",
            "related": ["量变"],
        },
        
        # 否定之否定律
        "否定": {
            "type": "否定之否定",
            "description": "对事物的批判和克服",
            "action": "negation",
            "related": ["扬弃", "综合"],
        },
        "扬弃": {
            "type": "否定之否定",
            "description": "既克服又保留",
            "action": "synthesis",
            "related": ["否定", "综合"],
        },
        "综合": {
            "type": "否定之否定",
            "description": "在更高层次上统一对立双方",
            "action": "synthesis",
            "related": ["否定", "扬弃"],
        },
        "螺旋": {
            "type": "否定之否定",
            "description": "螺旋式上升的发展",
            "action": "spiral_evolution",
            "related": ["上升", "发展"],
        },
        
        # 唯物辩证法基础
        "物质": {
            "type": "物质观",
            "description": "不依赖于意识的客观存在",
            "action": "material_base",
            "related": ["意识", "存在"],
        },
        "意识": {
            "type": "物质观",
            "description": "物质派生的能动反映",
            "action": "consciousness_emergence",
            "related": ["物质", "反映"],
        },
        "实践": {
            "type": "认识论",
            "description": "主观见之于客观的活动",
            "action": "practice_feedback",
            "related": ["认识", "真理"],
        },
        "认识": {
            "type": "认识论",
            "description": "主体对客体的能动反映",
            "action": "cognition_update",
            "related": ["实践", "真理"],
        },
        "真理": {
            "type": "认识论",
            "description": "主观与客观相符合的认识",
            "action": "truth_verification",
            "related": ["认识", "实践"],
        },
        "发展": {
            "type": "总特征",
            "description": "新事物产生、旧事物灭亡",
            "action": "development_promote",
            "related": ["螺旋", "上升"],
        },
        "联系": {
            "type": "总特征",
            "description": "事物之间相互影响相互作用",
            "action": "relation_enhance",
            "related": ["发展", "矛盾"],
        },
    }
    
    def __init__(self):
        self.concepts: List[DialecticalConcept] = []
        self.parsed_count = 0
        
    def parse_text(self, text: str, source: str = "dialectics") -> List[DialecticalConcept]:
        """
        解析辩证法文本
        """
        concepts = []
        
        # 分句
        sentences = self._split_sentences(text)
        
        for i, sentence in enumerate(sentences):
            # 查找概念
            for concept_name, concept_def in self.CORE_CONCEPTS.items():
                if concept_name in sentence:
                    concept = DialecticalConcept(
                        id=f"dial_{source}_{i:04d}_{concept_name}",
                        name=concept_name,
                        concept_type=concept_def["type"],
                        description=concept_def["description"],
                        activation_strength=self._estimate_strength(sentence),
                        topology_action=concept_def["action"],
                        related_concepts=concept_def["related"],
                    )
                    concepts.append(concept)
                    self.concepts.append(concept)
        
        self.parsed_count += len(concepts)
        return concepts
    
    def _split_sentences(self, text: str) -> List[str]:
        """分句"""
        text = re.sub(r'([。！？；])', r'\1|', text)
        sentences = [s.strip() for s in text.split('|') if s.strip()]
        return sentences
    
    def _estimate_strength(self, sentence: str) -> float:
        """
        估计概念的激活强度
        """
        base = 0.5
        
        # 强调词增强
        emphasis_words = ["根本", "核心", "关键", "本质", "最", "极其", "深刻"]
        for word in emphasis_words:
            if word in sentence:
                base += 0.1
        
        # 否定词略微降低
        neg_words = ["不是", "非", "无", "没有"]
        for word in neg_words:
            if word in sentence:
                base -= 0.05
        
        return min(max(base, 0.3), 1.0)
    
    def get_concepts_by_type(self, concept_type: str) -> List[DialecticalConcept]:
        """按类型获取概念"""
        return [c for c in self.concepts if c.concept_type == concept_type]
    
    def get_statistics(self) -> Dict:
        """统计"""
        type_counts = {}
        for c in self.concepts:
            type_counts[c.concept_type] = type_counts.get(c.concept_type, 0) + 1
        return {
            "total_concepts": len(self.concepts),
            "by_type": type_counts,
        }


def load_dialectics_sample() -> List[DialecticalConcept]:
    """
    加载辩证法样本（内置简化版）
    """
    sample_text = """
    唯物辩证法是关于事物普遍联系和永恒发展的科学理论。
    
    矛盾是事物发展的根本动力。矛盾双方既对立又统一，既相互依存又相互斗争。
    矛盾的普遍性是指矛盾存在于一切事物的发展过程中，矛盾贯穿每一事物发展过程的始终。
    矛盾的特殊性是指不同事物的矛盾各有其特点，同一事物的矛盾在不同发展过程和阶段各有不同特点。
    
    量变和质变是事物发展的两种状态。量变是事物数量的增减和场所的变更，
    是一种渐进的、不显著的变化。质变是事物根本性质的改变，是一种突发的、显著的变化。
    量变是质变的必要准备，质变是量变的必然结果。
    
    否定之否定是事物发展的基本规律。任何事物都包含肯定和否定两个方面。
    肯定方面是事物维持其存在的方面，否定方面是促使事物灭亡的方面。
    辩证的否定是事物的自我否定，是既克服又保留，即扬弃。
    否定之否定规律揭示了事物发展是螺旋式上升或波浪式前进的过程。
    
    物质决定意识，意识反作用于物质。存在决定思维，社会存在决定社会意识。
    实践是认识的基础，实践决定认识，实践是认识的来源、动力、目的和检验真理的唯一标准。
    认识是在实践基础上从感性认识上升到理性认识，又从理性认识回到实践的过程。
    真理是客观的、具体的、历史的。真理和谬误在一定条件下可以相互转化。
    
    事物是普遍联系的。联系是指事物之间以及事物内部各要素之间的相互影响、相互制约和相互作用。
    联系具有客观性、普遍性、多样性。发展是新事物的产生和旧事物的灭亡，
    是事物从低级到高级、从简单到复杂的螺旋式上升过程。
    """
    
    parser = DialecticsParser()
    concepts = parser.parse_text(sample_text, source="辩证法样本")
    return concepts


if __name__ == "__main__":
    # 测试
    concepts = load_dialectics_sample()
    
    print(f"解析出 {len(concepts)} 个辩证法概念")
    
    parser = DialecticsParser()
    concepts2 = parser.parse_text("""
    矛盾是事物发展的根本动力。对立统一是辩证法的核心。
    量变引起质变。否定之否定推动事物螺旋上升。
    物质决定意识，实践决定认识。
    """, source="test")
    stats = parser.get_statistics()
    print(f"\n按类型统计:")
    for ctype, count in stats["by_type"].items():
        print(f"  {ctype}: {count}")
    
    print("\n前5个概念:")
    for c in concepts[:5]:
        print(f"  [{c.concept_type}] {c.name}: {c.topology_action}")
