"""Materialize a Chinese, LaTeX-preserving review for M7 OPC mapping batch 001.

Translation is presentation-only. The immutable English candidate remains the
source of record. Translations are cached so the review artifact rebuilds
without repeatedly calling the translation endpoint.
"""

from __future__ import annotations

import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data/benchmarks/m7/opc_250_v0_1"
OUT = ROOT / "human_review/m7_opc_250_v0_1"
CACHE = OUT / "translation_cache_zh.json"
ERROR_TYPE_ZH = {
    "false_generalization": "错误推广",
    "proof_gap": "证明缺口",
    "missing_assumption": "缺少前提",
    "unsupported_external_dependency": "依赖未说明的外部结论",
    "wrong_conclusion": "结论错误",
    "invalid_inference": "推理无效",
    "other": "其他",
}


def translate(text: str, cache: dict[str, str]) -> str:
    source = text.strip()
    key = "protected-v3|" + source
    if not source:
        return ""
    if key in cache:
        return cache[key]
    protected: list[str] = []
    def lock(match: re.Match) -> str:
        protected.append(match.group(0))
        return f"<span class=\"notranslate\">ZXQ{len(protected) - 1}QXZ</span>"
    marked = re.sub(r"\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|\$[^$]*\$", lock, source)
    marked = re.sub(r"\b(?!ZXQ)[A-Z](?:[A-Z0-9_]|_[a-zA-Z0-9]+)*\b", lock, marked)
    query = urllib.parse.urlencode({"client": "gtx", "sl": "en", "tl": "zh-CN", "dt": "t", "format": "html", "q": marked})
    url = "https://translate.googleapis.com/translate_a/single?" + query
    for attempt in range(5):
        try:
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = json.loads(response.read())
            result = ("".join(part[0] for part in payload[0] if part[0])
                      if payload and payload[0] else marked)
            result = re.sub(r"</?span[^>]*>", "", result)
            for index, value in enumerate(protected):
                result = result.replace(f"ZXQ{index}QXZ", value)
            cache[key] = result
            CACHE.write_text(json.dumps(cache, ensure_ascii=False, indent=2) + "\n")
            return result
        except Exception:
            if attempt == 4:
                raise
            time.sleep(2 ** attempt)
    raise AssertionError("unreachable")


def chunks(text: str, limit: int = 3500) -> list[str]:
    paragraphs = re.split(r"\n\s*\n", text)
    result: list[str] = []
    current = ""
    for paragraph in paragraphs:
        parts = [paragraph[i:i + limit] for i in range(0, len(paragraph), limit)] or [""]
        for part in parts:
            candidate = (current + "\n\n" + part).strip()
            if current and len(candidate) > limit:
                result.append(current)
                current = part
            else:
                current = candidate
    if current:
        result.append(current)
    return result


def verbalize(text: str) -> str:
    replacements = [
        (r"\\xrightarrow\s*\[[^]]*\]\s*\{[^}]*\}", " 趋向于 "),
        (r"\\rightarrow|\\to", " 趋向于 "), (r"\\infty", "无穷大"),
        (r"\\leq|\\le", " 小于或等于 "), (r"\\geq|\\ge", " 大于或等于 "),
        (r"\\neq", " 不等于 "), (r"\\approx", " 约等于 "),
        (r"\\cdot|\\times", " 乘 "), (r"\\div", " 除以 "),
        (r"\\parallel", " 平行于 "), (r"\\perp", " 垂直于 "),
        (r"\\cap", " 与……相交 "), (r"\\angle", "角"),
        (r"\\sum", "求和"), (r"\\lim", "极限"), (r"\\log", "对数"),
        (r"\\(?:tfrac|dfrac|frac)\s*\{([^{}]+)\}\s*\{([^{}]+)\}", r"（\1 除以 \2）"),
        (r"\\Longrightarrow|\\Rightarrow|\\implies", " 因此 "),
        (r"\\Gamma", "伽马圆"), (r"\\Delta", "德尔塔"), (r"\\theta", "西塔"),
        (r"\\gamma", "伽马"), (r"\\ell", "直线 l"), (r"\\vec", "向量"),
        (r"\\binom\{([^{}]+)\}\{([^{}]+)\}", r"组合数（\1 取 \2）"),
    ]
    for pattern, value in replacements:
        text = re.sub(pattern, value, text)
    text = text.replace("+", " 加 ").replace("−", " 减 ")
    text = re.sub(r"(?<=\s)-(?=\s|\d)", " 减 ", text)
    text = text.replace("=", " 等于 ").replace("<", " 小于 ").replace(">", " 大于 ")
    text = text.replace("\\[", "").replace("\\]", "").replace("\\(", "").replace("\\)", "")
    text = re.sub(r"\\(?:,|;|!)(?!\w)", " ", text)
    text = re.sub(r"\\(?:quad|qquad|displaystyle|textstyle|left|right|bigl|bigr|mathrm|text|boxed|tag)\b", " ", text)
    text = re.sub(r"\\begin\{[^}]+\}|\\end\{[^}]+\}", " ", text)
    text = text.replace("\\\\", "；").replace("\\", "")
    text = text.replace("^", " 的幂 ").replace("_", " 下标 ")
    text = text.replace("$", "").replace("{", "").replace("}", "")
    text = re.sub(r"[ \t]+", " ", text)
    return text.strip()


