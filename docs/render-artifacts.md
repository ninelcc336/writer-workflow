# 衍生物渲染说明

本文件把 `render-artifacts` 定义成一套可直接执行的流程。

目标只有一个：

- 在 `sync-state` 完成后，从 canon 与 state 中生成便于阅读、审稿和回顾的衍生文件

`render-artifacts` 的职责是“生成可读产物”，不是改正文，也不是改 state。

## 一、触发条件

满足以下条件后，才允许执行 `render-artifacts`：

- `sync-state` 已完成
- 当前章 state diff 报告已存在
- `book/state/*.yaml` 已更新
- 当前章正式版本已存在

## 二、禁止前提

有以下任一情况时，不得执行 `render-artifacts`：

- state 尚未同步
- 当前章仍处于草稿阶段
- 当前章 state diff 缺失
- state 仍有明显占位值未清理

## 三、最小输入

执行 `render-artifacts` 时，至少需要这些输入：

1. `book/state/*.yaml`
2. 当前章 `state diff` 报告
3. 当前章正式版本
4. 必要的 canon 文件

## 四、典型输出物

V1 至少应支持两类衍生物：

### 1. 剧情回顾类

例如：

- 最近章节剧情 recap
- 当前卷剧情摘要

### 2. 状态总览类

例如：

- 角色状态总览
- 伏笔追踪总览
- 势力与资源总览

## 五、执行步骤

### 步骤 1：读取最新 state

优先读取：

- `book/state/characters.yaml`
- `book/state/factions.yaml`
- `book/state/foreshadows.yaml`
- `book/state/power_state.yaml`
- `book/state/chapter_index.yaml`

同时参考：

- 当前章 `state diff`
- 当前章正式版本

### 步骤 2：决定要重建哪些 artifacts

V1 建议至少重建：

- `book/artifacts/recaps/plot-recap.md`
- `book/artifacts/recaps/state-recap.md`

如果书已很长，也可以只重建受影响部分，但 V1 可以先全量重建。

### 步骤 3：渲染剧情回顾

剧情回顾应回答：

- 最近发生了什么
- 当前卷推进到了哪里
- 现在主要矛盾是什么
- 下一章最相关的接续点是什么

要求：

- 以事实压缩为主
- 不做长段文学复述

### 步骤 4：渲染状态总览

状态总览应回答：

- 当前有哪些关键角色
- 他们各自处于什么状态
- 当前有哪些关键势力和资源
- 哪些伏笔未回收

要求：

- 结构清楚
- 便于 agent 和人类快速读懂

### 步骤 5：写入 artifacts

建议输出到：

- `book/artifacts/recaps/plot-recap.md`
- `book/artifacts/recaps/state-recap.md`

如果后续要扩展，还可新增：

- `foreshadow-recap.md`
- `faction-recap.md`

## 六、渲染阶段禁止事项

在 `render-artifacts` 阶段，不允许：

- 反向修改 `book/state/*.yaml`
- 反向修改正文
- 用艺术化扩写替代结构化回顾
- 将 artifacts 当成唯一事实源

## 七、完成标准

满足以下条件时，可视为 `render-artifacts` 完成：

- 至少 1 份剧情回顾已生成
- 至少 1 份状态总览已生成
- 内容与最新 state 保持一致

完成后，本章主流程才算真正闭环。
