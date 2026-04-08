# OOM 分析快速诊断清单

## 🚨 紧急响应 (5分钟内)

### 确认问题
- [ ] `dmesg | grep -i oom` 查看是否有 OOM 日志
- [ ] `uptime` 查看系统负载
- [ ] `free -h` 确认内存状态

### 立即止血
- [ ] 识别被 OOM Killer 杀掉的进程
- [ ] 评估业务影响范围
- [ ] 如果是关键进程，考虑重启
- [ ] 准备回滚方案

### 扩容应对
```bash
# 临时增加 swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# 或者杀掉非关键进程释放内存
ps aux --sort=-rss | head -20
kill -9 <high_rss_pid>
```

## 🔍 系统性排查 (15分钟内)

### 内存使用分析
- [ ] `ps aux --sort=-rss | head -20` 找出内存消耗大户
- [ ] `cat /proc/meminfo` 详细内存信息
- [ ] 检查是否有内存泄漏进程

### 缓存和缓冲区
- [ ] `sync; echo 3 > /proc/sys/vm/drop_caches` 清理缓存（谨慎）
- [ ] 检查 /tmp 和 /var/tmp 是否过大
- [ ] 检查日志文件是否暴涨

### Swap 状态
- [ ] `swapon -s` 查看 swap 使用
- [ ] 检查是否有大量 swap in/out (`vmstat 1`)
- [ ] 如果 swap 使用率高，说明物理内存严重不足

### Container/Kubernetes
- [ ] 检查 Pod memory limit
- [ ] 检查 Node 内存容量
- [ ] `kubectl describe pod` 查看 OOMKilled 事件

## 🛠️ 修复操作

### 临时修复
```bash
# 1. 重启可疑进程
systemctl restart <service>
kubectl delete pod <pod> -n <namespace>

# 2. 调低进程优先级防止被 kill
renice 19 $(pgrep <process>)
echo -1000 > /proc/<pid>/oom_score_adj

# 3. 限制进程内存 (cgroups)
# CentOS/RHEL:
yum install libcgroup-tools
cgcreate -g memory:/limited
cgset -r memory.limit_in_bytes=1073741824 /limited
cgexec -g memory:/limited <command>
```

### 永久修复
```bash
# 1. 添加物理内存

# 2. 优化应用内存使用
# Java: -Xmx 参数
# Node.js: --max-old-space-size

# 3. 配置 OOM 控制
# sysctl vm.overcommit_memory=1
# echo "vm.overcommit_memory=1" >> /etc/sysctl.conf

# 4. 调整 OOM Killer 策略
# /proc/<pid>/oom_score_adj: -1000 到 1000，越高越容易被杀
```

## 📋 复盘检查清单

### 根因确认
- [ ] 明确是内存泄漏还是配置不足
- [ ] 确定受影响的服务
- [ ] 找到内存增长的根本原因

### 监控完善
- [ ] 添加内存使用告警 (>80%)
- [ ] 添加 OOM 事件告警
- [ ] 配置 Prometheus node_memory_* 指标

### 容量规划
- [ ] 评估正常内存使用峰值
- [ ] 制定扩容计划
- [ ] 考虑资源隔离

## 📊 关键监控指标

| 指标 | 正常值 | 告警阈值 |
|------|--------|----------|
| memory.used / memory.total | < 70% | > 85% |
| swap.used / swap.total | < 20% | > 50% |
| oom_kills | 0 | > 0 |
| vmware_balloon | - | 持续增长 |
