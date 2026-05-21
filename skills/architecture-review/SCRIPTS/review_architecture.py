#!/usr/bin/env python3
"""
Architecture Review - 架构预审助手
分析架构文档，评审稳定性/成本/扩展性，输出HTML报告
支持行业参考案例检索
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict

# ============ 配置 ============

DEFAULT_OLLAMA_URL = "http://127.0.0.1:11434"
DEFAULT_MODEL = "qwen3-vl:8b"
SCRIPT_DIR = Path(__file__).parent.resolve()
REFERENCE_DIR = SCRIPT_DIR.parent / "references"

# ============ 行业参考库 ============

def load_references(architecture_doc: str, scenario: str = "") -> tuple:
    """加载相关参考案例

    Returns:
        (references_text, references_list) - 参考文本和参考列表
    """
    if not REFERENCE_DIR.exists():
        return "", []

    keywords = extract_keywords(architecture_doc + " " + scenario)

    # 定义关键词到目录的映射
    keyword_map = {
        "大促": "电商/大促架构",
        "秒杀": "电商/大促架构",
        "双11": "电商/大促架构",
        "库存": "电商/库存系统",
        "防超卖": "电商/库存系统",
        "订单": "电商/订单系统",
        "支付": "支付/幂等设计",
        "幂等": "支付/幂等设计",
        "跨境": "支付/跨境支付",
        "退款": "支付/幂等设计",
        "优惠": "营销/优惠计算",
        "风控": "营销/活动风控",
        "金融": "金融/高可用架构",
        "高可用": "金融/高可用架构",
        "多活": "金融/高可用架构",
        "容灾": "金融/高可用架构",
        "分布式事务": "金融/高可用架构",
        "TCC": "金融/高可用架构",
    }

    # 找出匹配的目录
    matched_dirs = set()
    for kw, ref_dir in keyword_map.items():
        if kw in keywords:
            ref_path = REFERENCE_DIR / ref_dir
            if ref_path.exists():
                matched_dirs.add(ref_path)

    if not matched_dirs:
        # 如果没有精确匹配，搜索所有参考目录
        for ref_path in REFERENCE_DIR.rglob("*.md"):
            if ref_path.is_file():
                matched_dirs.add(ref_path.parent)

    # 加载匹配的参考文档
    references = []
    for ref_path in matched_dirs:
        if ref_path.is_file() and ref_path.suffix == ".md":
            # 单个文件
            try:
                content = ref_path.read_text(encoding="utf-8")
                front_matter = parse_front_matter(content)
                references.append({
                    "title": front_matter.get("title", ref_path.stem),
                    "domain": front_matter.get("domain", ""),
                    "company": front_matter.get("company", ""),
                    "path": str(ref_path.relative_to(REFERENCE_DIR)),
                    "content": extract_body(content)
                })
            except:
                pass
        elif ref_path.is_dir():
            # 目录下的所有md文件
            for md_file in ref_path.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    front_matter = parse_front_matter(content)
                    references.append({
                        "title": front_matter.get("title", md_file.stem),
                        "domain": front_matter.get("domain", ""),
                        "company": front_matter.get("company", ""),
                        "path": str(md_file.relative_to(REFERENCE_DIR)),
                        "content": extract_body(content)
                    })
                except:
                    pass

    # 去重并限制数量
    seen = set()
    unique_refs = []
    for ref in references:
        if ref["path"] not in seen:
            seen.add(ref["path"])
            unique_refs.append(ref)

    unique_refs = unique_refs[:5]  # 最多5个参考

    # 构建参考文本
    ref_text = ""
    ref_list = []
    for i, ref in enumerate(unique_refs, 1):
        ref_text += f"\n\n=== 参考案例 {i}: {ref['title']} ===\n"
        ref_text += f"领域: {ref['domain']} | 来源: {ref['company']}\n"
        ref_text += f"路径: {ref['path']}\n"
        ref_text += ref["content"][:2000]  # 限制每个参考的长度
        ref_list.append({
            "num": i,
            "title": ref["title"],
            "domain": ref["domain"],
            "company": ref["company"],
            "path": ref["path"]
        })

    return ref_text, ref_list


def extract_keywords(text: str) -> str:
    """提取关键词"""
    # 简单分词
    words = re.findall(r'[\w]+', text)
    return " ".join(words)


def parse_front_matter(content: str) -> dict:
    """解析 YAML front matter"""
    if content.startswith("---"):
        parts = content[3:].split("---", 1)
        if len(parts) >= 2:
            fm_text = parts[0].strip()
            result = {}
            for line in fm_text.split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    result[key.strip()] = val.strip()
            return result
    return {}


def extract_body(content: str) -> str:
    """提取正文（去掉 front matter）"""
    if content.startswith("---"):
        parts = content[3:].split("---", 1)
        if len(parts) >= 2:
            return parts[1].strip()
    return content.strip()

# ============ Prompt 模板 ============

REVIEW_PROMPT = """你是一个资深架构师，负责评审技术方案的稳定性、成本和扩展性。

