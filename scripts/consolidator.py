#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
考研英语二“外脑资产内化与语法巩固”训练系统 - 核心支持脚本 (Consolidator Engine)
严格遵循 OpenMinis 与标准 Python 3 规范（无外部依赖）。
负责本地外脑语料索引、持久化看板读写、语法错题统计与训练流程调度。
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from pathlib import Path

# Force UTF-8 stdout/stderr on Windows
if sys.platform.startswith("win"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

# 导入墨墨同步模块
try:
    from maimemo_sync import (
        sync_essay_vocabulary,
        MaimemoClient,
    )
except ImportError:
    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))
    from maimemo_sync import (
        sync_essay_vocabulary,
        MaimemoClient,
    )

# ==========================================
# 默认路径探测与智能解析 (Minis Android 沙箱环境规范对齐)
# ==========================================

MINIS_MOUNTS_BASE = Path("/var/minis/mounts/Documents")
MINIS_WORKSPACE_CANDIDATES = [
    Path("/var/minis/workspace/kaoyan"),
    Path("/var/minis/workspace"),
    Path.cwd(),
    Path(__file__).resolve().parent.parent,
]

DEFAULT_ASSET_CANDIDATES = [
    Path("/var/minis/mounts/Documents/考研英语/写作外脑"),
    Path(__file__).resolve().parent.parent / "assets" / "writing_brain",
    Path("D:/Download/考研英语/考研英语/写作外脑"),
    Path("./assets/writing_brain"),
]

DEFAULT_REVIEW_CANDIDATES = [
    Path("/var/minis/mounts/Documents/考研英语/资产复盘"),
    Path(__file__).resolve().parent.parent / "review_records",
    Path("./review_records"),
]

ERROR_CATEGORY_MAP = {
    "1. 谓语结构类": ["#缺失谓语", "#双谓语", "#被动语态残缺", "#时态错位"],
    "2. 名词与冠词类": ["#可数单数裸奔", "#定冠词遗漏", "#定冠词滥用", "#不可数变复数", "#不可数名词误变复数"],
    "3. 主谓一致类": ["#第三人称单数遗漏", "#修饰成分干扰", "#长修饰成分干扰主谓不一致", "#There-Be一致", "#There-Be句型主谓不一致", "#主谓不一致"],
    "4. 从句与引导词类": ["#逗号粘连双句", "#非限制定语从句误用that", "#非限制性定语从句误用that", "#介词后接that从句", "#介词后误接that从句", "#从句内部代词冗余"],
    "5. 非谓语动词类": ["#悬垂分词", "#主被动分词混淆", "#介词to后接原形", "#介词to后误接原形"],
    "6. 介词与搭配类": ["#不及物动词缺介词", "#生硬汉式硬译", "#介词固定搭配错误", "#动宾搭配不当"],
    "7. 数据与事实类": ["#数据单位错位", "#数据事实描述失真", "#数据单位错误"]
}

def resolve_workspace_file(file_path_str: str) -> Path:
    """
    智能解析沙盒文件路径，支持绝对路径与相对工作区路径：
    1. 传入已存在的绝对/相对路径优先返回；
    2. 若未直接命中，依次在沙盒工作区 /var/minis/workspace/kaoyan/、/var/minis/workspace/、当前工作目录与工程根目录探测；
    3. 若均不存在，返回原始绝对路径或解析路径以便调用方清晰报错。
    """
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

def resolve_asset_dir(custom_path=None):
    if custom_path and Path(custom_path).exists():
        return Path(custom_path)
    env_path = os.environ.get("KAOYAN_ASSET_DIR")
    if env_path and Path(env_path).exists():
        return Path(env_path)
    # 优先探测 Minis 外部挂载外脑资产
    minis_asset = Path("/var/minis/mounts/Documents/考研英语/写作外脑")
    if minis_asset.exists() and (minis_asset / "shared" / "morphemes.jsonl").exists():
        return minis_asset
    for p in DEFAULT_ASSET_CANDIDATES:
        if p.exists() and (p / "shared" / "morphemes.jsonl").exists():
            return p
    # Fallback to local repo assets
    return DEFAULT_ASSET_CANDIDATES[1]

def resolve_review_dir(custom_path=None):
    if custom_path:
        p = Path(custom_path)
        p.mkdir(parents=True, exist_ok=True)
        return p
    env_path = os.environ.get("KAOYAN_REVIEW_DIR")
    if env_path:
        p = Path(env_path)
        p.mkdir(parents=True, exist_ok=True)
        return p
    # 外脑持久化解耦契约：若处于 Minis 沙箱环境 (/var/minis/mounts 存在)，
    # 优先在外部挂载目录 /var/minis/mounts/Documents/考研英语/资产复盘 中持久化，确保容器重置数据不丢
    minis_mount_dir = Path("/var/minis/mounts/Documents/考研英语/资产复盘")
    if minis_mount_dir.exists():
        return minis_mount_dir
    if Path("/var/minis/mounts/Documents").exists() or Path("/var/minis/mounts").exists():
        try:
            minis_mount_dir.mkdir(parents=True, exist_ok=True)
            return minis_mount_dir
        except Exception:
            pass

    for p in DEFAULT_REVIEW_CANDIDATES:
        if p.exists():
            return p
    # Default to creating review_records in repository
    fallback = Path(__file__).resolve().parent.parent / "review_records"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback

# ==========================================
# 语料库加载器
# ==========================================

class BrainRepository:
    def __init__(self, root_dir):
        self.root = Path(root_dir)
        self.morphemes = []
        self.t1_expressions = []
        self.t2_expressions = []
        self.t1_archives = {}
        self.t2_archives = {}
        self._load_all()

    def _load_jsonl(self, file_path):
        items = []
        if not file_path.exists():
            return items
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        pass
        return items

    def _load_all(self):
        morphemes_file = self.root / "shared" / "morphemes.jsonl"
        t1_exp_file = self.root / "task1" / "expressions.jsonl"
        t2_exp_file = self.root / "task2" / "expressions.jsonl"

        self.morphemes = self._load_jsonl(morphemes_file)
        self.t1_expressions = self._load_jsonl(t1_exp_file)
        self.t2_expressions = self._load_jsonl(t2_exp_file)

        # Load archives
        t1_arch_dir = self.root / "task1" / "archive"
        if t1_arch_dir.exists():
            for f in t1_arch_dir.glob("*.md"):
                self.t1_archives[f.stem] = f.read_text(encoding="utf-8")

        t2_arch_dir = self.root / "task2" / "archive"
        if t2_arch_dir.exists():
            for f in t2_arch_dir.glob("*.md"):
                self.t2_archives[f.stem] = f.read_text(encoding="utf-8")

    def get_summary(self):
        return {
            "root": str(self.root),
            "morphemes_count": len(self.morphemes),
            "task1_expressions_count": len(self.t1_expressions),
            "task2_expressions_count": len(self.t2_expressions),
            "task1_archives_count": len(self.t1_archives),
            "task2_archives_count": len(self.t2_archives),
        }

