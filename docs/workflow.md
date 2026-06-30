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
2. `record-review --stage plan --decision approved`
3. `prompt-chapter`
4. `draft-chapter`（可选）
5. `humanize-chapter`
6. `review-draft`
7. 人工审核正文并落文件：`record-review --stage final --decision approved`
8. `sync-state`
9. `render-artifacts`

`plan-chapter` 的详细执行规则见：

- `docs/plan-chapter.md`

`prompt-chapter` 的详细执行规则见：

- `docs/prompt-chapter.md`

`draft-chapter` 的详细执行规则见：

- `docs/draft-chapter.md`

`humanize-chapter` 的详细执行规则见：

- `docs/humanize-chapter.md`

`review-draft` 的详细执行规则见：

- `docs/review-draft.md`

`sync-state` 的详细执行规则见：

- `docs/sync-state.md`

`render-artifacts` 的详细执行规则见：

- `docs/render-artifacts.md`

文件职责区分：

- `chapter_brief` 是章节输入简报，通常由人提供或先行整理
- `chapter_plan` 是 agent 基于 brief、canon、state 产出的施工图
- `chapter_prompt` 是 agent 基于 plan 组装出的正文骨架 / 提示词
- `chapter_draft` 是 agent 基于 prompt 写出的正文初稿
- `chapter_humanized_draft` 是 agent 对正文初稿做的主动修订版本
- `draft_review` 是 agent 对正文初稿做的人审前质检报告
- `state_diff` 是 agent 在正文通过人审后生成的事实回写报告
- `artifacts_recaps` 是基于最新 state 生成的可读回顾产物

## 三、两个审核节点

### 章节计划审核

通过前不得进入正文写作。

审核通过不是口头约定，必须落成文件。

建议约定：

- `book/drafts/chapter-XXX/human-plan-review.yaml`

章节计划至少需要包含：

- 本章目标
- 3 到 5 个节拍
- 字数预算
- 必写节点
- 禁忌和风险点
- 章末钩子或冷收束说明

建议直接使用模板：

- `templates/chapter_plan.template.md`

计划通过后，建议先生成：

- `book/drafts/chapter-XXX/prompt.md`

### 正文审核

通过前不得更新 state。

审核通过不是口头约定，必须落成文件。

建议约定：

- `book/drafts/chapter-XXX/human-final-review.yaml`

正文审核通过后，agent 才能：

- 写入定稿
- 更新结构化状态
- 生成剧情汇总和状态汇总

在此之前：

- 初稿只能视为工作文件
- 初稿不得直接替代定稿
- 建议先完成 `review-draft`，再交给人审

建议约定：

- 人审通过版本落为 `book/drafts/chapter-XXX/final.md`
- `sync-state` 首次执行时，如果缺少 `state-update.yaml`，脚本会先生成脚手架并停止
- 之后再执行 `sync-state`

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