## 业务场景
{scenario}

## 约束条件
{constraints}

## 架构文档
{architecture_doc}

## 评审重点
{review_focus}

{references}

请从以下三个维度进行评审：

### 1. 稳定性 (Stability)
- 可用性目标（SLA/SLO）
- 单点故障识别
- 降级方案
- 容灾设计
- 监控告警覆盖

### 2. 成本 (Cost)
- 基础设施成本预估
- 研发复杂度
- 运维成本
- 成本上限分析

### 3. 扩展性 (Scalability)
- 水平扩展能力
- 垂直扩展瓶颈
- 缩容能力
- 架构演进路径

请在评审时参考上述行业案例，并结合被评审方案的特点给出具体建议。

请以JSON格式输出评审结果：

{{
  "summary": "方案概览（一句话描述）",
  "stability_score": 85,
  "cost_score": 70,
  "scalability_score": 75,
  "overall_score": 77,
  "risks": [
    {{
      "level": "critical",
      "dimension": "stability",
      "title": "风险标题",
      "description": "风险描述",
      "suggestion": "具体建议"
    }}
  ],
  "strengths": [
    {{
      "dimension": "stability",
      "title": "优势标题",
      "description": "优势描述"
    }}
  ],
  "recommendations": [
    {{
      "priority": "P0",
      "dimension": "stability",
      "title": "建议标题",
      "description": "具体建议",
      "expected_impact": "预期效果"
    }}
  ],
  "alternatives": [
    {{
      "name": "方案B",
      "pros": "优势",
      "cons": "劣势",
      "suitable_for": "适用场景"
    }}
  ],
  "decision": "conditional",
  "decision_reason": "决策理由"
}}

