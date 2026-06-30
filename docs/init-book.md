# 新书初始化说明

本文件把 `init-book` 定义成一套可直接执行的流程，而不是抽象概念。

目标只有一个：

- 在空白新书仓库里，建立最小可用的创作骨架

初始化完成后，仓库应具备：

- 最小 canon
- 最小 state
- 一组最小但明确的长篇连载强约束
- 一份供人审核的初始化摘要

在这之前，agent 不得直接开始写第 1 章。

## 一、触发条件

满足以下任一条件时，必须执行 `init-book`：

- 用户明确说“初始化一本新书”
- 用户给出一个新书 brief，希望开始搭建创作仓库
- `book/canon/premise.md` 不存在
- `book/canon/setting.md` 不存在
- `book/state/characters.yaml` 不存在

补充说明：

- 即使 `book/state/*.yaml` 已经存在，只要它们仍是模板占位内容，也仍然属于初始化流程范围

## 二、执行原则

`init-book` 要遵守 4 条原则：

1. 先收集最小高价值信息，再创建文件。
2. 先建骨架，再填内容，不追求一次补全一切。
3. 明确区分“用户明确给出”与“agent 推断”。
4. 初始化结束后必须停下，等待人审，而不是直接写章节。

补充原则：

5. 初始化阶段至少要写入“主线承诺、升级主轴、平台节奏、主角红线”四类约束。

## 三、输入信息清单

初始化时最少需要确认 5 类信息：

1. 题材
2. 目标平台
3. 核心卖点
4. 主角定位
5. 目标篇幅

可选补充信息：

- 文风偏好
- 参考作品
- 节奏偏好
- 是否偏爽文、悬疑、群像、言情、现实向等

## 四、建议提问顺序

为了减少用户负担，建议 agent 按以下顺序提问，不要一上来铺十几个问题。

### 第一步：确认作品定位

至少问清：

- 这本书是什么题材
- 主要发在哪个平台

### 第二步：确认核心卖点

至少问清：

- 这本书最想让读者上头的地方是什么

### 第三步：确认主角

至少问清：

- 主角是谁
- 主角当前处境是什么
- 主角最强的吸引点是什么

### 第四步：确认篇幅和节奏预期

至少问清：

- 预计写多长
- 是否偏快节奏

### 第五步：确认风格参照

可问可不问：

- 有没有想靠近的参考风格

## 五、执行步骤

以下步骤按顺序执行，不能跳。

### 步骤 1：整理初始化简报

把用户给出的信息整理成一份内部初始化简报，至少包含：

- 书名占位或项目代称
- 题材
- 平台
- 核心卖点
- 主角定位
- 目标篇幅
- 文风偏好
- 明确输入项
- 推断项

要求：

- 明确标注哪些是用户原话
- 明确标注哪些是 agent 补全推断

### 步骤 2：创建目录

确保以下目录存在：

- `book/canon/`
- `book/canon/characters/`
- `book/canon/volumes/`
- `book/state/`
- `book/drafts/`
- `book/artifacts/reports/`
- `book/artifacts/recaps/`

### 步骤 3：创建最小 canon 文件

按模板生成这些文件：

- `book/canon/premise.md`
- `book/canon/setting.md`
- `book/canon/style_rules.md`
- `book/canon/characters/protagonist.md`
- `book/canon/volumes/volume-01-outline.md`

填写原则：

- 用户已明确提供的信息直接写入
- 用户未明确但初始化必须存在的信息，可做最小推断
- 推断内容必须写清“这是当前假设”
- 暂时无法确定的内容保留 `待补充`
- 但不能把所有高价值约束都留成 `待补充`

建议使用的模板来源：

- `templates/premise.template.md`
- `templates/setting.template.md`
- `templates/style_rules.template.md`
- `templates/protagonist.template.md`
- `templates/volume_outline.template.md`

### 步骤 4：创建最小 state 文件

创建以下文件：

- `book/state/characters.yaml`
- `book/state/factions.yaml`
- `book/state/foreshadows.yaml`
- `book/state/power_state.yaml`
- `book/state/chapter_index.yaml`

填写原则：

- `characters.yaml` 至少要有主角一条
- `factions.yaml` 可先为空列表或只放主角阵营
- `foreshadows.yaml` 可为空列表
- `power_state.yaml` 至少要有主角基础状态和核心规则占位
- `chapter_index.yaml` 初始化阶段可为空列表

如果模板仓库中已预置这些文件，执行 `init-book` 时应覆盖占位内容，而不是把占位内容当成完成状态。

建议使用的模板来源：

- `templates/characters.template.yaml`
- `templates/factions.template.yaml`
- `templates/foreshadows.template.yaml`
- `templates/power_state.template.yaml`
- `templates/chapter_index.template.yaml`

### 步骤 5：生成初始化摘要

必须生成一份初始化摘要，建议路径：

- `book/artifacts/reports/init-book-summary.md`

摘要必须回答 4 个问题：

1. 创建了哪些文件
2. 哪些内容来自用户明确输入
3. 哪些内容是 agent 推断
4. 还有哪些空缺需要人补
5. 本次初始化已经写入了哪些强约束

建议使用模板：

- `templates/init_book_summary.template.md`

### 步骤 6：停止并等待审核

初始化完成后，必须暂停并等待用户确认。

此时允许的动作：

- 解释初始化结果
- 根据用户意见修改初始化文件

此时不允许的动作：

- 直接开始 `plan-chapter`
- 自动补完整卷大纲
- 自动生成正文

## 六、初始化输出标准

执行完成后，仓库里至少应出现这些文件：

### Canon

- `book/canon/premise.md`
- `book/canon/setting.md`
- `book/canon/style_rules.md`
- `book/canon/characters/protagonist.md`
- `book/canon/volumes/volume-01-outline.md`

### State

- `book/state/characters.yaml`
- `book/state/factions.yaml`
- `book/state/foreshadows.yaml`
- `book/state/power_state.yaml`
- `book/state/chapter_index.yaml`

### Report

- `book/artifacts/reports/init-book-summary.md`

## 七、初始化阶段禁止事项

初始化阶段禁止以下行为：

- 直接写第 1 章正文
- 跳过主角文件
- 假装 state 已完整
- 伪造完整百万字大纲
- 把推断内容写成用户已确认事实
- 把“主线承诺、升级轴、人设红线、平台适配”全部留空

## 八、初始化完成标准

满足以下条件，可视为 `init-book` 完成：

- 最小 canon 文件已存在
- 最小 state 文件已存在
- 初始化摘要已生成
- 用户确认初始化结果可接受

但这不等于已经可以直接进入章节规划。

进入 `plan-chapter` 之前，至少还要保证这些关键项不再是占位值：

- `setting.md` 的时间背景、空间背景、社会环境、约束条件
- `protagonist.md` 的身份、初始处境、短期必须解决的问题
- `volume-01-outline.md` 的阶段一冲突与结果
- `characters.yaml` 中主角的位置、能力概述、未收束主线
- `power_state.yaml` 中主角基础战力、当前约束、系统或世界硬规则

只有在这些条件成立后，才允许进入章节规划。

## 九、推荐输出话术

当 agent 执行完 `init-book` 后，建议用类似结构向用户汇报：

1. 已建立哪些基础文件
2. 我根据你的输入补了哪些最小假设
3. 哪些地方仍待你确认
4. 请先审核初始化结果，再进入第 1 章规划
