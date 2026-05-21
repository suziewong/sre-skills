---
domain: 电商/缓存
company: 通用
scenario: Redis缓存设计
pattern: 多级缓存 + 失效策略 + 热点处理
stability_target: 99.99%
date: 2024-10
---

# Redis 缓存设计实践

## 缓存策略

### Cache Aside（旁路缓存，最常用）

```
读：
应用 → 缓存（命中） → 直接返回
应用 → 缓存（未命中） → 查DB → 写缓存 → 返回

写：
应用 → DB（写）
应用 → 缓存（删除/更新）
```

**特点**：业务代码侵入小，推荐使用

### Read Through

```
读：
应用 → 缓存（未命中） → 缓存自动查DB → 返回
```

**特点**：缓存组件封装读逻辑，适合通用场景

### Write Through

```
写：
应用 → DB（同步写）
应用 → 缓存（同步写）
```

**特点**：数据一致性强，但性能差

## 数据结构选择

| 数据结构 | 适用场景 | 示例 |
|----------|----------|------|
| String | 简单值、JSON | 用户信息、配置 |
| Hash | 对象、字典 | 商品详情、用户画像 |
| List | 队列、列表 | 最新订单、消息队列 |
| Set | 去重、标签 | 用户标签、黑名单 |
| Sorted Set | 排行、限流 | 实时排行榜、滑动窗口限流 |

## 缓存失效策略

### TTL 设计原则

| 数据类型 | TTL | 说明 |
|----------|-----|------|
| 热点商品信息 | 5-10分钟 | 频繁访问，可以接受短暂过期 |
| 用户信息 | 15-30分钟 | 变更不频繁 |
| 库存数据 | 10-30秒 | 必须接近实时 |
| 配置信息 | 1-24小时 | 变更时主动删除 |

### 缓存失效后处理

```python
# 缓存击穿：单个key过期时，大量请求同时打到DB
# 解决方案：分布式锁

def get_product(product_id):
    cache_key = f"product:{product_id}"
    cache_val = redis.get(cache_key)

    if cache_val:
        return cache_val

    # 获取锁
    lock_key = f"lock:{cache_key}"
    if redis.setnx(lock_key, "1", ex=5):
        # 查DB
        product = db.query("SELECT * FROM products WHERE id = %s", product_id)
        # 写缓存
        redis.setex(cache_key, 300, json.dumps(product))
        redis.delete(lock_key)
        return product
    else:
        # 等待一下再试
        time.sleep(0.1)
        return redis.get(cache_key)
```

## 热点数据处理

### 热点 Key 问题

```
一个爆款商品：100万QPS
    ↓
打到同一台Redis：扛不住！
```

### 解决方案：热点 Key 打散

```python
# 方案1：key后缀随机
cache_key = f"product:{product_id}:{random.randint(1, 10)}"

# 方案2：本地缓存兜底
local_cache = threading.local()

def get_product(product_id):
    # 先查本地缓存
    local_val = local_cache.get(product_id)
    if local_val:
        return local_val

    # 查Redis
    val = redis.get(f"product:{product_id}")
    if val:
        local_cache[product_id] = val  # 存到本地
    return val
```

### 大促热点 Key 监控

```python
# 热点 key 发现
def detect_hot_keys():
    # 采样方式：INFO commandstats
    info = redis.info("commandstats")
    hot_keys = []

    for cmd, stats in info.items():
        if stats.get("calls", 0) > threshold:
            # 需要结合 keytracking 或 MONITOR 来定位具体 key
            pass
    return hot_keys
```

## 缓存与数据库一致性

### 方案对比

| 方案 | 一致性 | 复杂度 | 适用场景 |
|------|--------|--------|----------|
| Cache Aside | 最终一致 | 低 | 大多数场景 |
| 先更DB再删缓存 | 最终一致 | 低 | 读多写少 |
| 先删缓存再更DB | 最终一致+1 | 中 | 写多读少 |
| 延迟双删 | 最终一致 | 中 | 强一致场景 |
| Canal订阅 | 准实时 | 高 | 需要强一致 |

### 延迟双删（推荐）

```python
def update_user(user_id, data):
    # 1. 先删缓存
    redis.delete(f"user:{user_id}")

    # 2. 更新DB
    db.execute("UPDATE users SET ... WHERE id = %s", user_id)

    # 3. 延迟再删（等DB写完成）
    threading.Timer(0.5, lambda: redis.delete(f"user:{user_id}")).start()
```

## Redis 集群方案

### 主从 + Sentinel（简单场景）

```
         Sentinel
        /   |   \
       ▼    ▼    ▼
      M  →  S1   S2
```

**特点**：
- 自动故障转移
- 1主2从3哨兵
- 不支持横向扩展

### Cluster（大规模场景）

```
客户端
   │
   └── Cluster（16384 slots）
       │
       ├── Slot 0-5460  → 节点A
       ├── Slot 5461-10922 → 节点B
       └── Slot 10923-16383 → 节点C
```

**特点**：
- 数据分片
- 自动故障转移
- 支持横向扩展

## 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 缓存雪崩 | 大量key同时过期 | 过期时间+随机偏移 |
| 缓存击穿 | 单个热点key过期 | 分布式锁 |
| 缓存穿透 | 查询不存在的数据 | 空值缓存+布隆过滤器 |
| 缓存脑裂 | 网络分区导致多主 | 合理配置min-slaves |
