# MySQL 慢查询诊断流程

## 诊断流程图

```
┌─────────────────┐
│  1. 收集信息    │
│  - 慢查询日志   │
│  - 数据库配置   │
│  - 连接状态     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  2. 分析慢查询  │
│  - 识别 Top N   │
│  - 分类问题类型 │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  3. 执行检查    │
│  - EXPLAIN 分析 │
│  - 索引检查     │
│  - 统计信息     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  4. 生成报告    │
│  - 问题定位     │
│  - 优化建议     │
│  - 参考文档     │
└─────────────────┘
```

## Step 1: 收集信息

### 1.1 检查慢查询日志配置

```sql
-- 查看慢查询是否开启
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';
SHOW VARIABLES LIKE 'slow_query_log_file';

-- 查看日志文件位置
SHOW VARIABLES LIKE 'log_output';
```

### 1.2 检查数据库状态

```sql
-- 当前连接数
SHOW STATUS LIKE 'Threads_connected';
SHOW STATUS LIKE 'Max_used_connections';
```

### 1.3 获取当前执行的查询

```sql
-- 查看当前连接和执行的查询
SHOW FULL PROCESSLIST;

-- 或者使用 information_schema
SELECT * FROM information_schema.PROCESSLIST 
WHERE Command != 'Sleep' 
ORDER BY Time DESC;
```

## Step 2: 分析慢查询

### 2.1 识别 Top N 慢查询

```sql
-- 查看最慢的查询
SELECT 
    start_time,
    query_time,
    lock_time,
    rows_sent,
    rows_examined,
    db,
    sql_text
FROM mysql.slow_log
ORDER BY query_time DESC
LIMIT 10;
```

### 2.2 分类问题类型

| 类型 | 特征 | 常见原因 |
|------|------|----------|
| 全表扫描 | rows_examined >> rows_sent | 缺少索引、SQL 写的有问题 |
| 索引失效 | type=ALL 或 index=N | 索引列上有函数、类型不匹配 |
| 临时表/排序 | Created_tmp_tables > 0 | GROUP BY/DISTINCT/ORDER BY 优化 |
| 锁等待 | Lock_time 高 | 并发冲突、大事务 |
| 网络/结果集大 | rows_sent 很大 | 分页查询不当 |

## Step 3: 执行检查

### 3.1 EXPLAIN 分析

```sql
-- 获取查询执行计划
EXPLAIN <your_query>;

-- 更详细的分析（MySQL 8.0+）
EXPLAIN ANALYZE <your_query>;
```

### 3.2 检查索引

```sql
-- 查看表的所有索引
SHOW INDEX FROM <table_name>;

-- 检查索引使用情况
SELECT 
    object_schema,
    object_name,
    index_name,
    cardinality,
    table_rows
FROM information_schema.STATISTICS
WHERE table_schema = '<database>'
ORDER BY cardinality DESC;
```

### 3.3 检查表统计信息

```sql
-- 查看表状态
SHOW TABLE STATUS FROM <database> LIKE '<table_name>';

-- 更新统计信息（如果统计过期）
ANALYZE TABLE <table_name>;
```

## Step 4: 生成报告

### 4.1 问题定位

根据分析结果，定位问题类型：

1. **缺少索引** → 添加索引
2. **索引失效** → 修改 SQL 或索引设计
3. **SQL 写法问题** → 重写 SQL
4. **配置问题** → 调整 MySQL 配置
5. **架构问题** → 考虑读写分离、分库分表

### 4.2 优化建议模板

```markdown
## MySQL 慢查询诊断报告

### 问题概览
- 慢查询数量: N
- 影响数据库: xxx
- 建议优先级: P0/P1/P2

### Top 3 问题查询

#### 问题 1: [标题]
- SQL: `SELECT ...`
- 执行时间: X.XX 秒
- 扫描行数: XXX
- 问题类型: [全表扫描/索引失效/...] 

**优化建议:**
1. [具体建议]
2. [具体建议]

### 后续行动
- [ ] 优化 SQL
- [ ] 添加索引
- [ ] 验证效果
```

## 常见优化方案

### 1. 添加索引

```sql
-- 添加单列索引
ALTER TABLE <table> ADD INDEX idx_<column> (<column>);

-- 添加联合索引（注意顺序）
ALTER TABLE <table> ADD INDEX idx_<columns> (<col1>, <col2>, <col3>);
```

### 2. 优化 SQL

```sql
-- 避免 SELECT *
SELECT id, name FROM users WHERE status = 1;

-- 使用 LIMIT 分页
SELECT * FROM orders ORDER BY id LIMIT 100, 20;

-- 避免隐式类型转换
SELECT * FROM users WHERE phone = '13800138000';
```

### 3. 调整配置

```ini
# my.cnf
slow_query_log = 1
slow_query_log_file = /var/log/mysql/slow.log
long_query_time = 1

# 连接池配置
max_connections = 200
wait_timeout = 600
```
