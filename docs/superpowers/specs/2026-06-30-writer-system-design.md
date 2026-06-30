# Writer System 设计说明

日期：2026-06-30

## 1. 目标

`writer-system` 是一个可复用的长篇小说创作工作流模板仓库，用于配合 Codex、Claude Code 这类编程 agent 进行创作辅助。

这个仓库不是某一本书的项目仓库，而是一个会被 fork 出去、用于新书创作的工作流脚手架。

核心目标：

- 让 agent 能稳定辅助约 100 万字量级的长篇小说创作
- 优先保证连续性、可维护性和人工验收
- 保持模板通用，不绑定某一本书的设定和目录

V1 不做的事：

- 多书中央管理平台
- Web UI 或 SaaS 平台
- 强绑定某个模型 API
- 重型数据库系统

## 2. 产品定位

这个仓库的定位是“模板仓库”，不是“运行中的写作平台”。

预期使用方式：

1. 以 `writer-system` 为模板，fork 出一本新书仓库。
2. 在新仓库里，让 agent 先完成新书初始化。
3. 然后用同一套工作流推进章节规划、正文起草、审稿、状态同步和衍生物生成。

核心原则：

- `writer-system` 只提供工作流脚手架
- 具体书稿内容在 fork 之后生成
- agent 必须先学会如何初始化一本空白新书，再开始写章节

## 3. 人类介入规则

每一章采用两个强制人工审核节点。

### 审核点一：章节计划

人类审核内容：

- 节拍设计
- 必写情节
- 章末钩子方向
- 字数预算
- 风险和禁忌

在这个审核通过前，agent 不得开始写正文。

### 审核点二：正文成稿

人类审核内容：

- 正文可读性
- 节奏和爽点
- 连续性与伏笔兑现质量
- 是否达到可发布水准

在这个审核通过前，agent 不得同步结构化状态。

## 4. 工作流模型

整个系统采用“显式阶段工作流”，而不是自由散射式提示词驱动。

### 4.1 新书初始化

命令概念：`init-book`

职责：

- 为一本全新的书创建最小 canon 和 state 基础文件
- 只收集高价值信息，不一上来追问大量细节
- 禁止在基础资料缺失时直接写章节

预期输入：

- 题材与目标平台
- 核心卖点
- 主角概念
- 目标篇幅
- 可选的文风参照

预期输出：

- 初版 canon 文件
- 初版结构化 state 文件
- 一份供人审核的初始化摘要

### 4.2 单章生产流程

推荐命令顺序：

1. `plan-chapter`
2. 人审章节计划
3. `draft-chapter`
4. `humanize-chapter`
5. 人审正文
6. `sync-state`
7. `render-artifacts`

### 4.3 硬边界

在正文审核通过之前：

- 不允许修改结构化状态
- 不允许覆盖正式定稿
- 不允许生成下一章正式提示包

## 5. 仓库结构

模板仓库必须保持轻量、通用、可 fork。

```text
writer-system/
  AGENTS.md
  README.md
  docs/
    workflow.md
    init-book.md
    review-checklist.md
    superpowers/
      specs/
        YYYY-MM-DD-writer-system-design.md
  templates/
    premise.template.md
    setting.template.md
    style_rules.template.md
    protagonist.template.md
    volume_outline.template.md
    chapter_brief.template.md
  schemas/
    characters.schema.yaml
    factions.schema.yaml
    foreshadows.schema.yaml
    power_state.schema.yaml
    chapter_index.schema.yaml
  scripts/
    init-book
    plan-chapter
    draft-chapter
    review-draft
    sync-state
    render-artifacts
  book/
    canon/
    state/
    drafts/
    artifacts/
```

说明：

- `book/` 是模板仓库内的空白创作工作区
- fork 后由 agent 在 `book/` 内初始化具体书稿结构
- 模板仓库本身不应内置某本样板小说作为依赖

## 6. Canon、State、Drafts、Artifacts 的分层

