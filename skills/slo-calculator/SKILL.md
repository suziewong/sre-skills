# SLO-Calculator - SLO/SLI 计算器

> 📊 快速计算 SLO 可用性、错误预算和燃尽进度

## 元数据

```yaml
name: slo-calculator
name_zh: SLO 计算器
category: sre
tags: [slo, sli, availability, error-budget, calculation, monitoring]
severity: medium
icon: 📊
status: ready

description: |
  SLO/SLI 计算器，帮助 SRE 和业务方快速计算服务可用性、
  错误预算剩余量、燃尽进度，支持多窗口分析。

triggers:
  - "SLO"
  - "可用性"
  - "错误预算"
  - "error budget"
  - "SLO 计算"
  - "服务可用性"
  - "每月可用性"

capabilities:
  - 计算实际可用性百分比
  - 计算剩余错误预算
  - 预测错误预算耗尽时间
  - 支持多种时间窗口（30天/滚动/自然月）
  - 批量多服务计算
  - 输出可视化结果

inputs:
  - name: total_requests
    type: number
    required: true
    description: 总请求量
  - name: error_count
    type: number
    required: true
    description: 错误请求数
  - name: target_slo
    type: number
    required: false
    default: 99.9
    description: 目标 SLO（百分比，如 99.9）
  - name: window_days
    type: number
    required: false
    default: 30
    description: 时间窗口（天）
  - name: service_name
    type: string
    required: false
    description: 服务名称（用于批量计算）

outputs:
  - name: availability
    type: number
    description: 实际可用性百分比
  - name: error_budget_remaining
    type: number
    description: 剩余错误预算百分比
  - name: budget_exhaustion_date
    type: string
    description: 预计错误预算耗尽日期
  - name: status
    type: string
    description: 健康状态 (healthy/warning/critical)
  - name: report
    type: markdown
    description: 完整的计算报告
```

## 使用方式

### 方式一：Python 脚本

```bash
# 单服务计算
python SCRIPTS/slo_calc.py \
  --service order-service \
  --requests 13140000 \
  --errors 394 \
  --target 99.9 \
  --window 30

# 批量计算（从 JSON 文件读取）
python SCRIPTS/slo_calc.py --batch services.json
```

### 方式二：Web 界面

直接打开 `SCRIPTS/slo_calculator.html` 即可使用可视化界面。

### 方式三：集成调用

```python
from slo_calc import SloCalculator

calc = SloCalculator(
    service_name="order-service",
    total_requests=13_140_000,
    error_count=394,
    target_slo=99.9,
    window_days=30
)

report = calc.generate_report()
print(report)
```

## 输出示例

```
## SLO 计算结果

### 📊 order-service (30天滚动窗口)

| 指标 | 值 | 状态 |
|------|-----|------|
| 实际可用性 | 99.97% | ✅ 超标 |
| 目标可用性 | 99.9% | - |
| 高出目标 | +0.07% | - |
| 剩余错误预算 | 78.3% | 🟢 健康 |
| 已消耗预算 | 21.7% | - |
| 距耗尽剩余 | 约 47 天 | - |

状态：🟢 健康
```

## SLO 标准参考

| SLO 目标 | 月允许停机时间 | 说明 |
|----------|----------------|------|
| 99% | 7.3 小时 | 基础可用性 |
| 99.5% | 3.65 小时 | 标准可用性 |
| 99.9% | 43.8 分钟 | 高可用性 |
| 99.95% | 21.9 分钟 | 金融/支付级 |
| 99.99% | 4.4 分钟 | 极端高可用 |
| 99.999% | 26 秒 | 超高可用 |
