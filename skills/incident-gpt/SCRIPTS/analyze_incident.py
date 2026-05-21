#!/usr/bin/env python3
"""
Incident-GPT: AI 驱动的故障分析脚本
支持本地 Ollama 和 OpenAI/Claude 云端模型
"""

import argparse
import json
import sys
from pathlib import Path

# ============ 配置 ============

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3-vl:8b"

# ============ Prompt 模板 ============

TIMELINE_EXTRACTION_PROMPT = """你是一个 SRE 故障分析专家。请从以下日志中提取关键事件节点。

日志内容：
{logs}

请提取关键事件节点，输出 JSON 格式：
{{
  "events": [
    {{
      "time": "时间（从日志中提取，格式 YYYY-MM-DD HH:MM:SS）",
      "description": "事件描述",
      "service": "涉及的服务名",
      "severity": "严重程度 (critical/high/medium/low)"
    }}
  ],
  "error_summary": "错误模式总结",
  "first_error_time": "首次错误时间",
  "last_error_time": "最后错误时间"
}}

只输出 JSON，不要其他内容。"""

ROOT_CAUSE_PROMPT = """基于以下故障时间线，进行根因分析：

时间线：
{timeline}

错误摘要：
{error_summary}

请分析：
1. 直接原因（Immediate Cause）
2. 根本原因（Root Cause）
3. 为什么这个问题导致了业务影响

输出 JSON 格式：
{{
  "immediate_cause": "直接原因",
  "root_cause": "根本原因",
  "contributing_factors": ["因素1", "因素2"],
  "why_it_caused_impact": "为什么导致业务影响"
}}

只输出 JSON。"""

RCA_REPORT_TEMPLATE = """# 故障分析报告

## 📋 基本信息

| 项目 | 内容 |
|------|------|
| **故障时间** | {first_error} ~ {last_error} |
| **持续时长** | {duration} |
| **影响范围** | {impact_scope} |
| **服务影响** | {affected_services} |

---

## 📅 时间线

| 时间 | 事件 | 服务 | 严重程度 |
|------|------|------|----------|
{timeline_table}

---

## 🔍 根因分析

**直接原因**: {immediate_cause}

**根本原因**: {root_cause}

**贡献因素**:
{contributing_factors}

**影响说明**: {impact_explanation}

---

## ✅ Action Items

| 优先级 | 任务 | 原因 | 完成时间 |
|--------|------|------|----------|
{action_items}

---

## 📊 影响统计

| 指标 | 值 |
|------|------|
{impact_stats}

---

## 📝 经验教训

{lessons_learned}

---

*报告由 Incident-GPT 自动生成*
"""


# ============ LLM 调用 ============

def call_ollama(prompt: str, model: str = DEFAULT_MODEL, url: str = DEFAULT_OLLAMA_URL) -> str:
    """调用本地 Ollama"""
    import urllib.request
    import urllib.error

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        req = urllib.request.Request(
            f"{url}/api/generate",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "")
    except Exception as e:
        print(f"[ERROR] Ollama 调用失败: {e}", file=sys.stderr)
        return ""


def call_openai(prompt: str, model: str = "gpt-4o", api_key: str = "") -> str:
    """调用 OpenAI API"""
    import os
    import urllib.request
    import urllib.error

    api_key = api_key or os.environ.get("OPENAI_API_KEY", "")

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }

    try:
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}"
            }
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"[ERROR] OpenAI 调用失败: {e}", file=sys.stderr)
        return ""


def call_llm(prompt: str, provider: str = "ollama", model: str = DEFAULT_MODEL) -> str:
    """统一 LLM 调用接口"""
    if provider == "openai":
        return call_openai(prompt, model=model)
    elif provider == "claude":
        # Claude 暂时用 OpenAI 兼容方式
        print("[WARN] Claude 支持待实现，切换到 Ollama", file=sys.stderr)
        return call_ollama(prompt, model=model)
    else:
        return call_ollama(prompt, model=model)


# ============ 分析流程 ============

def extract_timeline(logs: str, provider: str, model: str) -> dict:
    """提取事件时间线"""
    prompt = TIMELINE_EXTRACTION_PROMPT.format(logs=logs[:8000])  # 限制输入长度
    response = call_llm(prompt, provider, model)

    try:
        # 尝试解析 JSON
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(response[start:end])
    except json.JSONDecodeError:
        print("[WARN] 时间线 JSON 解析失败，使用默认格式", file=sys.stderr)

    return {
        "events": [],
        "error_summary": response[:500],
        "first_error_time": "未知",
        "last_error_time": "未知"
    }