系统需要把“长期真实事实”和“便于阅读的输出物”严格分离。

### 6.1 Canon

用途：

- 存放人类主导或人类确认的故事基础信息
- 低频修改，但重要性很高

典型内容：

- 故事主旨
- 世界设定
- 文风规则
- 人物卡
- 分卷纲要
- 章节简报

### 6.2 State

用途：

- 存放会影响后续写作判断的结构化事实
- 作为连续性检查的主要输入源

典型内容：

- 角色状态
- 势力归属与关系
- 未兑现伏笔
- 战力与关键资源状态
- 章节索引

### 6.3 Drafts

用途：

- 存放章节生产过程中的工作文件
- 保留清晰的创作痕迹

典型内容：

- 章节计划
- 提示词
- 初稿
- 去 AI 味修订稿
- 定稿

### 6.4 Artifacts

用途：

- 存放便于阅读、审阅、汇总的派生产物
- 这些文件可以重建，不应充当唯一事实源

典型内容：

- 剧情回顾
- 审稿报告
- 状态差异报告
- 剧情汇总
- 数值或能力汇总

核心规则：

- 只要一个事实可以被程序校验，它就不应只存在于自然语言段落中

## 7. 结构化状态设计

V1 只保留最有价值的结构化状态，不追求全面数据库化。

### 7.1 `characters.yaml`

每个角色至少应包含：

- `id`
- `name`
- `faction`
- `status`
- `current_location`
- `relationship_to_protagonist`
- `capability_summary`
- `latest_chapter`
- `open_threads`

### 7.2 `factions.yaml`

每个势力至少应包含：

- `id`
- `name`
- `leader`
- `members_summary`
- `territory`
- `resources`
- `relationship_to_protagonist`
- `latest_change_chapter`

### 7.3 `foreshadows.yaml`

每个伏笔至少应包含：

- `id`
- `description`
- `introduced_in`
- `current_status`
- `related_characters`
- `expected_payoff_window`
- `last_progress_chapter`

### 7.4 `power_state.yaml`

这个文件只记录会影响后续剧情判断的关键事实，例如：

- 主角基础战力
- 属性共享或成长规则
- 关键装备
- 宠物或同伴战斗状态
- 基地模块
- 稀有资源

不应把所有临时修辞或每个微小事件都结构化。

### 7.5 `chapter_index.yaml`

每章至少应包含：

- `chapter_no`
- `title`
- `volume`
- `status`
- `summary`
- `must_payoff_ids`
- `new_state_changes`
- `ending_hook`

## 8. 审核与校验系统

agent 不只是“产出正文”，还必须产出“可审阅的报告”。

### 8.1 计划覆盖检查

在 `plan-chapter` 阶段，应检查：

- 所有必须处理的伏笔是否已标记为“兑现 / 推进 / 延后”
- 节拍预算是否前后一致
- 本章是否有明确的章末钩子，或者明确的冷收束

### 8.2 连续性检查

在正文审查阶段，应检查：

- 已死亡角色是否重新行动
- 势力关系是否无缘无故改变
- 人物位置是否与当前状态冲突
- 战力、装备、资源是否前后打架
- 本章结尾是否和既定的下一步方向一致

### 8.3 文风与平台风险检查

工作流应内置一轮类似“去 AI 痕迹”的审查，重点检查：

- 套板化程度副词
- 面部表情模板
- 机械过渡词
- 过量精确秒数
- 模板化对话标签
- 过长、手机阅读不友好的段落
- 模板化章末钩子

### 8.4 状态差异检查

在正文审核通过之后、渲染衍生物之前，应产出结构化 diff：

- 哪些角色状态改变了
- 哪些伏笔推进或回收了
- 哪些势力关系变了
- 哪些资源或能力发生变化

## 9. Agent 逻辑角色

即使只有一个 agent 执行，也应在逻辑上拆分职责。

### 9.1 Planner

职责：

