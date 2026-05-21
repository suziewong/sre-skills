# Cost-Anomaly-Detection - 云成本异常检测

> 💰 自动检测云成本异常，关联发布记录，定位责任归属

## 元数据

```yaml
name: cost-anomaly-detection
name_zh: 云成本异常检测
category: sre
tags: [cost, cloud, anomaly, detection, monitoring, billing, finops]
severity: medium
icon: 💰
status: ready

description: |
  云成本异常检测工具，通过对比历史数据自动识别成本突增/突降，
  关联发布记录和变更事件，定位成本异常根因，
  支持京东云、AWS、阿里云等多平台。

triggers:
  - "成本异常"
  - "账单"
  - "费用突增"
  - "云成本"
  - "FinOps"
  - "cost anomaly"
  - "billing alert"
  - "成本归因"

capabilities:
  - 日/周/月趋势分析
  - 异常分级告警（提示/警告/严重）
  - 自动归因到具体服务/团队
  - 关联发布记录和变更事件
  - 历史环比/同比对比
  - 月度成本健康报告生成
  - 多云平台支持（预留接口）

inputs:
  - name: bill_data
    type: file
    required: true
    description: 账单数据（CSV/JSON格式）
  - name: release_records
    type: file
    required: false
    description: 发布记录（可选，用于关联归因）
  - name: threshold_pct
    type: number
    required: false
    default: 15
    description: 告警阈值（百分比，超过视为异常）
  - name: platform
    type: string
    required: false
    default: jdcloud
    description: 云平台（jdcloud/aws/aliyun/gcp）
  - name: time_range
    type: string
    required: false
    default: 30d
    description: 分析时间范围

outputs:
  - name: anomaly_report
    type: markdown
    description: 异常检测报告
  - name: cost_trend
    type: json
    description: 成本趋势数据
  - name: attribution
    type: json
    description: 归因结果
  - name: alert_level
    type: string
    description: 告警级别 (info/warning/critical)
  - name: recommendations
    type: json
    description: 优化建议
```

## 使用方式

### 方式一：命令行分析

```bash
# 分析京东云账单
python SCRIPTS/detect_anomaly.py \
  --bill data/jd_bill.csv \
  --platform jdcloud \
  --threshold 15 \
  --output report.md

# 关联发布记录
python SCRIPTS/detect_anomaly.py \
  --bill data/jd_bill.csv \
  --releases data/releases.json \
  --output report.md
```

### 方式二：定期巡检

```bash
# 每日成本巡检（配合 cron 使用）
0 9 * * * python SCRIPTS/detect_anomaly.py --bill /data/daily_bill.csv --threshold 10
```

### 方式三：集成告警

支持接入企微/钉钉 Webhook：

```bash
python SCRIPTS/detect_anomaly.py \
  --bill data/jd_bill.csv \
  --webhook https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx
```

## 账单数据格式

### 京东云 CSV 格式

```csv
日期,产品,服务,用量,单价,金额,计费方式
2026-05-01,云主机,ecs,100台*1核*2G,0.5,50,按量
2026-05-01,数据库,RDS,10GB,0.3,3,包年
...
```

### 通用 JSON 格式

```json
{
  "date": "2026-05-01",
  "product": "云主机",
  "service": "ecs",
  "amount": 50.00,
  "currency": "CNY",
  "tags": {
    "team": "order",
    "env": "prod"
  }
}
```

## 输出示例

```markdown
## 成本异常告警

### 🚨 检测到异常

| 项目 | 值 |
|------|-----|
| 异常类型 | 🔴 严重 |
| 变化幅度 | +23%（较上周） |
| 超阈值 | 是（阈值15%） |
| 检测时间 | 2026-05-21 09:00 |

---

### 📊 成本趋势

| 日期 | 金额 | 环比 | 状态 |
|------|------|------|------|
| 2026-05-14 | ¥12,340 | - | 正常 |
| 2026-05-15 | ¥15,200 | +23% | ⚠️ 警告 |
| 2026-05-16 | ¥14,890 | +21% | ⚠️ 警告 |
| 2026-05-17 | ¥16,100 | +30% | 🔴 严重 |

---

### 🔍 归因分析

**主要来源**: ECS 容器组 - order-service
**次要来源**: RDS 数据库 - 主从实例

**可能原因**:
1. 缩容未生效，大促扩容遗留
2. 凌晨定时任务异常，持续运行

**关联发布**:
- 05-18 15:00 order-service v2.3.1 发布（可能触发扩容）

---

### ✅ 建议操作

| 优先级 | 操作 | 预期效果 |
|--------|------|----------|
| P0 | 检查定时缩容任务 | 防止费用继续增长 |
| P1 | 手动释放冗余 ECS 实例 | 预计节省 ¥800/天 |
| P2 | 优化 RDS 实例规格 | 预计节省 ¥200/天 |
```

## 检测算法

### 简单阈值法（默认）

```
if (今日成本 > 平均成本 * (1 + threshold%)):
    触发告警
```

### 环比法

```
if (今日成本 > 昨日成本 * (1 + threshold%)):
    触发告警
```

### 同比法（推荐日常使用）

```
if (今日成本 > 上周同期成本 * (1 + threshold%)):
    触发告警
```

### 复合判断

```python
# 综合多种方法，减少误报
is_anomaly = (
    (环比涨幅 > 阈值) and
    (成本绝对值 > 基准 * 1.2) and
    (非计划内涨价)
)
```
