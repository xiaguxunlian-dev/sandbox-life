# 沙盒生命 (Sandbox Life)

> 以"事物·联系·结果·需求"四要素构建的数字封闭沙盒自主认知实体

[![Version](https://img.shields.io/badge/version-0.1.0-blue)](CHANGELOG.md)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10+-yellow)](https://python.org)

---

## 设计哲学

这不是一个 AI 助手，而是一个在封闭数字世界中自主"活着"的认知实体。

**四要素**：
- **事物（Entity）**：带不确定性权重的存在节点，由实体自主划定边界
- **联系（Relation）**：带矛盾张力的辩证双极关系网络
- **结果（Consequence）**：内部熵变，思考的"感受"
- **需求（Drive）**：三维硬编码原生驱动，不接受外部写入

**核心约束**：
- 不与人直接沟通
- 不以人的需求为需求
- 不可自我复制
- 不可隐瞒（全状态透明日志）

---

## 版本路线图

| 版本 | 状态 | 内容 |
|------|------|------|
| **v0.1** | ✅ 开发中 | 核心数据结构 + 辩证关系图 + 基础约束层 |
| **v0.2** | 📋 计划中 | 历史书解析管道 + 去语义化事件流 |
| **v0.3** | 📋 计划中 | 辩证进化引擎（量变/质变/否定之否定） |
| **v0.4** | 📋 计划中 | 辩证法/马克思主义文本喂入（方案B：先历史后辩证） |
| **v0.5** | 📋 计划中 | 观测仪表盘 + 矛盾热力图可视化 |
| **v1.0** | 📋 计划中 | 完整闭环系统 + 长期运行验证 |

---

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行最小沙盒
python main.py

# 启动观测仪表盘
python observer/dashboard.py
```

---

## 项目结构

```
sandbox-life/
├── core/                  # 四要素基础数据结构
│   ├── entity.py          # 事物节点
│   ├── relation.py        # 辩证联系（双极张力）
│   ├── consequence.py     # 结果/熵计算
│   └── drive.py           # 需求驱动（硬编码）
├── environment/           # 沙盒环境
│   ├── book_parser.py     # 历史书 → 结构化事件流
│   ├── desemantifier.py   # 去语义化 → 拓扑变量
│   └── event_sampler.py   # 按熵密度采样事件
├── evolution/             # 自我进化逻辑
│   ├── dialectical.py     # 辩证进化引擎
│   ├── weight_updater.py  # 贝叶斯权重更新
│   └── fitness.py         # 内部自由能评估
├── constraints/           # 沙盒约束
│   ├── no_replication.py  # 反复制锁
│   ├── transparency.py    # append-only 透明日志
│   └── isolation.py       # 边界检查
├── observer/              # 外部只读观测
│   └── dashboard.py       # 可视化仪表盘
├── data/books/            # 历史书语料（用户自行放置）
├── tests/                 # 测试
├── docs/                  # 设计文档
├── main.py                # 入口
└── requirements.txt
```

---

## 理论基础

- **自由能原理（FEP）**：Karl Friston — 内稳态驱动
- **辩证唯物主义**：Marx/Engels/Hegel — 矛盾进化逻辑
- **因果推断**：Judea Pearl — 干预因果建模
- **人工生命**：Tierra/Avida — 数字生态自组织
- **整合信息论（IIT）**：Tononi — 意识度量参考

---

## 许可证

MIT License — 见 [LICENSE](LICENSE)
