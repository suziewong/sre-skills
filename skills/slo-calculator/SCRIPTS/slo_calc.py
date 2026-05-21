#!/usr/bin/env python3
"""
SLO Calculator - SLO/SLI 计算器
快速计算服务可用性、错误预算和燃尽进度
"""

import argparse
import json
from datetime import datetime, timedelta
from typing import Optional


class SloCalculator:
    """SLO 计算器"""

    # SLO 标准参考
    SLO_REFERENCE = {
        99: ("基础可用性", "7.3 小时/月"),
        99.5: ("标准可用性", "3.65 小时/月"),
        99.9: ("高可用性", "43.8 分钟/月"),
        99.95: ("金融级", "21.9 分钟/月"),
        99.99: ("极高可用", "4.4 分钟/月"),
        99.999: ("超高可用", "26 秒/月"),
    }

    def __init__(
        self,
        service_name: str,
        total_requests: int,
        error_count: int,
        target_slo: float = 99.9,
        window_days: int = 30,
    ):
        self.service_name = service_name
        self.total_requests = total_requests
        self.error_count = error_count
        self.target_slo = target_slo
        self.window_days = window_days

    @property
    def availability(self) -> float:
        """计算实际可用性"""
        if self.total_requests == 0:
            return 0.0
        return ((self.total_requests - self.error_count) / self.total_requests) * 100

    @property
    def error_rate(self) -> float:
        """错误率"""
        if self.total_requests == 0:
            return 0.0
        return (self.error_count / self.total_requests) * 100

    @property
    def error_budget_total(self) -> float:
        """总错误预算（允许的错误次数）"""
        return self.total_requests * (1 - self.target_slo / 100)

    @property
    def error_budget_remaining(self) -> float:
        """剩余错误预算"""
        remaining = self.error_budget_total - self.error_count
        return max(0, remaining)

    @property
    def error_budget_consumed_pct(self) -> float:
        """已消耗错误预算百分比"""
        if self.error_budget_total == 0:
            return 0.0
        consumed = self.error_count / self.error_budget_total * 100
        return min(100, max(0, consumed))

    @property
    def status(self) -> str:
        """健康状态"""
        remaining_pct = 100 - self.error_budget_consumed_pct
        if remaining_pct > 50:
            return "healthy"
        elif remaining_pct > 20:
            return "warning"
        else:
            return "critical"

    @property
    def status_emoji(self) -> str:
        return {"healthy": "🟢", "warning": "🟡", "critical": "🔴"}.get(self.status, "⚪")

    def estimate_exhaustion_date(self) -> Optional[str]:
        """预测错误预算耗尽日期"""
        if self.error_budget_consumed_pct <= 0:
            return None

        if self.error_budget_consumed_pct >= 100:
            return "已耗尽"

        # 计算每天消耗量
        days_elapsed = self.window_days * (self.error_budget_consumed_pct / 100)
        if days_elapsed <= 0:
            return None

        daily_consumption = self.error_budget_consumed_pct / days_elapsed
        remaining_days = (100 - self.error_budget_consumed_pct) / daily_consumption * self.window_days / self.window_days

        exhaustion_date = datetime.now() + timedelta(days=remaining_days)
        return exhaustion_date.strftime("%Y-%m-%d")

    def generate_report(self) -> str:
        """生成完整报告"""
        reference = self.SLO_REFERENCE.get(
            self.target_slo, ("自定义", "根据目标计算")
        )

        exhaustion_date = self.estimate_exhaustion_date()
        budget_status = "🟢 健康" if self.status == "healthy" else "🟡 注意" if self.status == "warning" else "🔴 严重"

        report = f"""## SLO 计算结果

### 📊 {self.service_name} ({self.window_days}天滚动窗口)

| 指标 | 值 | 说明 |
|------|-----|------|
| **总请求量** | {self.total_requests:,} | - |
| **错误次数** | {self.error_count:,} | - |
| **实际可用性** | {self.availability:.4f}% | {'✅ 超标' if self.availability >= self.target_slo else '❌ 未达标'} |
| **目标可用性** | {self.target_slo}% | {reference[0]} |
| **实际错误率** | {self.error_rate:.4f}% | - |

---

### 💰 错误预算

| 指标 | 值 | 状态 |
|------|-----|------|
| **总错误预算** | {self.error_budget_total:,.0f} 次 | 基于 {self.target_slo}% SLO |
| **已消耗** | {self.error_count:,.0f} 次 | {self.error_budget_consumed_pct:.1f}% |
| **剩余预算** | {self.error_budget_remaining:,.0f} 次 | {self.error_budget_remaining / self.error_budget_total * 100:.1f}% |
| **健康状态** | {budget_status} | - |
| **预计耗尽** | {exhaustion_date or 'N/A'} | {'按当前消耗速度' if exhaustion_date else ''} |

---

### 📈 SLO 达标参考

| 目标 SLO | 级别 | 月允许停机 |
|----------|------|------------|
| 99% | 基础 | {self.SLO_REFERENCE[99][1]} |
| 99.5% | 标准 | {self.SLO_REFERENCE[99.5][1]} |
| 99.9% | 高可用 | {self.SLO_REFERENCE[99.9][1]} |
| 99.95% | 金融级 | {self.SLO_REFERENCE[99.95][1]} |
| 99.99% | 极高可用 | {self.SLO_REFERENCE[99.99][1]} |

---
*计算时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"""

        return report

    def to_json(self) -> dict:
        """输出 JSON 格式"""
        return {
            "service": self.service_name,
            "window_days": self.window_days,
            "total_requests": self.total_requests,
            "error_count": self.error_count,
            "availability": round(self.availability, 4),
            "target_slo": self.target_slo,
            "error_rate": round(self.error_rate, 4),
            "error_budget_total": round(self.error_budget_total, 2),
            "error_budget_remaining": round(self.error_budget_remaining, 2),
            "error_budget_consumed_pct": round(self.error_budget_consumed_pct, 2),
            "status": self.status,
            "estimated_exhaustion": self.estimate_exhaustion_date(),
        }