注意：
- stability_score/cost_score/scalability_score 为0-100的数字评分
- overall_score 为加权平均 (stability*0.4 + cost*0.3 + scalability*0.3)
- decision 可选值：approve（有条件通过）/ conditional（需修改后通过）/ reject（不通过）
- risks.level 可选值：critical/warning/info
- 只输出JSON，不要其他内容
"""


# ============ HTML 报告模板 ============

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>架构预审报告 - {service_name}</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0d1117;
            color: #e6edf3;
            min-height: 100vh;
            padding: 24px;
        }}
        .container {{ max-width: 1100px; margin: 0 auto; }}
        .header {{
            background: linear-gradient(135deg, #1a1f35, #2d1b4e);
            border-radius: 16px;
            padding: 28px 32px;
            margin-bottom: 24px;
            border: 1px solid #30363d;
        }}
        .header h1 {{
            font-size: 1.6rem;
            margin-bottom: 8px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .header .meta {{
            color: #8b949e;
            font-size: 0.85rem;
            margin-top: 8px;
        }}
        .scores-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-top: 20px;
        }}
        .score-card {{
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 16px;
            text-align: center;
        }}
        .score-value {{
            font-size: 2.2rem;
            font-weight: 700;
            margin-bottom: 4px;
        }}
        .score-label {{
            font-size: 0.8rem;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .score-stability {{ color: #58a6ff; }}
        .score-cost {{ color: #f0883e; }}
        .score-scalability {{ color: #a371f7; }}
        .overall {{ color: #3fb950; }}

        .section {{
            background: #161b22;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 16px;
            border: 1px solid #30363d;
        }}
        .section-title {{
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 10px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        .badge-critical {{ background: #3d1d1d; color: #f85149; }}
        .badge-warning {{ background: #3d2d1d; color: #d29922; }}
        .badge-info {{ background: #1d2d3d; color: #58a6ff; }}
        .badge-approve {{ background: #1d3d1d; color: #3fb950; }}
        .badge-conditional {{ background: #3d3d1d; color: #d29922; }}
        .badge-reject {{ background: #3d1d1d; color: #f85149; }}

        .risk-list, .strength-list, .rec-list {{ list-style: none; }}
        .risk-item, .strength-item, .rec-item {{
            padding: 14px 16px;
            border-radius: 8px;
            margin-bottom: 10px;
            border-left: 3px solid;
        }}
        .risk-item {{ background: #1a1a2e; }}
        .risk-item.critical {{ border-color: #f85149; }}
        .risk-item.warning {{ border-color: #d29922; }}
        .risk-item.info {{ border-color: #58a6ff; }}
        .strength-item {{ background: #0d2416; border-color: #3fb950; margin-bottom: 8px; }}
        .rec-item {{ background: #1a1a2e; border-color: #a371f7; }}

        .risk-title, .strength-title, .rec-title {{
            font-weight: 600;
            margin-bottom: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .risk-desc, .strength-desc, .rec-desc {{
            font-size: 0.9rem;
            color: #8b949e;
            margin-bottom: 8px;
        }}
        .rec-suggestion, .strength-desc {{
            font-size: 0.85rem;
            color: #adbac7;
        }}
        .priority {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
            background: rgba(163,113,247,0.2);
            color: #a371f7;
        }}

        .summary-text {{
            background: #1a1f35;
            border-radius: 8px;
            padding: 16px 20px;
            color: #adbac7;
            line-height: 1.7;
            font-size: 0.95rem;
        }}

        .alternatives-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 12px;
        }}
        .alt-card {{
            background: #1a1a2e;
            border-radius: 8px;
            padding: 16px;
            border: 1px solid #30363d;
        }}

        .references-list {{ display: flex; flex-direction: column; gap: 10px; }}
        .ref-card {{ background: #1a1a2e; border-radius: 8px; padding: 14px 16px; border-left: 3px solid #58a6ff; }}
        .ref-title {{ font-weight: 600; margin-bottom: 4px; color: #e6edf3; }}
        .ref-meta {{ font-size: 0.8rem; color: #8b949e; margin-bottom: 6px; }}
        .ref-path {{ font-size: 0.75rem; color: #484f58; font-family: monospace; }}
        .alt-name {{
            font-weight: 600;
            margin-bottom: 8px;
            color: #e6edf3;
        }}
        .alt-pros {{ color: #3fb950; font-size: 0.85rem; margin-bottom: 4px; }}
        .alt-cons {{ color: #f85149; font-size: 0.85rem; margin-bottom: 4px; }}
        .alt-suitable {{ color: #8b949e; font-size: 0.8rem; margin-top: 8px; }}

        .decision-banner {{
            border-radius: 12px;
            padding: 24px;
            text-align: center;
            margin-bottom: 16px;
        }}
        .decision-banner.approve {{ background: linear-gradient(135deg, #0d2416, #1a3d1a); border: 1px solid #238636; }}
        .decision-banner.conditional {{ background: linear-gradient(135deg, #2d2410, #3d3010); border: 1px solid #9e6a03; }}
        .decision-banner.reject {{ background: linear-gradient(135deg, #2d1010, #3d1a1a); border: 1px solid #da3633; }}
        .decision-icon {{ font-size: 2.5rem; margin-bottom: 8px; }}
        .decision-text {{ font-size: 1.1rem; font-weight: 600; margin-bottom: 8px; }}
        .decision-reason {{ font-size: 0.9rem; color: #8b949e; max-width: 600px; margin: 0 auto; }}

        .footer {{
            text-align: center;
            color: #484f58;
            font-size: 0.8rem;
            margin-top: 24px;
            padding-top: 16px;
            border-top: 1px solid #21262d;
        }}

        @media (max-width: 600px) {{
            .scores-grid {{ grid-template-columns: 1fr; }}
            .alternatives-grid {{ grid-template-columns: 1fr; }}
        }}
    </style>
</head>
<body>
<div class="container">

    <div class="header">
        <h1>🏛️ 架构预审报告</h1>
        <div class="meta">Generated: {generated_at} &nbsp;|&nbsp; Review Dimensions: Stability / Cost / Scalability</div>
        <div class="scores-grid">
            <div class="score-card">
                <div class="score-value score-stability">{stability_score}</div>
                <div class="score-label">Stability</div>
            </div>
            <div class="score-card">
                <div class="score-value score-cost">{cost_score}</div>
                <div class="score-label">Cost</div>
            </div>
            <div class="score-card">
                <div class="score-value score-scalability">{scalability_score}</div>
                <div class="score-label">Scalability</div>
            </div>
        </div>
    </div>

    <div class="decision-banner {decision}">
        <div class="decision-icon">{decision_icon}</div>
        <div class="decision-text">{decision_text}</div>
        <div class="decision-reason">{decision_reason}</div>
    </div>

    <div class="section">
        <div class="section-title">📋 方案概览</div>
        <div class="summary-text">{summary}</div>
    </div>

    <div class="section">
        <div class="section-title">🔴 风险项 {risk_badge}</div>
        {risk_items}
    </div>

    <div class="section">
        <div class="section-title">✅ 优势确认</div>
        <ul class="strength-list">
        {strength_items}
        </ul>
    </div>

    <div class="section">
        <div class="section-title">💡 优化建议</div>
        <ul class="rec-list">
        {rec_items}
        </ul>
    </div>

    <div class="section">
        <div class="section-title">📊 备选方案对比</div>
        <div class="alternatives-grid">
        {alt_items}
        </div>
    </div>

    <div class="section">
        <div class="section-title">📚 参考案例</div>
        <div class="references-list">
        {ref_items}
        </div>
    </div>

    <div class="footer">
        由 Architecture Review Skill 自动生成 &nbsp;|&nbsp; 仅供参考，最终决策需结合业务实际情况
    </div>
</div>
</body>
</html>
"""