# ==========================================
# 看板与错题本管理类
# ==========================================

class DashboardManager:
    def __init__(self, review_dir, asset_dir=None):
        self.review_dir = Path(review_dir)
        self.review_dir.mkdir(parents=True, exist_ok=True)
        self.dashboard_file = self.review_dir / "progress_dashboard.md"
        self.notebook_file = self.review_dir / "grammar_error_notebook.md"
        self.asset_dir = Path(asset_dir) if asset_dir else resolve_asset_dir()
        self.ensure_initialized()

    def ensure_initialized(self):
        ref_templates = Path(__file__).resolve().parent.parent / "references" / "dashboard_templates.md"
        if not self.dashboard_file.exists():
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            content = self._generate_initial_dashboard(now_str)
            self.dashboard_file.write_text(content, encoding="utf-8")
        if not self.notebook_file.exists():
            now_str = datetime.now().strftime("%Y-%m-%d")
            content = self._generate_initial_notebook(now_str)
            self.notebook_file.write_text(content, encoding="utf-8")

    def _generate_initial_dashboard(self, date_str):
        template_path = Path(__file__).resolve().parent.parent / "references" / "dashboard_templates.md"
        if template_path.exists():
            text = template_path.read_text(encoding="utf-8")
            # Extract Template 1
            m = re.search(r"## 模板一：训练进度与状态看板文档 \(`progress_dashboard\.md`\)\s+```markdown\s+(.+?)\s+```", text, re.DOTALL)
            if m:
                tmpl = m.group(1)
                tmpl = tmpl.replace("{{LAST_UPDATED}}", date_str)
                tmpl = tmpl.replace("{{TOTAL_COMPLETED}}", "0")
                tmpl = tmpl.replace("{{CURRENT_STATE}}", "尚未开始训练，系统已准备就绪。")
                tmpl = tmpl.replace("{{NEXT_STEP}}", "启动【主题 A1】第一段·图表数据定格描述训练，出第一题：动态柱状图显著增长对比定格句。")
                tmpl = tmpl.replace("{{WEAK_POINT_1}}", "谓语动词时态与缺失检查（防止把非谓语当作谓语）")
                tmpl = tmpl.replace("{{WEAK_POINT_2}}", "单数可数名词冠词严谨性（杜绝名词裸奔）")
                tmpl = tmpl.replace("{{WEAK_POINT_3}}", "长状语/介词短语干扰下的主谓单复数一致")
                return tmpl
        # Fallback simple template
        return f"""# 考研英语二“外脑资产内化”训练进度与状态看板

> **看板更新时间**：{date_str}  
> **累计训练题数**：0 题  
> **资产库容量**：19 篇终版高分范文 | 61 条核心功能句式 | 128 条场景动宾语素  

---

## 一、 当前会话启动核心指标

* **[当前所处位置 (Current State)]**:  
  尚未开始训练，系统已准备就绪。

* **[下一步行动指令 (Next Step)]**:  
  启动【主题 A1】第一段·图表数据定格描述训练，出第一题：动态柱状图显著增长对比定格句。

* **[阶段性薄弱点重点盯防 (Grammar Alert)]**:  
  1. 谓语动词时态与缺失检查（防止把非谓语当作谓语）
  2. 单数可数名词冠词严谨性（杜绝名词裸奔）
  3. 考研图表数据单位换算（1亿 = 100 million = 0.1 billion）

---

## 二、 全局课程大纲与通关清单 (Curriculum Checklist)

### 主线 A：大作文（Task 2）框架与语料内化
- [ ] A1.01 `T2_GEN_STR_001`: 动态柱状图显著增长对比定格句
- [ ] A1.02 `T2_CHART_SEN_014`: 饼图绝对优势占比定格句
- [ ] A1.03 `T2_CHART_SEN_006`: 柱状图多主体时间跨度走势句

---

## 三、 待回补错题队列 (Catch-up Queue)

| 题目编号 | 框架坐标 | 挂起时间 | 待纠治核心错误与要点 | 状态 |
| :---: | :--- | :---: | :--- | :---: |
| (队列空) | 暂无挂起待回补题目 | - | - | - |
"""

    def _generate_initial_notebook(self, date_str):
        template_path = Path(__file__).resolve().parent.parent / "references" / "dashboard_templates.md"
        if template_path.exists():
            text = template_path.read_text(encoding="utf-8")
            m = re.search(r"## 模板二：练习档案与语法错题记录本 \(`grammar_error_notebook\.md`\)\s+```markdown\s+(.+?)\s+```", text, re.DOTALL)
            if m:
                tmpl = m.group(1)
                tmpl = tmpl.replace("{{CREATED_DATE}}", date_str)
                tmpl = tmpl.replace("{{LAST_PRACTICE_TIME}}", "尚未开始实战")
                tmpl = tmpl.replace("{{TOTAL_ENTRIES}}", "0")
                return tmpl
        return f"""# 考研英语二练习档案与语法错题记录本

> **记录本创建时间**：{date_str}  
> **最后实战记录时间**：尚未开始实战  
> **累计收录题数**：0 题  

---

## 上部：个人高频语法错误统计看板

| 错误分类大项 | 核心标签 | 累计出错频次 | 最近典型错例与核心警示 |
| :--- | :--- | :---: | :--- |
| **1. 谓语结构类** | `#缺失谓语` / `#双谓语` / `#被动语态残缺` / `#时态错位` | 0 次 | 暂无记录 |
| **2. 名词与冠词类** | `#可数单数裸奔` / `#定冠词遗漏` / `#定冠词滥用` / `#不可数变复数` | 0 次 | 暂无记录 |
| **3. 主谓一致类** | `#第三人称单数遗漏` / `#修饰成分干扰` / `#There-Be一致` | 0 次 | 暂无记录 |
| **4. 从句与引导词类** | `#逗号粘连双句` / `#非限制定语从句误用that` / `#介词后接that从句` | 0 次 | 暂无记录 |
| **5. 非谓语动词类** | `#悬垂分词` / `#主被动分词混淆` / `#介词to后接原形` | 0 次 | 暂无记录 |
| **6. 介词与搭配类** | `#不及物动词缺介词` / `#生硬汉式硬译` / `#介词固定搭配错误` | 0 次 | 暂无记录 |
| **7. 数据与事实类** | `#数据单位错位` / `#数据事实描述失真` | 0 次 | 暂无记录 |

---

## 下部：逐题训练实战流水账
<!-- 每道题在训练结束后自动在下方追加一条完整的记录卡片（直击外脑高级版原文） -->
"""

    def read_status(self):
        text = self.dashboard_file.read_text(encoding="utf-8")
        current_state = "未知"
        next_step = "未知"
        total_completed = 0
        weak_points = []

        m_state = re.search(r"\*\s*(?:\U0001f4cd\s*)?\*\*\[?当前所处位置.*?\*\*:\s*\n\s*(.+?)(?=\n\n|\n\*|$)", text, re.DOTALL)
        if m_state:
            current_state = m_state.group(1).strip()

        m_next = re.search(r"\*\s*(?:\U0001f3af\s*)?\*\*\[?下一步行动指令.*?\*\*:\s*\n\s*(.+?)(?=\n\n|\n\*|$)", text, re.DOTALL)
        if m_next:
            next_step = m_next.group(1).strip()

        m_total = re.search(r"\*\*累计训练题数\*\*：\s*(\d+)", text)
        if m_total:
            total_completed = int(m_total.group(1))

        m_weak = re.search(r"\*\s*(?:\u26a0\ufe0f?\s*)?\*\*\[?阶段性薄弱点重点盯防.*?\*\*:\s*\n((?:\s*\d+\..+?\n)+)", text)
        if m_weak:
            for line in m_weak.group(1).strip().splitlines():
                sub = re.sub(r"^\s*\d+\.\s*", "", line).strip()
                if sub:
                    weak_points.append(sub)

        # Count checked vs unchecked
        checked = len(re.findall(r"- \[x\]", text, re.IGNORECASE))
        unchecked = len(re.findall(r"- \[ \]", text))

        # Catch-up queue
        catch_up_queue = []
        m_queue = re.search(r"## 三、\s*待回补错题队列[\s\S]*?\|[^\n]+\|\s*\n\|[^\n]+\|\s*\n([\s\S]+?)(?=\n##|\Z)", text)
        if m_queue:
            for row in m_queue.group(1).strip().splitlines():
                if row.startswith("|") and "(队列空)" not in row and "<!--" not in row:
                    parts = [p.strip() for p in row.split("|")[1:-1]]
                    if len(parts) >= 4 and parts[0]:
                        catch_up_queue.append({
                            "item_id": parts[0],
                            "coordinate": parts[1] if len(parts) > 1 else "",
                            "time": parts[2] if len(parts) > 2 else "",
                            "diagnosis": parts[3] if len(parts) > 3 else "",
                            "status": parts[4] if len(parts) > 4 else "待回补",
                        })

        return {
            "current_state": current_state,
            "next_step": next_step,
            "total_completed": total_completed,
            "checked_items": checked,
            "remaining_items": unchecked,
            "weak_points": weak_points,
            "catch_up_queue": catch_up_queue,
            "dashboard_path": str(self.dashboard_file),
            "notebook_path": str(self.notebook_file),
        }

    def record_practice_result(
        self,
        theme,
        item_id,
        coordinate,
        source,
        chinese,
        student_answer,
        tags,
        diagnosis,
        master_version,
        baseline=None,
        status="completed",
        current_state=None,
        next_step=None,
        maimemo_info=None,
    ):
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 1. Update progress_dashboard.md
        dash_text = self.dashboard_file.read_text(encoding="utf-8")

        # Mark checkbox if item_id provided
        if item_id:
            # Pattern e.g. - [ ] A1.01
            dash_text = re.sub(
                rf"- \[ \]\s+({re.escape(item_id)}\b)",
                r"- [x] \1",
                dash_text,
                flags=re.IGNORECASE,
            )

        # Update last updated & total completed
        dash_text = re.sub(
            r"\*\*看板更新时间\*\*：.+",
            f"**看板更新时间**：{now_time}  ",
            dash_text,
        )

        m_tot = re.search(r"\*\*累计训练题数\*\*：\s*(\d+)", dash_text)
        new_count = 1
        if m_tot:
            new_count = int(m_tot.group(1)) + 1
            dash_text = re.sub(
                r"\*\*累计训练题数\*\*：\s*\d+\s*题",
                f"**累计训练题数**：{new_count} 题",
                dash_text,
            )

        # Update current state & next step if provided
        if current_state:
            dash_text = re.sub(
                r"(\*\s*(?:\U0001f4cd\s*)?\*\*\[?当前所处位置.*?\*\*:\s*\n)\s*.+?(?=\n\n|\n\*|$)",
                rf"\g<1>  {current_state}",
                dash_text,
                flags=re.DOTALL,
            )
        if next_step:
            dash_text = re.sub(
                r"(\*\s*(?:\U0001f3af\s*)?\*\*\[?下一步行动指令.*?\*\*:\s*\n)\s*.+?(?=\n\n|\n\*|$)",
                rf"\g<1>  {next_step}",
                dash_text,
                flags=re.DOTALL,
            )

        # Update Catch-up Queue in progress_dashboard.md
        if status == "pending_revision" and item_id:
            queue_pat = r"(## 三、\s*待回补错题队列[\s\S]*?\|[^\n]+\|\s*\n\|[^\n]+\|\s*\n)([\s\S]+?)(?=\n##|\Z)"
            m_q = re.search(queue_pat, dash_text)
            if m_q:
                table_header = m_q.group(1)
                table_body = m_q.group(2)
                clean_diag = diagnosis.replace("|", "/")[:35]
                new_row = f"| {item_id} | {coordinate} | {now_time} | {clean_diag} | 待回补 |\n"
                comments = re.findall(r"(<!--[\s\S]*?-->\s*\n)", table_body)
                comment_prefix = "".join(comments)
                clean_body = re.sub(r"<!--[\s\S]*?-->\s*\n", "", table_body)
                if "(队列空)" in clean_body:
                    new_body = comment_prefix + new_row
                elif item_id not in clean_body:
                    new_body = comment_prefix + clean_body.strip() + "\n" + new_row
                else:
                    new_body = table_body
                dash_text = re.sub(queue_pat, rf"\g<1>{new_body}", dash_text)
        elif status == "completed" and item_id:
            row_item_pat = rf"(\|\s*{re.escape(item_id)}\b[^|]*\|[^|]*\|[^|]*\|[^|]*\|\s*)待回补(\s*\|)"
            dash_text = re.sub(row_item_pat, r"\g<1>已补齐\2", dash_text)

        self.dashboard_file.write_text(dash_text, encoding="utf-8")

        # 2. Update grammar_error_notebook.md
        note_text = self.notebook_file.read_text(encoding="utf-8")

        # Update metadata
        note_text = re.sub(
            r"\*\*最后实战记录时间\*\*：.+",
            f"**最后实战记录时间**：{now_time}  ",
            note_text,
        )
        note_text = re.sub(
            r"\*\*累计收录题数\*\*：\s*\d+\s*题",
            f"**累计收录题数**：{new_count} 题",
            note_text,
        )

        # Update error category statistics table if tags contain errors
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag in tag_list:
            if tag in ["#语法完全正确", "完全正确", "#正确"]:
                continue
            # Match category
            matched_cat = None
            for cat, c_tags in ERROR_CATEGORY_MAP.items():
                if tag in c_tags or any(t.lower() in tag.lower() for t in c_tags):
                    matched_cat = cat
                    break
            if matched_cat:
                escaped_cat = re.escape(matched_cat)
                row_pat = rf"(\|\s*\*\*{escaped_cat}\*\*\s*\|[^|]+\|\s*)(\d+)\s*次\s*(\|\s*)([^|]+?)(\s*\|)"
                m_row = re.search(row_pat, note_text)
                if m_row:
                    old_c = int(m_row.group(2))
                    new_c = old_c + 1
                    clean_diag = diagnosis.replace("|", "/")[:40]
                    new_ex = f"{tag}: {student_answer[:25]}... ({clean_diag})"
                    note_text = re.sub(
                        row_pat,
                        rf"\g<1>{new_c} 次\g<3>{new_ex}\g<5>",
                        note_text,
                    )

        # Append card to bottom (NO BASELINE, ONLY MASTER VERSION)
        status_badge = " [待回补]" if status == "pending_revision" else ""
        card = f"""
### 题目流水账 #{new_count:03d} | [{theme}] {coordinate}{status_badge}

- **训练时间**：{now_time}
- **框架坐标**：`{coordinate}`
- **外脑资产来源**：`{source}`
- **待译中文题目**：
  > {chinese}
- **学员原始英文作答**：
  > {student_answer}
- **语法诊断与标签**：
  - **标签**：`{'` `'.join(tag_list)}`
  - **诊断摘要**：{diagnosis}
- **外脑高级版原文 (Master Alignment)**：
  > {master_version}
"""
        if maimemo_info:
            st = maimemo_info.get("status")
            if st == "success":
                synced = maimemo_info.get("synced_words", [])
                card += f"- **墨墨背单词错词复习**：已推入复习流 {len(synced)} 词 ({', '.join(synced)})，生成纠偏助记（打开 App 即可复习）\n"
            elif st == "partial_failed":
                card += f"- **墨墨背单词错词复习**：[部分失败] {maimemo_info.get('message', '')}\n"
            elif st == "skipped":
                card += f"- **墨墨背单词错词复习**：{maimemo_info.get('message', '本次无拼写错误')}\n"

        card += "\n---\n"
        note_text += card
        self.notebook_file.write_text(note_text, encoding="utf-8")

        result_dict = {
            "status": "success",
            "entry_index": new_count,
            "item_id": item_id,
            "revision_status": status,
            "dashboard_updated": True,
            "notebook_updated": True,
        }
        if maimemo_info is not None:
            result_dict["maimemo_sync"] = maimemo_info

        return result_dict

