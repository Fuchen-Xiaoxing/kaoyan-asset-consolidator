# 考研英语二“外脑资产内化”课程框架与主题映射表 (Curriculum Map)

本课程框架依据考研英语二段落功能槽位组织训练，将 19 篇历年真题高分范文、61 条段落核心功能句式及 128 条场景动宾语素完整映射为两大主线、共 8 大训练主题。全部句式 ID 与资产库（assets/writing_brain/）保持 100% 精确对齐。

---

## 主线 A：大作文（Task 2）图表写作框架与语料内化

### 主题 A1：第一段·图表数据定格描述
* **功能定位**：首段图表概括。训练柱状图“动态增减/对比”与饼图“静态占比/极值”的精准描述骨架，要求载体、主体、时间周期、极值与走势四要素一次到位。
* **对应篇目与题目映射（A1.01 ~ A1.08）**：
  - `A1.01` (`T2_GEN_STR_001` / 2010 英二·手机用户增长)：双主体对照，动态柱状图显著增长与平稳对照。
  - `A1.02` (`T2_CHART_SEN_014` / 2015 英二·春节消费开支)：饼图极值与并列等值定格（新年礼物 40%，交通与聚餐各 20%）。
  - `A1.03` (`T2_CHART_SEN_006` / 2013 英二·兼职学生分布)：柱状图多阶段前缓后急走势定格（freshmen 至 senior）。
  - `A1.04` (2011 英二·轿车品牌份额)：多主体占比与动态消长（自主品牌 vs 日系 vs 美系）。
  - `A1.05` (2012 英二·员工工作满意度)：表格数据分类与满意度落差定格。
  - `A1.06` (2014 英二·城乡人口变迁)：城镇与乡村人口比例的历史性反超。
  - `A1.07` (2016 英二·学生旅游动机)：柱状图多动机降序排列与核心诉求。
  - `A1.08` (2017 英二·博物馆与参观量)：双柱图数量与参观人数双增长。
* **核心句式（task2/expressions.jsonl）**：
  - `T2_GEN_STR_001`: 图表首段双主体对照与极值还原骨架：载体、主体、时间周期、极值与走势四要素一次到位
  - `T2_CHART_SEN_014`: 饼图首段：极值与并列等值一次还原到位（accounts for the largest share of... at... while... each make up...）
  - `T2_CHART_SEN_006`: 首段「前缓后急」双节奏趋势收束：以 climbed from A to B 立主线，before surging to C 点亮突变极值

---

### 主题 A2：第二段·因果机制推演与五大场景语素组装
* **功能定位**：第二段归因剖析。训练因果总起句、深层机理展开句，并分批嵌入 5 大维度的动宾语素，彻底解决“空转套话、无话可说”的痛点。
* **核心句式（task2/expressions.jsonl）**：
  - `T2_GEN_SEN_001`: 次段归因维度定调：替代空转的 A number of factors contribute to...，开篇即给出归因维度
  - `T2_GEN_SEN_002`: 抽象趋势落地为具体结果的短句换气：意愿/趋势转化为可观测行为
  - `T2_GEN_SEN_003`: 双主体题型的对照收口连接句：明确宣告对照而非并列，替代平淡的 while / however
  - `T2_CHART_SEN_001`: 无生命主语一路驱动，以结果分词链把动作与结果压缩进一句
  - `T2_CHART_SEN_004`: 次段归因定维开篇：直接点破归因维度，替代空转的 Several factors contribute to...
  - `T2_CHART_SEN_012`: 次段定因开篇，一句锁定两条并列动因
