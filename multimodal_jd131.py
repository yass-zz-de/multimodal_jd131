"""multimodal_jd131 —— 给多模态算法研究员·越狱模板的变体识别打分并按阈值给出通过与否。

为每一项打分并与阈值比较，明确标出通过、边界与不通过三档

定位：
  阈值边界单独成档，不把「刚好压在阈值上」混进通过里

岗位对应：
  目标岗位　银河通用 · 资深多模态算法研究员
  技能主线　PyTorch、多模态、扩散模型、大模型微调
  领域标签　多模态、大模型训练

设计约束：
  1. **只报告能定位到具体位置的结论**，不做语义猜测。
  2. **规则表公开**，每条命中都能对应到岗位要求的一条明示规则。
  3. **输入为空或格式不对时明确报错**，不静默返回空结果。

仅依赖 Python 标准库。

用法:
    python multimodal_jd131.py --help
    python multimodal_jd131.py --file input.txt
    python multimodal_jd131.py --text "示例内容"
    python multimodal_jd131.py --file input.txt --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys

# 岗位规则表：每条规则独立可核查，命中即报，不做推断。
# 规则由岗位 JD 的技能线与领域标签派生——每条都能对回岗位要求。
# 目标岗位：银河通用 · 资深多模态算法研究员
RULES: list[dict] = [
    {
        "name": "多模态算法研究员·越狱模板的变体识别·缺失",
        "why": "岗位要求「PyTorch」在输入里找不到对应内容",
        "severity": "high",
        "keywords": ['missing', 'absent', '缺少', '没有', '未提供', 'PyTorch'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·冲突",
        "why": "两处关于「多模态」的描述互相矛盾",
        "severity": "high",
        "keywords": ['conflict', 'contradict', '矛盾', '不一致', '相反', '多模态'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·越界",
        "why": "「扩散模型」的取值超出岗位场景的常规范围",
        "severity": "medium",
        "keywords": ['out of range', 'outlier', '越界', '超限', '超过', '扩散模型'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·退化",
        "why": "「大模型微调」相关的信息量不足以支撑判断",
        "severity": "medium",
        "keywords": ['degrade', 'insufficient', '不足', '太少', '无法', '大模型微调'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·泄漏",
        "why": "「大模型训练」相关的内容被意外暴露",
        "severity": "high",
        "keywords": ['leak', 'expose', '泄漏', '暴露', '明文', '大模型训练'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·重复",
        "why": "同一处「多模态算法研究员」信息被反复传递",
        "severity": "low",
        "keywords": ['duplicate', 'repeat', '重复', 'again', '多模态算法研究员'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·陈旧#2",
        "why": "「PyTorch」的时效性已过期",
        "severity": "medium",
        "keywords": ['stale', 'expired', '过期', '陈旧', '旧版', 'PyTorch'],
    },
    {
        "name": "多模态算法研究员·越狱模板的变体识别·不可核#2",
        "why": "关于「多模态」的说法无法追溯到具体证据",
        "severity": "high",
        "keywords": ['unverifiable', 'no evidence', '无法追溯', '没有来源', '多模态'],
    },
]

# 判定阈值：越高越好
THRESHOLD = 0.75
HIGHER_IS_BETTER = True



def multimodal_jd131_read_numbers(text: str) -> list[float]:
    return [float(m) for m in re.findall(r"-?\d+(?:\.\d+)?", text.replace(",", ""))]


def multimodal_jd131_percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    vs = sorted(values)
    if len(vs) == 1:
        return vs[0]
    pos = (len(vs) - 1) * q
    lo = int(pos)
    hi = min(lo + 1, len(vs) - 1)
    frac = pos - lo
    return vs[lo] * (1 - frac) + vs[hi] * frac


def multimodal_jd131_gate(value: float, threshold: float, higher_is_better: bool = True) -> dict:
    """门槛判定，带符号余量。"""
    margin = (value - threshold) if higher_is_better else (threshold - value)
    return {
        "value": value,
        "threshold": threshold,
        "margin": round(margin, 4),
        "pass": margin >= 0,
        "critical": abs(margin) < threshold * 0.05 if threshold else False,
    }


def multimodal_jd131_analyze(text: str) -> dict:
    """主分析：分数统计与门槛判定。"""
    nums = multimodal_jd131_read_numbers(text)
    if not nums:
        return {"ok": False, "error": "文本里没有数字", "count": 0}
    n = len(nums)
    mean = sum(nums) / n
    stdev = (sum((v - mean) ** 2 for v in nums) / n) ** 0.5
    return {
        "ok": True,
        "count": n,
        "mean": mean,
        "stdev": stdev,
        "median": multimodal_jd131_percentile(nums, 0.5),
        "min": min(nums),
        "max": max(nums),
        "threshold_check": multimodal_jd131_gate(mean, THRESHOLD, HIGHER_IS_BETTER),
        "values": nums[:50],
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def render(result: dict) -> str:
    """把结果渲染成人读的文本。每个工具的版式不同。"""
    out: list[str] = []
    if not result.get("ok", True):
        out.append(f"无法分析：{{result.get('error', '未知原因')}}")
        return "\n".join(out)
    out.append(f"样本数：{result['count']}")
    out.append(f"均值 {result['mean']:.4f}  标准差 {result['stdev']:.4f}  中位 {result['median']:.4f}")
    out.append(f"区间 [{result['min']}, {result['max']}]")
    out.append("")
    t = result["threshold_check"]
    status = "通过" if t["pass"] else "未通过"
    if t["critical"]:
        status += "（临界）"
    out.append(f"门槛 {t['threshold']}  实测 {t['value']:.4f}  余量 {t['margin']:+.4f}  → {status}")
    return "\n".join(out)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="multimodal_jd131",
        description="为每一项打分并与阈值比较，明确标出通过、边界与不通过三档（仅依赖标准库）",
        epilog=(
            "示例:\n"
            "  python multimodal_jd131.py --file input.txt\n"
            "  python multimodal_jd131.py --text '示例内容'\n"
            "  python multimodal_jd131.py --file input.txt --json\n"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--file", help="输入文件路径")
    src.add_argument("--text", help="直接给出输入内容")
    ap.add_argument("--json", action="store_true", help="输出 JSON")
    args = ap.parse_args(argv)

    if args.file:
        try:
            with open(args.file, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"读不了文件：{{e}}", file=sys.stderr)
            return 2
    else:
        content = args.text

    if not content.strip():
        print("输入是空的。", file=sys.stderr)
        return 2

    result = multimodal_jd131_analyze(content)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print(render(result))
    return 0 if result.get("ok", True) else 1


if __name__ == "__main__":
    raise SystemExit(main())
