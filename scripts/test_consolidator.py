#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单元测试与功能验证套件 (Unit Tests for Consolidator Engine)
"""

import unittest
import tempfile
import shutil
import json
import sys
import subprocess
from pathlib import Path

# Add scripts directory to sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from consolidator import (
    BrainRepository,
    DashboardManager,
    resolve_asset_dir,
    resolve_review_dir,
    resolve_workspace_file,
    get_theme_items,
    ERROR_CATEGORY_MAP
)

class TestConsolidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.review_dir = Path(self.test_dir) / "review_records"
        self.asset_dir = resolve_asset_dir()
        self.repo = BrainRepository(self.asset_dir)
        self.dash_mgr = DashboardManager(self.review_dir, self.asset_dir)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_repo_loading(self):
        summary = self.repo.get_summary()
        self.assertEqual(summary["morphemes_count"], 128)
        self.assertEqual(summary["task1_expressions_count"], 35)
        self.assertEqual(summary["task2_expressions_count"], 26)
        self.assertEqual(summary["task1_archives_count"], 11)
        self.assertEqual(summary["task2_archives_count"], 8)

    def test_dashboard_initialization(self):
        status = self.dash_mgr.read_status()
        self.assertEqual(status["total_completed"], 0)
        self.assertEqual(status["checked_items"], 0)
        self.assertGreater(status["remaining_items"], 40)
        self.assertTrue(len(status["weak_points"]) >= 3)
        self.assertIn("尚未开始", status["current_state"])

    def test_record_practice_result_success(self):
        res = self.dash_mgr.record_practice_result(
            theme="A1",
            item_id="A1.01",
            coordinate="大作文 > 第一段：图表数据定格描述 > 动态柱状图显著增长对比",
            source="T2010-E2-CHART / T2_GEN_STR_001",
            chinese="正如柱状图清晰所示，发展中国家的手机用户数量大幅激增，而发达国家则保持平稳。",
            student_answer="As is clearly show in chart, mobile users in developing countries increase sharp, while those in developed country stayed stable.",
            tags="#主谓不一致,#可数单数裸奔,#时态错位",
            diagnosis="1. As is clearly show 应为 shown (过去分词)；2. increase 应使用一般过去时 increased 且需用副词 sharply 修饰；3. developed country 可数单数裸奔，需加复数 countries。",
            baseline="As is clearly shown in the chart, the number of mobile phone users in developing countries increased sharply from 2000 to 2008, while that in developed countries remained stable.",
            master_version="As is distinctly illustrated in the chart, mobile-phone subscriptions in developing countries surged dramatically from about 0.4 billion in 2000 to nearly 4 billion in 2008, while those in developed countries experienced a rather slow increase and stayed at about 1 billion.",
            current_state="完成【主题 A1】第 1 题（动态柱状图显著增长对比句），已订正通过。",
            next_step="推进【主题 A1】第 2 题：饼图绝对优势占比定格句 (T2_PIE_STR_001)。"
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["entry_index"], 1)

        # Verify progress_dashboard.md
        status = self.dash_mgr.read_status()
        self.assertEqual(status["total_completed"], 1)
        self.assertEqual(status["checked_items"], 1)
        self.assertIn("完成【主题 A1】第 1 题", status["current_state"])
        self.assertIn("饼图绝对优势占比定格句", status["next_step"])

        # Verify grammar_error_notebook.md
        note_text = self.dash_mgr.notebook_file.read_text(encoding="utf-8")
        self.assertIn("题目流水账 #001", note_text)
        self.assertIn("#主谓不一致", note_text)
        self.assertIn("1 次", note_text)

    def test_record_with_maimemo_spelling_fix(self):
        """测试在记录实战结果的同时附带墨墨错词推送状态。"""
        maimemo_info = {
            "status": "success",
            "synced_words": ["accommodate"],
            "misspellings": ["acommodate"],
            "notes_created": 1,
            "study_advance": True,
        }
        res = self.dash_mgr.record_practice_result(
            theme="A1",
            item_id="A1.01",
            coordinate="大作文 > 第一段",
            source="T2_GEN_STR_001",
            chinese="图书馆延长时间以容纳学生。",
            student_answer="The library is expected to acommodate students.",
            tags="#拼写错误",
            diagnosis="acommodate 拼写错误，双 c 双 m",
            baseline="The library is expected to accommodate students.",
            master_version="The library is expected to accommodate students.",
            maimemo_info=maimemo_info,
        )
        self.assertEqual(res["status"], "success")
        self.assertIn("maimemo_sync", res)
        self.assertEqual(res["maimemo_sync"]["synced_words"], ["accommodate"])

        # Verify markdown card contains MaiMemo sync line
        note_text = self.dash_mgr.notebook_file.read_text(encoding="utf-8")
        self.assertIn("墨墨背单词错词复习", note_text)
        self.assertIn("accommodate", note_text)

    def test_theme_items_coverage(self):
        for theme in ["A1", "A2", "A3", "A4", "B1", "B2", "B3", "B4"]:
            items = get_theme_items(self.repo, theme)
            self.assertGreater(len(items), 0, f"Theme {theme} should have items")

    def test_cli_doctor_mock(self):
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "consolidator.py"),
            "doctor",
            "--mock",
            "--json"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(result.stdout)
        self.assertIn("brain_assets", data)
        self.assertIn("review_records", data)
        self.assertIn("maimemo_credentials", data)
        self.assertIn("sandbox_compliance", data)
        self.assertEqual(data["sandbox_compliance"]["short_lived_process_model"]["status"], "PASS")
        self.assertEqual(data["sandbox_compliance"]["file_persistence_flow"]["status"], "PASS")
        self.assertEqual(data["maimemo_credentials"]["vocabulary_endpoint"]["status"], "PASS")

    def test_cli_record_via_file(self):
        """测试通过 --file 传入结算 JSON 文件进行落盘持久化与墨墨联动。"""
        settle_data = {
            "theme": "A1",
            "item_id": "A1.02",
            "coordinate": "大作文 > 第一段：图表数据定格描述 > 饼图绝对优势占比定格句",
            "source": "T2_PIE_STR_001",
            "chinese": "饼图清晰显示，自主品牌占据绝大部分市场份额。",
            "student_answer": "As is show in pie chart, domestic brand occupy the lion's share.",
            "tags": ["#主谓不一致", "#可数单数裸奔", "#缺失谓语"],
            "diagnosis": "1. show 应为 shown；2. brand 可数单数裸奔；3. occupy 应为 occupies 或过去时 occupied。",
            "baseline": "As is clearly shown in the pie chart, domestic brands occupy the lion's share.",
            "master_version": "According to the pie chart, domestic automobile brands occupy the lion's share of the market.",
            "current_state": "完成【主题 A1】第 2 题，已订正通过。",
            "next_step": "推进【主题 A1】第 3 题：多主体时间跨度走势句。",
            "misspelled_words": "occupi:occupy"
        }
        settle_file = Path(self.test_dir) / "settle.json"
        settle_file.write_text(json.dumps(settle_data, ensure_ascii=False, indent=2), encoding="utf-8")

        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "consolidator.py"),
            "record",
            "--review-dir", str(self.review_dir),
            "--file", str(settle_file),
            "--mock"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["item_id"], "A1.02")
        self.assertIn("maimemo_sync", data)
        self.assertEqual(data["maimemo_sync"]["status"], "success")
        self.assertEqual(data["maimemo_sync"]["synced_words"], ["occupy"])

        # 检查看板中对应 checkbox 是否打勾
        dash_text = (self.review_dir / "progress_dashboard.md").read_text(encoding="utf-8")
        self.assertIn("- [x] A1.02", dash_text)

    def test_resolve_workspace_file_resolution(self):
        # 1. 绝对路径已存在
        test_file = Path(self.test_dir) / "test_payload.json"
        test_file.write_text("{}", encoding="utf-8")
        resolved = resolve_workspace_file(str(test_file))
        self.assertEqual(resolved, test_file)

        # 2. None 或空字符串
        self.assertIsNone(resolve_workspace_file(None))
        self.assertIsNone(resolve_workspace_file(""))

    def test_cli_record_with_misspelled_words_mock(self):
        cmd = [
            sys.executable,
            str(SCRIPT_DIR / "consolidator.py"),
            "record",
            "--review-dir", str(self.review_dir),
            "--theme", "A1",
            "--item-id", "A1.01",
            "--coordinate", "大作文 > 第一段",
            "--source", "T2_GEN_STR_001",
            "--chinese", "图书馆延长时间以容纳学生。",
            "--student-answer", "The library is expected to acommodate students.",
            "--tags", "#拼写错误",
            "--diagnosis", "acommodate 拼写错误",
            "--master-version", "The library accommodates students.",
            "--misspelled-words", "acommodate:accommodate",
            "--mock"
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(result.stdout)
        self.assertEqual(data["status"], "success")
        self.assertIn("maimemo_sync", data)
        self.assertEqual(data["maimemo_sync"]["status"], "success")
        self.assertEqual(data["maimemo_sync"]["synced_words"], ["accommodate"])

    def test_get_exercise_cli(self):
        # Test by item-id
        cmd = [sys.executable, str(SCRIPT_DIR / "consolidator.py"), "get-exercise", "--item-id", "A1.01"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertIn("动态柱状图显著增长对比", res.stdout)
        self.assertIn("T2_GEN_STR_001", res.stdout)
        self.assertNotIn("保底版", res.stdout)

        # Test by theme and index
        cmd = [sys.executable, str(SCRIPT_DIR / "consolidator.py"), "get-exercise", "--theme", "A1", "--index", "2", "--json"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["item_id"], "A1.02")
        self.assertEqual(data["source_id"], "T2_CHART_SEN_014")

    def test_prepare_image_cli(self):
        from PIL import Image
        t_img = Path(self.test_dir) / "sample_hw.jpg"
        Image.new("RGB", (120, 240), color="white").save(t_img)

        cmd = [sys.executable, str(SCRIPT_DIR / "consolidator.py"), "prepare-image", "--image", str(t_img), "--rotate", "90"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        data = json.loads(res.stdout)
        self.assertEqual(data["status"], "success")
        self.assertTrue(Path(data["processed_path"]).exists())
        self.assertEqual(data["size"], [240, 120])

    def test_record_pending_revision_and_catchup_queue(self):
        """测试冲刺模式下将题目挂起进入待回补错题队列。"""
        res = self.dash_mgr.record_practice_result(
            theme="A1",
            item_id="A1.01",
            coordinate="大作文 > 第一段：图表数据定格描述 > 动态柱状图显著增长对比",
            source="T2_GEN_STR_001",
            chinese="正如柱状图清晰所示，手机用户激增。",
            student_answer="As is show, mobile user increase.",
            tags="#数据单位错位,#可数单数裸奔",
            diagnosis="1. show应为shown；2. 单位换算失真",
            master_version="As is distinctly illustrated in the chart, mobile-phone subscriptions surged.",
            status="pending_revision",
            current_state="完成 A1.01 初稿，学员选择冲刺下一题，挂起待回补。",
            next_step="推进 A1.02 饼图极值定格句。"
        )
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["revision_status"], "pending_revision")

        # Verify catch_up_queue in read_status
        status = self.dash_mgr.read_status()
        self.assertEqual(len(status["catch_up_queue"]), 1)
        self.assertEqual(status["catch_up_queue"][0]["item_id"], "A1.01")
        self.assertEqual(status["catch_up_queue"][0]["status"], "待回补")

        # Verify notebook card has [待回补] and NO baseline
        note_text = self.dash_mgr.notebook_file.read_text(encoding="utf-8")
        self.assertIn("[待回补]", note_text)
        self.assertNotIn("降维保底版", note_text)
        self.assertIn("外脑高级版原文", note_text)

    def test_zero_emoji_enforcement(self):
        import re
        emoji_pattern = re.compile(r"[\U00010000-\U0010ffff]|[\u2600-\u27bf]")

        # 1. get-exercise output
        cmd = [sys.executable, str(SCRIPT_DIR / "consolidator.py"), "get-exercise", "--item-id", "A1.01"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(len(emoji_pattern.findall(res.stdout)), 0)

        # 2. doctor output
        cmd = [sys.executable, str(SCRIPT_DIR / "consolidator.py"), "doctor", "--mock"]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        self.assertEqual(len(emoji_pattern.findall(res.stdout)), 0)


if __name__ == "__main__":
    unittest.main()
