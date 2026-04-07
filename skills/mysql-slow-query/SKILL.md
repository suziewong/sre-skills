# MySQL 慢查询诊断

> 🐬 MySQL 慢查询自动诊断技能

## 元数据

```yaml
name: mysql-slow-query
name_zh: MySQL 慢查询诊断
category: sre
tags: [mysql, performance, diagnosis, database]
severity: high
icon: 🐬
status: ready

description: |
  MySQL 慢查询自动诊断技能，帮助快速定位和优化慢 SQL。
  支持分析慢查询日志、检查索引使用情况、提供优化建议。

triggers:
  - "MySQL 慢"
  - "数据库慢"
  - "slow query"
  - "MySQL 性能"
  - "查询超时"
  - "数据库连接池"

capabilities:
  - 自动分析慢查询日志
  - 检查索引使用情况
  - 分析执行计划
  - 提供优化建议
  - 生成诊断报告
  - 识别全表扫描
  - 检测缺失索引

inputs:
  - name: slow_log_path
    type: string
    required: false
    default: /var/log/mysql/slow.log
    description: 慢查询日志路径
  - name: host
    type: string
    required: false
    description: 数据库主机
  - name: port
    type: number
    required: false
    default: 3306
    description: 数据库端口
  - name: database
    type: string
    required: false
    description: 目标数据库名

outputs:
  - name: diagnosis_report
    type: markdown
    description: 完整的诊断报告
  - name: top_slow_queries
    type: json
    description: Top N 慢查询列表
  - name: optimization_suggestions
    type: json
    description: 优化建议列表
```

## 使用示例

### 方式一：交互式

```bash
# 进入技能目录
cd skills/mysql-slow-query

# 运行诊断脚本
python SCRIPTS/check_slow_log.py --path /var/log/mysql/slow.log
```

### 方式二：参数式

```bash
python SCRIPTS/check_slow_log.py \
  --host localhost \
  --port 3306 \
  --database myapp \
  --limit 10
```

## 诊断流程

详见 [DIAGNOSIS.md](DIAGNOSIS.md)

## 检查清单

详见 [CHECKLIST.md](CHECKLIST.md)
