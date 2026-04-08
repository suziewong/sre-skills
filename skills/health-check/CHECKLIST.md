# Health Check 快速诊断清单

## 🚨 紧急情况处理 (5分钟内)

### 确认问题范围
- [ ] `kubectl get pods -n <namespace>` 查看所有 Pod 状态
- [ ] `kubectl get svc -n <namespace>` 查看 Service 和 Endpoints
- [ ] 确定是单 Pod 还是 Deployment 级别问题

### 快速止血
- [ ] 如果滚动更新卡住: `kubectl rollout undo deployment <name> -n <ns>`
- [ ] 如果单个 Pod 问题: `kubectl delete pod <pod> -n <ns>`
- [ ] 临时禁用 probe (不推荐长期使用)

### 收集信息
```bash
# 一键收集关键信息
kubectl describe pod <pod> -n <namespace> | grep -A 20 "Conditions"
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod> --sort-by='.lastTimestamp'
```

## 🔍 系统性排查 (15分钟内)

### Probe 配置检查
- [ ] Readiness/Liveness/Startup Probe 都配置了吗？
- [ ] initialDelaySeconds 是否 ≥ 应用启动时间？
- [ ] periodSeconds 是否合理？(推荐 5-30s)
- [ ] timeoutSeconds 是否够用？(网络延迟考虑)
- [ ] failureThreshold 是否给够重试机会？

### 依赖检查
- [ ] 健康检查端点 `/health` 响应 200 吗？
- [ ] 端点是否依赖数据库/缓存等外部服务？
- [ ] 如果依赖，是否应该依赖？（推荐只检查自身状态）

### 资源配置检查
- [ ] resources.requests.cpu/memory 是否合理？
- [ ] 是否存在资源不足导致的启动慢？
- [ ] Pod 是否被 OOMKilled 导致重启循环？

## 🛠️ 修复操作

### 调整 initialDelaySeconds
```bash
# 查看应用实际启动时间
kubectl describe pod <pod> | grep "Started:"
# 或者
kubectl get pod <pod> -o jsonpath='{.status.startTime}'

# 编辑 deployment
kubectl edit deployment <name> -n <namespace>

# 建议: initialDelaySeconds = 启动时间 + 10s buffer
```

### 测试 probe 配置
```bash
# 在 Pod 内测试 HTTP probe
kubectl exec -it <pod> -- wget -qO- http://localhost:8080/health

# 在 Pod 内测试 TCP probe
kubectl exec -it <pod> -- nc -zv localhost 8080

# 测试 exec probe
kubectl exec -it <pod> -- /myhealthcheck.sh
```

### 优化健康检查端点
```python
# Python Flask 示例
@app.route('/healthz')
def healthz():
    # 只检查自身，不依赖外部
    return jsonify({
        "status": "healthy",
        "uptime": time.time() - start_time
    }), 200
```

### 设置优雅终止
```yaml
spec:
  terminationGracePeriodSeconds: 60  # 给予足够时间处理现有请求
  containers:
  - name: app
    lifecycle:
      preStop:
        exec:
          command: ["/bin/sh", "-c", "sleep 10"]  # 等待 LB 移除流量
```

## 📋 配置最佳实践

### Startup Probe (必须时)
```yaml
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  failureThreshold: 30  # 给够 30*10=300s 启动时间
  periodSeconds: 10
```


### Readiness Probe
```yaml
readinessProbe:
  httpGet:
    path: /readyz
    port: 8080
  initialDelaySeconds: 10
  periodSeconds: 5
  successThreshold: 1
  failureThreshold: 3
```

### Liveness Probe (谨慎使用)
```yaml
livenessProbe:
  httpGet:
    path: /livez
    port: 8080
  initialDelaySeconds: 30
  periodSeconds: 15
  timeoutSeconds: 5
  failureThreshold: 3
```

## 📊 常见问题对照表

| 症状 | 原因 | 解决方案 |
|------|------|----------|
| Pod Running 但 NotReady | Readiness probe 失败 | 检查 /health 端点 |
| Pod 不断重启 | Liveness 失败或 OOM | 调整 threshold 或资源 |
| 滚动更新卡住 | Readiness 变红 | 检查新 Pod 健康状态 |
| 启动时被 kill | StartupProbe 失败 | 增加 failureThreshold |
| 有流量但响应慢 | Readiness 太激进 | 放宽 successThreshold |
| Terminating 卡住 | 优雅终止时间不够 | 增加 terminationGracePeriodSeconds |

## 📝 配置检查清单

### 部署前检查
- [ ] 已测试 `/health` 端点返回 200
- [ ] initialDelaySeconds > 启动时间
- [ ] failureThreshold 考虑了网络抖动
- [ ] 添加了 terminationGracePeriodSeconds

### 部署后验证
- [ ] Pod Ready 状态为 True
- [ ] Endpoints 包含该 Pod
- [ ] 测试流量正常路由
- [ ] 监控指标正常