def translated_long(text: str, cache: dict[str, str]) -> str:
    text = re.sub(r"(?m)^\s*[-–—]{5,}\s*$", "", text)
    return "\n\n".join(translate(part, cache).strip() for part in chunks(text))


def quoted_node(node_id: str, text: str, *, highlighted: bool = False) -> list[str]:
    """Keep each proof node visually bounded without breaking display math."""
    body = text.strip()
    if re.fullmatch(r"[-–—\s]+", body):
        body = "（段落分隔）"
    label = f"**{node_id}**"
    if highlighted:
        label += "　⬅️ **候选首错节点**"
    return [f"> {label}", ">"] + [f"> {line}" if line else ">" for line in body.splitlines()]


def main() -> None:
    review = json.loads((OUT / "mapping_review_batch_001.json").read_text())
    candidates = {row["case_id"]: row for row in map(json.loads, (BASE / "candidate.jsonl").read_text().splitlines())}
    annotations = {row["case_id"]: row for row in json.loads((BASE / "node_annotations.json").read_text())["rows"]}
    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    lines = ["# M7 OPC-250 节点映射人工复核：中文 LaTeX 版（25 题）", "",
             "> 自然语言为便于审查的中文机器翻译；所有数学变量和公式保留源数据的 LaTeX。英文原始数据保持不变，节点编号与正式数据一一对应。", "",
             "每题请同时检查：判错理由是否成立、首错节点是否准确、修改方向是否合理。填写 `确认`，或填写 `纠正：首错节点……；错误类型……；修改方向……`。", ""]
    for number, item in enumerate(review["rows"], 1):
        case_id = item["case_id"]
        candidate = candidates[case_id]
        annotation = annotations[case_id]
        print(f"[{number}/25] translating {case_id}", flush=True)
        problem_zh = translated_long(candidate["problem"], cache)
        reason_zh = translate(item["error_description"], cache).strip()
        proposed = item["proposed_first_error_node"] or "尚未自动定位（请在完整证明中指出）"
        direction = f"从节点 {proposed} 开始，改正下述问题，并重新检查依赖该步骤的后续结论：{reason_zh}"
        error_type = item["proposed_error_type"]
        error_type_display = f"{ERROR_TYPE_ZH.get(error_type, error_type)}（`{error_type}`）"
        lines += [f"## 第 {number} 题｜{case_id}", "",
                  "### 审查摘要", "",
                  "| 项目 | 内容 |", "|---|---|",
                  f"| 建议首错节点 | **{proposed}** |",
                  f"| 建议错误类型 | {error_type_display} |",
                  f"| 判错理由 | {reason_zh} |",
                  f"| 修改方向 | {direction} |", "",
                  "### 原题（中文释义）", "", f"> {problem_zh.replace(chr(10), chr(10) + '> ')}", "",
                  "<details>", "<summary><strong>展开完整原证明（已按节点编号）</strong></summary>", ""]
        for node in annotation["proof_nodes"]:
            node_zh = translated_long(node["text"], cache)
            lines += quoted_node(node["node_id"], node_zh,
                                 highlighted=node["node_id"] == item["proposed_first_error_node"]) + [""]
        lines += ["</details>", "", "### 你的复核", "",
                  "- 同意上述判断：`确认`",
                  "- 不同意：`纠正：首错节点……；错误类型……；修改方向……`", "", "---", ""]
    (OUT / "mapping_review_batch_001_zh.md").write_text("\n".join(lines) + "\n")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"translation failed: {exc}", file=sys.stderr)
        raise
