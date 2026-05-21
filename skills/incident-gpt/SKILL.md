# Incident-GPT - AI 故障分析助手

> 🤖 AI 驱动的故障分析工具，自动从日志/错误信息中提取时间线、推断根因并生成 RCA 报告

## 元数据

```yaml
name: incident-gpt
name_zh: AI 故障分析助手
category: sre
tags: [incident, rca, ai, diagnosis, automation, llm]
severity: high
icon: 🧠
status: ready

description: |
  基于大语言模型的故障分析助手，帮助 SRE 快速从日志、错误堆栈、
  链路追踪等原始数据中提取关键事件、构建时间线、推断根因，
  并自动生成结构化 RCA 报告。

triggers:
  - "故障分析"
  - "RCA"
  - "根因分析"
  - "incident analysis"
  - "事故报告"
  - "复盘"
  - "故障复盘"
  - "错误日志分析"
  - "堆栈分析"

capabilities:
  - 多源数据输入（日志片段、JSON、纯文本）
  - 自动提取关键事件节点
  - 按时间排序构建事件时间线
  - 基于错误模式识别根因
  - 自动评估影响范围
  - 生成结构化 Markdown RCA 报告
  - 输出 Action Items 改进建议
  - 支持调用本地 Ollama 或云端 LLM

inputs:
  - name: incident_description
    type: string
    required: true
    description: 故障描述（用户视角的简要说明）
  - name: logs
    type: string
    required: false
    description: 日志内容或错误堆栈
  - name: trace_data
    type: string
    required: false
    description: 链路追踪 JSON 数据
  - name: metrics
    type: string
    required: false
    description: 监控指标摘要（如错误率、RT、QPS）
  - name: llm_provider
    type: string
    required: false
    default: ollama
    description: LLM 提供者（ollama/openai/claude）
  - name: llm_model
    type: string
    required: false
    default: qwen3-vl:8b
    description: 模型名称

outputs:
  - name: rca_report
    type: markdown
    description: 完整的 RCA 报告
  - name: timeline
    type: json
    description: 事件时间线
  - name: root_cause
    type: string
    description: 推断的根因
  - name: action_items
    type: json
    description: 改进建议列表
  - name: impact_assessment
    type: json
    description: 影响评估
```

## 使用方式

### 方式一：交互式对话（推荐）

直接向 WorkBuddy 描述故障现象，粘贴日志片段，让 AI 自动分析。

```
示例对话：
用户：订单服务今天10:23开始大量超时，这是相关的日志片段
[粘贴日志]

WorkBuddy 自动：
1. 解析日志，提取关键事件
2. 构建时间线
3. 推断根因
4. 生成 RCA 报告
```

### 方式二：参数式调用

```bash
# 使用本地 Ollama 分析故障
python SCRIPTS/analyze_incident.py \
  --description "订单服务大量超时" \
  --logs @/path/to/error.log \
  --provider ollama \
  --model qwen3-vl:8b

# 使用 OpenAI 分析
python SCRIPTS/analyze_incident.py \
  --description "支付链路失败" \
  --logs @/path/to/pay.log \
  --provider openai \
  --model gpt-4o
```

## 输出示例

### RCA 报告结构

```markdown
## 故障分析报告

### 📋 基本信息
- **故障时间**: 2026-05-21 10:23:00 ~ 10:45:00
- **持续时长**: 约22分钟
- **影响范围**: 订单支付成功率下降至 73%
- **服务影响**: 涉及 order-service, payment-service
- **提交人**: SRE Team

---

### 📅 时间线
| 时间 | 事件 | 详情 |
|------|------|------|
| 10:23:14 | 错误率上升 | order-service 错误率从 0.1% 升至 5.2% |
| 10:23:45 | 连接池告警 | 数据库连接池使用率 100% |
| 10:24:02 | 下游超时 | payment-service 超时增加 |
| 10:25:30 | 扩容触发 | 尝试自动扩容，未见效 |
| 10:30:00 | 人工介入 | 开始排查 |
| 10:42:00 | 定位根因 | 发现慢查询 |
| 10:45:00 | 恢复 | 杀掉慢查询进程 |

---

### 🔍 根因分析
**直接原因**: 数据库某慢查询（执行时间 > 30s）导致连接池耗尽

**根本原因**: 
- 订单查询缺少复合索引
- 大促期间查询量突增3倍

---

### ✅ Action Items
| 优先级 | 任务 | 负责人 | 完成时间 |
|--------|------|--------|----------|
| P0 | 添加 (user_id, order_id) 复合索引 | @SRE-DB | 2026-05-22 |
| P1 | 优化慢查询 SQL | @Order-Dev | 2026-05-23 |
| P2 | 连接池告警阈值调低 | @SRE-Ops | 2026-05-22 |

---

### 📊 影响统计
- **受影响用户**: 约 12,847 人
- **失败订单**: 3,421 单
- **SLO 损失**: 0.04% (月错误预算消耗 3%)
```

## 诊断流程

详见 [DIAGNOSIS.md](DIAGNOSIS.md)

## 适用场景

- 故障复盘时，快速生成 RCA 文档
- 值班时，日志量太大难以快速定位
- 周报/月报需要的故障统计
- 跨团队事故同步，统一格式输出
