#!/usr/bin/env python3
"""
OOM 日志分析工具
分析 dmesg 中的 OOM Killer 日志，提取关键信息
"""

import re
import sys
import subprocess
from collections import defaultdict
from datetime import datetime

def get_oom_logs():
    """获取 dmesg 中的 OOM 日志"""
    try:
        # 尝试 journalctl
        result = subprocess.run(
            ['journalctl', '-k', '--no-pager'],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    
    try:
        # 尝试 dmesg
        result = subprocess.run(
            ['dmesg'], capture_output=True, text=True, timeout=30
        )
        if result.returncode == 0:
            return result.stdout
    except:
        pass
    
    return ""

def parse_oom_logs(logs):
    """解析 OOM 日志"""
    oom_events = []
    
    # OOM Killer 日志正则
    oom_pattern = re.compile(
        r'\[\s*(?P<timestamp>[^\]]+)\] '
        r'(?P<message>Out of memory.*?killed|'
        r'Killed process.*?total-vm.*?)',
        re.IGNORECASE
    )
    
    # 解析每条日志
    for match in oom_pattern.finditer(logs):
        timestamp = match.group('timestamp')
        message = match.group('message')
        
        event = {
            'timestamp': timestamp,
            'message': message,
            'process_name': None,
            'pid': None,
            'total_vm': None,
            'anon_rss': None,
            'file_rss': None
        }
        
        # 提取进程信息
        pid_match = re.search(r'Killed process\s+(?:\d+\s+)?(?:\((\w+)\))?\s+(?:total-vm:(\d+)kB,?)?\s*(?:anon-rss:(\d+)kB)?', 
                             message, re.IGNORECASE)
        if pid_match:
            event['process_name'] = pid_match.group(1)
            event['total_vm'] = int(pid_match.group(2)) if pid_match.group(2) else None
            event['anon_rss'] = int(pid_match.group(3)) if pid_match.group(3) else None
        
        oom_events.append(event)
    
    return oom_events

def analyze_oom_events(events):
    """分析 OOM 事件"""
    if not events:
        return {
            'total_count': 0,
            'top_processes': [],
            'total_memory_killed_kb': 0,
            'severity': 'low'
        }
    
    # 统计每个进程被杀次数
    process_counts = defaultdict(int)
    process_memory = defaultdict(int)
    
    for event in events:
        name = event['process_name'] or 'unknown'
        process_counts[name] += 1
        if event['anon_rss']:
            process_memory[name] += event['anon_rss']
    
    # 按被杀次数排序
    top_processes = sorted(process_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    
    total_memory = sum(p.get('anon_rss', 0) or 0 for p in events)
    
    # 评估严重程度
    severity = 'low'
    if len(events) >= 10:
        severity = 'critical'
    elif len(events) >= 5:
        severity = 'high'
    elif len(events) >= 1:
        severity = 'medium'
    
    return {
        'total_count': len(events),
        'top_processes': top_processes,
        'total_memory_killed_kb': total_memory,
        'severity': severity
    }

def generate_report(events, analysis):
    """生成分析报告"""
    print(f"\n{'='*70}")
    print(f"📊 OOM 分析报告")
    print(f"{'='*70}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n🔍 基本统计:")
    print(f"  - OOM 事件总数: {analysis['total_count']}")
    print(f"  - 被杀进程总内存: {analysis['total_memory_killed_kb'] / 1024:.2f} MB")
    print(f"  - 严重程度: {analysis['severity'].upper()}")
    
    if analysis['top_processes']:
        print(f"\n🔴 被杀次数最多的进程:")
        print(f"{'进程名':<30} {'被杀次数':<10}")
        print(f"{'-'*40}")
        for name, count in analysis['top_processes'][:5]:
            print(f"  {name:<28} {count:>6}")
    
    if events:
        print(f"\n📝 最近 OOM 事件 (最多显示10条):")
        print(f"{'时间戳':<25} {'进程':<15} {'RSS (MB)':<12} {'描述'}")
        print(f"{'-'*70}")
        
        for event in events[-10:]:
            name = event['process_name'] or 'unknown'
            rss = event['anon_rss'] / 1024 if event['anon_rss'] else 0
            msg = event['message'][:30] + '...' if len(event['message']) > 30 else event['message']
            print(f"{event['timestamp']:<25} {name:<15} {rss:>8.2f}    {msg}")
    
    print(f"\n💡 建议:")
    if analysis['severity'] in ['high', 'critical']:
        print(f"  ⚠️  OOM 事件频繁发生，需要立即处理！")
        print(f"  1. 检查 top 进程的内存使用是否正常")
        print(f"  2. 考虑增加系统内存或优化应用内存使用")
        print(f"  3. 添加 OOM 监控告警")
    else:
        print(f"  - 当前 OOM 事件较少，继续监控")
        print(f"  - 建议添加 Prometheus OOM 告警")
    
    print(f"\n{'='*70}")
    
    return analysis

if __name__ == "__main__":
    print("正在获取 OOM 日志...")
    logs = get_oom_logs()
    
    if not logs:
        print("无法获取 OOM 日志 (可能需要 sudo 权限)")
        print("或者使用: sudo dmesg | grep -i oom")
        sys.exit(1)
    
    events = parse_oom_logs(logs)
    analysis = analyze_oom_events(events)
    generate_report(events, analysis)