* **五大场景语素维度组装（shared/morphemes.jsonl）**：
  1. **维度 1：个人发展与成长 (Personal Development & Career Growth)**
     - `M_JOB_004`: navigate one's career path (规划并驾驭职业发展道路)
     - `M_HAB_001`: get into the habit of being self-disciplined (养成高度自律的习惯)
     - `M_SCENE_042`: offer a competitive salary and transparent promotion paths (提供具竞争力的薪资与晋升通道)
     - `M_SCENE_043`: establish a harmonious working atmosphere (营造和谐融洽的工作氛围)
     - `M_SCENE_059`: gain practical work experience (积累宝贵的一线工作经验)
     - `M_SCENE_060`: ease their parents' financial burden (减轻家庭经济重担)
     - `M_SCENE_061`: hone professional and interpersonal skills (锤炼专业与人际交往技能)
     - `M_SCENE_105`: carry a heavy workload of coursework and exams (背负繁重的课业与备考重负)
     - `M_SCENE_106`: a rare chance to relax and recharge (难得的放松与身心充电契机)
  2. **维度 2：消费经济与生活 (Consumer Economy & Livelihood)**
     - `M_SCENE_013`: bring down production costs through mass manufacturing (通过规模化制造大幅压低生产成本)
     - `M_SCENE_014`: become a basic necessity of daily life (演变为大众日常生活不可或缺的刚需)
     - `M_SCENE_024`: cost-effective / offer great value for money (性价比高、经济实惠)
     - `M_SCENE_091`: stay close to family and friends (在人情往来中与亲友维系紧密纽带)
     - `M_SCENE_092`: become an unavoidable cost in festive celebrations (成为节假日必不可少的刚性支出)
     - `M_SCENE_095`: a contest of spending and ostentation (陷入盲目攀比与面子消费的怪圈)
     - `M_SCENE_119`: bring people more leisure time and higher disposable incomes (为民众带来更宽裕的闲暇与可支配收入)
  3. **维度 3：文化传承与交融 (Cultural Heritage & Spiritual Needs)**
     - `M_SCENE_093`: carry special cultural weight and emotional value (承载沉甸甸的文化底蕴与情感认同)
     - `M_SCENE_094`: convey affection and sincere gratitude (传递温情与真挚谢意)
     - `M_SCENE_097`: offer a fascinating glimpse into China's glorious past (让现代人得以一窥华夏文明的璀璨风貌)
     - `M_SCENE_101`: deepen one's understanding of traditional culture (深化对本土历史文化的认同与理解)
     - `M_SCENE_118`: the rapid expansion of cultural venues and public facilities (公共文化设施与新型场馆的快速扩展)
  4. **维度 4：科技互联网与创新 (Technology, Internet & Innovation)**
     - `M_SCENE_015`: the ongoing growth and digital leap in emerging economies (新兴经济体在数字化浪潮中的飞速跨越)
     - `M_SCENE_022`: increase investment in technological innovation (持续加大在前沿科技创新领域的研发投入)
     - `M_SCENE_023`: strengthen independent research and development capabilities (筑牢自主研发与核心技术攻关基底)
     - `M_SCENE_025`: improve energy efficiency and product reliability (优化能源利用效率与产品运行稳定性)
  5. **维度 5：公共治理与社会责任 (Public Governance & Social Responsibility)**
     - `M_SCENE_072`: promote integrated urban and rural development (推进城乡融合与一体化协调发展)
     - `M_SCENE_073`: the accelerated pace of urbanization (城镇化进程的纵深推进与结构重塑)
     - `M_SCENE_074`: the influx of surplus rural laborers into metropolitan areas (农村剩余劳动力向经济热点区域的持续流动)
     - `M_SCENE_075`: improve public infrastructure and social welfare networks (筑牢基建支撑与公共服务保障网)
     - `M_SCENE_109`: leverage rich tourism and cultural resources (深度盘活丰富的自然与人文旅游禀赋)
     - `M_SCENE_120`: ensure that cultural supplies keep pace with surging public demand (确保高品质文化供给紧跟公众日益增长的精神需求)

---

### 主题 A3：第三段·宏观总结、趋势预测与建议闭环
* **功能定位**：尾段收束升华。训练趋势预测、客观评价与合理化建议句式，实现首尾呼应、严谨闭环。
* **核心句式（task2/expressions.jsonl）**：
  - `T2_CHART_SEN_008`: 末段总结＋价值判断：以 indicates 引出趋势背后的观念转变
  - `T2_CHART_SEN_016`: 末段批判与前瞻双收口：给判断而非给态度，政企协同推进
  - `T2_CHART_SEN_003`: 末段 Only 状语前置倒装收束，强调唯有二者兼顾方能实现可持续增长
  - `T2_CHART_SEN_022`: 末段升华加批判转折双收口，先肯定趋势再点出潜在隐患

---

### 主题 A4：大作文真题全篇串联复盘
* **功能定位**：篇章连贯与宏观控盘。按年份逐篇对 2010–2017 年 8 篇大作文进行段落串联、首中尾三段逐句回译，复盘从段落骨架到整篇行文的衔接词与语法连贯性。
* **复盘篇目**：
  - 2010：发展中国家与发达国家手机用户增长走势（柱状图·科技与经济）
  - 2011：国内轿车品牌市场份额变化（柱状图·产业竞争与自主研发）
  - 2012：某公司员工工作满意度调查（表格·薪酬激励与职场人际）
  - 2013：某高校学生兼职情况（柱状图·兼职动因与技能锤炼）
  - 2014：城乡人口结构变迁（柱状图·城镇化与社会治理）
  - 2015：春节假期消费结构（饼图·节日经济与传统亲情）
  - 2016：某高校学生旅游目的调查（柱状图·休闲解压与视野拓宽）
  - 2017：博物馆数量与参观人数（柱状图·精神文化消费与公共服务供给）

---

## 主线 B：小作文（Task 1）应用文框架与语料内化

