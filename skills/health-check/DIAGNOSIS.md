# Health Check 诊断流程

## 诊断步骤

### Step 1: 查看 Pod 当前状态

```bash
# Pod 概要状态
kubectl get pod <pod-name> -n <namespace>

# 详细状态信息
kubectl describe pod <pod-name> -n <namespace>

# 查看 Conditions
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{
  "Phase: "}{.status.phase}{"\n"}
  {"Conditions:\n"}{"  "}{.status.conditions[*].message}{"\n"}
}
```

**关键信息:**
- `Initialized`: 是否初始化完成
- `Ready`: 是否就绪（影响 Service 流量）
- `ContainersReady`: 所有容器是否就绪
- `PodScheduled`: 是否调度完成

### Step 2: 检查 Probe 配置

```bash
# 获取完整 probe 配置
kubectl get pod <pod-name> -n <namespace> -o json | jq '.spec.containers[0] | {
  readinessProbe,
  livenessProbe,
  startupProbe
}'

# 示例输出
{
  "readinessProbe": {
    "httpGet": {
      "path": "/healthz",
      "port": 8080
    },
    "initialDelaySeconds": 5,
    "periodSeconds": 5,
    "timeoutSeconds": 1,
    "failureThreshold": 3
  },
  "livenessProbe": {
    "exec": {
      "command": ["cat", "/tmp/healthy"]
    },
    "initialDelaySeconds": 15,
    "periodSeconds": 10
  }
}
```

### Step 3: 测试健康检查端点

```bash
# HTTP 健康检查测试
kubectl exec -it <pod> -n <namespace> -- curl -v localhost:8080/healthz
kubectl exec -it <pod> -n <namespace> -- wget -qO- http://localhost:8080/healthz

# TCP 端口检查
kubectl exec -it <pod> -n <namespace> -- nc -zv localhost 8080
kubectl exec -it <pod> -n <namespace> -- ss -tlnp | grep 8080

# Exec 命令检查
kubectl exec -it <pod> -n <namespace> -- /bin/sh -c "cat /tmp/healthy"
```

### Step 4: 分析失败原因

```bash
# 查看最近事件
kubectl get events -n <namespace> \
  --field-selector involvedObject.name=<pod-name> \
  --sort-by='.lastTimestamp' | tail -20

# 查看 probe 失败日志
# 注意: kubectl logs 不显示 probe 失败，但 events 会显示

# 常见失败原因
# 1. 端点返回非 200
kubectl exec -it <pod> -n <namespace> -- curl -s -o /dev/null -w "%{http_code}" localhost:8080/health

# 2. 端口未监听
kubectl exec -it <pod> -n <namespace> -- netstat -tlnp

# 3. 依赖服务不可用
kubectl exec -it <pod> -n <namespace> -- curl -s http://db:5432/  # 测试数据库连接
```

## 常见场景诊断

### 场景 1: Startup Probe 配置不当

**症状**: Pod 一直处于 `ContainerCreating` 或 `PodInitializing`

**诊断:**
```bash
# 检查启动时间
kubectl describe pod <pod> | grep "Created"
kubectl describe pod <pod> | grep "Started"

# 如果启动需要 60s，但 initialDelaySeconds 只有 10s
# startupProbe 会在 10*3=30s 后判定失败
```

**解决方案:**
```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 0
  periodSeconds: 5
  timeoutSeconds: 3
  failureThreshold: 60  # 60*5=300s，给够启动时间
```

### 场景 2: Readiness 过于严格

**症状**: Pod Running 但不在 Service 中

**诊断:**
```bash
kubectl get endpoints <service-name> -n <namespace>
# 查看 endpoints 数量是否和 ready pods 一致
```

**常见原因:**
1. 健康检查路径依赖数据库/缓存
2. 检查超时时间太短
3. failureThreshold 太小

**解决方案:**
```yaml
readinessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  timeoutSeconds: 2
  failureThreshold: 5  # 放宽到 5 次
  successThreshold: 1
```

### 场景 3: Liveness 过于激进

**症状**: Pod 不断被重启

**诊断:**
```bash
kubectl get pod <pod> --watch
# 查看 Restart Count 是否不断增长
```

**解决方案:**
```yaml
# 原则: Liveness 应该是最后手段，不轻易杀死进程
livenessProbe:
  httpGet:
    path: /healthz
    port: 8080
  initialDelaySeconds: 30  # 给够启动时间
  periodSeconds: 15  # 间隔不要太短
  timeoutSeconds: 3
  failureThreshold: 5  # 允许一定波动
```

## 最佳实践

### 不同应用的 Probe 配置

#### Java/Spring Boot
```yaml
# Spring Boot Actuator
readinessProbe:
  httpGet:
    path: /actuator/health/readiness
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 10

livenessProbe:
  httpGet:
    path: /actuator/health/liveness
    port: 8080
  initialDelaySeconds: 60
  periodSeconds: 15
```

#### Go
```yaml
# Go net/http Server
readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 5
  periodSeconds: 5

livenessProbe:
  httpGet:
    path: /livez
    port: 8080
  initialDelaySeconds: 15
  periodSeconds: 10
```

#### Nginx
```yaml
# Nginx ngx_http_stub_status
readinessProbe:
  httpGet:
    path: /basic_status
    port: 80
  initialDelaySeconds: 5
  periodSeconds: 5

livenessProbe:
  exec:
    command: ["nginx", "-t"]
  initialDelaySeconds: 10
  periodSeconds: 30
```

#### 数据库/中间件
```yaml
# 通常不需要 livenessProbe，避免自愈失败
readinessProbe:
  exec:
    command: ["pg_isready", "-U", "postgres"]
  initialDelaySeconds: 10
  periodSeconds: 10
```

## 输出模板

```markdown
# Health Check 诊断报告

## Pod 状态
- **Name**: <pod-name>
- **Namespace**: <namespace>
- **Phase**: <Running/Pending/etc>
- **Ready**: <True/False>
- **Restarts**: <count>

## Probe 配置
### Readiness Probe
- **Type**: HTTP/TCP/Exec
- **配置**: <details>
- **状态**: <working/failing>

### Liveness Probe
- **Type**: HTTP/TCP/Exec
- **配置**: <details>
- **状态**: <working/failing>

## 问题分析
<问题描述>

## 建议配置
<优化的 YAML 配置>
```
