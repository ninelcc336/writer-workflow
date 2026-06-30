# 工作流说明

本文件描述 fork 出去的一本新书仓库应如何推进。

## 一、初始化阶段

当一本新书刚创建时，`book/` 目录是空的。

此时 agent 必须先完成初始化，而不是直接写章节。

初始化目标：

- 建立最小 canon
- 建立最小 state
- 生成一份初始化摘要给人审核

最小 canon 建议包括：

- `book/canon/premise.md`
- `book/canon/setting.md`
- `book/canon/style_rules.md`
- `book/canon/characters/protagonist.md`
- `book/canon/volumes/volume-01-outline.md`

最小 state 建议包括：

- `book/state/characters.yaml`
- `book/state/factions.yaml`
- `book/state/foreshadows.yaml`
- `book/state/power_state.yaml`
- `book/state/chapter_index.yaml`

注意：

- 模板仓库可以预置这些文件的示例形态
- 但只要内容仍是 `待补充` 或模板默认值，就不能视为初始化完成

## 二、章节阶段

每一章固定按以下顺序执行：

1. `plan-chapter`
2. 人工审核章节计划
3. `draft-chapter`
4. `humanize-chapter`
5. `review-draft`
6. 人工审核正文
7. `sync-state`
8. `render-artifacts`

`plan-chapter` 的详细执行规则见：

- `docs/plan-chapter.md`

`draft-chapter` 的详细执行规则见：

- `docs/draft-chapter.md`

`humanize-chapter` 的详细执行规则见：

- `docs/humanize-chapter.md`

`review-draft` 的详细执行规则见：

- `docs/review-draft.md`

文件职责区分：

- `chapter_brief` 是章节输入简报，通常由人提供或先行整理
- `chapter_plan` 是 agent 基于 brief、canon、state 产出的施工图
- `chapter_draft` 是 agent 按 plan 写出的正文初稿
- `chapter_humanized_draft` 是 agent 对正文初稿做的主动修订版本
- `draft_review` 是 agent 对正文初稿做的人审前质检报告

## 三、两个审核节点

### 章节计划审核

通过前不得进入正文写作。

章节计划至少需要包含：

- 本章目标
- 3 到 5 个节拍
- 字数预算
- 必写节点
- 禁忌和风险点
- 章末钩子或冷收束说明

建议直接使用模板：

- `templates/chapter_plan.template.md`

### 正文审核

通过前不得更新 state。

正文审核通过后，agent 才能：

- 写入定稿
- 更新结构化状态
- 生成剧情汇总和状态汇总

在此之前：

- 初稿只能视为工作文件
- 初稿不得直接替代定稿
- 建议先完成 `review-draft`，再交给人审

## 四、State 的使用原则

`book/state/` 是后续写作的结构化事实源。

判断规则：

- 影响后续剧情判断的事实，要写入 state
- 只属于修辞和文学表达的内容，不写入 state

例如应入 state 的内容：

- 角色生死、阵营、位置
- 关键资源获得或消耗
- 势力归属变化
- 伏笔出现、推进、兑现

例如不应入 state 的内容：

- 一次情绪化比喻
- 局部段落的文采表达
- 无后续影响的临时描写

## 五、Artifacts 的定位

`book/artifacts/` 里的内容便于阅读，但不是唯一真相。

它们应该来自 canon 和 state 的派生渲染。

常见 artifacts：

- 剧情回顾
- 角色状态汇总
- 伏笔清单
- 审稿报告
- 状态差异报告