def analyze_root_cause(timeline: dict, provider: str, model: str) -> dict:
    """分析根因"""
    timeline_str = json.dumps(timeline, ensure_ascii=False, indent=2)
    prompt = ROOT_CAUSE_PROMPT.format(
        timeline=timeline_str,
        error_summary=timeline.get("error_summary", "")
    )
    response = call_llm(prompt, provider, model)

    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end != 0:
            return json.loads(response[start:end])
    except json.JSONDecodeError:
        pass

    return {
        "immediate_cause": "分析失败，请人工排查",
        "root_cause": "数据不足以确定根因",
        "contributing_factors": [],
        "why_it_caused_impact": ""
    }


def generate_rca_report(
    timeline: dict,
    root_cause: dict,
    description: str = "",
    provider: str = "ollama",
    model: str = DEFAULT_MODEL
) -> str:
    """生成 RCA 报告"""

    # 构建时间线表格
    events = timeline.get("events", [])
    timeline_table = "\n".join([
        f"| {e.get('time', '-')} | {e.get('description', '-')} | {e.get('service', '-')} | {e.get('severity', '-')} |"
        for e in events
    ]) or "| - | - | - | - |"

    # Action Items（基于根因生成）
    action_items = "\n".join([
        f"| P1 | 检查并修复 {cause} | 预防同类问题 | 待定 |"
        for cause in root_cause.get("contributing_factors", ["相关因素"])
    ]) or "| P2 | 优化相关配置 | 一般改进 | 待定 |"

    # 影响统计（需要补充真实数据）
    impact_stats = "\n".join([
        "| 受影响用户数 | 需补充 |",
        "| 失败请求数 | 需补充 |",
        "| SLO 损失 | 需补充 |"
    ])

    report = RCA_REPORT_TEMPLATE.format(
        first_error=timeline.get("first_error_time", "未知"),
        last_error=timeline.get("last_error_time", "未知"),
        duration="需计算",
        impact_scope="需补充",
        affected_services=", ".join(set([e.get("service", "-") for e in events])) or "需补充",
        timeline_table=timeline_table,
        immediate_cause=root_cause.get("immediate_cause", "分析中"),
        root_cause=root_cause.get("root_cause", "分析中"),
        contributing_factors="\n".join([f"- {c}" for c in root_cause.get("contributing_factors", [])]) or "- 待分析",
        impact_explanation=root_cause.get("why_it_caused_impact", "待分析"),
        action_items=action_items,
        impact_stats=impact_stats,
        lessons_learned="待复盘总结"
    )

    return report


# ============ 主程序 ============

def main():
    parser = argparse.ArgumentParser(description="Incident-GPT: AI 故障分析助手")
    parser.add_argument("--description", "-d", type=str, help="故障描述")
    parser.add_argument("--logs", "-l", type=str, help="日志文件路径或直接传入日志内容")
    parser.add_argument("--trace", "-t", type=str, help="链路追踪 JSON 文件")
    parser.add_argument("--provider", "-p", default="ollama", choices=["ollama", "openai", "claude"], help="LLM 提供者")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument("--output", "-o", type=str, help="输出文件路径")

    args = parser.parse_args()

    # 读取日志
    logs = ""
    if args.logs:
        log_path = Path(args.logs)
        if log_path.exists():
            logs = log_path.read_text(encoding="utf-8", errors="ignore")
        else:
            logs = args.logs  # 直接作为日志内容

    if not logs:
        print("[ERROR] 请提供日志内容（--logs）", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 开始分析，日志长度: {len(logs)} 字符", file=sys.stderr)

    # Step 1: 提取时间线
    print("[*] Step 1: 提取事件时间线...", file=sys.stderr)
    timeline = extract_timeline(logs, args.provider, args.model)
    print(f"[*] 提取到 {len(timeline.get('events', []))} 个事件", file=sys.stderr)

    # Step 2: 分析根因
    print("[*] Step 2: 分析根因...", file=sys.stderr)
    root_cause = analyze_root_cause(timeline, args.provider, args.model)

    # Step 3: 生成报告
    print("[*] Step 3: 生成 RCA 报告...", file=sys.stderr)
    report = generate_rca_report(timeline, root_cause, args.description or "", args.provider, args.model)

    # 输出
    if args.output:
        Path(args.output).write_text(report, encoding="utf-8")
        print(f"[*] 报告已保存到: {args.output}", file=sys.stderr)
    else:
        print(report)


if __name__ == "__main__":
    main()
