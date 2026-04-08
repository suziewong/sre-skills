# K8s Pod Crash 诊断流程

## 诊断步骤

### Step 1: 收集 Pod 信息

```bash
# 基础信息
kubectl get pod <pod-name> -n <namespace> -o wide

# 详细事件
kubectl describe pod <pod-name> -n <namespace>

# 查看当前和上次运行的日志
kubectl logs <pod-name> -n <namespace> --tail=100
kubectl logs <pod-name> -n <namespace> --previous --tail=100
```

**关键检查点：**
- `Status`: CrashLoopBackOff / Error / OOMKilled
- `Restart Count`: 重启次数
- `Exit Code`: 退出码
- `Last State`: 上次退出原因

### Step 2: 分析退出码

```bash
# 检查容器退出码
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.containerStatuses[0].state.terminated.exitCode}'
```

**退出码对照表：**

| Exit Code | 可能的根因 |
|-----------|-----------|
| 137 (SIGKILL) | OOMKilled 或被驱逐 |
| 139 (SIGSEGV) | 段错误，可能是内存越界 |
| 1 或其他 | 应用自身错误 |

### Step 3: 检查资源限制

```bash
# 查看资源请求和限制
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{
  "Requests: "}{.spec.containers[0].resources.requests}{"\n"}
  {"Limits: "}{.spec.containers[0].resources.limits}{"\n"}'

# 查看 Node 资源使用
kubectl top nodes
kubectl describe node <node-name> | grep -A 5 "Allocated resources"
```

### Step 4: 检查 Events 和 Conditions

```bash
# 查看相关 Events
kubectl get events -n <namespace> --field-selector involvedObject.name=<pod-name> --sort-by='.lastTimestamp'

# 查看 Pod Conditions
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.status.conditions[*]}' | jq .
```

## 常见场景诊断

### 场景 1: OOMKilled

**特征:** `Exit Code: 137`, `OOMKilled: true`

**诊断流程:**
1. 检查 Container Memory Limit
2. 检查 Node 内存可用量
3. 分析应用内存增长曲线
4. 查看 / memory_limit 设置是否合理

**解决方案:**
```bash
# 方案1: 提高内存限制
kubectl patch deployment <deploy-name> -n <namespace> --type=merge -p '{
  "spec": {
    "template": {
      "spec": {
        "containers": [{
          "name": "<container>",
          "resources": {"limits": {"memory": "2Gi"}}
        }]
      }
    }
  }
}'

# 方案2: 优化应用内存使用
# - 检查内存泄漏
# - 减少缓存大小
# - 调整 JVM heap size
```

### 场景 2: CrashLoopBackOff

**特征:** Pod 反复重启，状态在 Running 和 Crash 之间切换

**诊断流程:**
1. `kubectl logs --previous` 查看上次退出日志
2. 检查启动命令是否正确
3. 检查依赖服务是否可用
4. 检查配置文件挂载是否正确

**解决方案:**
```bash
# 检查 ConfigMap/Secret 挂载
kubectl describe pod <pod-name> -n <namespace> | grep -A 10 "Mounts"

# 检查 ConfigMap 内容
kubectl get configmap <config-name> -n <namespace> -o yaml
```

### 场景 3: ImagePullBackOff

**特征:** 镜像拉取失败

**诊断流程:**
1. 检查镜像名称和标签
2. 检查 imagePullSecrets
3. 检查私有仓库认证
4. 检查网络策略

**解决方案:**
```bash
# 检查镜像
kubectl get pod <pod-name> -n <namespace> -o jsonpath='{.spec.containers[0].image}'

# 手动测试拉取
docker pull <image>

# 检查 Secret
kubectl get secret -n <namespace> | grep docker
```

## 输出模板

### 诊断报告格式

```markdown
# Pod 崩溃诊断报告

## 基本信息
- **Pod**: <pod-name>
- **Namespace**: <namespace>
- **Status**: <status>
- **Restart Count**: <count>
- **Exit Code**: <code>

## 根因分析
<具体分析>

## 解决方案
1. <方案1>
2. <方案2>

## 预防措施
- <措施1>
- <措施2>
```
