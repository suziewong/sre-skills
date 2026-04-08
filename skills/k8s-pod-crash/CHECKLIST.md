# K8s Pod Crash 快速诊断清单

## 🚨 紧急情况处理 (5分钟内)

### 第一步：确认问题范围
- [ ] `kubectl get pods -n <namespace>` - 查看所有 Pod 状态
- [ ] 确定是单 Pod 问题还是多个 Pod 问题
- [ ] 检查是否有 Node 级别的故障

### 第二步：获取关键信息
- [ ] `kubectl describe pod <pod-name> -n <namespace>`
- [ ] `kubectl logs <pod-name> -n <namespace> --previous`
- [ ] 记录 Exit Code 和 Status

### 第三步：临时止血
- [ ] 如果是单 Pod 问题，考虑删除让它重新调度
- [ ] 如果影响服务，考虑扩容
- [ ] 准备回滚方案

## 🔍 系统性排查 (15分钟内)

### 资源相关
- [ ] 检查 Memory Limit 是否设置过低
- [ ] 检查 CPU Limit 是否设置过紧
- [ ] 检查 Node 资源是否充足 `kubectl top nodes`
- [ ] 检查 Limits vs Requests 的比例

### 镜像相关
- [ ] 镜像标签是否正确（latest vs 固定版本）
- [ ] 私有镜像仓库认证是否过期
- [ ] 镜像是否存在于 registry
- [ ] 镜像大小是否导致拉取超时

### 配置相关
- [ ] ConfigMap/Secret 是否正确挂载
- [ ] 环境变量是否正确设置
- [ ] 依赖服务是否可访问
- [ ] 启动命令是否正确

### 网络相关
- [ ] Service/DNS 是否正常
- [ ] 网络策略是否阻止连接
- [ ] 健康检查配置是否正确

## 🛠️ 修复操作

### 内存相关修复
```bash
# 查看当前资源限制
kubectl get deployment <deploy> -n <ns> -o jsonpath='{.spec.template.spec.containers[0].resources}'

# 临时扩容 Pod
kubectl scale deployment <deploy> -n <ns> --replicas=3

# 增加内存限制
kubectl set resources deployment <deploy> -n <ns> --limits=memory=2Gi
```

### 配置相关修复
```bash
# 删除 Pod 强制重启
kubectl delete pod <pod-name> -n <namespace>

# 编辑配置
kubectl edit deployment <deploy-name> -n <namespace>

# 回滚到上一版本
kubectl rollout undo deployment <deploy-name> -n <namespace>
```

## 📋 复盘检查清单

### 根因确认
- [ ] 找到明确的根因（不是表面现象）
- [ ] 能复现问题
- [ ] 有完整的日志和证据

### 修复验证
- [ ] 修复后 Pod 状态正常
- [ ] 应用功能正常
- [ ] 监控指标正常

### 预防措施
- [ ] 资源限制是否合理调整
- [ ] 是否需要添加监控告警
- [ ] 是否需要添加健康检查
- [ ] 文档是否更新
- [ ] 是否需要 Postmortem

## 📊 关键指标

| 指标 | 健康值 | 告警阈值 |
|------|--------|----------|
| Pod Restart Count | < 3次/小时 | > 5次/小时 |
| Memory Usage | < 80% Limit | > 90% Limit |
| CPU Usage | < 70% Limit | > 90% Limit |
| Image Pull Duration | < 30s | > 60s |