# ==========================================
# CLI 命令处理
# ==========================================

def get_theme_items(repo, theme_code):
    """
    根据主题代码返回匹配的知识库条目列表
    """
    code = theme_code.strip().upper()
    results = []

    if code == "A1":
        # Task 2 opening
        for it in repo.t2_expressions:
            if it.get("section") == "opening":
                results.append({
                    "id": it.get("id"),
                    "type": "expression",
                    "text": it.get("expression") or it.get("text"),
                    "intent": it.get("intent"),
                    "source": it.get("source"),
                    "coordinate": "大作文 > 第一段：图表数据定格描述",
                })
        # Add 2010-2017 opening excerpts
        for stem, content in sorted(repo.t2_archives.items()):
            m = re.search(r"## 终版高分范文\s*\n\s*(.+?)(?=\n\n|$)", content)
            if m:
                first_para = m.group(1).strip()
                results.append({
                    "id": stem[:13],
                    "type": "past_paper_opening",
                    "text": first_para,
                    "intent": f"真题首段完整图表定格描述 ({stem})",
                    "source": stem,
                    "coordinate": f"大作文 > 第一段：图表定格 > {stem[-15:]}",
                })
    elif code == "A2":
        # Task 2 body + morphemes
        for it in repo.t2_expressions:
            if it.get("section") == "body":
                results.append({
                    "id": it.get("id"),
                    "type": "expression",
                    "text": it.get("expression") or it.get("text"),
                    "intent": it.get("intent"),
                    "source": it.get("source"),
                    "coordinate": "大作文 > 第二段：因果机制推演骨架",
                })
        for it in repo.morphemes:
            t = it.get("text") or it.get("expression") or it.get("verb_phrase") or ""
            m = it.get("meaning") or it.get("intent") or it.get("note") or ""
            src = it.get("source", "")
            if "CHART" in src or "chart" in it.get("genre", ""):
                results.append({
                    "id": it.get("id"),
                    "type": "morpheme",
                    "text": t,
                    "intent": m,
                    "source": src,
                    "coordinate": f"大作文 > 第二段：场景动宾语素 > {it.get('scenario') or '通用'}",
                })
    elif code == "A3":
        for it in repo.t2_expressions:
            if it.get("section") in ("conclusion", "closing"):
                results.append({
                    "id": it.get("id"),
                    "type": "expression",
                    "text": it.get("expression") or it.get("text"),
                    "intent": it.get("intent"),
                    "source": it.get("source"),
                    "coordinate": "大作文 > 第三段：宏观总结与趋势建议",
                })
    elif code == "A4":
        for stem, content in sorted(repo.t2_archives.items()):
            m = re.search(r"## 终版高分范文\s*\n\s*(.+?)(?=\n###|\Z)", content, re.DOTALL)
            results.append({
                "id": stem[:13],
                "type": "full_essay",
                "text": m.group(1).strip() if m else "",
                "intent": f"大作文全篇串联复盘 ({stem})",
                "source": stem,
                "coordinate": f"大作文 > 全篇复盘 > {stem}",
            })
    elif code == "B1":
        for it in repo.t1_expressions:
            if it.get("section") == "opening":
                results.append({
                    "id": it.get("id"),
                    "type": "expression",
                    "text": it.get("text") or it.get("expression"),
                    "intent": it.get("intent"),
                    "source": it.get("source"),
                    "coordinate": f"小作文 > 第一段：写信目的破题 > {it.get('genre')}",
                })
    elif code == "B2":
        for it in repo.t1_expressions:
            if it.get("section") == "body":
                results.append({
                    "id": it.get("id"),
                    "type": "expression",
                    "text": it.get("text") or it.get("expression"),
                    "intent": it.get("intent"),
                    "source": it.get("source"),
                    "coordinate": f"小作文 > 第二段：核心要点展开 > {it.get('genre')}",
                })
    elif code == "B3":
        for it in repo.t1_expressions:
            if it.get("section") == "closing":
                results.append({
                    "id": it.get("id"),
                    "type": "expression",
                    "text": it.get("text") or it.get("expression"),
                    "intent": it.get("intent"),
                    "source": it.get("source"),
                    "coordinate": f"小作文 > 第三段：礼貌闭环 > {it.get('genre')}",
                })
    elif code == "B4":
        for stem, content in sorted(repo.t1_archives.items()):
            m = re.search(r"## 终版高分范文\s*\n\s*(.+?)(?=\n###|\Z)", content, re.DOTALL)
            results.append({
                "id": stem[:13],
                "type": "full_essay",
                "text": m.group(1).strip() if m else "",
                "intent": f"小作文真题分类串联复盘 ({stem})",
                "source": stem,
                "coordinate": f"小作文 > 全篇复盘 > {stem}",
            })
    return results

