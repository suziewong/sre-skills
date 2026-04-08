#!/usr/bin/env python3
"""
K8s Pod Restart 分析工具
统计命名空间下所有 Pod 的重启次数，识别异常
"""

import json
import subprocess
from datetime import datetime
from collections import defaultdict

def run_kubectl(cmd):
    """执行 kubectl 命令并返回 JSON 输出"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True, encoding='utf-8'
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return None
    except Exception as e:
        print(f"执行命令失败: {e}")
        return None

def analyze_pod_restarts(namespace="default"):
    """分析 Pod 重启情况"""
    pods = run_kubectl(f'kubectl get pods -n {namespace} -o json')
    
    if not pods:
        print(f"无法获取 namespace {namespace} 的 Pod 列表")
        return
    
    restart_stats = []
    
    for pod in pods.get('items', []):
        name = pod['metadata']['name']
        status = pod['status'].get('phase', 'Unknown')
        restart_count = 0
        last_state = None
        
        for container in pod['status'].get('containerStatuses', []):
            restart_count += container.get('restartCount', 0)
            if container.get('lastState', {}).get('terminated'):
                last_state = container['lastState']['terminated'].get('exitCode')
        
        restart_stats.append({
            'name': name,
            'status': status,
            'restart_count': restart_count,
            'last_exit_code': last_state
        })
    
    # 按重启次数排序
    restart_stats.sort(key=lambda x: x['restart_count'], reverse=True)
    
    # 生成报告
    print(f"\n{'='*60}")
    print(f"📊 Pod 重启分析报告 - Namespace: {namespace}")
    print(f"{'='*60}")
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"\n{'Pod Name':<45} {'Status':<12} {'Restarts':<10} {'Last Exit'}")
    print(f"{'-'*60}")
    
    critical_pods = []
    
    for pod in restart_stats:
        status_icon = "✅" if pod['restart_count'] == 0 else "⚠️" if pod['restart_count'] < 5 else "🔴"
        print(f"{status_icon} {pod['name']:<43} {pod['status']:<12} {pod['restart_count']:<10} {pod['last_exit_code'] or 'N/A'}")
        
        if pod['restart_count'] >= 5:
            critical_pods.append(pod)
    
    # 汇总统计
    total_pods = len(restart_stats)
    problematic_pods = len([p for p in restart_stats if p['restart_count'] > 0])
    
    print(f"\n{'='*60}")
    print(f"📈 统计汇总:")
    print(f"  - 总 Pod 数: {total_pods}")
    print(f"  - 有重启的 Pod: {problematic_pods}")
    print(f"  - 高危 Pod (重启≥5次): {len(critical_pods)}")
    
    if critical_pods:
        print(f"\n🚨 高危 Pod 需要立即处理:")
        for pod in critical_pods:
            print(f"  - {pod['name']} (重启 {pod['restart_count']} 次)")
            
            # 获取详细日志
            print(f"    上次退出日志:")
            log_result = subprocess.run(
                f'kubectl logs {pod["name"]} -n {namespace} --previous --tail=5',
                shell=True, capture_output=True, text=True, encoding='utf-8'
            )
            if log_result.stdout:
                for line in log_result.stdout.strip().split('\n')[-5:]:
                    print(f"      {line}")
    
    print(f"\n{'='*60}")
    
    return restart_stats

def suggest_fixes(namespace="default"):
    """生成修复建议"""
    print(f"\n💡 修复建议:")
    print(f"\n1. 查看详细事件:")
    print(f"   kubectl describe pod <pod-name> -n {namespace}")
    
    print(f"\n2. 常见修复命令:")
    print(f"   # 删除 Pod 强制重启")
    print(f"   kubectl delete pod <pod-name> -n {namespace}")
    
    print(f"   # 增加内存限制")
    print(f"   kubectl set resources deployment <deploy> -n {namespace} --limits=memory=2Gi")
    
    print(f"   # 回滚版本")
    print(f"   kubectl rollout undo deployment <deploy> -n {namespace}")
    
    print(f"\n3. 添加监控告警:")
    print(f"   # PrometheusRule 示例")
    print(f"   kubectl get pod -n {namespace} -o json | jq '.items[] | select(.status.containerStatuses[].restartCount > 5) | .metadata.name'")

if __name__ == "__main__":
    import sys
    namespace = sys.argv[1] if len(sys.argv) > 1 else "default"
    
    stats = analyze_pod_restarts(namespace)
    
    if stats and any(p['restart_count'] >= 5 for p in stats):
        suggest_fixes(namespace)
