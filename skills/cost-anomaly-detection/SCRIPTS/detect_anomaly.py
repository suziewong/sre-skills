#!/usr/bin/env python3
"""
Cost Anomaly Detection - 云成本异常检测
自动检测成本异常，关联发布记录，定位责任归属
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class CostAnomalyDetector:
    """成本异常检测器"""

    def __init__(
        self,
        threshold_pct: float = 15.0,
        platform: str = "jdcloud",
        time_range: str = "30d",
    ):
        self.threshold_pct = threshold_pct
        self.platform = platform
        self.time_range = time_range
        self.daily_costs: Dict[str, float] = {}
        self.service_costs: Dict[str, Dict[str, float]] = defaultdict(dict)
        self.alerts: List[dict] = []
        self.release_records: List[dict] = []

    def load_bill_from_csv(self, filepath: str) -> None:
        """从 CSV 文件加载账单数据"""
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                date = row.get("日期", row.get("date", ""))
                product = row.get("产品", row.get("product", ""))
                service = row.get("服务", row.get("service", ""))
                amount = float(row.get("金额", row.get("amount", 0)))

                if not date:
                    continue

                # 累计日成本
                self.daily_costs[date] = self.daily_costs.get(date, 0) + amount

                # 累计服务成本
                key = f"{product}/{service}"
                self.service_costs[key][date] = self.service_costs[key].get(date, 0) + amount

    def load_bill_from_json(self, filepath: str) -> None:
        """从 JSON 文件加载账单数据"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        records = data if isinstance(data, list) else data.get("records", [])

        for record in records:
            date = record.get("date", "")
            product = record.get("product", "")
            service = record.get("service", "")
            amount = float(record.get("amount", 0))

            if not date:
                continue

            self.daily_costs[date] = self.daily_costs.get(date, 0) + amount
            key = f"{product}/{service}"
            self.service_costs[key][date] = self.service_costs[key].get(date, 0) + amount

    def load_releases(self, filepath: str) -> None:
        """加载发布记录"""
        with open(filepath, "r", encoding="utf-8") as f:
            self.release_records = json.load(f)

    def load_bill(self, filepath: str) -> None:
        """自动识别格式加载账单"""
        suffix = Path(filepath).suffix.lower()
        if suffix == ".csv":
            self.load_bill_from_csv(filepath)
        elif suffix == ".json":
            self.load_bill_from_json(filepath)
        else:
            raise ValueError(f"不支持的文件格式: {suffix}")

    def detect_anomalies(self) -> List[dict]:
        """检测异常"""
        if len(self.daily_costs) < 2:
            return []

        sorted_dates = sorted(self.daily_costs.keys())
        anomalies = []

        for i in range(1, len(sorted_dates)):
            prev_date = sorted_dates[i - 1]
            curr_date = sorted_dates[i]
            prev_cost = self.daily_costs[prev_date]
            curr_cost = self.daily_costs[curr_date]

            if prev_cost == 0:
                continue

            pct_change = ((curr_cost - prev_cost) / prev_cost) * 100

            # 计算滚动平均值作为基准
            window_size = min(7, i)
            window_dates = sorted_dates[max(0, i - window_size):i]
            avg_cost = sum(self.daily_costs[d] for d in window_dates) / len(window_dates)

            pct_vs_avg = ((curr_cost - avg_cost) / avg_cost) * 100 if avg_cost > 0 else 0

            # 判断异常级别
            alert_level = "info"
            if abs(pct_change) >= self.threshold_pct or abs(pct_vs_avg) >= self.threshold_pct:
                if abs(pct_change) >= 30 or abs(pct_vs_avg) >= 30:
                    alert_level = "critical"
                elif abs(pct_change) >= 20 or abs(pct_vs_avg) >= 20:
                    alert_level = "warning"
                else:
                    alert_level = "warning"

                anomalies.append({
                    "date": curr_date,
                    "cost": curr_cost,
                    "prev_cost": prev_cost,
                    "change_pct": pct_change,
                    "vs_avg_pct": pct_vs_avg,
                    "avg_cost": avg_cost,
                    "alert_level": alert_level,
                })

        return anomalies

    def find_top_contributors(self, date: str, limit: int = 5) -> List[dict]:
        """找出当日成本最高的服务"""
        contributions = []
        for service, daily_data in self.service_costs.items():
            if date in daily_data:
                contributions.append({
                    "service": service,
                    "cost": daily_data[date],
                })

        contributions.sort(key=lambda x: x["cost"], reverse=True)
        return contributions[:limit]

    def correlate_releases(self, date: str) -> List[dict]:
        """关联发布记录"""
        target_date = datetime.strptime(date, "%Y-%m-%d")
        related = []

        for release in self.release_records:
            try:
                release_date = datetime.strptime(
                    release.get("date", release.get("timestamp", "")[:10],
                    "%Y-%m-%d"
                )
                diff = abs((target_date - release_date).days)

                if diff <= 3:  # 3天内发布的都相关
                    related.append({
                        "date": release.get("date"),
                        "service": release.get("service", "unknown"),
                        "version": release.get("version", ""),
                        "days_diff": diff,
                    })
            except (ValueError, KeyError):
                continue

        return related

    def generate_report(self, anomalies: List[dict]) -> str:
        """生成异常报告"""
        if not anomalies:
            return "## ✅ 成本检查结果\n\n**未检测到明显异常**\n\n- 阈值: ±{}%\n- 分析天数: {}天\n- 日均成本: ¥{:,.2f}".format(
                self.threshold_pct,
                len(self.daily_costs),
                sum(self.daily_costs.values()) / len(self.daily_costs) if self.daily_costs else 0
            )

        # 找出最严重的异常
        worst = max(anomalies, key=lambda x: abs(x["change_pct"]))

        # 构建趋势表格
        trend_rows = []
        for a in anomalies[-7:]:  # 最近7条
            status = "⚠️ 警告" if a["alert_level"] == "warning" else "🔴 严重"
            trend_rows.append(
                f"| {a['date']} | ¥{a['cost']:,.2f} | {a['change_pct']:+.1f}% | {status} |"
            )

        # 找出问题服务
        top_services = self.find_top_contributors(worst["date"])
        service_rows = []
        for svc in top_services:
            service_rows.append(f"| {svc['service']} | ¥{svc['cost']:,.2f} |")

        # 关联发布
        related_releases = self.correlate_releases(worst["date"])
        release_rows = []
        for r in related_releases[:3]:
            release_rows.append(
                f"| {r['date']} | {r['service']} v{r['version']} | {r['days_diff']}天前 |"
            )

        # 生成建议
        suggestions = self._generate_suggestions(worst)

        report = f"""## 💰 成本异常告警

### 🚨 检测到异常

| 项目 | 值 |
|------|-----|
| 异常日期 | {worst['date']} |
| 变化幅度 | {worst['change_pct']:+.1f}%（较前日） |
| 超阈值 | 是（阈值 ±{self.threshold_pct}%） |
| 告警级别 | {"🔴 严重" if worst['alert_level'] == 'critical' else '🟡 警告'} |
| 检测时间 | {datetime.now().strftime('%Y-%m-%d %H:%M')} |

---

### 📊 成本趋势（近7天）

| 日期 | 金额 | 环比 | 状态 |
|------|------|------|------|
{chr(10).join(trend_rows) if trend_rows else '| - | - | - | - |'}

---

### 🔍 归因分析

**当日成本TOP服务**：

| 服务 | 成本 |
|------|------|
{service_rows[0] if service_rows else '| - | - |'}
{service_rows[1] if len(service_rows) > 1 else ''}
{service_rows[2] if len(service_rows) > 2 else ''}

**可能原因**:
1. 扩缩容未按预期执行
2. 非预期流量突增
3. 凌晨定时任务异常

{"**关联发布记录**:\n\n| 日期 | 服务 | 距今 |\n|------|------|------|\n" + chr(10).join(release_rows) + "\n" if release_rows else ""}
---

### ✅ 建议操作

| 优先级 | 操作 | 预期效果 |
|--------|------|----------|
{"".join([f"| {s['priority']} | {s['action']} | {s['effect']} |" + chr(10) for s in suggestions])}
---

*报告由 Cost-Anomaly-Detection 自动生成*
"""

        return report

    def _generate_suggestions(self, anomaly: dict) -> List[dict]:
        """生成优化建议"""
        suggestions = []

        pct = abs(anomaly["change_pct"])

        if pct >= 30:
            suggestions.append({
                "priority": "P0",
                "action": "立即检查资源释放情况",
                "effect": "防止费用继续增长"
            })

        if anomaly["cost"] > anomaly["avg_cost"] * 1.2:
            suggestions.append({
                "priority": "P1",
                "action": "手动释放冗余资源",
                "effect": f"预计节省 ¥{anomaly['cost'] - anomaly['avg_cost']:,.0f}/天"
            })

        suggestions.extend([
            {
                "priority": "P2",
                "action": "检查定时扩缩容任务",
                "effect": "确保按预期执行"
            },
            {
                "priority": "P2",
                "action": "添加成本监控告警",
                "effect": "提前发现异常"
            }
        ])

        return suggestions

    def to_json(self, anomalies: List[dict]) -> dict:
        """输出 JSON 格式"""
        return {
            "platform": self.platform,
            "threshold_pct": self.threshold_pct,
            "anomalies": anomalies,
            "summary": {
                "total_days": len(self.daily_costs),
                "avg_cost": sum(self.daily_costs.values()) / len(self.daily_costs) if self.daily_costs else 0,
                "max_cost": max(self.daily_costs.values()) if self.daily_costs else 0,
                "min_cost": min(self.daily_costs.values()) if self.daily_costs else 0,
            }
        }


def main():
    parser = argparse.ArgumentParser(description="Cost Anomaly Detection - 云成本异常检测")
    parser.add_argument("--bill", "-b", required=True, help="账单文件路径 (CSV/JSON)")
    parser.add_argument("--releases", "-r", help="发布记录文件 (JSON)")
    parser.add_argument("--threshold", "-t", type=float, default=15.0, help="告警阈值百分比 (默认: 15)")
    parser.add_argument("--platform", "-p", default="jdcloud", help="云平台 (jdcloud/aws/aliyun)")
    parser.add_argument("--output", "-o", help="输出文件路径")
    parser.add_argument("--json", "-j", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    # 初始化检测器
    detector = CostAnomalyDetector(
        threshold_pct=args.threshold,
        platform=args.platform,
    )

    # 加载数据
    try:
        detector.load_bill(args.bill)
    except Exception as e:
        print(f"[ERROR] 加载账单失败: {e}", file=sys.stderr)
        sys.exit(1)

    if args.releases:
        try:
            detector.load_releases(args.releases)
        except Exception as e:
            print(f"[WARN] 加载发布记录失败: {e}", file=sys.stderr)

    # 检测异常
    anomalies = detector.detect_anomalies()

    # 输出
    if args.json:
        output = json.dumps(detector.to_json(anomalies), ensure_ascii=False, indent=2)
    else:
        output = detector.generate_report(anomalies)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"[*] 报告已保存到: {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