# ============ LLM 调用 ============

def call_ollama(prompt: str, model: str = DEFAULT_MODEL, url: str = DEFAULT_OLLAMA_URL) -> str:
    """调用本地 Ollama"""
    import urllib.request

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
        with urllib.request.urlopen(req, timeout=180) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result.get("response", "")
    except Exception as e:
        print(f"[ERROR] Ollama 调用失败: {e}", file=sys.stderr)
        return ""


# ============ 分析流程 ============

def review_architecture(
    architecture_doc: str,
    scenario: str = "",
    constraints: str = "",
    review_focus: str = "stability,cost,scalability",
    provider: str = "ollama",
    model: str = DEFAULT_MODEL
) -> dict:
    """调用AI进行架构评审"""

    # 加载相关参考案例
    ref_text, ref_list = load_references(architecture_doc, scenario)
    if ref_text:
        print(f"[*] 已加载 {len(ref_list)} 个相关参考案例", file=sys.stderr)
        ref_section = f"\n## 行业参考案例\n以下案例仅供参考，评审时请结合实际情况：\n{ref_text}"
    else:
        ref_section = "\n## 行业参考案例\n（未找到相关参考案例，请基于通用架构原则进行评审）"

    prompt = REVIEW_PROMPT.format(
        scenario=scenario or "未提供",
        constraints=constraints or "未提供",
        architecture_doc=architecture_doc[:6000],  # 限制长度
        review_focus=review_focus,
        references=ref_section
    )

    print("[*] AI 架构评审中...", file=sys.stderr)
    response = call_ollama(prompt, model)

    if not response:
        return {"error": "AI 调用失败，请检查 Ollama 是否运行"}

    # 解析 JSON
    try:
        start = response.find("{")
        end = response.rfind("}") + 1
        if start != -1 and end != 0:
            result = json.loads(response[start:end])
            result["references"] = ref_list
            return result
    except json.JSONDecodeError as e:
        print(f"[WARN] JSON 解析失败: {e}", file=sys.stderr)

    return {"error": "无法解析评审结果"}


