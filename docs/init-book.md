# 新书初始化说明

本文件规定 agent 在 fork 出来的空白新书仓库中，如何完成初始化。

## 一、初始化触发条件

以下任一情况都应触发 `init-book`：

- 用户明确说“初始化一本新书”
- `book/canon/premise.md` 不存在
- `book/canon/setting.md` 不存在
- `book/state/characters.yaml` 不存在

## 二、初始化时应收集的信息

初始化只问高价值信息，避免一次性追问过多细节。

最少应明确：

- 题材
- 目标平台
- 核心卖点
- 主角定位
- 目标篇幅

可选信息：

- 参考作品
- 文风偏好
- 是否偏爽文、悬疑、群像、言情等

## 三、初始化产出

初始化后至少应生成：

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

### 说明文件

- 初始化摘要
- 哪些内容来自用户明确输入
- 哪些内容来自 agent 推断
- 哪些位置仍然留空，需要人补充

## 四、初始化阶段禁止事项

- 不得直接写第 1 章正文
- 不得跳过主角文件
- 不得伪造完整长篇大纲
- 不得假装 state 已经完整

## 五、初始化完成标准

满足以下条件，可视为初始化完成：

- canon 最小骨架存在
- state 最小骨架存在
- 用户确认初始化结果可接受

只有满足这些条件，才能进入章节规划。
