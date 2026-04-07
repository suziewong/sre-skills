#!/usr/bin/env python3
"""
MySQL 慢查询日志分析工具

用法:
    python check_slow_log.py --path /var/log/mysql/slow.log
    python check_slow_log.py --host localhost --user root --password xxx
"""

import argparse
import re
import sys
import json
from datetime import datetime
from collections import defaultdict

try:
    import mysql.connector
except ImportError:
    print("请安装 mysql-connector-python: pip install mysql-connector-python")
    sys.exit(1)


def parse_slow_log(log_path, limit=20):
    """
    解析 MySQL 慢查询日志
    """
    queries = []
    
    try:
        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"文件不存在: {log_path}")
        return []
    except Exception as e:
        print(f"读取文件失败: {e}")
        return []
    
    # 使用正则提取查询
    query_pattern = re.compile(
        r'# Time: (.+?)\n'
        r'(?:.*?\n)*?'
        r'# Query_time: ([\d.]+)\s+Lock_time: ([\d.]+)\s+Rows_sent: (\d+)\s+Rows_examined: (\d+).*?\n'
        r'SET timestamp=(\d+);\s*(.*?);',
        re.DOTALL
    )
    
    for match in query_pattern.finditer(content):
        time_str, query_time, lock_time, rows_sent, rows_examined, timestamp, sql = match.groups()
        
        queries.append({
            'time': time_str.strip(),
            'query_time': float(query_time),
            'lock_time': float(lock_time),
            'rows_sent': int(rows_sent),
            'rows_examined': int(rows_examined),
            'sql': sql.strip(),
            'efficiency': int(rows_sent) / int(rows_examined) if int(rows_examined) > 0 else 0
        })
    
    # 按查询时间排序
    queries.sort(key=lambda x: x['query_time'], reverse=True)
    
    return queries[:limit]


def analyze_query_via_mysql(host, port, user, password, database, sql):
    """
    通过 MySQL 执行 EXPLAIN 分析查询
    """
    try:
        conn = mysql.connector.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        cursor = conn.cursor()
        
        # 执行 EXPLAIN
        cursor.execute(f"EXPLAIN {sql}")
        explain_result = cursor.fetchall()
        
        columns = [desc[0] for desc in cursor.description]
        explain_data = [dict(zip(columns, row)) for row in explain_result]
        
        cursor.close()
        conn.close()
        
        return explain_data
    except Exception as e:
        return {"error": str(e)}


def generate_report(queries, output_format='markdown'):
    """
    生成诊断报告
    """
    if not queries:
        return "未找到慢查询"
    
    if output_format == 'markdown':
        report = """# MySQL 慢查询诊断报告

Generated: {timestamp}

## 概览

- 慢查询总数: {total}
- 最慢查询: {slowest}s
- 平均查询时间: {avg}s
- 平均扫描行数: {avg_rows}

## Top 10 慢查询

""".format(
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total=len(queries),
            slowest=queries[0]['query_time'],
            avg=sum(q['query_time'] for q in queries) / len(queries),
            avg_rows=sum(q['rows_examined'] for q in queries) / len(queries)
        )
        
        for i, q in enumerate(queries[:10], 1):
            # 效率评估
            efficiency = q['efficiency']
            if efficiency < 0.01:
                flag = "⚠️ 全表扫描"
            elif efficiency < 0.1:
                flag = "⚡ 低效查询"
            else:
                flag = "✅ 正常"
            
            # 截断长 SQL
            sql_display = q['sql'][:200] + '...' if len(q['sql']) > 200 else q['sql']
            
            report += """### #{i} {flag}

- **执行时间**: {query_time}s
- **扫描行数**: {rows_examined} (返回 {rows_sent})
- **SQL**: 
```sql
{sql}
```

""".format(
                i=i,
                flag=flag,
                query_time=q['query_time'],
                rows_examined=q['rows_examined'],
                rows_sent=q['rows_sent'],
                sql=sql_display
            )
        
        # 优化建议
        report += """## 优化建议

### 高优先级

"""
        
        # 检查是否有全表扫描
        table_scans = [q for q in queries if q['efficiency'] < 0.01]
        if table_scans:
            report += f"- ⚠️ 发现 {len(table_scans)} 个疑似全表扫描，建议检查 WHERE 条件列是否有索引\n"
        
        # 检查是否需要 LIMIT
        large_result = [q for q in queries if q['rows_sent'] > 1000]
        if large_result:
            report += f"- ⚡ 发现 {len(large_result)} 个返回大量数据的查询，建议添加 LIMIT\n"
        
        report += "\n### 中优先级\n\n"
        
        # 检查 SELECT *
        select_star = [q for q in queries if 'SELECT *' in q['sql'].upper()]
        if select_star:
            report += f"- 📝 发现 {len(select_star)} 个 SELECT * 查询，建议指定需要的字段\n"
        
        report += "\n### 低优先级\n\n"
        report += "- 💡 建议定期执行 ANALYZE TABLE 更新统计信息\n"
        report += "- 💡 考虑开启查询缓存（如使用 MySQL 5.7 及以下）\n"
        
        return report
    
    elif output_format == 'json':
        return json.dumps(queries, indent=2, ensure_ascii=False)
    
    return ""


def main():
    parser = argparse.ArgumentParser(description='MySQL 慢查询分析工具')
    parser.add_argument('--path', '-p', help='慢查询日志文件路径')
    parser.add_argument('--host', '-H', default='localhost', help='MySQL 主机')
    parser.add_argument('--port', '-P', type=int, default=3306, help='MySQL 端口')
    parser.add_argument('--user', '-u', help='MySQL 用户名')
    parser.add_argument('--password', '-pw', help='MySQL 密码')
    parser.add_argument('--database', '-d', help='目标数据库')
    parser.add_argument('--limit', '-l', type=int, default=20, help='返回的查询数量')
    parser.add_argument('--format', '-f', choices=['markdown', 'json'], default='markdown', help='输出格式')
    
    args = parser.parse_args()
    
    if args.path:
        # 从文件分析
        queries = parse_slow_log(args.path, args.limit)
        report = generate_report(queries, args.format)
        print(report)
    elif args.host and args.user:
        # 从数据库查询
        print("直接从数据库查询慢查询请确保开启了 slow_query_log")
        print("或者手动执行 SELECT * FROM mysql.slow_log")
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