def generate_html_report(review_result: dict, service_name: str = "方案") -> str:
    """生成 HTML 报告"""

    # 提取数据
    stability = review_result.get("stability_score", 0)
    cost = review_result.get("cost_score", 0)
    scalability = review_result.get("scalability_score", 0)
    summary = review_result.get("summary", "无")
    decision = review_result.get("decision", "conditional")
    decision_reason = review_result.get("decision_reason", "")

    # 风险项
    risks = review_result.get("risks", [])
    risk_items_html = ""
    critical_count = sum(1 for r in risks if r.get("level") == "critical")
    warning_count = sum(1 for r in risks if r.get("level") == "warning")

    if not risks:
        risk_items_html = '<li class="risk-item info"><div class="risk-title">未发现重大风险</div><div class="risk-desc">架构方案整体可控</div></li>'
    else:
        for r in risks:
            level = r.get("level", "info")
            badge = f'<span class="badge badge-{level}">{level.upper()}</span>'
            risk_items_html += f"""
            <li class="risk-item {level}">
                <div class="risk-title">{badge} {r.get('title', '')} <span style="color:#8b949e;font-weight:400;font-size:0.85rem">[{r.get('dimension', '')}]</span></div>
                <div class="risk-desc">{r.get('description', '')}</div>
                <div class="rec-suggestion">💡 {r.get('suggestion', '')}</div>
            </li>"""

    risk_badge = ""
    if critical_count > 0:
        risk_badge = f'<span class="badge badge-critical">{critical_count} Critical</span>'
    if warning_count > 0:
        risk_badge += f' <span class="badge badge-warning">{warning_count} Warning</span>'

    # 优势项
    strengths = review_result.get("strengths", [])
    strength_items_html = ""
    if not strengths:
        strength_items_html = '<li class="strength-item"><div class="strength-desc">暂无明显优势记录</div></li>'
    else:
        for s in strengths:
            strength_items_html += f"""
            <li class="strength-item">
                <div class="strength-title">✨ {s.get('title', '')} <span style="color:#8b949e;font-weight:400;font-size:0.8rem">[{s.get('dimension', '')}]</span></div>
                <div class="strength-desc">{s.get('description', '')}</div>
            </li>"""

    # 建议项
    recommendations = review_result.get("recommendations", [])
    rec_items_html = ""
    if not recommendations:
        rec_items_html = '<li class="rec-item"><div class="rec-desc">暂无优化建议</div></li>'
    else:
        for rec in recommendations:
            rec_items_html += f"""
            <li class="rec-item">
                <div class="rec-title"><span class="priority">{rec.get('priority', 'P1')}</span> {rec.get('title', '')}</div>
                <div class="rec-desc">{rec.get('description', '')}</div>
                <div class="rec-suggestion">📈 预期效果: {rec.get('expected_impact', '')}</div>
            </li>"""

    # 备选方案
    alternatives = review_result.get("alternatives", [])
    alt_items_html = ""
    if not alternatives:
        alt_items_html = '<div class="alt-card"><div class="alt-pros">暂无备选方案</div></div>'
    else:
        for alt in alternatives:
            alt_items_html += f"""
            <div class="alt-card">
                <div class="alt-name">📌 {alt.get('name', '')}</div>
                <div class="alt-pros">✅ {alt.get('pros', '')}</div>
                <div class="alt-cons">❌ {alt.get('cons', '')}</div>
                <div class="alt-suitable">🎯 适用: {alt.get('suitable_for', '')}</div>
            </div>"""

    # 决策
    decision_icon = {"approve": "✅", "conditional": "⚠️", "reject": "❌"}.get(decision, "⚠️")
    decision_text = {"approve": "推荐通过", "conditional": "需修改后通过", "reject": "建议否决"}.get(decision, "需评审")

    # 参考案例
    references = review_result.get("references", [])
    if references:
        ref_items_html = ""
        for ref in references:
            ref_items_html += f"""
            <div class="ref-card">
                <div class="ref-title">📚 {ref.get('title', '')}</div>
                <div class="ref-meta">{ref.get('domain', '')} | {ref.get('company', '')}</div>
                <div class="ref-path">{ref.get('path', '')}</div>
            </div>"""
    else:
        ref_items_html = '<div class="ref-card"><div class="ref-title">未找到相关参考案例</div></div>'

    return HTML_TEMPLATE.format(
        service_name=service_name,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M"),
        stability_score=stability,
        cost_score=cost,
        scalability_score=scalability,
        summary=summary,
        decision=decision,
        decision_icon=decision_icon,
        decision_text=decision_text,
        decision_reason=decision_reason,
        risk_badge=risk_badge,
        risk_items=risk_items_html,
        strength_items=strength_items_html,
        rec_items=rec_items_html,
        alt_items=alt_items_html,
        ref_items=ref_items_html,
    )


