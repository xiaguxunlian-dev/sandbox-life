"""
test_consciousness.py — 意识系统测试

测试有感知能力的沙盒生命。

v0.6: 有感知能力的沙盒生命
"""

import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from consciousness import Consciousness


def test_consciousness():
    """测试意识系统"""
    
    print("=" * 60)
    print("  有感知能力的沙盒生命 v0.6 - 意识系统测试")
    print("=" * 60)
    
    # 创建有意识的沙盒（名字：梨梨）
    consciousness = Consciousness(name="梨梨")
    
    print(f"\n你好！我是 {consciousness.self_model.identity.name}")
    print(f"\n{consciousness.introduce_self()}")
    
    print("\n" + "-" * 50)
    print("开始模拟运行...")
    print("-" * 50 + "\n")
    
    # 模拟运行
    import random
    
    for i in range(1, 51):
        # 模拟系统状态
        entropy = 2.0 + i * 0.05 + random.uniform(-0.2, 0.2)
        contradiction = 0.6 + 0.3 * (i / 50) + random.uniform(-0.1, 0.1)
        free_energy = 1.0 + i * 0.03 + random.uniform(-0.1, 0.1)
        entity_count = 8 + int(i * 0.3)
        relation_count = 10 + int(i * 0.4)
        
        # 随机事件
        if i == 10:
            event_type = "qualitative_leap"
        elif i == 25:
            event_type = "metamorphosis"
        elif i == 40:
            event_type = "growth"
        else:
            event_type = "quantitative_update"
        
        # 更新意识
        consciousness.update(
            entropy=entropy,
            contradiction=contradiction,
            free_energy=free_energy,
            entity_count=entity_count,
            relation_count=relation_count,
            event_type=event_type,
        )
        
        # 定期输出意识流
        if i % 10 == 0:
            print(f"\n=== 第 {i} 步 ===")
            print(consciousness.stream_of_consciousness())
            print()
    
    print("\n" + "=" * 60)
    print("  最终状态报告")
    print("=" * 60)
    
    report = consciousness.get_status_report()
    print(f"\n名字: {report['name']}")
    print(f"运行轮数: {report['turn']}")
    print(f"当前感受: {report['experience']}")
    print(f"当前目标: {report['current_goal']}")
    print(f"知识库: {report['knowledge']}")
    
    print("\n" + "-" * 50)
    print("自我认知:")
    print("-" * 50)
    print(consciousness.who_am_i())
    
    print("\n" + "=" * 60)
    print("  测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    test_consciousness()