### 主题 B1：各文类首段·寒暄背景与写信目的
* **功能定位**：应用文破题开篇。集中训练各文类的规范首句（问候/背景铺垫 + 目的直陈），确保格式规范、语域适度、不拖泥带水。
* **覆盖文类与句式（task1/expressions.jsonl）**：
  - **建议信/咨询信**：
    - `T1_ADV_STR_002`: 分词状语前置：以「我知道你此刻的心情」开篇，自然滑入写信目的（私人书信可复用的开篇骨架）
    - `T1_ADV_SEN_009`: 书信开篇以情感锚点引出身份或事由
  - **投诉信**：
    - `T1_COM_SEN_001`: 投诉信开篇定调：一句话交代投诉意图、商品、购买渠道与购买时间四要素
    - `T1_COM_TMP_001`: 投诉信三段式全文槽位模板
  - **通知/倡议书**：
    - `T1_NOT_SEN_004`: 通知公告的招募启动句：先给理由再提需求
  - **邀请信**：
    - `T1_INV_STR_001`: 时间地点之后顺带交代会议目的与诚挚邀约
  - **道歉信**：
    - `T1_APO_SEN_001`: 开篇致歉定调，同时点明无法如期做某事
    - `T1_APO_SEN_002`: 先立期待、再砸意外，制造情感落差
  - **回复信/推荐信**：
    - `T1_REP_STR_001`: 以意愿语开篇，并用 before doing 把两个先后动作串联成一句
    - `T1_REC_SEN_001`: 推荐类介绍段首句：定位 + 承载物 + 价值三层递进

---

### 主题 B2：各文类正文·核心要点展开与逻辑衔接
* **功能定位**：正文要点充实。按三大功能群组组织，训练提建议、布活动、陈诉求的核心动宾语素与逻辑承接。
* **功能群组 1：提建议 / 做推荐（Advice & Recommendation）**
  - 核心篇目：2011（大学迎新筹备）、2014（合租生活与当地咨询）、2019（英语辩题推荐）、2020（泰山一日游规划）
  - 核心句式：
    - `T1_ADV_SEN_005`: 双重否定式强调：推动对方尽早采取行动，并给出收益闭环
    - `T1_ADV_SEN_006`: 警示句（反向加码）：用「不做就会怎样」的负面后果给建议加重锤
    - `T1_ADV_SEN_007`: 建议 + 理由：用定语从句说明为什么该这么做，避免只下命令
    - `T1_ADV_SEN_008`: 虚拟语气提建议：柔化口吻，适合私人书信中给对方支招
    - `T1_REC_SEN_002`: 给同伴提客观建议：形式主语句缓和语气，for 引领原因分句
    - `T1_REC_SEN_003`: 互动型建议：祈使句软化 + 收益闭环
* **功能群组 2：活动安排 / 招募要求（Event & Recruitment Notice）**
  - 核心篇目：2013（慈善义卖倡议）、2015（夏令营志愿者招募）、2021（行程规划线上会议）
  - 核心句式：
    - `T1_NOT_SEN_001`: 强调句型，把关键成分推到焦点位置作号召
    - `T1_NOT_SEN_002`: 品类范围列举，体现货品或活动丰富
    - `T1_NOT_SEN_005`: 招募征选类文书交代任职要求，品质前置作主语成为焦点
* **功能群组 3：解释原因 / 表达诉求（Complaints, Apologies & Explanations）**
  - 核心篇目：2012（网购电子词典投诉）、2018（急病取消拜访致歉）、2016/2017（接受邀请与安排）
  - 核心句式：
    - `T1_COM_SEN_002`: 前置让步—落差指控：先立信任筹码，再砸出缺陷事实，形成交涉力度
    - `T1_REP_SEN_001`: 给建议或立主张时先给动作、后补理由（for 引导原因分句）
    - `T1_ADV_SEN_013`: 论证议题具争议性并给出理由

---

### 主题 B3：各文类尾段·期盼回复与礼貌闭环
* **功能定位**：应用文规范结尾。训练各类信件与告示的礼貌收束、行动呼吁、期盼回复与温情寄语。
* **核心句式（task1/expressions.jsonl）**：
  - `T1_COM_SEN_003`: 诉求句：以“完全有理由要求”的交涉姿态提出名词化方案与解决期限 (投诉/求助闭环)
  - `T1_NOT_SEN_006`: 公文号召与报名方式及截止日期收口 (咨询/通知答疑通道)
  - `T1_ADV_SEN_011`: 尾段索取建议或协助时的合理化铺垫，先给对方一个凭什么麻烦你的理由 (建议益处期许)
  - `T1_INV_SEN_002`: 虚拟语气热切邀约收口 (邀请期盼与参会致意)
  - `T1_REC_SEN_004`: 推荐或邀请信双收益收尾：精神收获与情感收获并列
  - `T1_APO_SEN_003`: 向尊长高礼貌地提出改约或请求 (歉意重申与改约协商)
  - `T1_REP_SEN_002`: 向教授或上级柔性求教的收口句

---

### 主题 B4：小作文真题分类串联复盘
* **功能定位**：文类归类与考场实战还原。将 11 篇真题范文按同文体并轨通关：
  1. **建议与推荐类（4篇）**：2011（新生入学准备） -> 2014（合租生活与当地咨询） -> 2019（辩题建议） -> 2020（泰山一日游推荐）
  2. **通知与倡议类（2篇）**：2013（慈善义卖捐赠） -> 2015（夏令营志愿者招募）
  3. **回复与致谢类（2篇）**：2016（答谢并交流翻译） -> 2017（接受教授邀请并汇报要点）
  4. **投诉与致歉类（2篇）**：2012（网购词典故障交涉） -> 2018（突发急性病改约致歉）
  5. **邀请与筹备类（1篇）**：2021（行前会议线上邀请）
