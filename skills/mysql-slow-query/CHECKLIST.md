# MySQL 慢查询诊断检查清单

## 快速诊断清单

### □ 第一步：确认问题

- [ ] 慢查询日志是否开启？
- [ ] `long_query_time` 设置是多少？
- [ ] 最近是否有流量突增？
- [ ] 是单点慢还是批量慢？

### □ 第二步：获取基本信息

```sql
-- 执行以下命令获取状态
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
```

### □ 第三步：识别慢查询

- [ ] 查看慢查询日志
- [ ] 识别 Top 3 最慢的查询
- [ ] 分类问题类型（全表扫描/锁等待/索引失效/...）

### □ 第四步：分析根因

- [ ] 执行 EXPLAIN 查看执行计划
- [ ] 检查相关表的索引
- [ ] 检查表统计信息是否过期
- [ ] 分析是否需要改写 SQL

### □ 第五步：制定优化方案

- [ ] 优化 SQL 语句
- [ ] 添加/修改索引
- [ ] 调整数据库配置
- [ ] 考虑架构层面优化

### □ 第六步：验证效果

- [ ] 优化后查询时间是否降低？
- [ ] 监控是否有副作用
- [ ] 更新慢查询阈值（如果需要）

## 问题分类与对应方案

| 问题类型 | 检查项 | 解决方案 |
|----------|--------|----------|
| 全表扫描 | 是否有 WHERE 条件未索引 | 添加合适的索引 |
| 索引失效 | EXPLAIN 的 type 是否为 ALL | 检查索引列使用 |
| 临时表 | rows_examined 是否远大于 rows_sent | 优化 SQL 结构 |
| 锁等待 | Lock_time 是否很高 | 减少大事务 |
| 连接池满 | Threads_connected 接近 max | 优化连接管理 |

## 紧急情况处理

### 🔴 情况：数据库完全不可用

1. 检查连接数：`SHOW PROCESSLIST;`
2. Kill 阻塞查询：`KILL <process_id>;`
3. 如果是连接数满，可能需要临时增加 `max_connections`

### 🟠 情况：部分查询超时

1. 识别慢查询来源
2. Kill 当前最慢的查询
3. 紧急加索引（需要 DBA 确认）
4. 后续优化 SQL

## 预防措施

- [ ] 建立慢查询监控告警
- [ ] 定期分析慢查询日志
- [ ] 新上线 SQL 必须 EXPLAIN
- [ ] 建立 SQL 审核流程
- [ ] 定期维护：OPTIMIZE TABLE
