"""
去语义化器：将历史事件转换为拓扑变量
Desemantifier: Transform historical events into topology variables

核心思想：
- 实体感知不到"秦始皇"这个词
- 它只能感知到：一个高连接度节点出现、多个节点消失、新的强联系建立
- 这个模块负责这种转换
"""

import hashlib
import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class TopologyVariable:
    """
    实体可感知的拓扑变量（去语义化后）
    """
    # 节点变化
    new_node_count: int          # 新出现的实体数量
    removed_node_count: int      # 消失的实体数量（本研究暂不处理）
    node_degree_delta: List[int] # 各节点度数变化 [delta_degree, ...]
    
    # 边变化
    new_edge_count: int          # 新建立的关系数量
    edge_weight_changes: List[Tuple[str, str, float]]  # (src_id, tgt_id, weight_delta)
    
    # 结构影响
    structural_impact: float     # [0,1] 结构变化程度
    causal_depth: int            # 因果链深度
    hub_emergence: bool          # 是否出现高连接度中心节点
    
    # 元数据
    event_timestamp: Optional[int]
    event_id: str


class Desemantifier:
    """
    历史事件 → 拓扑变量
    
    这个类的设计基于一个关键假设：
    实体没有"语言"能力，它只能通过拓扑结构的变化来感知世界
    """
    
    def __init__(self):
        # 记录已知实体，生成稳定的哈希ID
        self.entity_id_map: Dict[str, str] = {}
        self.next_entity_seq: int = 0
        
        # 统计
        self.total_processed_events = 0
        
    def _get_entity_id(self, entity_name: str) -> str:
        """
        为实体生成稳定的哈希ID
        这样同一个实体在不同事件中会被识别为同一节点
        """
        if entity_name not in self.entity_id_map:
            # 使用确定性哈希，避免随机ID
            hash_input = f"{entity_name}_{self.next_entity_seq}"
            self.entity_id_map[entity_name] = hashlib.sha256(
                hash_input.encode('utf-8')
            ).hexdigest()[:12]
            self.next_entity_seq += 1
            
        return self.entity_id_map[entity_name]
    
    def transform_event(self, event) -> TopologyVariable:
        """
        将历史事件转换为拓扑变量
        """
        self.total_processed_events += 1
        
        # 转换实体名称为节点ID
        entity_ids = [self._get_entity_id(e) for e in event.entities]
        
        # 转换关系为边
        edge_changes = []
        new_edges = []
        
        for subj, rel_type, obj in event.relations:
            src_id = self._get_entity_id(subj)
            tgt_id = self._get_entity_id(obj)
            
            # 根据关系类型估计权重变化
            # 战争/杀害 = 高强度负面
            # 继承/禅让 = 中等强度
            # 婚姻 = 低强度
            # 建立/废除 = 结构重组
            
            rel_strength = self._estimate_relation_strength(rel_type)
            edge_changes.append((src_id, tgt_id, rel_strength))
            new_edges.append((src_id, tgt_id))
        
        # 检测是否出现中心节点（hub）
        # 简化判断：实体数量 > 3 且关系数量 > 2
        hub_emergence = len(entity_ids) >= 3 and len(new_edges) >= 2
        
        return TopologyVariable(
            new_node_count=len(entity_ids),
            removed_node_count=0,  # 本简化版不处理节点消失
            node_degree_delta=[len(new_edges)] * len(entity_ids),  # 简化：所有新节点都有边
            new_edge_count=len(new_edges),
            edge_weight_changes=edge_changes,
            structural_impact=event.entropy_delta,
            causal_depth=event.causal_chain_depth,
            hub_emergence=hub_emergence,
            event_timestamp=event.timestamp,
            event_id=event.id,
        )
    
    def _estimate_relation_strength(self, rel_type: str) -> float:
        """
        根据关系类型估计权重强度
        """
        strength_map = {
            # 高强度（结构性剧变）
            '战争': 0.9,
            '灭亡': 0.95,
            '杀害': 0.9,
            '废立': 0.85,
            '废除': 0.8,
            
            # 中等强度（权力更迭）
            '继承': 0.6,
            '禅让': 0.5,
            '册封': 0.6,
            '任命': 0.5,
            '朝贡': 0.5,
            
            # 低强度（日常互动）
            '婚姻': 0.3,
            '生育': 0.2,
            '建立': 0.7,
            '实行': 0.4,
            '颁布': 0.4,
            
            # 身份关系
            '是': 0.1,  # 判断句，弱关系
        }
        
        return strength_map.get(rel_type, 0.3)
    
    def transform_batch(self, events: List) -> List[TopologyVariable]:
        """
        批量转换事件
        """
        return [self.transform_event(e) for e in events]
    
    def get_entity_statistics(self) -> Dict:
        """
        获取实体统计
        """
        return {
            'total_unique_entities': len(self.entity_id_map),
            'total_events_processed': self.total_processed_events,
        }


class CuriositySampler:
    """
    好奇心驱动的采样器
    
    选择"最出乎意料"的事件喂入实体
    基于KL散度：选择那些与当前预测差异最大的事件
    """
    
    def __init__(self):
        # 记录历史输入，用于计算"预期"
        self.event_history: List[TopologyVariable] = []
        
        # 统计各类型的输入频率
        self.type_frequency: Dict[str, int] = {}
        
    def select_next_event(
        self, 
        candidate_events: List, 
        entity_state
    ) -> Optional[Tuple[int, any]]:
        """
        选择下一个最值得喂入的事件
        
        返回: (index, event) 或 None
        """
        if not candidate_events:
            return None
        
        scored_events = []
        
        for i, event in enumerate(candidate_events):
            topo_var = Desemantifier().transform_event(event)
            
            # 计算"意外度"分数
            surprise_score = self._calculate_surprise(topo_var)
            
            scored_events.append((i, event, surprise_score))
        
        # 按意外度排序，选择最高的
        scored_events.sort(key=lambda x: x[2], reverse=True)
        
        # 返回最意外的事件
        return scored_events[0][0], scored_events[0][1]
    
    def _calculate_surprise(self, topo_var: TopologyVariable) -> float:
        """
        计算拓扑变量的"意外度"
        
        意外度来自：
        1. 高结构冲击（熵变大）
        2. 深度因果链
        3. Hub节点出现
        4. 事件类型稀有度
        """
        surprise = 0.0
        
        # 结构冲击
        surprise += topo_var.structural_impact * 0.4
        
        # 因果深度
        surprise += min(topo_var.causal_depth / 4.0, 0.3) * 0.3
        
        # Hub出现加成
        if topo_var.hub_emergence:
            surprise += 0.2
        
        # 边数量（关系越多越复杂）
        surprise += min(topo_var.new_edge_count / 5.0, 0.1)
        
        return min(surprise, 1.0)
    
    def update_history(self, event: any):
        """
        更新历史记录
        """
        self.event_history.append(event)


if __name__ == "__main__":
    # 测试去语义化器
    from book_parser import load_sample_shiji
    
    events = load_sample_shiji()
    des = Desemantifier()
    
    print(f"处理 {len(events)} 个事件")
    
    for evt in events[:5]:
        topo = des.transform_event(evt)
        print(f"\n事件: {evt.id}")
        print(f"  新节点: {topo.new_node_count}, 新边: {topo.new_edge_count}")
        print(f"  结构冲击: {topo.structural_impact:.2f}")
        print(f"  Hub出现: {topo.hub_emergence}")
        print(f"  边变化: {topo.edge_weight_changes[:2]}")
    
    stats = des.get_entity_statistics()
    print(f"\n统计: {stats}")
