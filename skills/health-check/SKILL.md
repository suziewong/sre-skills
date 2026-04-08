# Health Check Skill

## Metadata

```yaml
name: health-check
version: 1.0.0
display_name: 健康检查配置
description: 设计、配置和优化 Kubernetes/应用健康检查，实现零停机部署
tags: [kubernetes, k8s, health-check, readiness, liveness, startup, probe]
category: container
severity: medium
openclaw_compatible: true
```

## Triggers

用户可能这样触发此技能：
- "健康检查配置"
- "Pod 起不来"
- "服务不可用但 Pod 是 Running"
- "滚动更新失败"
- "Readiness/Liveness Probe"
- "服务灰度发布"

## Capabilities

### 输入 (Inputs)
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| deployment_yaml | string | 否 | Deployment YAML 内容 |
| service_name | string | 否 | 服务名称 |
| namespace | string | 否 | 命名空间 |
| check_result | string | 否 | 当前健康检查结果 |

### 输出 (Outputs)
- **健康检查配置建议**: 优化的 probe 配置
- **诊断报告**: 当前配置的问题分析
- **修复方案**: YAML 配置或 kubectl 命令

## Diagnosis Flow

详见 [DIAGNOSIS.md](./DIAGNOSIS.md)

## Checklists

详见 [CHECKLIST.md](./CHECKLIST.md)

## Quick Commands

```bash
# 查看 Pod 健康检查状态
kubectl get pod <pod> -o jsonpath='{.status.conditions[*]}' | jq .

# 查看 probe 配置
kubectl get pod <pod> -o jsonpath='{.spec.containers[0].readinessProbe}'
kubectl get pod <pod> -o jsonpath='{.spec.containers[0].livenessProbe}'

# 测试健康检查端点
kubectl exec -it <pod> -- curl -s localhost:<port>/health
kubectl exec -it <pod> -- wget -qO- http://localhost:<port>/health

# 查看容器事件
kubectl describe pod <pod> | grep -A 10 "Liveness"
kubectl describe pod <pod> | grep -A 10 "Readiness"

# 检查 probe 失败次数
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].started}'
```

## Probe 类型

| 类型 | 作用 | 失败后果 |
|------|------|----------|
| **Startup Probe** | 应用启动中 | 启动期间禁用其他 probe |
| **Readiness Probe** | 服务就绪 | 从 Service 移除，不接收流量 |
| **Liveness Probe** | 存活检测 | 杀死并重启容器 |

## 配置参数

| 参数 | 说明 | 建议值 |
|------|------|--------|
| `initialDelaySeconds` | 启动后多久开始探测 | ≥ 启动时间 |
| `periodSeconds` | 探测间隔 | 默认 10s |
| `timeoutSeconds` | 探测超时 | 默认 1s |
| `failureThreshold` | 连续失败多少次认为失败 | 默认 3 |
| `successThreshold` | 连续成功多少次认为成功 | 默认 1 |
| `terminationGracePeriodSeconds` | 优雅终止时间 | 默认 30s |

## Author

sre-skills Team

## License

MIT
