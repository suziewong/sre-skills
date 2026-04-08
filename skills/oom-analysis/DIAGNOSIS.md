# OOM Analysis 诊断流程

## 诊断步骤

### Step 1: 确认 OOM 类型

```bash
# 检查 dmesg 中的 OOM 日志
dmesg | grep -i "oom" | tail -50

# 检查 OOM Killer 击杀记录
dmesg | grep -i "killed process"
```

**输出示例:**
```
[1234567.890123] Out of memory: Killed process 12345 (java) total-vm:8096124kB, anon-rss:2048576kB, file-rss:0kB
```

**关键信息解读:**
- `total-vm`: 进程虚拟内存总量
- `anon-rss`: 匿名内存(堆/栈)实际使用
- `file-rss`: 文件映射内存

### Step 2: 分析系统内存状态

```bash
# 内存使用概览
free -h

# 详细内存信息
cat /proc/meminfo | grep -E "^(MemTotal|MemFree|MemAvailable|Cached|Buffers|SwapTotal|SwapFree):"

# 按内存使用排序的进程
ps aux --sort=-rss | awk '{print $6" "$11}' | head -20

# 查看 slab 内存使用
slabtop -o | head -15
```

### Step 3: 识别可疑进程

```bash
# 查看内存使用最多的进程
for pid in $(ls /proc | grep '^[0-9]'); do 
  if [ -f /proc/$pid/status ]; then
    name=$(cat /proc/$pid/cmdline 2>/dev/null | tr '\0' ' ' | cut -c1-50)
    rss=$(grep VmRSS /proc/$pid/status 2>/dev/null | awk '{print $2}')
    if [ ! -z "$rss" ] && [ "$rss" -gt 500000 ]; then
      echo "PID: $pid, RSS: $rss KB, CMD: $name"
    fi
  fi
done | sort -t: -k3 -n -r | head -10

# 查看进程打开的文件描述符
ls -la /proc/<pid>/fd | wc -l
```

### Step 4: 内存泄漏检测

```bash
# 重复执行，监控内存增长
while true; do
  date
  ps aux | grep <process_name> | grep -v grep
  sleep 10
done

# 查看 /proc/{pid}/smaps 细节
cat /proc/<pid>/smaps | grep -E "^(Size|Rss|Pss|Shared_Clean|Shared_Dirty|Private_Clean|Private_Dirty):" | awk '{sum += $2} END {print "Total: " sum " KB"}'

# 内存泄漏工具
# - pmap: 进程内存映射
pmap -x <pid> | tail -5

# - valgrind (需要重新启动)
valgrind --leak-check=full --log-file=valgrind.log ./program
```

### Step 5: Container OOM 特殊检查

```bash
# 查看容器内存限制
docker stats --no-stream

# 查看容器 OOM 事件
docker events --filter 'event=oom'

# 查看 cgroup 内存
cat /sys/fs/cgroup/memory/memory.usage_in_bytes
cat /sys/fs/cgroup/memory/memory.limit_in_bytes

# Kubernetes Pod OOM
kubectl get pod <pod> -o jsonpath='{.status.containerStatuses[0].lastState.terminated.reason}'
```

## JVM OOM 专项诊断

### Step 1: 获取 Heap Dump

```bash
# jmap 生成 heap dump (需要 jdk)
jmap -dump:format=b,file=heap.hprof <pid>

# 自动生成 (OutOfMemoryError 时)
-XX:+HeapDumpOnOutOfMemoryError -XX:HeapDumpPath=/path/to/dumps/

# kubectl exec 到 Java Pod
kubectl exec -it <pod> -- jmap -dump:format=b,file=/tmp/heap.hprof <pid>
```

### Step 2: 分析 Heap Dump

```bash
# 使用 jhat 分析
jhat -port 7000 heap.hprof
# 然后浏览器访问 http://localhost:7000

# 使用 MAT (Memory Analyzer Tool)
# 下载: https://eclipse.dev/mat/
# 打开 heap.hprof 文件

# 常用 MAT 查询
# - Histogram: 按类统计对象数量
# - Dominator Tree: 查找最大内存占用
# - Top Consumers: 最大的对象
# - Leak Suspects: 疑似泄漏点
```

### Step 3: GC 日志分析

```bash
# 开启 GC 日志
-XX:+PrintGCDetails -Xloggc:gc.log -XX:+PrintGCDateStamps

# 分析 GC 日志
gc_log_analyzer.py gc.log

# 在线分析工具: https://gceasy.io/
```

## 输出模板

```markdown
# OOM 分析报告

## 基本信息
- **时间**: <timestamp>
- **类型**: System OOM / Container OOM / JVM OOM
- **影响**: <影响范围>

## 系统状态
| 指标 | 值 |
|------|-----|
| Total Memory | <val> |
| Used Memory | <val> |
| Free Memory | <val> |
| Swap Used | <val> |

## 根因分析
<详细分析>

## 嫌疑进程
1. <process_name> (PID: xxx, RSS: xxx MB)

## 解决方案
1. <方案>

## 预防措施
- <措施>
```