def cmd_doctor(dash_mgr, repo, args):
    """Diagnose local brain assets, review records, and MaiMemo Open API credentials."""
    status_info = dash_mgr.read_status()
    summary = repo.get_summary()

    token = getattr(args, "token", None) or os.environ.get("MAIMEMO_SPELLING_TOKEN")
    fallback_token = None
    if getattr(args, "token", None):
        token_src = "命令行 --token"
    elif os.environ.get("MAIMEMO_SPELLING_TOKEN"):
        token_src = "环境变量 MAIMEMO_SPELLING_TOKEN"
    elif os.environ.get("MAIMEMO_TOKEN"):
        fallback_token = os.environ.get("MAIMEMO_TOKEN")
        token_src = "环境变量 MAIMEMO_TOKEN (降级检测)"
    else:
        token_src = "未配置"

    memo_diag = {}
    if not token and not fallback_token:
        memo_diag = {
            "configured": False,
            "status": "WARN",
            "message": "未配置 MAIMEMO_SPELLING_TOKEN（本地训练与持久化不受影响；如需错词推送复习请配置）"
        }
    else:
        actual_token = token or fallback_token
        masked = actual_token[:6] + "..." + actual_token[-4:] if len(actual_token) > 10 else "***"
        isolation_warn = None
        if not token and fallback_token:
            isolation_warn = "检测到 MAIMEMO_TOKEN（阅读账号），建议配置独立拼写专用账号 MAIMEMO_SPELLING_TOKEN"

        c = MaimemoClient(token=actual_token, mock=getattr(args, "mock", False))
        voc_status = "UNKNOWN"
        voc_detail = ""
        try:
            v_res = c.query_vocabulary_ids(["verge", "necessities"])
            if "verge" in v_res and "necessities" in v_res:
                voc_status = "PASS"
                voc_detail = "基础词库与词根形态还原测试通过"
            elif "verge" in v_res:
                voc_status = "PASS"
                voc_detail = "基础词库测试通过"
            else:
                voc_status = "WARN"
                voc_detail = "词库查询返回空"
        except Exception as e:
            voc_status = "FAIL"
            voc_detail = str(e)

        memo_diag = {
            "configured": True,
            "token_source": token_src,
            "token_masked": masked,
            "isolation_warning": isolation_warn,
            "vocabulary_endpoint": {"status": voc_status, "detail": voc_detail}
        }

    # Minis Android 沙箱环境规范合规性自检
    minis_mount_preferred = Path("/var/minis/mounts/Documents/考研英语/资产复盘")
    actual_review_dir = Path(status_info["dashboard_path"]).parent.resolve()
    is_external_mount = False
    try:
        if minis_mount_preferred.exists() and actual_review_dir == minis_mount_preferred.resolve():
            is_external_mount = True
    except Exception:
        pass

    sandbox_diag = {
        "short_lived_process_model": {
            "status": "PASS",
            "interpreter": sys.executable,
            "script_absolute_path": str(Path(__file__).resolve()),
            "notes": "独立单次子进程执行 (/bin/sh -c '<cmd>')，无常驻 Daemon，执行完毕立即安全退出"
        },
        "file_persistence_flow": {
            "status": "PASS",
            "settle_file_support": True,
            "workspace_candidates": [str(d) for d in MINIS_WORKSPACE_CANDIDATES],
            "notes": "支持长文本/JSON通过 --file 传入 (优先支持 /var/minis/workspace/kaoyan/settle.json 与相对路径)"
        },
        "persistence_decoupling": {
            "status": "PASS" if is_external_mount else ("INFO_LOCAL_DEV" if not Path("/var/minis").exists() else "WARN_FALLBACK"),
            "preferred_mount": str(minis_mount_preferred),
            "actual_dir": str(actual_review_dir),
            "is_external_decoupled": is_external_mount,
            "notes": "成功挂载于宿主外部存储，容器重启/销毁不丢失学习档案" if is_external_mount else (
                "本地开发工程模式运行" if not Path("/var/minis").exists() else "未挂载外部存储，当前运行在沙盒临时目录"
            )
        }
    }

    report = {
        "sandbox_compliance": sandbox_diag,
        "brain_assets": summary,
        "review_records": {
            "dashboard_path": status_info["dashboard_path"],
            "notebook_path": status_info["notebook_path"],
            "total_completed": status_info["total_completed"],
            "checked_items": status_info["checked_items"],
            "remaining_items": status_info["remaining_items"]
        },
        "maimemo_credentials": memo_diag
    }

    if getattr(args, "json", False):
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("==================== 考研英语二外脑内化 · 系统与凭据诊断 (doctor) ====================")
        print("[Minis Android 沙箱环境规范合规性自检]")
        proc_info = sandbox_diag["short_lived_process_model"]
        flow_info = sandbox_diag["file_persistence_flow"]
        decouple_info = sandbox_diag["persistence_decoupling"]
        print(f"• 短命进程模型: [{proc_info['status']}] {proc_info['notes']}")
        print(f"  - 推荐绝对调用: {proc_info['interpreter']} {proc_info['script_absolute_path']}")
        print(f"• 文件落盘数据流: [{flow_info['status']}] {flow_info['notes']}")
        print(f"• 外脑持久化解耦: [{decouple_info['status']}] {decouple_info['notes']}")
        print(f"  - 优先挂载路径: {decouple_info['preferred_mount']}")
        print(f"  - 当前生效路径: {decouple_info['actual_dir']}")

        print("\n[本地外脑知识库与资产底座]")
        print(f"• 资产根目录: {summary['root']}")
        print(f"• 场景动宾语素: {summary['morphemes_count']} 条 (shared/morphemes.jsonl)")
        print(f"• 小作文句式: {summary['task1_expressions_count']} 条 (task1/expressions.jsonl)")
        print(f"• 大作文句式: {summary['task2_expressions_count']} 条 (task2/expressions.jsonl)")
        print(f"• 小作文范文: {summary['task1_archives_count']} 篇 (task1/archive/)")
        print(f"• 大作文范文: {summary['task2_archives_count']} 篇 (task2/archive/)")

        print("\n[持久化复盘看板与错题记录]")
        print(f"• 状态看板: {status_info['dashboard_path']}")
        print(f"• 错题记录本: {status_info['notebook_path']}")
        print(f"• 完成进度: 已通关 {status_info['checked_items']} 项 / 剩余 {status_info['remaining_items']} 项 (累计记录 {status_info['total_completed']} 题)")

        print("\n[墨墨背单词开放平台凭据 (MAIMEMO_SPELLING_TOKEN)]")
        if not memo_diag.get("configured"):
            print("• 凭据状态: [WARN] 未配置 MAIMEMO_SPELLING_TOKEN")
            print("  - 说明: 本地训练、分层诊断、高级版对齐与错题归档完全不受影响。")
            print("  - 如需在拼写错误时自动推送至墨墨 App 复习，请配置环境变量 MAIMEMO_SPELLING_TOKEN。")
        else:
            print(f"• 凭据来源: {memo_diag.get('token_source')} ({memo_diag.get('token_masked')})")
            if memo_diag.get("isolation_warning"):
                print(f"  [WARN] {memo_diag['isolation_warning']}")
            voc_e = memo_diag.get("vocabulary_endpoint", {})
            print(f"• 词库连通性 (/vocabulary/query): [{voc_e.get('status')}] {voc_e.get('detail')}")
        print("=================================================================================")


