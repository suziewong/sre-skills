# Architecture Review - 架构预审助手

> 🏛️ AI 驱动的架构预审工具，评审稳定性、成本、扩展性三大维度

## 元数据

```yaml
name: architecture-review
name_zh: 架构预审助手
category: sre
tags: [architecture, review, stability, cost, scalability, decision, ai]
severity: high
icon: 🏛️
status: ready

description: |
  AI 驱动的架构预审工具，帮助团队在评审会前快速识别架构方案的风险点。
  支持输入架构文档或直接描述业务场景，从稳定性、成本、扩展性三维度
  输出结构化预审报告，评审会上重点讨论红标项，提升决策效率。

triggers:
  - "架构评审"
  - "架构预审"
  - "架构分析"
  - "architecture review"
  - "技术方案评审"
  - "架构风险"
  - "帮我看看这个架构"

capabilities:
  - 多源文档输入（MD/TXT/HTML直接解析）
  - 稳定性评审（可用性、单点、降级、容灾）
  - 成本分析（基础设施、研发、运维预估）
  - 扩展性评估（水平/垂直扩、缩容能力）
  - 风险分级（Critical/Warning/Info）
  - HTML可视化报告输出
  - 备选方案对比建议

inputs:
  - name: architecture_doc
    type: string
    required: true
    description: 架构文档内容（直接粘贴或文件路径）
  - name: business_scenario
    type: string
    required: false
    description: 业务场景（流量、并发、数据量、用户量）
  - name: constraints
    type: string
    required: false
    description: 约束条件（预算、上线时间、技术栈限制）
  - name: review_focus
    type: string
    required: false
    default: "stability,cost,scalability"
    description: 评审重点维度（逗号分隔）
  - name: llm_provider
    type: string
    required: false
    default: ollama
    description: LLM提供者
  - name: llm_model
    type: string
    required: false
    default: qwen3-vl:8b
    description: 模型名称

outputs:
  - name: review_report
    type: html
    description: HTML可视化预审报告
  - name: risk_items
    type: json
    description: 风险项列表（分级）
  - name: stability_score
    type: number
    description: 稳定性评分 (0-100)
  - name: cost_score
    type: number
    description: 成本评分 (0-100)
  - name: scalability_score
    type: number
    description: 扩展性评分 (0-100)
  - name: recommendations
    type: json
    description: 优化建议列表
  - name: decision
    type: string
    description: 决策建议 (approve/conditional/reject)
```

## 使用方式

### 方式一：对话式（推荐）

直接向 WorkBuddy 描述架构方案，AI 自动生成预审报告：

```
用户：帮我预审这个架构 [粘贴架构文档内容]
业务场景：日均PV 1000万，峰值QPS 5万
约束：预算有限，想用最低成本方案

→ AI 生成 HTML 预审报告
```

### 方式二：命令行脚本

```bash
python SCRIPTS/review_architecture.py \
  --doc @architecture.md \
  --scenario "日均PV 1000万，峰值QPS 5万" \
  --constraints "预算有限，想用最低成本方案" \
  --output report.html
```

### 方式三：直接生成

```bash
# 传入架构描述文本
python SCRIPTS/review_architecture.py \
  --text "计划做一个订单服务，用单体架构，MySQL单库" \
  --scenario "日订单量10万" \
  --output report.html
```

## 输出报告预览

报告包含以下板块：

```
┌─────────────────────────────────────────┐
│  🏛️ 架构预审报告                          │
├─────────────────────────────────────────┤
│  📋 方案概览                              │
│  ⭐ 三维评分 (稳定性/成本/扩展性)            │
│  🔴 风险项 (Critical / Warning)           │
│  💡 优化建议                              │
│  ✅ 优势确认                             │
│  📊 备选方案对比                          │
│  🎯 决策建议                             │
└─────────────────────────────────────────┘
```

## 评审维度详解

### 稳定性维度
| 检查项 | 说明 |
|--------|------|
| 可用性目标 | 是否明确SLA/SLO |
| 单点故障 | 是否有单点组件 |
| 降级方案 | 核心功能故障时的降级策略 |
| 容灾设计 | 跨机房/跨区域部署 |
| 监控告警 | 关键指标覆盖情况 |
| 扩缩容触发 | 自动扩缩容是否配置 |

### 成本维度
| 检查项 | 说明 |
|--------|------|
| 基础设施成本 | 云资源预估 |
| 研发成本 | 开发复杂度估算 |
| 运维成本 | 维护成本预估 |
| 成本天花板 | 极端流量下的费用上限 |

### 扩展性维度
| 检查项 | 说明 |
|--------|------|
| 水平扩展 | 能否通过加机器提升容量 |
| 垂直扩展 | 瓶颈在哪儿 |
| 缩容能力 | 低峰期能否缩减资源 |
| 架构演进 | 未来扩展路径是否清晰 |
