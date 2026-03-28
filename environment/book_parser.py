"""
历史书解析器：将文本转换为结构化事件流
Book Parser: Transform text into structured event streams

设计原则：
- 不依赖大型NLP模型，使用规则+统计方法
- 输出：HistoricalEvent 列表
- 每个事件包含：实体、关系、时间戳、熵变估计、因果链深度
"""

import re
import json
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path
import numpy as np


@dataclass
class HistoricalEvent:
    """历史事件结构"""
    id: str
    timestamp: int           # 年份（负数为公元前）
    entities: List[str]      # 涉及的实体（人名/地名/朝代名）
    relations: List[Tuple[str, str, str]]  # (主体, 关系类型, 客体)
    entropy_delta: float     # 世界状态变化幅度 [0,1]
    causal_chain_depth: int   # 因果链深度
    source_text: str         # 原文摘录（用于调试）
    chapter: str             # 来源章节

    def to_topology_input(self) -> Dict:
        """
        转换为实体可感知的拓扑变量（去语义化）
        """
        return {
            "new_entity_count": len(self.entities),
            "relation_changes": len(self.relations),
            "structural_impact": self.entropy_delta,
            "causal_depth": self.causal_chain_depth,
        }


class BookParser:
    """
    历史书 → 事件流 解析器
    
    使用规则方法提取：
    - 人名、地名、朝代名作为实体
    - 动词短语作为关系
    - 年份作为时间戳
    """

    # 常见关系类型映射（繁体→简体+标准化）
    RELATION_PATTERNS = {
        # 政治关系
        r"(.*)立为(.*)": "继承",
        r"(.*)禅让于(.*)": "禅让",
        r"(.*)伐(.*)": "战争",
        r"(.*)灭(.*)": "灭亡",
        r"(.*)朝贡于(.*)": "朝贡",
        r"(.*)封(.*)为(.*)": "册封",
        r"(.*)以(.*)为(.*)": "任命",
        r"(.*)废(.*)立(.*)": "废立",
        r"(.*)杀(.*)": "杀害",
        r"(.*)烹(.*)": "杀害",
        
        # 社会关系
        r"(.*)娶(.*)": "婚姻",
        r"(.*)嫁(.*)于(.*)": "婚姻",
        r"(.*)生(.*)": "生育",
        
        # 制度关系
        r"(.*)建立(.*)": "建立",
        r"(.*)废除(.*)": "废除",
        r"(.*)实行(.*)": "实行",
        r"(.*)颁布(.*)": "颁布",
    }

    def __init__(self):
        self.events: List[HistoricalEvent] = []
        self.entity_vocabulary: Set[str] = set()
        self.chapter_events: Dict[str, int] = {}  # 章节→事件数
        
    def parse_file(self, filepath: str) -> List[HistoricalEvent]:
        """
        解析文本文件
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {filepath}")
        
        content = path.read_text(encoding='utf-8')
        return self.parse_text(content, chapter=path.stem)
    
    def parse_text(self, text: str, chapter: str = "unknown") -> List[HistoricalEvent]:
        """
        解析文本内容
        """
        events = []
        
        # 按句分割
        sentences = self._split_sentences(text)
        
        for i, sentence in enumerate(sentences):
            if len(sentence) < 5:  # 跳过过短的句子
                continue
            
            # 提取实体
            entities = self._extract_entities(sentence)
            if not entities:
                continue
            
            # 提取时间
            timestamp = self._extract_timestamp(sentence)
            
            # 提取关系
            relations = self._extract_relations(sentence)
            
            # 跳过无关系的句子
            if not relations:
                continue
            
            # 估计熵变
            entropy_delta = self._estimate_entropy_delta(entities, relations)
            
            # 估计因果链深度（简化版：根据关系数量）
            causal_depth = min(len(relations), 4)
            
            event = HistoricalEvent(
                id=f"evt_{chapter}_{i:04d}",
                timestamp=timestamp,
                entities=entities,
                relations=relations,
                entropy_delta=entropy_delta,
                causal_chain_depth=causal_depth,
                source_text=sentence[:100],  # 保留原文用于调试
                chapter=chapter,
            )
            
            events.append(event)
            self.entity_vocabulary.update(entities)
        
        self.events.extend(events)
        self.chapter_events[chapter] = len(events)
        
        return events
    
    def _split_sentences(self, text: str) -> List[str]:
        """按句号、逗号、分号分割"""
        # 保留标点符号用于断句
        text = re.sub(r'([。！？；])', r'\1|', text)
        sentences = [s.strip() for s in text.split('|') if s.strip()]
        return sentences
    
    def _extract_entities(self, sentence: str) -> List[str]:
        """
        提取实体（人名、地名、朝代名）
        使用规则+常用词表
        """
        entities = []
        
        # 常见帝王后缀（更宽松的匹配）
        suffixes = ['帝', '王', '皇', '后', '公', '侯', '伯', '子', '男', '君', '主']
        
        # 提取带后缀的人名
        for suffix in suffixes:
            pattern = f'([一-龥]{{1,3}}{suffix})'
            matches = re.findall(pattern, sentence)
            entities.extend(matches)
        
        # 提取朝代名
        dynasties = ['夏', '商', '周', '秦', '汉', '楚', '燕', '赵', '魏', '齐', '韩', '晋', '吴', '越', '宋', '卫', '郑', '鲁', '唐', '虞']
        for dyn in dynasties:
            if dyn in sentence:
                # 检查是否是朝代上下文
                for suffix in ['朝', '代', '国']:
                    if dyn + suffix in sentence:
                        entities.append(dyn + suffix)
                # 单独出现也可能需要
                if len(sentence) < 50:  # 短句中更可能是朝代
                    entities.append(dyn)
        
        # 提取地名（简单规则：XX郡、XX县、XX州、XX山、XX泽）
        places = re.findall(r'([一-龥]{2,4}(?:郡|县|州|城|邑|国|山|泽|野|河|海))', sentence)
        entities.extend(places)
        
        # 提取神话/传说人物
        legendary = ['黄帝', '炎帝', '神农', '蚩尤', '尧', '舜', '禹', '汤', '文王', '武王', '周公']
        for name in legendary:
            if name in sentence:
                entities.append(name)
        
        # 去重，保留2-4字的实体
        entities = [e for e in set(entities) if 2 <= len(e) <= 4]
        
        return entities[:8]  # 最多8个实体
    
    def _extract_timestamp(self, sentence: str) -> Optional[int]:
        """
        提取时间戳（年份）
        返回：正数=公元后，负数=公元前
        
        简化版：根据句子中提到的历史时代推断大致时间
        """
        # 匹配具体年份
        year_match = re.search(r'(\d+)年', sentence)
        if year_match:
            year = int(year_match.group(1))
            
            # 检查是否"公元前"
            if '公元前' in sentence or ('前' in sentence[:8] and '年' in sentence[:10]):
                return -year
            return year
        
        # 根据关键词推断时代
        if any(w in sentence for w in ['黄帝', '尧', '舜', '禹', '神农']):
            return -2500  # 上古时代
        elif any(w in sentence for w in ['夏', '桀']):
            return -1800  # 夏
        elif any(w in sentence for w in ['商', '汤', '纣', '殷']):
            return -1300  # 商
        elif any(w in sentence for w in ['周', '文王', '武王', '成王', '康王']):
            return -1000  # 周初
        elif any(w in sentence for w in ['春秋', '战国']):
            return -500  # 春秋战国
        elif any(w in sentence for w in ['秦', '始皇', '始皇帝', '嬴政']):
            return -220  # 秦
        elif any(w in sentence for w in ['汉', '刘邦', '高祖', '武帝', '项羽']):
            return -200  # 汉初
        
        # 匹配"正月"、"二月"等（返回0表示时间未知/同年）
        if re.search(r'正?[一二三四五六七八九十]+月', sentence):
            return 0
            
        return None
    
    def _extract_relations(self, sentence: str) -> List[Tuple[str, str, str]]:
        """
        提取关系三元组 (主体, 关系, 客体)
        """
        relations = []
        
        for pattern, rel_type in self.RELATION_PATTERNS.items():
            match = re.search(pattern, sentence)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    subject = groups[0].strip()
                    obj = groups[-1].strip()
                    
                    # 过滤太短的主体/客体
                    if len(subject) >= 2 and len(obj) >= 2:
                        relations.append((subject, rel_type, obj))
        
        # 特殊处理："X 是 Y"
        if '是' in sentence:
            parts = sentence.split('是')
            if len(parts) >= 2:
                subject = parts[0].strip()
                obj = parts[1].strip()
                if len(subject) >= 2 and len(obj) >= 2:
                    relations.append((subject, "是", obj))
        
        return relations
    
    def _estimate_entropy_delta(self, entities: List[str], relations: List[Tuple]) -> float:
        """
        估计事件导致的熵变幅度
        - 涉及新实体越多，熵增越大
        - 涉及关系越多，结构性变化越大
        """
        base = 0.1
        
        # 实体数量贡献
        entity_factor = min(len(entities) / 10.0, 0.4)
        
        # 关系数量贡献
        relation_factor = min(len(relations) / 5.0, 0.5)
        
        return min(base + entity_factor + relation_factor, 1.0)
    
    def get_event_stream(self) -> List[HistoricalEvent]:
        """获取完整事件流"""
        return sorted(self.events, key=lambda e: e.timestamp if e.timestamp is not None else 0)
    
    def get_entity_list(self) -> List[str]:
        """获取所有实体列表"""
        return sorted(self.entity_vocabulary)
    
    def get_statistics(self) -> Dict:
        """获取解析统计"""
        timestamps = [e.timestamp for e in self.events if e.timestamp is not None]
        return {
            "total_events": len(self.events),
            "total_entities": len(self.entity_vocabulary),
            "time_range": (min(timestamps), max(timestamps)) if timestamps else (None, None),
            "chapter_counts": self.chapter_events,
            "avg_relations_per_event": np.mean([len(e.relations) for e in self.events]) if self.events else 0,
        }


def load_sample_shiji() -> List[HistoricalEvent]:
    """
    加载《史记》样本数据（内置简化版）
    用于测试和演示
    """
    sample_text = """
    黄帝者，少典之子，姓公孙，名曰轩辕。
    神农氏世衰，诸侯相侵伐，暴虐百姓，而神农氏弗能征。
    于是轩辕乃习用干戈，以征不享，诸侯咸来宾从。
    炎帝欲侵陵诸侯，诸侯咸归轩辕。
    轩辕与炎帝战于阪泉之野，三战，然后得其志。
    蚩尤作乱，不用帝命。
    于是黄帝乃征师诸侯，与蚩尤战于涿鹿之野，遂擒杀蚩尤。
    诸侯咸尊轩辕为天子，代神农氏，是为黄帝。
    天下有不顺者，黄帝从而征之，平者去之。
    披山通道，未尝宁居。
    
    帝尧者，放勋。其仁如天，其知如神。
    帝舜者，名曰重华。
    舜耕历山，渔雷泽，陶河滨，作什器于寿丘。
    舜得举用事二十年，而尧使摄政。
    尧崩，三年之丧毕，舜让辟丹朱于南河之南。
    诸侯朝觐者不之丹朱而之舜，狱讼者不之丹朱而之舜。
    舜代尧践位，是为帝舜。
    
    夏禹，名曰文命。禹之父曰鲧。
    鲧治水九年，功用不成。
    舜举鲧子禹，继鲧之功。
    禹疏九河，瀹济漯，决汝汉，排淮泗。
    禹致辟州木，平水土，功成。
    舜崩，禹让天下于益。
    禹王天下，国号曰夏后。
    
    殷汤，名曰履。外丙仲壬之世，湯崩。
    太子太丁早死，乃立太丁之弟外丙。
    外丙崩，立中壬。
    中壬崩，伊尹立太甲。
    太甲修德，诸侯咸归。
    殷复兴，迁于毫。
    
    周文王名昌。昌之脱羑里之囚归。
    阴行善，诸侯皆来决平。
    西伯崩，太子发立，是为武王。
    武王东观兵孟津，诸侯不期而会者八百。
    武王伐纣，纣兵败，登上鹿台，衣其宝玉衣，赴火而死。
    周武王封尚父于齐，封周公旦于鲁。
    成康之际，天下安宁，刑错四十余年不用。
    
    秦始皇帝者，秦庄襄王子也。
    庄襄王为秦质子于赵，见吕不韦姬，悦而取之，生始皇。
    及生，名为政，姓赵氏。
    年十三岁，庄襄王死，政代立为秦王。
    当是之时，秦地已并巴、蜀、汉中，越宛有郢，置南郡矣。
    北收上郡以东，有河东、太原、上党郡。
    东至荥阳，灭二周，置三川郡。
    吕不韦为相，封十万户，号曰文信侯。
    招致宾客游士，欲以并天下。
    李斯为舍人。蒙骜、王齮、麃公等为将军。
    
    秦王兼收六国，废封建，置郡县。
    书同文，车同轨，统一度量衡。
    筑长城以拒胡，筑阿房宫以自娱。
    焚诗书，坑儒士，以愚黔首。
    法令诛罚，日益刻深。
    七月丙寅，始皇崩于沙丘平台。
    赵高、李斯矫诏立胡亥为帝。
    胡亥即位，残暴更甚。
    陈胜、吴广起兵于大泽乡，诸侯并起。
    沛公刘邦入关，子婴降。
    项羽引兵屠咸阳，杀秦降王子婴。
    楚汉相争，项羽乌江自刎。
    汉高祖刘邦即皇帝位，都长安。
    """
    
    parser = BookParser()
    events = parser.parse_text(sample_text, chapter="史记样本")
    
    return events


if __name__ == "__main__":
    # 测试解析器
    events = load_sample_shiji()
    
    print(f"解析出 {len(events)} 个事件")
    print(f"实体数量: {len(set(e for evt in events for e in evt.entities))}")
    
    # 打印前5个事件
    print("\n前5个事件:")
    for evt in events[:5]:
        print(f"  [{evt.timestamp}] {evt.entities[:2]} - {evt.relations[:1]}")
