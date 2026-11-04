#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
maimemo_sync.py - MaiMemo (墨墨背单词) Sync Engine for Kaoyan Asset Consolidator

Tailored specifically for pushing misspelled words directly to today's review stream:
  1. Filters exclusively for user spelling mistakes (type == 'spelling_fix' or misspelling specified)
  2. Resolves vocabulary IDs via POST /vocabulary/query (with lemma fallback)
  3. Generates deep "borrowed-shell" spelling correction mnemonics via POST /notes (type: '语法')
  4. Pushes words directly into today's review stream via POST /study/add_words (advance: true)
  5. Strictly zero notepad creation (/notepads) and zero phrase creation (/phrases)
"""

import os
import sys
import json
import time
import re
import argparse
import urllib.request
import urllib.error
from pathlib import Path

# Force UTF-8 stdout/stderr on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

MAIMEMO_BASE_URL = "https://open.maimemo.com/open/api/v1"

# 官方频控契约：20 次/10 秒、40 次/60 秒、2000 次/5 小时
RATE_LIMITS = ((20, 10.0), (40, 60.0), (2000, 5 * 3600.0))
MIN_CALL_GAP = 0.5  # 20 次/10 秒 ⇒ 平均 0.5 秒一次，留出安全余量

MINIS_WORKSPACE_CANDIDATES = [
    Path("/var/minis/workspace/kaoyan"),
    Path("/var/minis/workspace"),
    Path.cwd(),
    Path(__file__).resolve().parent.parent,
]

def resolve_workspace_file(file_path_str: str) -> Path:
    """智能解析沙盒文件路径，支持绝对路径与相对工作区路径"""
    if not file_path_str:
        return None
    p = Path(file_path_str).expanduser()
    if p.is_absolute() and p.exists():
        return p
    if p.exists():
        return p.resolve()
    file_name = p.name
    for d in MINIS_WORKSPACE_CANDIDATES:
        cand = d / file_path_str
        if cand.exists():
            return cand.resolve()
        cand_name = d / file_name
        if cand_name.exists():
            return cand_name.resolve()
    return p.resolve() if not p.is_absolute() else p


def format_mnemonic_note(word_data: dict) -> str:
    """
    Format 'borrowed-shell' writing mnemonic note for spelling correction.
    Includes spelling fix explanation, kaoyan writing usage, and syntax breakdown.
    """
    parts = []

    mis = word_data.get("misspelling", "初稿拼写")
    correct = word_data.get("spelling", "")
    parts.append(f"【初稿纠偏】：初稿误拼为 {mis}，正确拼写为 {correct}（考场务必防范拼写扣分）！")

    usage = word_data.get("usage_note", "").strip()
    if usage:
        parts.append(f"【考研写作用法】：{usage}")

    grammar = word_data.get("grammar_note", "").strip()
    if grammar:
        parts.append(f"【原句语法剖析】：{grammar}")

    if len(parts) == 1:
        parts.append("【考研写作实战】：收录于考研英语二外脑内化真题高分范文核心表达。")

    return "\n".join(parts)


def get_lemma_candidates(word: str) -> list:
    """Generate canonical lemma candidates for inflected words (plurals, past tense, gerunds)."""
    w = word.strip().lower()
    cands = []
    if w.endswith("ies") and len(w) > 3:
        cands.append(w[:-3] + "y")
    elif w.endswith("es") and len(w) > 3:
        cands.extend([w[:-2], w[:-1]])
    elif w.endswith("s") and not w.endswith("ss") and len(w) > 2:
        cands.append(w[:-1])
    elif w.endswith("ed") and len(w) > 3:
        if w.endswith("ied") and len(w) > 4:
            cands.append(w[:-3] + "y")
        cands.extend([w[:-1], w[:-2]])
        if len(w) > 4 and w[-3] == w[-4]:
            cands.append(w[:-3])
    elif w.endswith("ing") and len(w) > 4:
        cands.extend([w[:-3], w[:-3] + "e"])
        if len(w) > 5 and w[-4] == w[-5]:
            cands.append(w[:-4])
    seen = set()
    res = []
    for c in cands:
        if c and c != w and c not in seen:
            seen.add(c)
            res.append(c)
    return res


class MaimemoClient:
    """
    Lightweight, self-contained MaiMemo API Client with zero third-party dependencies.
    """
    def __init__(self, token: str = None, base_url: str = MAIMEMO_BASE_URL, mock: bool = False, dry_run: bool = False):
        self.token = token if token is not None else os.environ.get("MAIMEMO_SPELLING_TOKEN", "")
        self.base_url = base_url.rstrip("/")
        self.mock = mock
        self.dry_run = dry_run
        self.last_req_time = 0.0
        self._call_times = []

    def _throttle(self):
        """滑动窗口限流：严格执行 20 次/10 秒、40 次/60 秒、2000 次/5 小时。"""
        now = time.time()
        five_hours = 5 * 3600.0
        self._call_times = [t for t in self._call_times if now - t < five_hours]
        for limit, window in RATE_LIMITS:
            while True:
                recent = [t for t in self._call_times if now - t < window]
                if len(recent) < limit:
                    break
                sleep_for = window - (now - min(recent)) + 0.05
                time.sleep(max(0.05, sleep_for))
                now = time.time()
        if self._call_times and now - self._call_times[-1] < MIN_CALL_GAP:
            time.sleep(MIN_CALL_GAP - (now - self._call_times[-1]))
            now = time.time()
        self._call_times.append(now)
        self.last_req_time = now

    def request(self, method: str, path: str, body: dict = None) -> dict:
        """Execute HTTP request against MaiMemo Open API"""
        if self.mock:
            return self._mock_response(method, path, body)

        if not self.token:
            raise ValueError(
                "MAIMEMO_SPELLING_TOKEN 未设置！错词复习推送需连接【背单词拼写专用账号】。\n"
                "请配置环境变量 MAIMEMO_SPELLING_TOKEN 或通过 --token 传入。\n"
                "获取方式：使用拼写背单词账号登录墨墨背单词 App → 设置 → 开放 API 或打开 https://open.maimemo.com/open/api/v1/tokens/openapi 复制 Token。"
            )

        if self.dry_run and method != "GET":
            return {"status": "dry_run_success", "mock": True}

        self._throttle()
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "KaoyanAssetConsolidator/1.0"
        }
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                resp_bytes = resp.read()
                if not resp_bytes:
                    return {}
                return json.loads(resp_bytes.decode("utf-8"))
        except urllib.error.HTTPError as e:
            error_body = ""
            try:
                error_body = e.read().decode("utf-8")
            except Exception:
                pass

            # Rate limit backoff
            if e.code == 429:
                time.sleep(2.0)
                try:
                    with urllib.request.urlopen(req, timeout=15) as resp:
                        return json.loads(resp.read().decode("utf-8"))
                except Exception:
                    pass

            raise RuntimeError(f"MaiMemo API 请求失败 [{e.code}]: {error_body or e.reason}")
        except urllib.error.URLError as e:
            raise RuntimeError(f"MaiMemo API 网络连接失败: {e.reason}")

    @staticmethod
    def _unwrap_data(resp: dict) -> dict:
        """Unwrap 'data' payload from MaiMemo Open API response if present."""
        if isinstance(resp, dict) and "data" in resp and isinstance(resp["data"], dict):
            return resp["data"]
        return resp

    def _mock_response(self, method: str, path: str, body: dict = None) -> dict:
        """Provide deterministic mock responses for offline unit tests"""
        if path == "/vocabulary/query":
            spellings = (body or {}).get("spellings", [])
            voc_list = [{"id": f"voc_mock_{w}", "spelling": w} for w in spellings]
            return {"success": True, "data": {"voc": voc_list}, "errors": []}
        elif path == "/notes" and method == "POST":
            return {"success": True, "data": {"id": "nt_mock_1", "note": {"id": "nt_mock_1", **(body.get("note", {}))}}, "errors": []}
        elif path == "/study/add_words" and method == "POST":
            words = (body or {}).get("words", [])
            return {"success": True, "data": {"added_count": len(words)}, "errors": []}
        return {"success": True, "data": {}, "errors": []}

    def query_vocabulary_ids(self, spellings: list) -> dict:
        """Batch query voc_id for a list of spellings with automatic lemmatization fallback.
        Returns mapping of spelling.lower() -> voc_id.
        """
        if not spellings:
            return {}
        clean_spellings = list({s.strip() for s in spellings if s.strip()})
        resp = self.request("POST", "/vocabulary/query", {"spellings": clean_spellings})
        data = self._unwrap_data(resp)
        voc_items = data.get("voc", [])
        mapping = {item["spelling"].lower(): item["id"] for item in voc_items if "spelling" in item and "id" in item}

        # Check for unmatched words and attempt lemmatization fallback
        unmatched = [s for s in clean_spellings if s.lower() not in mapping]
        if unmatched:
            lemma_map = {}
            fallback_queries = []
            for u in unmatched:
                cands = get_lemma_candidates(u)
                for cand in cands:
                    if cand not in lemma_map:
                        lemma_map[cand] = u.lower()
                    fallback_queries.append(cand)
            if fallback_queries:
                fb_resp = self.request("POST", "/vocabulary/query", {"spellings": list(set(fallback_queries))})
                fb_data = self._unwrap_data(fb_resp)
                for item in fb_data.get("voc", []):
                    sp_lower = item.get("spelling", "").lower()
                    if sp_lower in lemma_map:
                        orig = lemma_map[sp_lower]
                        if orig not in mapping:
                            mapping[orig] = item["id"]
                    mapping[sp_lower] = item["id"]

        return mapping

    def create_mnemonic_note(self, voc_id: str, note_text: str) -> dict:
        """Create mnemonic note with note_type: '语法'."""
        body = {
            "note": {
                "voc_id": voc_id,
                "note_type": "语法",
                "note": note_text
            }
        }
        return self.request("POST", "/notes", body)

    def add_to_today_review(self, voc_ids: list, advance: bool = True) -> dict:
        """Add words to study plan and advance to immediate review."""
        if not voc_ids:
            return {"added_count": 0}
        body = {
            "words": [{"id": vid} for vid in voc_ids],
            "advance": advance
        }
        resp = self.request("POST", "/study/add_words", body)
        data = self._unwrap_data(resp)
        return data if isinstance(data, dict) else {"added_count": len(voc_ids)}


def sync_essay_vocabulary(payload: dict, token: str = None, mock: bool = False, dry_run: bool = False, **_kwargs) -> dict:
    """
    Main orchestration function to push user misspelled words to today's review stream.

    Per strict user instruction:
      - ONLY words with spelling mistakes (type == 'spelling_fix' or misspelling specified) are processed.
      - NO notepad creation or updating (/notepads is completely skipped).
      - NO phrase creation (/phrases is completely skipped).
      - Creates deep 'borrowed-shell' spelling correction mnemonic notes (/notes).
      - Pushes words directly into today's immediate review stream (/study/add_words with advance: true).
    """
    if isinstance(payload, dict) and "maimemo" in payload and isinstance(payload["maimemo"], dict):
        sub = dict(payload["maimemo"])
        if "task_id" not in sub and "task_id" in payload:
            sub["task_id"] = payload["task_id"]
        payload = sub

    raw_words = payload.get("words", []) if isinstance(payload, dict) else []
    if not raw_words:
        return {"status": "skipped", "message": "待同步单词列表为空，已跳过。"}

    # 1. 严格过滤：仅收录初稿拼写错误的单词
    spelling_fixes = []
    seen = set()
    for w in raw_words:
        sp = str(w.get("spelling", "")).strip()
        mis = str(w.get("misspelling", "")).strip()
        is_spelling_fix = w.get("type") == "spelling_fix" or bool(mis)
        if is_spelling_fix and sp and sp.lower() not in seen:
            seen.add(sp.lower())
            spelling_fixes.append(w)

    if not spelling_fixes:
        return {
            "status": "skipped",
            "message": "本次作答无拼写错误单词，无需推送至墨墨复习流。",
            "synced_words": []
        }

    client = MaimemoClient(token=token, mock=mock, dry_run=dry_run)

    # 2. 批量解析 voc_id
    spellings = [w.get("spelling", "").strip() for w in spelling_fixes]
    voc_map = client.query_vocabulary_ids(spellings)

    matched_words = []
    skipped_words = []
    for w in spelling_fixes:
        sp = w.get("spelling", "").strip()
        vid = voc_map.get(sp.lower())
        if vid:
            matched_words.append({**w, "voc_id": vid})
        else:
            skipped_words.append(sp)

    if not matched_words:
        return {
            "status": "partial_failed",
            "message": f"所选拼错单词均未能匹配到墨墨官方词库 ID：{', '.join(skipped_words)}",
            "skipped_words": skipped_words
        }

    # 3. 创建专属纠偏语法助记 (POST /notes)
    note_count = 0
    note_failures = []
    for w in matched_words:
        vid = w["voc_id"]
        spelling = w["spelling"]
        note_text = format_mnemonic_note(w)
        try:
            client.create_mnemonic_note(vid, note_text)
            note_count += 1
        except Exception as e:
            note_failures.append(f"{spelling}: {e}")

    # 4. 推入今日复习流 (POST /study/add_words with advance: true)
    vids = [w["voc_id"] for w in matched_words]
    study_res = client.add_to_today_review(vids, advance=True)

    status = "success"
    message = "拼写错误单词已成功推入今日复习流并生成纠偏助记"
    if note_failures:
        status = "partial_failed"
        message = f"助记创建失败 {len(note_failures)} 条"

    return {
        "status": status,
        "message": message,
        "synced_words": [w["spelling"] for w in matched_words],
        "misspellings": [w.get("misspelling", "") for w in matched_words if w.get("misspelling")],
        "skipped_words": skipped_words,
        "notes_created": note_count,
        "notes_failed": len(note_failures),
        "study_advance": True,
        "added_count": study_res.get("added_count", len(vids)),
        "remote_side_effects": {
            "review_pushed": bool(vids),
        },
    }


def main():
    parser = argparse.ArgumentParser(description="MaiMemo Spelling Mistake Review Pusher for Kaoyan Asset Consolidator")
    parser.add_argument("--file", type=str, default=None, help="Path to JSON payload file")
    parser.add_argument("--data", type=str, default=None, help="Raw JSON payload string")
    parser.add_argument("--token", type=str, default=None, help="MaiMemo API token (默认为环境变量 MAIMEMO_SPELLING_TOKEN)")
    parser.add_argument("--dry-run", action="store_true", help="Dry run without modifying remote MaiMemo data")
    parser.add_argument("--mock", action="store_true", help="Mock API responses for offline tests")
    parser.add_argument("--example", action="store_true", help="Print payload template and exit")
    parser.add_argument("--json", action="store_true", help="Output result as pure JSON")

    args = parser.parse_args()

    if args.example:
        example_payload = {
            "task_id": "A1.01",
            "words": [
                {
                    "spelling": "accommodate",
                    "type": "spelling_fix",
                    "misspelling": "acommodate",
                    "sentence": "The library is expected to prolong opening hours to accommodate students.",
                    "translation": "图书馆预计将延长开放时间以方便/容纳学生。",
                    "usage_note": "考研高频及物动词，常接 students / needs，表示‘迎合、容纳、迁就’，写作中可完美替换普通的 meet 或 help。",
                    "grammar_note": "主干为 The library is expected to prolong opening hours；不定式短语 to accommodate students 作后置目的状语。"
                }
            ]
        }
        print(json.dumps(example_payload, indent=2, ensure_ascii=False))
        return

    payload = None
    if args.data:
        try:
            payload = json.loads(args.data)
        except Exception as e:
            print(f"[ERROR] 解析 --data JSON 失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.file:
        target_file = resolve_workspace_file(args.file)
        if not target_file or not target_file.exists():
            print(f"[ERROR] 指定文件不存在: {args.file} (探测路径: {target_file})", file=sys.stderr)
            sys.exit(1)
        with open(target_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        parser.error("必须通过 --file 或 --data 指定 JSON 载荷，或使用 --example 查看样例")

    try:
        res = sync_essay_vocabulary(payload, token=args.token, mock=args.mock, dry_run=args.dry_run)
        if res.get("status") in ("partial_failed", "error"):
            if args.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(f"[ERROR] 墨墨推送失败: {res.get('message')}", file=sys.stderr)
                if res.get("skipped_words"):
                    print(f"未匹配跳过: {', '.join(res.get('skipped_words', []))}", file=sys.stderr)
            sys.exit(1)
        elif res.get("status") == "skipped":
            if args.json:
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(f"[INFO] {res.get('message')}")
            return
        elif args.json:
            print(json.dumps(res, ensure_ascii=False, indent=2))
        else:
            print("=== 墨墨背单词错词复习推送完成 ===")
            synced = res.get("synced_words", [])
            mis = res.get("misspellings", [])
            for s, m in zip(synced, mis):
                print(f"推入复习: {s} (初稿误拼: {m})")
            print(f"生成纠偏助记: {res.get('notes_created')} 条")
            if res.get('skipped_words'):
                print(f"未匹配跳过: {', '.join(res.get('skipped_words', []))}")
            print("今日复习流: 已直接注入 (advance=True)")
    except Exception as e:
        err_msg = str(e)
        if args.json:
            print(json.dumps({"status": "error", "message": err_msg}, ensure_ascii=False))
        else:
            print(f"推送失败: {err_msg}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
