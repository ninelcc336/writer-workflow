# writer-system

`writer-system` 是一个给长篇小说创作使用的 agent 工作流模板仓库。

它不是某一本书的项目，也不内置样板小说正文。它的用途是：

1. 作为模板仓库被 fork
2. 在新仓库里由 agent 完成新书初始化
3. 用统一流程推进章节规划、写作、审核和状态同步

## 仓库结构

- `AGENTS.md`：给 agent 的运行契约
- `docs/`：给人和 agent 的流程文档
- `templates/`：新书初始化时要复制和填写的模板
- `schemas/`：结构化状态文件规范
- `scripts/`：命令入口与脚本实现
- `book/`：fork 后真正的书稿工作区

其中 `templates/` 现在同时包含：

- canon 模板
- state YAML 模板
- 初始化摘要模板

## 建议使用方式

### 1. fork 本仓库

把本仓库作为一本新书的起点。

### 2. 让 agent 初始化新书

在空白仓库中，先让 agent 执行“初始化新书”流程，而不是直接写第一章。

常见指令：

- 帮我初始化一本新书
- 根据这个 brief 建立新书骨架
- 为这本书生成 canon 和 state 基础文件

### 3. 通过双审核节点推进章节

每章固定流程：

1. 章节计划
2. 人审计划并记录 `record-review --stage plan --decision approved`
3. 正文骨架 / 提示词
4. 正文初稿（可选）
5. 去 AI 味修订
6. 正文审查报告
7. 人审正文并记录 `record-review --stage final --decision approved`
8. 状态同步
9. 汇总渲染

## 当前版本定位

当前版本是“工作流模板骨架”，重点是：

- 约束 agent 的行为顺序
- 明确新书初始化方式
- 规定结构化状态该怎么放
- 规定章节推进必须经过哪些关口

当前版本还没有做：

- 模型 API 自动写作脚本
- 图形界面
- 多书集中管理

## 当前可执行命令

当前已经有真实脚本实现的是：

- `init-book`
- `init-state`
- `plan-chapter`
- `record-review`
- `prompt-chapter`
- `draft-chapter`
- `humanize-chapter`
- `review-draft`
- `sync-state`
- `render-artifacts`

在 Windows / PowerShell 下可直接调用：

```powershell
.\scripts\init-book.cmd --title "书名" --genre "题材" --platform "平台" --hook "核心卖点" --protagonist "主角" --length "100万字"
```

这些命令当前都属于“最小可运行实现”：

- 能创建、读取、更新工作流文件
- 能串起完整主流程
- 还不等于高质量智能创作引擎

也就是说，它们现在更像“可靠的流程骨架”，不是“强内容生成器”。

正文骨架命令示例：

```powershell
.\scripts\prompt-chapter.cmd --chapter 1
```

## 从哪里开始看

建议按这个顺序阅读：

1. `AGENTS.md`
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
12. `docs/superpowers/specs/2026-06-30-writer-system-design.md`