def main():
    parser = argparse.ArgumentParser(description="SLO Calculator - SLO/SLI 计算器")
    parser.add_argument("--service", "-s", type=str, help="服务名称")
    parser.add_argument("--requests", "-r", type=int, help="总请求量")
    parser.add_argument("--errors", "-e", type=int, help="错误请求数")
    parser.add_argument("--target", "-t", type=float, default=99.9, help="目标 SLO (默认: 99.9)")
    parser.add_argument("--window", "-w", type=int, default=30, help="时间窗口天数 (默认: 30)")
    parser.add_argument("--batch", "-b", type=str, help="批量计算 JSON 文件")
    parser.add_argument("--json", "-j", action="store_true", help="输出 JSON 格式")

    args = parser.parse_args()

    if args.batch:
        # 批量计算
        with open(args.batch, "r", encoding="utf-8") as f:
            services = json.load(f)

        for svc in services:
            calc = SloCalculator(
                service_name=svc.get("name", "unknown"),
                total_requests=svc.get("requests", 0),
                error_count=svc.get("errors", 0),
                target_slo=svc.get("target", 99.9),
                window_days=svc.get("window", 30),
            )
            if args.json:
                print(json.dumps(calc.to_json(), ensure_ascii=False, indent=2))
            else:
                print(calc.generate_report())
                print()
    else:
        # 单服务计算
        if not all([args.service, args.requests is not None, args.errors is not None]):
            parser.print_help()
            return

        calc = SloCalculator(
            service_name=args.service,
            total_requests=args.requests,
            error_count=args.errors,
            target_slo=args.target,
            window_days=args.window,
        )

        if args.json:
            print(json.dumps(calc.to_json(), ensure_ascii=False, indent=2))
        else:
            print(calc.generate_report())


if __name__ == "__main__":
    main()
