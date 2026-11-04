# MaiMemo (墨墨背单词) Open API 裁剪规范与接口契约

本文档为考研英语二“外脑资产内化与语法巩固”训练系统专用的墨墨背单词 Open API 裁剪规范。根据用户教学实战决议：**仅在学员初稿出现拼写错误时，将错词纠偏助记推入今日复习流；彻底不创建、不维护云词本（无需 `/notepads`），彻底不停留改写例句（无需 `/phrases`）。**

---

## 一、核心定位与极简契约

1. **唯一触发条件**：仅当学员在英文作答中出现**拼写错误**（如 `acommodate` ➔ `accommodate`）时触发推送；语法完全正确或无拼写错误的题目直接跳过，零打扰。
2. **零词本负担**：**不调用 `/notepads`，不创建任何新词本**，杜绝学员墨墨 App 词本列表被零散小词本刷屏。
3. **零例句权限风险**：**不调用 `/phrases`**，彻底规避 403 权限限制与 API 额度浪费。
4. **两大核心动作**：
   - **生成【初稿纠偏】深度助记 (`POST /notes`)**：在墨墨单词卡片内注入错拼纠正、考研写作用法与原句语法剖析；
   - **直接推入今日复习流 (`POST /study/add_words` with `advance: true`)**：无视等级门槛，直接加入学员当天复习队列，打开墨墨 App 即可立即刷到订正。

---

## 二、基础配置与认证

- **Base URL**: `https://open.maimemo.com/open/api/v1`
- **认证方式**: HTTP 请求头 `Authorization: Bearer $MAIMEMO_SPELLING_TOKEN`
- **账号隔离契约**:
  - 本 Skill 专职服务【背单词拼写】，绑定**拼写背单词专用账号**，使用环境变量 **`$MAIMEMO_SPELLING_TOKEN`**；
  - 考研英语阅读 Skill 保持独立，绑定**识记背单词账号**（只要求认识不要求拼写），使用环境变量 **`$MAIMEMO_TOKEN`**；
  - 两者 Token 与账号完全物理隔离，本 Skill 绝不回退读取 `$MAIMEMO_TOKEN`，杜绝串号污染。
- **Token 来源**:
  - 手机 App: 使用【拼写背单词专用账号】登录墨墨背单词 → 设置 → 开放 API
  - Web 端: 打开 `https://open.maimemo.com/open/api/v1/tokens/openapi` 登录该账号后复制 Token
- **Token 缺省处理**: 若未设置环境变量 `$MAIMEMO_SPELLING_TOKEN`，系统提示学员获取并配置，不阻断本地语法诊断与错题持久化主流程。
- **频控限制 (Rate Limits)**:
  - 20 次 / 10 秒
  - 40 次 / 60 秒
  - 2000 次 / 5 小时
  *(注: 每次练习仅涉及 1~3 个错词，脚本内部已内置**滑动窗口限流器**，严格执行上述上限并保持平均 ≥0.5 秒/次的安全调用间隔；命中 429 后退避重试一次。)*

---

## 三、调用的 3 大极简端点

### 1. 单词查询与 voc_id 解析 (`POST /vocabulary/query`)
- **作用**: 批量将纠正后的标准单词解析为墨墨内部唯一的 `voc_id`。
- **请求体**:
  ```json
  {
    "spellings": ["accommodate"]
  }
  ```
- **响应体**:
  ```json
  {
    "data": {
      "voc": [
        {"id": "voc_12345", "spelling": "accommodate"}
      ]
    }
  }
  ```
- **词根形态自动回退**: 若生词拼写在墨墨词库中未直接命中（如复数、过去式、进行时），脚本内置形态还原算法回退词根重试。

---

### 2. “借壳”错词纠偏深度助记 (`POST /notes`)
- **作用**: 点开助记卡片不是网上的搞笑段子，而是学员刚刚写错的原句剖析与纠偏警示。
- **类型参数 (`note_type`)**: 统一固定为 `"语法"`。
- **助记内容规范**（纯文本三段式，禁用 Markdown 标题）:
  - `【初稿纠偏】：初稿误拼为 <错拼>，正确拼写为 <正拼>（考场务必防范拼写扣分）！`
  - `【考研写作用法】：及物性、高频搭配、可替换的普通表达`
  - `【原句语法剖析】：原句的主干与修饰成分拆解`
- **请求体**:
  ```json
  {
    "note": {
      "voc_id": "voc_12345",
      "note_type": "语法",
      "note": "【初稿纠偏】：初稿误拼为 acommodate，正确拼写为 accommodate（考场务必防范拼写扣分）！\n【考研写作用法】：及物动词常接 students / needs，表示“容纳、迎合”，可替换普通 meet。\n【原句语法剖析】：不定式短语 to accommodate students 作后置目的状语。"
    }
  }
  ```

---

### 3. 立刻推入今日复习流 (`POST /study/add_words`)
- **作用**: 无视等级门槛，直接将拼写纠正后的单词加入当天复习队列，退出会话后打开 App 即可立即刷到。
- **请求体**:
  ```json
  {
    "words": [
      {"id": "voc_12345"}
    ],
    "advance": true
  }
  ```
- **特性**: `"advance": true` 会同时触发提前复习（无需学员达到 10 级），当天复习队列立即可见。

---

## 四、数据载荷规范

推送错词载荷示例：
```json
{
  "task_id": "A1.01",
  "words": [
    {
      "spelling": "accommodate",
      "type": "spelling_fix",
      "misspelling": "acommodate",
      "sentence": "The facility was expanded to accommodate students.",
      "translation": "该设施已扩建以容纳学生。",
      "usage_note": "考研高频及物动词，常接 students / needs，表示‘迎合、容纳、迁就’，写作中可完美替换普通的 meet 或 help。",
      "grammar_note": "不定式短语 to accommodate students 作后置目的状语。"
    }
  ]
}
```

### 字段说明：
- `task_id`：（可选）关联训练题目 ID，如 `A1.01`；
- `words[]`：**仅收录拼写错误的单词**（必须包含 `spelling` 与 `misspelling`）；
  - `spelling`（必填）：纠正后的正确拼写；
  - `type`：固定为 `"spelling_fix"`；
  - `misspelling`（必填）：学员初稿中的错拼形式；
  - `sentence`：原句出处；
  - `translation`：原句中文翻译；
  - `usage_note`：考研写作用法；
  - `grammar_note`：原句语法剖析。
