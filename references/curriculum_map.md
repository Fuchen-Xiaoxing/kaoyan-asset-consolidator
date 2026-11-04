# 考研英语二“外脑资产内化”课程框架与主题映射表 (Curriculum Map)

本课程框架依据《需求说明书》中“按文章段落功能槽位组织训练”的核心原则，将 19 篇历年真题高分范文、61 条段落功能句式及 128 条场景动宾语素完整映射为两大主线、共 8 大训练主题。

---

## 主线 A：大作文（Task 2）图表写作框架与语料内化

### 主题 A1：第一段·图表数据定格描述
* **功能定位**：首段图表概括。训练柱状图“动态增减/对比”与饼图“静态占比/极值”的精准描述骨架，要求载体、主体、时间周期、极值与走势四要素一次到位。
* **对应篇目（2010–2017 真题首段）**：
  - `2010 英二`（手机用户增长）：双主体对照，动态柱状图显著增长与平稳对照。
  - `2011 英二`（轿车品牌份额）：多主体占比与动态消长（自主品牌 vs 日系 vs 德系）。
  - `2012 英二`（员工工作满意度）：表格数据分类与满意度落差定格。
  - `2013 英二`（兼职学生分布）：柱状图各类兼职占比与两极分化。
  - `2014 英二`（城乡人口变迁）：城镇与乡村人口比例的历史性反超。
  - `2015 英二`（春节消费开支）：饼图多项支出排序与峰值（礼品、聚餐等）。
  - `2016 英二`（学生旅游动机）：柱状图多动机降序排列与核心诉求。
  - `2017 英二`（博物馆与参观量）：双柱图数量与参观人数双增长。
* **核心句式（task2/expressions.jsonl）**：
  - `T2_GEN_STR_001`: As is distinctly illustrated in the [Chart Type], [Entity A] witnessed a(n) [Adjective] [Trend Noun] in [Metric], from [Data 1] in [Year 1] to [Data 2] in [Year 2], while the figure grew at a far more [Adjective] pace in [Entity B].
  - `T2_PIE_STR_001`: According to the data provided by the pie chart, [Dominant Entity] accounts for the lion's share of [Total Metric], reaching [Percentage 1], whereas [Entity B] and [Entity C] make up [Percentage 2] and [Percentage 3] respectively.
  - `T2_BAR_STR_001`: The bar chart vividly portrays that [Subject] underwent a dramatic shift between [Year 1] and [Year 2], with [Category A] climbing markedly to [Number 1].

---

### 主题 A2：第二段·因果机制推演与五大场景语素组装
* **功能定位**：第二段归因剖析。训练因果总起句、深层机理展开句，并分批嵌入 5 大维度的动宾语素，彻底解决“空转模板、无话可说”的痛点。
* **核心句式（task2/expressions.jsonl）**：
  - `T2_GEN_SEN_001`: This wide [gap / discrepancy] was due in large part to the marked differences in [Dimension].
  - `T2_GEN_SEN_002`: A host of interrelated factors have converged to drive this unmistakable trend.
  - `T2_GEN_SEN_003`: First and foremost, [Cause Clause], which serves as the primary catalyst behind [Phenomenon].
  - `T2_GEN_SEN_004`: Moreover, it is worth noting that [Secondary Cause], thereby fueling the rapid expansion of [Target].
  - `T2_GEN_SEN_005`: In stark contrast, [Counter Subject] has been severely impeded by [Obstacle], leaving little room for further growth.
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
  - `T2_GEN_SEN_006`: From what has been analyzed above, it is safe to predict that this trend will continue in the foreseeable future.
  - `T2_GEN_SEN_007`: In view of the discussion above, government authorities and relevant institutions should join hands to [action].
  - `T2_GEN_SEN_008`: Only by striking a balance between [Aspect A] and [Aspect B] can we ensure sustainable growth.
  - `T2_GEN_SEN_009`: To sum up, while [Phenomenon] brings tangible benefits, rational guidance is indispensable to avoid potential hazards.

---

### 主题 A4：大作文真题全篇串联复盘
* **功能定位**：篇章连贯与宏观控盘。按年份逐篇对 2010–2017 年 8 篇大作文进行段落串联、首中尾三段逐句回译，复盘从段落骨架到整篇行文的衔接词与语法连贯性。
* **复盘篇目**：
  - 2010：发展中国家与发达国家手机用户增长走势（柱状图·科技与经济）
  - 2011：国内轿车品牌市场份额变化（饼图·产业竞争与自主研发）
  - 2012：某公司员工工作满意度调查（表格·薪酬激励与职场人际）
  - 2013：某高校学生兼职情况（饼图·兼职动因与技能锤炼）
  - 2014：城乡人口结构变迁（柱状图·城镇化与社会治理）
  - 2015：春节假期消费结构（饼图·节日经济与传统亲情）
  - 2016：某高校学生旅游目的调查（柱状图·休闲解压与视野拓宽）
  - 2017：博物馆数量与参观人数（线柱图·精神文化消费与公共服务供给）

---

## 主线 B：小作文（Task 1）应用文框架与语料内化