# ============ 主程序 ============

def main():
    parser = argparse.ArgumentParser(description="Architecture Review - 架构预审助手")
    parser.add_argument("--doc", "-d", type=str, help="架构文档文件路径 (.md/.txt)")
    parser.add_argument("--text", "-t", type=str, help="架构文档文本内容")
    parser.add_argument("--scenario", "-s", type=str, default="", help="业务场景")
    parser.add_argument("--constraints", "-c", type=str, default="", help="约束条件")
    parser.add_argument("--focus", "-f", type=str, default="stability,cost,scalability", help="评审维度")
    parser.add_argument("--provider", "-p", default="ollama", help="LLM提供者")
    parser.add_argument("--model", "-m", default=DEFAULT_MODEL, help="模型名称")
    parser.add_argument("--output", "-o", default="architecture_review.html", help="输出HTML文件路径")

    args = parser.parse_args()

    # 读取文档
    architecture_doc = ""
    if args.doc:
        path = Path(args.doc)
        if path.exists():
            architecture_doc = path.read_text(encoding="utf-8", errors="ignore")
        else:
            print(f"[ERROR] 文件不存在: {args.doc}", file=sys.stderr)
            sys.exit(1)
    elif args.text:
        architecture_doc = args.text
    else:
        print("[ERROR] 请提供架构文档（--doc 或 --text）", file=sys.stderr)
        sys.exit(1)

    if not architecture_doc:
        print("[ERROR] 文档内容为空", file=sys.stderr)
        sys.exit(1)

    print(f"[*] 文档长度: {len(architecture_doc)} 字符", file=sys.stderr)

    # 评审
    result = review_architecture(
        architecture_doc=architecture_doc,
        scenario=args.scenario,
        constraints=args.constraints,
        review_focus=args.focus,
        provider=args.provider,
        model=args.model
    )

    if "error" in result:
        print(f"[ERROR] {result['error']}", file=sys.stderr)
        sys.exit(1)

    # 生成报告
    service_name = Path(args.doc).stem if args.doc else "方案"
    html = generate_html_report(result, service_name)

    # 写入文件
    Path(args.output).write_text(html, encoding="utf-8")
    print(f"[*] 报告已生成: {args.output}", file=sys.stderr)


if __name__ == "__main__":
    main()
