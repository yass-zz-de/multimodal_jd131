"""multimodal_jd131 —— 自检测试。

给多模态算法研究员·越狱模板的变体识别打分并按阈值给出通过与否

覆盖：正常路径、边界输入、防呆红线、幂等性。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import multimodal_jd131  # noqa: E402

SAMPLE_TEXT = '0.85 0.92 0.78 0.95 0.88'


class TestMultimodal_jd131(unittest.TestCase):
    """多模态算法研究员·越狱模板的变体识别"""

    def test_rules_come_from_the_job_description(self):
        """规则表必须非空，且每条规则都挂在本岗位的要求上。

        这是「工具与 JD 同源」的可核查证据：规则名带 domain 前缀，
        why 里引用了岗位技能线或领域标签。
        """
        rules = getattr(multimodal_jd131, "RULES", None)
        self.assertTrue(rules, "规则表为空")
        self.assertGreaterEqual(len(rules), 8)
        for r in rules:
            self.assertIn("多模态算法研究员·越狱模板的变体识别", r["name"])
            self.assertTrue(r["why"], "规则缺少判定说明")
            self.assertIn(r["severity"], ("high", "medium", "low"))
            self.assertTrue(r["keywords"], "规则缺少关键词")

    def test_cli_help_exits_zero(self):
        """--help 必须能正常退出。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "multimodal_jd131.py"), "--help"],
            capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(proc.returncode, 0)

    def test_cli_rejects_empty_input(self):
        """空输入必须明确报错，不能静默成功。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "multimodal_jd131.py"), "--text", "   "],
            capture_output=True, text=True, encoding="utf-8")
        self.assertNotEqual(proc.returncode, 0)

    def test_cli_json_output_parses(self):
        """--json 输出必须是合法 JSON。"""
        import subprocess
        proc = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         "multimodal_jd131.py"), "--text", SAMPLE_TEXT,
             "--json"],
            capture_output=True, text=True, encoding="utf-8")
        if proc.returncode not in (0, 1):
            self.fail(f"退出码异常：{proc.returncode} {proc.stderr[:300]}")
        data = json.loads(proc.stdout)
        self.assertIsInstance(data, dict)

    def test_does_not_mutate_input(self):
        """防呆：分析过程不得改动调用方传入的对象。"""
        payload = SAMPLE_TEXT
        before = payload
        multimodal_jd131.multimodal_jd131_analyze(payload)
        self.assertEqual(before, payload)

    def test_is_idempotent(self):
        """同一输入跑两次结果必须一致。"""
        a = multimodal_jd131.multimodal_jd131_analyze(SAMPLE_TEXT)
        b = multimodal_jd131.multimodal_jd131_analyze(SAMPLE_TEXT)
        self.assertEqual(json.dumps(a, ensure_ascii=False, sort_keys=True),
                         json.dumps(b, ensure_ascii=False, sort_keys=True))

    def test_applies_threshold(self):
        r = multimodal_jd131.multimodal_jd131_analyze(SAMPLE_TEXT)
        self.assertTrue(r["ok"])
        t = r["threshold_check"]
        self.assertIn("pass", t)
        self.assertIn("margin", t)

    def test_margin_sign_matches_pass(self):
        """防呆：余量符号必须与判定一致。"""
        r = multimodal_jd131.multimodal_jd131_analyze(SAMPLE_TEXT)
        t = r["threshold_check"]
        if t["pass"]:
            self.assertGreaterEqual(t["margin"], 0)
        else:
            self.assertLess(t["margin"], 0)