### 主题 B1：各文类首段·寒暄背景与写信目的
* **功能定位**：应用文破题开篇。集中训练各文类的规范首句（问候/背景铺垫 + 目的直陈），确保格式规范、语域适度、不拖泥带水。
* **覆盖文类与句式（task1/expressions.jsonl）**：
  - **建议信/咨询信**：
    - `T1_ADV_STR_001`: I am writing this letter to share with you a few constructive recommendations on [topic].
    - `T1_ADV_STR_002`: Knowing that/how [clause], I am writing to offer you some practical advice on [purpose].
  - **投诉信**：
    - `T1_CMP_STR_001`: I am writing to lodge a formal complaint regarding the defective [item/service] I purchased from your store.
    - `T1_CMP_STR_002`: Having placed great confidence in your brand, I was dismayed to discover that [problem].
  - **通知/倡议书**：
    - `T1_NOT_STR_001`: Notice is hereby given that [Event] is scheduled to be held on [Date] in [Location].
    - `T1_NOT_STR_002`: We are delighted to announce that an exciting campaign will be launched to [purpose].
  - **邀请信**：
    - `T1_INV_STR_001`: On behalf of [Organization], I have the great pleasure of inviting you to attend [Event].
  - **道歉信**：
    - `T1_APO_STR_001`: I am writing to express my deepest apologies for [mistake / missing appointment].
  - **回复信/感谢信**：
    - `T1_REP_STR_001`: Thank you very much for your congratulations. I am writing in reply to share with you my insights on [topic].

---

### 主题 B2：各文类正文·核心要点展开与逻辑衔接
* **功能定位**：正文要点充实。按三大功能群组组织，训练提建议、布活动、陈诉求的核心动宾语素与逻辑承接。
* **功能群组 1：提建议 / 做推荐（Advice & Recommendation）**
  - 核心篇目：2011（大学迎新筹备）、2014（合租生活与当地咨询）、2019（英语辩题推荐）、2020（泰山一日游规划）
  - 句式与语素：
    - `T1_ADV_SEN_005`: It is never too early to [action], which will undoubtedly help you [benefit].
    - `T1_ADV_SEN_006`: You had better [action], or [negative outcome] may follow.
    - `T1_ADV_SEN_007`: You are highly encouraged to [action], who will [benefit].
    - `M_LIFE_001`: manage monthly budget by keeping a record of spending
    - `M_SOC_001`: get along with one's roommates
    - `M_SCENE_009`: fit in with the local life smoothly
    - `M_SCENE_096`: be home to countless historical relics and stone carvings
* **功能群组 2：活动安排 / 招募要求（Event & Recruitment Notice）**
  - 核心篇目：2013（慈善义卖倡议）、2015（夏令营志愿者招募）、2021（行程规划线上会议）
  - 句式与语素：
    - `T1_NOT_SEN_001`: The event is scheduled to take place at [venue] from [time 1] to [time 2].
    - `T1_NOT_SEN_002`: Applicants are expected to possess strong communication skills and an earnest sense of responsibility.
    - `M_SCENE_016`: ensure the smooth running of the summer camp
    - `M_SCENE_017`: maintain order and provide guidance for participants
    - `M_SCENE_018`: receive and register distinguished guests
* **功能群组 3：解释原因 / 表达诉求（Complaints, Apologies & Explanations）**
  - 核心篇目：2012（网购电子词典投诉）、2018（急病取消拜访致歉）、2016/2017（接受邀请与安排）
  - 句式与语素：
    - `T1_CMP_SEN_001`: Much to my disappointment, the product failed to function properly shortly after its delivery.
    - `T1_CMP_SEN_002`: Under such circumstances, I would be grateful if you could either replace the defective goods or refund my payment in full.
    - `T1_APO_SEN_001`: Regrettably, an unexpected emergency has arisen, which compels me to postpone our prearranged appointment.
    - `M_SCENE_001`: offer a constructive and acceptable solution
    - `M_SCENE_066`: be stricken with an acute illness and hospitalized
    - `M_SCENE_067`: reschedule our meeting at your earliest convenience

---

### 主题 B3：各文类尾段·期盼回复与礼貌闭环
* **功能定位**：应用文规范结尾。训练各类信件与告示的礼貌收束、行动呼吁、期盼回复与温情寄语。
* **核心句式（task1/expressions.jsonl）**：
  - `T1_GEN_CLS_001`: I would greatly appreciate your prompt attention to this matter and look forward to hearing from you soon. (投诉/求助闭环)
  - `T1_GEN_CLS_002`: Should you have any inquiries or need further details, please feel free to reach out to me. (咨询/通知答疑通道)
  - `T1_ADV_CLS_001`: Hopefully, you will find these recommendations conducive to your upcoming endeavor. (建议益处期许)
  - `T1_INV_CLS_001`: We sincerely look forward to your presence and valuable contribution at the forum. (邀请期盼)
  - `T1_APO_CLS_001`: Once again, please accept my heartfelt apologies for any inconvenience this change may cause. (致歉重申)

---

### 主题 B4：小作文真题分类串联复盘
* **功能定位**：文类归类与考场实战还原。将 11 篇真题范文按同文体并轨通关：
  1. **建议与推荐类（4篇）**：2011（新生入学准备） $\rightarrow$ 2014（合租生活与当地咨询） $\rightarrow$ 2019（辩题建议） $\rightarrow$ 2020（泰山一日游推荐）
  2. **通知与倡议类（2篇）**：2013（慈善义卖捐赠） $\rightarrow$ 2015（夏令营志愿者招募）
  3. **回复与致谢类（2篇）**：2016（答谢并交流翻译） $\rightarrow$ 2017（接受教授邀请并汇报要点）
  4. **投诉与致歉类（2篇）**：2012（网购词典故障交涉） $\rightarrow$ 2018（突发急性病改约致歉）
  5. **邀请与筹备类（1篇）**：2021（行前会议线上邀请）
