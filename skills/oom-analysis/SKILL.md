# OOM Analysis Skill

## Metadata

```yaml
name: oom-analysis
version: 1.0.0
display_name: OOM 内存溢出分析
description: 深度分析系统级和应用级 OOM 问题，定位内存泄漏和溢出根因
tags: [oom, memory, leak, outofmemory, linux, kernel]
category: performance
severity: critical
openclaw_compatible: true
```

## Triggers

用户可能这样触发此技能：
- "内存爆了"
- "OOM Killer 杀进程"
- "系统内存不足"
- "应用内存泄漏"
- "dmesg 里有 OOM"
- "Pod 被 OOMKilled"

## Capabilities

### 输入 (Inputs)
| 参数 | 类型 | 必填 | 描述 |
|------|------|------|------|
| dmesg_output | string | 否 | dmesg 日志片段 |
| top_output | string | 否 | top/htop 输出 |
| vmstat_output | string | 否 | vmstat 输出 |
| process_info | string | 否 | 进程 PID 或名称 |
| oom_score | string | 否 | /proc/{pid}/oom_score |

### 输出 (Outputs)
- **分析报告**: Markdown 格式的完整分析
- **根因定位**: 内存泄漏点或配置问题
- **修复建议**: 具体可执行的步骤

## Diagnosis Flow

详见 [DIAGNOSIS.md](./DIAGNOSIS.md)

## Checklists

详见 [CHECKLIST.md](./CHECKLIST.md)

## Quick Commands

```bash
# 查看系统 OOM 事件
dmesg | grep -i "out of memory"
dmesg | grep -i "oom"

# 查看 OOM Killer 日志
cat /var/log/messages | grep "Out of memory"
journalctl -k | grep -i oom

# 查看进程内存使用
ps aux --sort=-rss | head -20
top -b -n 1 | head -20

# 查看详细内存信息
free -h
cat /proc/meminfo

# 查看 OOM Score
cat /proc/{pid}/oom_score
cat /proc/{pid}/oom_score_adj
```

## OOM 类型

| 类型 | 说明 | 常见场景 |
|------|------|----------|
| System OOM | 系统物理内存耗尽 | 物理机/VM 内存不足 |
| Container OOM | 容器内存限制触发 | K8s Pod memory limit |
| JVM OOM | Java heap 耗尽 | Java 应用内存问题 |
| Process OOM | 单进程内存耗尽 | C/C++ 程序泄漏 |
| Virtual OOM | 虚拟内存耗尽 | swap 满 + 内存满 |

## Author

sre-skills Team

## License

MIT
