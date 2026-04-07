# Case 001: 用户订单查询超时

## 场景描述

某电商系统，用户反馈订单页面加载超时，平均响应时间从 200ms 飙升至 30s+

## 诊断过程

### 1. 收集信息

```bash
# 查看慢查询日志
tail -100 /var/log/mysql/slow.log
```

### 2. 发现的慢查询

```sql
SELECT o.*, u.name, u.email 
FROM orders o 
LEFT JOIN users u ON o.user_id = u.id 
WHERE o.status = 'pending' 
ORDER BY o.created_at DESC 
LIMIT 100;
```

- 执行时间: 28.5s
- 扫描行数: 1,200,000
- 返回行数: 100
- 效率: 0.008%

### 3. 分析

```sql
EXPLAIN SELECT ...

+----+-------------+-------+------+---------------+------+---------+
| id | select_type | type  | key  | rows          | ...  |
+----+-------------+-------+------+---------------+------+---------+
|  1 | SIMPLE      | ALL   | NULL | 1,200,000     | ...  |
+----+-------------+-------+------+---------------+------+---------+
```

**问题**: type=ALL 表示全表扫描，orders 表有 120 万数据

### 4. 根因定位

- `orders.status` 字段没有索引
- `orders.created_at` 字段没有索引
- 查询需要排序，但 filesort 导致全表扫描

## 解决方案

### 方案 A: 添加索引

```sql
-- 添加复合索引覆盖查询
ALTER TABLE orders ADD INDEX idx_status_created (status, created_at DESC);
```

### 方案 B: 优化 SQL

```sql
-- 如果历史数据不需要，可以限制时间范围
SELECT o.*, u.name, u.email 
FROM orders o 
LEFT JOIN users u ON o.user_id = u.id 
WHERE o.status = 'pending' 
  AND o.created_at > DATE_SUB(NOW(), INTERVAL 30 DAY)
ORDER BY o.created_at DESC 
LIMIT 100;
```

## 效果验证

优化后:
- 执行时间: 45ms
- 扫描行数: 150
- 提升: 633 倍

## 经验总结

1. **状态类字段一定要索引**: 如果经常用 WHERE status = 'xxx'，必须加索引
2. **ORDER BY 的字段也要索引**: 可以避免 filesort
3. **复合索引注意顺序**: 区分度高的列放前面
4. **考虑覆盖索引**: 如果 SELECT 的列都在索引中，可以直接返回