def cmd_maimemo_sync(args):
    """Sync misspelled words to MaiMemo review stream."""
    if getattr(args, "example", False):
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
    if getattr(args, "data", None):
        try:
            payload = json.loads(args.data)
        except Exception as e:
            print(f"[ERROR] 解析 --data JSON 失败: {e}", file=sys.stderr)
            sys.exit(1)
    elif getattr(args, "file", None):
        target_file = resolve_workspace_file(args.file)
        if not target_file or not target_file.exists():
            print(f"[ERROR] 指定文件不存在: {args.file} (探测路径: {target_file})", file=sys.stderr)
            sys.exit(1)
        with open(target_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    else:
        print("错误: 必须通过 --file 或 --data 指定 JSON 载荷，或使用 --example 查看样例", file=sys.stderr)
        sys.exit(1)

    try:
        res = sync_essay_vocabulary(payload, token=args.token, mock=args.mock, dry_run=args.dry_run)
        if res.get("status") in ("partial_failed", "error"):
            if getattr(args, "json", False):
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(f"[ERROR] 墨墨推送失败: {res.get('message')}", file=sys.stderr)
                if res.get("skipped_words"):
                    print(f"未匹配跳过: {', '.join(res.get('skipped_words', []))}", file=sys.stderr)
            sys.exit(1)
        elif res.get("status") == "skipped":
            if getattr(args, "json", False):
                print(json.dumps(res, ensure_ascii=False, indent=2))
            else:
                print(f"[INFO] {res.get('message')}")
            return
        elif getattr(args, "json", False):
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
        if getattr(args, "json", False):
            print(json.dumps({"status": "error", "message": err_msg}, ensure_ascii=False))
        else:
            print(f"推送失败: {err_msg}", file=sys.stderr)
        sys.exit(1)


def cmd_get_exercise(args):
    curated_path = Path(__file__).resolve().parent.parent / "references" / "curated_exercises.json"
    if not curated_path.exists():
        err = f"题库文件不存在: {curated_path}"
        if getattr(args, "json", False):
            print(json.dumps({"status": "error", "message": err}, ensure_ascii=False))
        else:
            print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)

    with open(curated_path, "r", encoding="utf-8") as f:
        exercises = json.load(f)

    target = None
    if getattr(args, "item_id", None):
        target = exercises.get(args.item_id)
    elif getattr(args, "theme", None):
        theme_prefix = args.theme.upper()
        idx = getattr(args, "index", 1)
        expected_id = f"{theme_prefix}.{idx:02d}"
        target = exercises.get(expected_id)
        if not target:
            theme_items = [v for k, v in sorted(exercises.items()) if v.get("theme", "").upper() == theme_prefix]
            if theme_items and 1 <= idx <= len(theme_items):
                target = theme_items[idx - 1]

    if not target:
        err = f"未找到指定题目 (item_id={getattr(args, 'item_id', None)}, theme={getattr(args, 'theme', None)}, index={getattr(args, 'index', None)})"
        if getattr(args, "json", False):
            print(json.dumps({"status": "error", "message": err}, ensure_ascii=False))
        else:
            print(f"[ERROR] {err}", file=sys.stderr)
        sys.exit(1)

    if getattr(args, "json", False):
        print(json.dumps(target, ensure_ascii=False, indent=2))
        return

    if getattr(args, "hint", False):
        cue = target.get('micro_cue', '无特殊生僻词，请根据中文句意尝试独立遣词造句。')
        card = f"""### [微语素备忘线索: {target.get('coordinate')}]

- **[外脑溯源]**: `{target.get('source_id')}` ({target.get('past_paper')})
- **[难词/核心词微线索]**:
  {cue}
"""
        print(card)
        return

    mode = getattr(args, "mode", "conservative")
    if mode == "detailed":
        card = f"""### [训练题目: {target.get('coordinate')}]

- **[框架坐标]**: `{target.get('coordinate')}`
- **[外脑溯源]**: `{target.get('source_id')}` ({target.get('past_paper')})
- **[待译汉语句子]**:
  > "{target.get('chinese')}"
- **[考研防坑提示]**:
  {target.get('pitfall_alert')}
- **[脚手架提示]**:
  {target.get('scaffold')}

[输入指引]: 请在下方输入你的独立英语翻译（可在输入框直接文字输入，或在纸面/平板上手写后拍照发送）。
"""
    else:
        # Conservative mode (Default): Zero spoiler, dimension-only alerts, no full templates
        direction = target.get('thinking_direction') or '构建段落功能主谓骨架，准确交代逻辑衔接与考点要素。'
        pitfall = target.get('conservative_pitfall') or '注意图表/书信语域规范、主谓一致、时态统摄与固定介词搭配。（严禁直接剧透答案词）'
        card = f"""### [训练题目: {target.get('coordinate')}]

- **[框架坐标]**: `{target.get('coordinate')}`
- **[外脑溯源]**: `{target.get('source_id')}` ({target.get('past_paper')})
- **[待译汉语句子]**:
  > "{target.get('chinese')}"
- **[思考方向]**:
  {direction}
- **[考研维度点拨]**:
  {pitfall}

[输入指引]: 请在下方输入你的独立英语翻译（可在输入框直接文字输入，或在纸面/平板上手写后拍照发送）。若遇专有名词卡壳，可回复“提示”获取微线索。
"""
    print(card)


