# K8s Pod Crash Diagnostic Skill

## Metadata

```yaml
name: k8s-pod-crash
version: 1.0.0
display_name: K8s Pod 崩溃诊断
description: 快速定位和分析 Kubernetes Pod 崩溃、根因及解决方案
tags: [kubernetes, k8s, pod, crash, restart, oom, oomkilled]
category: container
severity: high
openclaw_compatible: true
```

## Triggers

用户可能这样触发此技能：
- "Pod 挂了"
- "Pod 一直重启"
- "Pod OOMKilled"
- "容器退出码非0"
- "Pod 状态是 CrashLoopBackOff"
- "K8s 集群故障排查"

## Capabilities

### 输入 (Inputs)
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| namespace | string | 否 | Pod 所在命名空间，默认 default |
| pod_name | string | 是 | Pod 名称 |
| error_log | string | 否 | 错误日志片段 |
| events | string | 否 | K8s Events 输出 |

### 输出 (Outputs)
- **诊断报告**: Markdown 格式，包含根因分析 + 解决方案
- **修复命令**: 可直接执行的 kubectl 命令
- **预防建议**: 避免同类问题的最佳实践

## Diagnosis Flow

详见 [DIAGNOSIS.md](./DIAGNOSIS.md)

## Checklists

详见 [CHECKLIST.md](./CHECKLIST.md)

## Quick Commands

```bash
# 查看 Pod 状态和事件
kubectl describe pod <pod-name> -n <namespace>

# 查看最近日志
kubectl logs <pod-name> -n <namespace> --previous

# 查看资源限制
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[0].resources}'

# 查看 Node 状态
kubectl get nodes -o wide
```

## Common Exit Codes

| Exit Code | 含义 | 常见原因 |
|-----------|------|----------|
| 0 | 正常退出 | 任务完成或优雅关闭 |
| 1 | 一般错误 | 应用崩溃、未处理异常 |
| 137 | OOMKilled | 内存超限被 kill |
| 139 | Segmentation Fault | 段错误，内存访问越界 |
| 143 | Graceful Shutdown | 收到 SIGTERM，正常终止 |
| 255 | 退出码异常 | 入口命令执行失败 |

## Author

sre-skills Team

## License

MIT