- 读取 canon 和 state
- 生成章节计划和提示词包

限制：

- 不直接写最终正文

### 9.2 Drafter

职责：

- 根据通过审核的计划撰写正文

限制：

- 不得擅自发明重大设定变更

### 9.3 Reviewer

职责：

- 做连续性检查
- 做文风风险检查
- 检查节拍是否完成

限制：

- 不得更新结构化状态

### 9.4 State Syncer

职责：

- 在正文通过审核后更新结构化状态
- 渲染衍生汇总文件

限制：

- 在正文审核通过前不得运行

## 10. `AGENTS.md` 的要求

`AGENTS.md` 是给编码型 agent 的核心运行契约。

它至少需要明确：

- 启动时必须先读哪些文件
- 工作流顺序
- 初始化分支逻辑
- 人类审核节点
- 审核前的禁止动作
- 多种信息源冲突时的优先级

建议的优先级顺序：

1. 人类明确指令
2. `AGENTS.md`
3. canon
4. state
5. artifacts
6. 历史提示词

初始化分支要求：

- 如果 canon 基础文件缺失，先执行 `init-book`
- 如果 canon 已存在，但 state 不完整，先执行 `init-state`
- 只有 canon 和 state 都齐备后，才能进入章节工作流

## 11. 模板文件要求

模板仓库应该提供“空白但有引导”的模板文件，而不是示例小说正文。

必需模板：

- `premise.template.md`
- `setting.template.md`
- `style_rules.template.md`
- `protagonist.template.md`
- `volume_outline.template.md`
- `chapter_brief.template.md`

这些模板应优化四件事：

- 快速填充
- 降低歧义
- 方便 agent 理解
- 支持长篇连续创作

## 12. 命令接口

即使 V1 还没完全脚本化，命令名也应该先固定。

必需命令概念：

- `init-book`
- `plan-chapter`
- `draft-chapter`
- `review-draft`
- `sync-state`
- `render-artifacts`

后续可追加命令：

- `init-state`
- `humanize-chapter`
- `validate-continuity`
- `generate-with-model`

规则：

- 即使尚未完全自动化，命令身份也应保持稳定

## 13. V1 范围

V1 只追求最小可用闭环，不做过度扩张。

必须具备的能力：

1. 能根据 brief 初始化一本新书
2. 能依据 canon、state 和上章上下文生成章节计划
3. 能对正文输出连续性与文风风险报告
4. 能在正文审核通过后把结果同步回结构化状态
5. 能从结构化状态渲染出可读的剧情和状态汇总

暂缓能力：

- 模型 API 自动写作流水线
- 多书统一管理
- 图形界面
- 重型 schema 校验工具链

## 14. 验收标准

如果一个刚 fork 出来的仓库能稳定完成以下流程，就说明模板设计成立：

1. 用户要求 agent 初始化一本新书
2. agent 创建最小 canon 与 state 骨架
3. 用户审核通过初始化结果
4. agent 基于书籍基础信息规划第 1 章
5. 用户审核通过章节计划
6. agent 起草第 1 章并输出审稿报告
7. 用户审核通过正文
8. agent 同步 state 并生成 recap 类衍生物

如果这条链能稳定跑通，模板就具备实用价值。

## 15. 实现阶段待定问题

以下内容留到下一阶段决定：

- schema 的具体格式规范
- 脚本语言选型
- 审核逻辑中规则校验与 prompt 校验的比例
- 提示词是持久文件还是临时生成物
- `book/` 是否保留为默认工作目录名

## 16. 总结

`writer-system` 应该被设计成一个可 fork 的长篇小说 agent 工作流模板仓库。

它的优先级应当是：

- 连续性优先于速度
- 结构化状态优先于纯上下文记忆
- 人工审核优先于全自动自治
- 可复用脚手架优先于某本书的个性化耦合

这个仓库真正要教会 agent 的，不只是“如何续写一本书”，而是“如何从空白开始建立一本书的可维护创作流程”。