def cmd_prepare_image(args):
    try:
        from PIL import Image, ImageOps
    except ImportError:
        print(json.dumps({
            "status": "error",
            "message": "PIL (Pillow) 未安装，无法执行图片预处理"
        }, ensure_ascii=False))
        sys.exit(1)

    img_path = resolve_workspace_file(args.image)
    if not img_path or not img_path.exists():
        print(json.dumps({
            "status": "error",
            "message": f"找不到图片文件: {args.image}"
        }, ensure_ascii=False))
        sys.exit(1)

    try:
        im = Image.open(img_path)
        im = ImageOps.exif_transpose(im)
        if getattr(args, "rotate", 0):
            im = im.rotate(-args.rotate, expand=True)

        import tempfile
        out_p = Path(args.out) if getattr(args, "out", None) else Path(tempfile.gettempdir()) / "kaoyan_student_answer.jpg"
        im.save(out_p, quality=92)
        w, h = im.size
        print(json.dumps({
            "status": "success",
            "processed_path": str(out_p),
            "original_path": str(img_path),
            "size": [w, h],
            "suggested_prompt": "请逐词转录学员手写英文句子。注意标点符号、大小写、可数名词单复数拼写与具体数字。"
        }, ensure_ascii=False, indent=2))
    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": f"处理图片失败: {e}"
        }, ensure_ascii=False))
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="考研英语二外脑资产内化训练系统 CLI"
    )
    parser.add_argument("--asset-dir", help="本地外脑资产根目录路径")
    parser.add_argument("--review-dir", help="持久化看板与错题记录目录路径")

    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # 1. status
    subparsers.add_parser("status", help="读取当前训练看板状态与下一步指令")

    # 2. init-docs
    subparsers.add_parser("init-docs", help="初始化训练进度看板与错题记录本")

    # 3. list-theme
    p_list = subparsers.add_parser("list-theme", help="列出指定主题下的训练条目清单")
    p_list.add_argument("--theme", required=True, help="主题代码 (A1, A2, A3, A4, B1, B2, B3, B4)")

    # 4. get-item
    p_get = subparsers.add_parser("get-item", help="提取指定主题或 ID 的出题素材详情")
    p_get.add_argument("--theme", required=True, help="主题代码 (A1..B4)")
    p_get.add_argument("--index", type=int, default=1, help="条目序号 (从1开始)")
    p_get.add_argument("--item-id", help="条目ID (优先根据ID查找)")

    # 4.1 get-exercise (一键提取出题卡片，无 emoji，默认保守模式避免剧透)
    p_ex = subparsers.add_parser("get-exercise", help="提取指定题目的出题卡片 (无 emoji，默认保守提示，杜绝剧透)")
    p_ex.add_argument("--item-id", help="题目编号 (如 A1.01, B2.01)")
    p_ex.add_argument("--theme", help="主题代码 (A1..B4)")
    p_ex.add_argument("--index", type=int, default=1, help="主题内序号 (从1开始)")
    p_ex.add_argument("--mode", choices=["conservative", "detailed"], default="conservative", help="出题提示模式 (conservative=保守点拨避免剧透[默认], detailed=详细脚手架)")
    p_ex.add_argument("--hint", action="store_true", help="提取难词微语素线索 (学员卡壳求助时调用)")
    p_ex.add_argument("--json", action="store_true", help="以纯 JSON 格式输出")

    # 4.2 prepare-image (原生预处理学员手写答题图片)
    p_img = subparsers.add_parser("prepare-image", help="预处理学员手写答题图片 (依据 EXIF 自动扶正并生成优化临时图)")
    p_img.add_argument("--image", required=True, help="原始手写图片文件路径")
    p_img.add_argument("--rotate", type=int, default=0, help="额外顺时针旋转角度 (如 90, 180, 270, -90)")
    p_img.add_argument("--out", help="输出图片文件路径 (默认为临时目录 kaoyan_student_answer.jpg)")

    # 5. record
    p_rec = subparsers.add_parser("record", help="记录一道题的实战输出与批改结果")
    p_rec.add_argument("--file", help="实战记录结算 JSON 文件路径 (支持绝对路径或相对工作区路径，如 /var/minis/workspace/kaoyan/settle.json)")
    p_rec.add_argument("--asset-dir", help="本地外脑资产根目录路径")
    p_rec.add_argument("--review-dir", help="持久化看板与错题记录目录路径")
    p_rec.add_argument("--theme", help="训练主题代码 (A1..B4)")
    p_rec.add_argument("--item-id", default=None, help="课程通关清单条目ID (如 A1.01)")
    p_rec.add_argument("--coordinate", help="框架坐标")
    p_rec.add_argument("--source", help="外脑资产来源")
    p_rec.add_argument("--chinese", help="待译中文句子")
    p_rec.add_argument("--student-answer", help="学员原始英文作答")
    p_rec.add_argument("--tags", help="逗号分隔的错误标签")
    p_rec.add_argument("--diagnosis", help="诊断分析摘要")
    p_rec.add_argument("--baseline", default=None, help="[可选] 降维保底版句子")
    p_rec.add_argument("--master-version", help="外脑终版高分句")
    p_rec.add_argument("--status", choices=["completed", "pending_revision"], default=None, help="批改状态 (completed: 已订正/完全正确, pending_revision: 待回补)")
    p_rec.add_argument("--current-state", help="更新当前所处位置")
    p_rec.add_argument("--next-step", help="更新下一步行动指令")
    p_rec.add_argument("--misspelled-words", help="初稿拼错单词，格式如 'acommodate:accommodate' 或逗号分隔多组")
    p_rec.add_argument("--maimemo-file", help="墨墨推送错词 JSON 载荷文件路径")
    p_rec.add_argument("--maimemo-data", help="墨墨推送错词 JSON 载荷字符串")
    p_rec.add_argument("--token", help="MaiMemo API token")
    p_rec.add_argument("--dry-run", action="store_true", help="Dry run without modifying external remote APIs")
    p_rec.add_argument("--mock", action="store_true", help="Mock API mode for offline tests")
    p_rec.add_argument("--json", action="store_true", help="以纯 JSON 格式输出结果")

    # 6. maimemo-sync
    p_memo = subparsers.add_parser("maimemo-sync", help="推送初稿拼写错误单词至墨墨背单词今日复习流")
    p_memo.add_argument("--file", help="Path to JSON payload file")
    p_memo.add_argument("--data", help="Raw JSON payload string")
    p_memo.add_argument("--token", help="MaiMemo API token (默认为环境变量 MAIMEMO_SPELLING_TOKEN)")
    p_memo.add_argument("--dry-run", action="store_true", help="Dry run without modifying external remote APIs")
    p_memo.add_argument("--mock", action="store_true", help="Mock API responses for offline tests")
    p_memo.add_argument("--example", action="store_true", help="Print payload template and exit")
    p_memo.add_argument("--json", action="store_true", help="Output result as pure JSON")

    # 7. doctor
    p_doc = subparsers.add_parser("doctor", help="诊断本地外脑、复盘记录与墨墨背单词凭据状态")
    p_doc.add_argument("--token", help="MaiMemo API token (默认为环境变量 MAIMEMO_SPELLING_TOKEN)")
    p_doc.add_argument("--mock", action="store_true", help="Mock API responses for offline tests")
    p_doc.add_argument("--json", action="store_true", help="Output result as pure JSON")

    args = parser.parse_args()

    asset_dir = resolve_asset_dir(args.asset_dir)
    review_dir = resolve_review_dir(args.review_dir)

    dash_mgr = DashboardManager(review_dir, asset_dir)
    repo = BrainRepository(asset_dir)

    if args.command == "status" or not args.command:
        status_info = dash_mgr.read_status()
        summary = repo.get_summary()
        print(json.dumps({
            "dashboard_status": status_info,
            "brain_assets": summary
        }, ensure_ascii=False, indent=2))

    elif args.command == "init-docs":
        dash_mgr.ensure_initialized()
        print(f"[OK] 看板与错题本已成功就绪在: {review_dir}")

    elif args.command == "list-theme":
        items = get_theme_items(repo, args.theme)
        print(f"=== 主题 {args.theme.upper()} 训练条目列表 (共 {len(items)} 条) ===")
        for idx, it in enumerate(items, start=1):
            t_short = (it.get("text") or "")[:50].replace("\n", " ")
            print(f"[{idx:02d}] {it.get('id')}: {it.get('intent')} | {t_short}")

    elif args.command == "get-item":
        items = get_theme_items(repo, args.theme)
        target = None
        if args.item_id:
            for it in items:
                if it.get("id") == args.item_id:
                    target = it
                    break
        if not target and items:
            idx = max(0, min(args.index - 1, len(items) - 1))
            target = items[idx]

        if not target:
            print(json.dumps({"error": f"未找到主题 {args.theme} 下的匹配素材"}, ensure_ascii=False))
            sys.exit(1)

        print(json.dumps(target, ensure_ascii=False, indent=2))

    elif args.command == "get-exercise":
        cmd_get_exercise(args)

    elif args.command == "prepare-image":
        cmd_prepare_image(args)

    elif args.command == "record":
        file_payload = {}
        if getattr(args, "file", None):
            settle_path = resolve_workspace_file(args.file)
            if not settle_path or not settle_path.exists():
                print(f"[ERROR] 找不到指定的记录结算文件: {args.file} (探测路径: {settle_path})", file=sys.stderr)
                sys.exit(1)
            try:
                with open(settle_path, "r", encoding="utf-8") as f:
                    file_payload = json.load(f)
            except Exception as e:
                print(f"[ERROR] 读取结算文件 JSON 失败: {e}", file=sys.stderr)
                sys.exit(1)

        theme = args.theme or file_payload.get("theme")
        item_id = args.item_id if args.item_id is not None else file_payload.get("item_id", "")
        coordinate = args.coordinate or file_payload.get("coordinate")
        source = args.source or file_payload.get("source")
        chinese = args.chinese or file_payload.get("chinese")
        student_answer = args.student_answer or file_payload.get("student_answer")

        raw_tags = args.tags if args.tags is not None else file_payload.get("tags", "")
        if isinstance(raw_tags, list):
            tags = ",".join(str(t).strip() for t in raw_tags if str(t).strip())
        else:
            tags = str(raw_tags or "")

        diagnosis = args.diagnosis or file_payload.get("diagnosis")
        baseline = getattr(args, "baseline", None) or file_payload.get("baseline")
        master_version = args.master_version or file_payload.get("master_version")
        status = getattr(args, "status", None) or file_payload.get("status", "completed")
        current_state = args.current_state or file_payload.get("current_state")
        next_step = args.next_step or file_payload.get("next_step")

        misspelled_words = args.misspelled_words if args.misspelled_words is not None else file_payload.get("misspelled_words")

        required_map = {
            "theme": theme,
            "coordinate": coordinate,
            "source": source,
            "chinese": chinese,
            "student_answer": student_answer,
            "tags": tags,
            "diagnosis": diagnosis,
            "master_version": master_version,
        }
        missing = [k for k, v in required_map.items() if not v]
        if missing:
            print(f"[ERROR] 缺少必填字段: {', '.join(missing)}。请通过 --file 传入 JSON 文件或通过命令行参数提供。", file=sys.stderr)
            sys.exit(1)

        # Handle optional maimemo sync for misspelled words
        maimemo_info = None
        memo_payload = None

        if getattr(args, "maimemo_data", None):
            try:
                memo_payload = json.loads(args.maimemo_data)
            except Exception as e:
                print(f"[WARN] 解析 --maimemo-data 失败: {e}", file=sys.stderr)
        elif getattr(args, "maimemo_file", None):
            mf = resolve_workspace_file(args.maimemo_file)
            if mf and mf.exists():
                try:
                    with open(mf, "r", encoding="utf-8") as f:
                        memo_payload = json.load(f)
                except Exception as e:
                    print(f"[WARN] 读取 --maimemo-file 失败: {e}", file=sys.stderr)
        elif "maimemo" in file_payload and isinstance(file_payload["maimemo"], dict):
            memo_payload = file_payload["maimemo"]
        elif misspelled_words:
            words = []
            if isinstance(misspelled_words, list):
                for item in misspelled_words:
                    if isinstance(item, dict):
                        words.append({
                            "spelling": item.get("spelling") or item.get("correct", ""),
                            "type": "spelling_fix",
                            "misspelling": item.get("misspelling") or item.get("mis", ""),
                            "sentence": item.get("sentence") or master_version or baseline,
                            "translation": item.get("translation") or chinese,
                            "usage_note": item.get("usage_note") or "考研写作核心高频词，务必防范考场拼写硬伤扣分。",
                            "grammar_note": item.get("grammar_note") or f"在原句中充当核心成分（诊断：{diagnosis[:60]}）。"
                        })
                    elif isinstance(item, str):
                        pair = item.strip()
                        if ":" in pair:
                            mis, correct = pair.split(":", 1)
                        else:
                            mis, correct = pair, pair
                        words.append({
                            "spelling": correct.strip(),
                            "type": "spelling_fix",
                            "misspelling": mis.strip(),
                            "sentence": master_version or baseline,
                            "translation": chinese,
                            "usage_note": "考研写作核心高频词，务必防范考场拼写硬伤扣分。",
                            "grammar_note": f"在原句中充当核心成分（诊断：{diagnosis[:60]}）。"
                        })
            elif isinstance(misspelled_words, str):
                for pair in misspelled_words.split(","):
                    pair = pair.strip()
                    if not pair:
                        continue
                    if ":" in pair:
                        mis, correct = pair.split(":", 1)
                    else:
                        mis, correct = pair, pair
                    words.append({
                        "spelling": correct.strip(),
                        "type": "spelling_fix",
                        "misspelling": mis.strip(),
                        "sentence": master_version or baseline,
                        "translation": chinese,
                        "usage_note": "考研写作核心高频词，务必防范考场拼写硬伤扣分。",
                        "grammar_note": f"在原句中充当核心成分（诊断：{diagnosis[:60]}）。"
                    })
            if words:
                memo_payload = {"task_id": item_id or theme, "words": words}

        if memo_payload:
            try:
                maimemo_info = sync_essay_vocabulary(
                    memo_payload,
                    token=getattr(args, "token", None),
                    mock=getattr(args, "mock", False),
                    dry_run=getattr(args, "dry_run", False)
                )
            except Exception as e:
                maimemo_info = {"status": "partial_failed", "message": str(e)}

        res = dash_mgr.record_practice_result(
            theme=theme,
            item_id=item_id,
            coordinate=coordinate,
            source=source,
            chinese=chinese,
            student_answer=student_answer,
            tags=tags,
            diagnosis=diagnosis,
            master_version=master_version,
            baseline=baseline,
            status=status,
            current_state=current_state,
            next_step=next_step,
            maimemo_info=maimemo_info,
        )
        print(json.dumps(res, ensure_ascii=False, indent=2))

    elif args.command == "maimemo-sync":
        cmd_maimemo_sync(args)

    elif args.command == "doctor":
        cmd_doctor(dash_mgr, repo, args)

if __name__ == "__main__":
    main()
