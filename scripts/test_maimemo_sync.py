#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_maimemo_sync.py - Unit Tests for MaiMemo (墨墨背单词) Review Pusher in Kaoyan Asset Consolidator
"""

import unittest
import os
import sys
import json
import tempfile
from pathlib import Path

# Ensure scripts dir is on sys.path
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import maimemo_sync as ms
from maimemo_sync import (
    format_mnemonic_note,
    get_lemma_candidates,
    MaimemoClient,
    sync_essay_vocabulary,
)


class TestMnemonicFormatting(unittest.TestCase):
    def test_spelling_fix_format(self):
        data = {
            "spelling": "accommodate",
            "type": "spelling_fix",
            "misspelling": "acommodate",
            "usage_note": "常接 students 表示容纳与迎合",
            "grammar_note": "不定式作目的状语"
        }
        note = format_mnemonic_note(data)
        self.assertIn("【初稿纠偏】：初稿误拼为 acommodate，正确拼写为 accommodate", note)
        self.assertIn("【考研写作用法】：常接 students 表示容纳与迎合", note)
        self.assertIn("【原句语法剖析】：不定式作目的状语", note)


class TestMaimemoSyncPipeline(unittest.TestCase):
    def test_sync_mock_spelling_fix_only(self):
        """只推送拼写错误的单词，不建词本，推入今日复习。"""
        payload = {
            "task_id": "A1.01",
            "words": [
                {
                    "spelling": "accommodate",
                    "type": "spelling_fix",
                    "misspelling": "acommodate",
                    "sentence": "The library is expected to prolong opening hours to accommodate students.",
                    "translation": "图书馆预计将延长开放时间以方便学生。",
                    "usage_note": "考研高频动词，替换 meet",
                    "grammar_note": "不定式短语作目的状语"
                },
                {
                    "spelling": "prolong",
                    "type": "advanced_vocab",  # Not a spelling fix!
                    "sentence": "The library is expected to prolong opening hours to accommodate students.",
                    "translation": "图书馆预计将延长开放时间以方便学生。",
                    "usage_note": "书面严谨，替换 lengthen",
                    "grammar_note": "核心不定式动词"
                }
            ]
        }
        res = sync_essay_vocabulary(payload, mock=True)
        self.assertEqual(res["status"], "success")
        # prolong should be ignored; only accommodate should be pushed
        self.assertEqual(res["synced_words"], ["accommodate"])
        self.assertEqual(res["notes_created"], 1)
        self.assertTrue(res["study_advance"])
        self.assertEqual(res["added_count"], 1)
        self.assertNotIn("notepad", res)

    def test_empty_or_non_spelling_skipped(self):
        """若没有拼错词，则自动跳过推送。"""
        payload = {
            "task_id": "A1.01",
            "words": [
                {
                    "spelling": "prolong",
                    "type": "advanced_vocab",
                    "sentence": "Prolong hours."
                }
            ]
        }
        res = sync_essay_vocabulary(payload, mock=True)
        self.assertEqual(res["status"], "skipped")
        self.assertIn("无拼写错误", res["message"])

    def test_missing_token_error_in_real_mode(self):
        old_token = os.environ.pop("MAIMEMO_SPELLING_TOKEN", None)
        try:
            client = MaimemoClient(token="", mock=False)
            with self.assertRaises(ValueError) as ctx:
                client.request("GET", "/test")
            self.assertIn("MAIMEMO_SPELLING_TOKEN 未设置", str(ctx.exception))
        finally:
            if old_token is not None:
                os.environ["MAIMEMO_SPELLING_TOKEN"] = old_token

    def test_env_spelling_token_resolution(self):
        old_token = os.environ.get("MAIMEMO_SPELLING_TOKEN")
        try:
            os.environ["MAIMEMO_SPELLING_TOKEN"] = "test_spell_tok_12345"
            client = MaimemoClient(token=None, mock=True)
            self.assertEqual(client.token, "test_spell_tok_12345")
        finally:
            if old_token is not None:
                os.environ["MAIMEMO_SPELLING_TOKEN"] = old_token
            else:
                os.environ.pop("MAIMEMO_SPELLING_TOKEN", None)

    def test_maimemo_token_is_ignored_for_isolation(self):
        """确保写作/拼写 Skill 绝不读取 MAIMEMO_TOKEN（阅读账号专用），保证账号物理隔离。"""
        old_spell = os.environ.pop("MAIMEMO_SPELLING_TOKEN", None)
        old_read = os.environ.get("MAIMEMO_TOKEN")
        try:
            os.environ["MAIMEMO_TOKEN"] = "reading_account_token_should_not_leak"
            client = MaimemoClient(token=None, mock=True)
            self.assertEqual(client.token, "")
        finally:
            if old_spell is not None:
                os.environ["MAIMEMO_SPELLING_TOKEN"] = old_spell
            if old_read is not None:
                os.environ["MAIMEMO_TOKEN"] = old_read
            else:
                os.environ.pop("MAIMEMO_TOKEN", None)

    def test_duplicate_spellings_are_deduped(self):
        payload = {
            "words": [
                {"spelling": "express", "type": "spelling_fix", "misspelling": "expres"},
                {"spelling": "Express", "type": "spelling_fix", "misspelling": "expres"},
            ],
        }
        res = sync_essay_vocabulary(payload, mock=True)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["synced_words"], ["express"])
        self.assertEqual(res["notes_created"], 1)

    def test_vocabulary_lemmatization_fallback(self):
        """测试词形屈折（复数/过去式/进行时）自动回退到词根原型并命中。"""
        cands_ies = ms.get_lemma_candidates("necessities")
        self.assertIn("necessity", cands_ies)
        cands_s = ms.get_lemma_candidates("constraints")
        self.assertIn("constraint", cands_s)
        cands_ed = ms.get_lemma_candidates("dropped")
        self.assertIn("drop", cands_ed)
        cands_ing = ms.get_lemma_candidates("helping")
        self.assertIn("help", cands_ing)

        def mock_query_with_lemma(self_client, method, path, body=None):
            if path == "/vocabulary/query":
                spells = (body or {}).get("spellings", [])
                vocs = []
                for s in spells:
                    if s == "necessities":
                        continue
                    vocs.append({"id": f"voc_{s}", "spelling": s})
                return {"success": True, "errors": [], "data": {"voc": vocs}}
            return MaimemoClient._mock_response(self_client, method, path, body)

        orig_request = MaimemoClient.request
        MaimemoClient.request = mock_query_with_lemma
        try:
            client = MaimemoClient(token="dummy")
            mapping = client.query_vocabulary_ids(["necessities", "verge"])
            self.assertIn("necessities", mapping)
            self.assertEqual(mapping["necessities"], "voc_necessity")
            self.assertIn("verge", mapping)
        finally:
            MaimemoClient.request = orig_request


class TestDataUnwrapping(unittest.TestCase):
    def test_unwrap_data_nested(self):
        resp = {"success": True, "data": {"voc": [{"id": "1", "spelling": "test"}]}, "errors": []}
        unwrapped = MaimemoClient._unwrap_data(resp)
        self.assertEqual(unwrapped, {"voc": [{"id": "1", "spelling": "test"}]})

    def test_unwrap_data_flat(self):
        resp = {"voc": [{"id": "1", "spelling": "test"}]}
        unwrapped = MaimemoClient._unwrap_data(resp)
        self.assertEqual(unwrapped, {"voc": [{"id": "1", "spelling": "test"}]})

    def test_unwrap_data_non_dict(self):
        self.assertEqual(MaimemoClient._unwrap_data([]), [])
        self.assertEqual(MaimemoClient._unwrap_data(None), None)


if __name__ == "__main__":
    unittest.main()
