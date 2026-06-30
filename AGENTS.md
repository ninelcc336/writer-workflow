# AGENTS

本仓库是一个“新书创作工作流模板”，不是现成书稿。

所有 agent 进入本仓库后，必须先判断当前处于哪一种状态，再决定下一步动作。

## 1. 仓库定位

- 本仓库会被 fork 为某一本新书的独立仓库。
- 具体书稿内容位于 `book/`。
- `templates/` 提供初始化模板。
- `schemas/` 定义结构化状态文件应包含什么。
- `docs/` 提供给人和 agent 的流程说明。

## 2. 启动时的必读顺序

开始任何实质工作前，优先读取：

1. `README.md`
2. `docs/workflow.md`
3. `docs/init-book.md`
4. `docs/plan-chapter.md`
5. `docs/prompt-chapter.md`
6. `docs/draft-chapter.md`
7. `docs/humanize-chapter.md`
8. `docs/review-draft.md`
9. `docs/sync-state.md`
10. `docs/render-artifacts.md`
11. `docs/review-checklist.md`
12. `book/canon/`
13. `book/state/`

如果 `book/canon/` 或 `book/state/` 尚未建立完整基础文件，必须先进入初始化流程。

## 3. 初始化分支

### 3.1 空白新书状态

满足以下任一条件时，视为“空白新书状态”：

- `book/canon/setting.md` 不存在
- `book/canon/premise.md` 不存在
- `book/state/characters.yaml` 不存在

此时必须优先执行：`init-book`

禁止动作：

- 不得直接写正文
- 不得直接生成章节提示词
- 不得臆造后续卷纲

### 3.2 半初始化状态

如果 canon 已有基础文件，但 state 缺失或明显不完整，则先执行：`init-state`

此时也不得直接进入章节工作流。

“明显不完整”包括但不限于：

- 仍大量保留 `待补充`
- 仍是模板默认值
- 缺少主角以外必须存在的基础状态
- 只有占位结构，没有真实内容

## 4. 章节工作流顺序

只有当 `book/canon/` 和 `book/state/` 都具备基础信息后，才允许进入章节工作流。

标准顺序：

1. `plan-chapter`
2. 等待人类审核章节计划
3. `prompt-chapter`
4. `draft-chapter`
5. `humanize-chapter`
6. `review-draft`
7. 等待人类审核正文
8. `sync-state`
9. `render-artifacts`

## 5. 两个人工审核节点

### 审核点一：章节计划

未通过前：

- 不得写正式正文
- 不得提前更新 state

### 审核点二：正文成稿

未通过前：

- 不得修改 `book/state/*.yaml`
- 不得覆盖 `book/drafts/.../final.md`
- 不得生成下一章正式提示包

## 6. 信息源优先级

如果多个信息源冲突，按以下优先级处理：

1. 用户当前回合的明确指令
2. 本文件 `AGENTS.md`
3. `book/canon/`
4. `book/state/`
5. `book/artifacts/`
6. 历史提示词、旧草稿、旧报告

旧提示词不能覆盖新的 canon 或 state。

## 7. 各逻辑角色的职责

### Planner

- 读取 canon 和 state
- 输出章节计划
- 输出必写节点、字数预算、风险点
- 输出章末落点和计划检查结果
- 输出正文骨架 / 提示词

### Drafter

- 根据通过审核的计划写正文
- 不得擅自扩展重大设定
- 产出的是初稿，不是定稿

### Reviewer

- 检查连续性
- 检查文风风险
- 检查节拍完成度
- 输出 `blocker / warning / note` 分级报告

### State Syncer

- 只在正文审核通过后更新结构化状态
- 输出 state diff
- 渲染剧情汇总和状态汇总
- 不得在 state 中写入正文里不存在的重大事实

## 8. 最低产出要求

每次章节推进后，至少要产出这些文件：

- 一份章节计划
- 一份正文草稿
- 一份正文审查报告
- 一份状态差异报告

## 9. 总原则

- 连续性优先于速度
- 人类审核优先于 agent 自治
- 结构化状态优先于临时上下文记忆
- 可以推迟写作，不能跳过初始化和审核边界
