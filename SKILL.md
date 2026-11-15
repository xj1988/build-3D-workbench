---
name: build-3d-workbench
description: 用一份 JSON 配置生成奶油色微缩风 Three.js 3D 工作台（个人主页/看板/小世界），底座可选立体书、漂浮岛、方块沙盘，7 套配色一键切换，16 种建筑积木自由组合，带昼夜、移轴、漫步小人、可点击详情面板和本地编辑。用户提到 3D 工作台、立体书、漂浮岛、沙盘、微缩小镇、可漫游个人空间、把计划/数据/作品做成 3D 场景、或想复刻这种手作纸艺风格时使用。附完整模板、生成脚本、校验脚本和详细手册，任何模型照步骤执行都能做出同样效果。
---

# 3D 工作台生成器

一句话：**先把用户的需求翻译成一份 JSON 配置，再用脚本注入模板。** 模板里已经有完整的场景、灯光、后期、交互和界面，你只负责“选底座、选配色、选建筑、填文字”。

记 `SKILL_DIR` = 本文件所在目录，`OUT` = 用户想要的输出目录（命令里替换成实际路径）。

## 必须遵守的 6 条

1. **不要从零写 Three.js。** 永远从 `assets/workbench-template.html` 生成。从零写的版本一定达不到这个质感（移轴、泛光、绒感材质、剪纸层、实例化花草都是调过的）。
2. **默认只改配置。** 99% 的需求靠 SCENE JSON 就能满足：标题、底座、配色、建筑种类和位置、面板内容、统计卡、进度条、昼夜文案。
3. **需要新造型时才写代码**，而且只能按 [积木手册](references/kits.md) 的“新增积木”规则加一个 `KITS.xxx`，不改其他部分。
4. **配色只用主题。** 不要在积木里写死色值；要新颜色就加一套主题（见 [配色手册](references/themes.md)）。
5. **一次只改一层**：配置 → 文字 → 配色 → 位置 → 新积木。每改一层就生成并校验一次，保留上一份能用的文件。
6. **只用用户给的内容。** 不去读用户的聊天记录、账号、照片、浏览器数据来“让它更真实”。没给内容就用通用示例文字，并在交付时说明是示例。

## 第 0 步：把需求翻译成配置（最重要）

按顺序回答 4 个问题，答案直接写进配置。用户没说的，用括号里的默认值，**不要停下来追问**。

**① 底座 `base`**（默认 `island`）

| 用户说的 | 选 |
|---|---|
| 手账、日记、书、读书、创作记录、旅行记录、“像一本书” | `book` 立体书 |
| 岛、小世界、梦想、成长、店铺、品牌、游戏感、“漂浮的” | `island` 漂浮岛 |
| 沙盘、模型、学习、项目、团队、作品集、展示台、“方的” | `diorama` 方块沙盘 |

**② 配色 `theme`**（默认 `cream`）

| 关键词 | 选 |
|---|---|
| 百搭、奶油、蓝色、默认 | `cream` 奶油蓝 |
| 粉、樱花、少女、春天、温柔 | `sakura` 樱花粉 |
| 绿、抹茶、自然、学习、自律 | `matcha` 抹茶绿 |
| 海、夏天、旅行、清爽、蓝绿 | `ocean` 海盐蓝 |
| 橙、橘子、美食、店铺、活力、暖 | `sunset` 橘子汽水 |
| 紫、梦、睡眠、疗愈、星空 | `lavender` 薰衣草 |
| 极简、高级、灰、商务、作品集 | `oat` 燕麦极简 |

用户给了具体色值或品牌色 → 用 `--palette` 做自定义主题（[配色手册](references/themes.md) 第 3 节）。

**③ 区域 `zones`**（3～9 个，推荐 5～7 个）

把用户的“模块/板块/功能/习惯/目标”逐个对应到积木。完整含义和数据联动见 [积木手册](references/kits.md)：

| 用户的模块像… | 用积木 | 用户的模块像… | 用积木 |
|---|---|---|---|
| 收集、灵感、入口、待办池 | `well` 灵感井 | 习惯、能量、日常循环 | `windmill` 风车 |
| 选题、愿望、候选、标签 | `noteTree` 便签树 | 专注、休息、户外、冒险 | `tent` 营地 |
| 调研、对标、参考、规划 | `lookout` 瞭望台 | 试验、培养、新品、错题 | `greenhouse` 温室 |
| 工作室、正在做、基地、家 | `cottage` 小屋 | 远大目标、梦想、研究 | `observatory` 天文台 |
| 打卡、连续天数、出勤 | `plaza` 打卡广场 | 发布、提交、订单、寄出 | `postOffice` 邮局 |
| 长期目标、KPI、里程碑 | `lighthouse` 灯塔 | 阅读、知识、课程、资料 | `bookTower` 书塔 |
| 成果、作品、收获、积累 | `garden` 菜园 | 流量、人气、社交、聚会 | `fountain` 喷泉 |
| 休息、菜单、店铺、补给 | `cafe` 咖啡车 | 活动、娱乐、周期、高光 | `ferris` 摩天轮 |

规则：
- 同一种积木最多用 2 次；相邻区域尽量用不同高度（高：灯塔/书塔/摩天轮/风车/瞭望台；矮：广场/营地/喷泉/菜园/温室），画面才有节奏。
- `name` ≤ 6 个字，`info` ≤ 10 个字（浮标里显示）。
- `pos` **可以不写**，引擎会按 9 个预设空位自动摆放，保证不撞河、不出界。只有用户明确要求布局时才写（坐标规则见 [配置手册](references/config-schema.md#坐标)）。
- 进度型积木（灯塔、广场、风车）给 `value`（0～1）或 `panel.progress`；数量型积木（便签树、菜园）由 `panel.items` 的条数决定。

**④ 文字**：`title`（≤ 12 字）、`subtitle`、`stats`（≤ 4 个计数卡）、`track`（底部进度条，2～7 步，不需要就删掉）、`modes` 三个时段的名字和一句话。

写配置时**复制最接近的预设再改**，不要从空白开始：

| 预设 | 底座 · 配色 | 场景 |
|---|---|---|
| `island-dream` | 漂浮岛 · 奶油蓝 | 个人成长 / 梦想岛（模板默认） |
| `island-shop` | 漂浮岛 · 橘子汽水 | 小店经营 |
| `book-creator` | 立体书 · 奶油蓝 | 内容创作手账 |
| `book-travel` | 立体书 · 海盐蓝 | 旅行手账 |
| `diorama-study` | 方块沙盘 · 抹茶绿 | 学习基地 |

## 第 1 步：生成

```bash
# 看所有选项
python3 "SKILL_DIR/scripts/build_workbench.py" --list

# 直接用预设（可叠加覆盖标题、配色、底座）
python3 "SKILL_DIR/scripts/build_workbench.py" --preset island-dream --theme sakura --title "我的小岛" --output "OUT/workbench.html"

# 用自己的配置（推荐：先 cp 一个预设到 OUT/config.json 再改）
python3 "SKILL_DIR/scripts/build_workbench.py" --config "OUT/config.json" --output "OUT/workbench.html"

# 自定义色板
python3 "SKILL_DIR/scripts/build_workbench.py" --config "OUT/config.json" --palette "OUT/palette.json" --output "OUT/workbench.html"
```

- 输出已存在会拒绝覆盖；确认可以覆盖时才加 `--force`。
- 脚本输出的“提醒”（重叠、太靠近书脊、文字过长）要处理掉再交付。
- **没有 Python**：复制模板，只改 `/* SCENE_BEGIN */` 和 `/* SCENE_END */` 之间的 JSON（保持合法 JSON，不要删标记），并把 `storageKey` 改成新名字。

## 第 2 步：检查

```bash
python3 "SKILL_DIR/scripts/validate_workbench.py" "OUT/workbench.html"
```

有浏览器工具时再实测（详见 [流程手册](references/workflow.md#浏览器实测)）：
1. 用 HTTP 地址打开（`python3 -m http.server 8000 --directory OUT`），`file://` 在部分浏览器里加载不了模块。
2. 等加载层消失约 3 秒，执行 `scripts/browser_check.js` 的内容，`ok: true` 才算通过。
3. 截图看：全景完整、没有建筑互相穿插、浮标文字可读；按 T 换色、点月亮看夜景、按 6 看特写。

没有浏览器时，只报告静态检查结果，**明确说画面未实测**，不要编造截图或效果描述。

## 第 3 步：常见微调

| 用户想要 | 改哪里 |
|---|---|
| 换颜色 | `theme`；或页面上按 T 实时切换（会记住） |
| 某个建筑挪位置 / 变大 / 转向 | 该区域的 `pos` / `scale`（0.5～1.6）/ `rot`（角度） |
| 不要河 | `"river": {"enabled": false}` |
| 不要底部进度条 / 计数卡 | 删掉 `track` / 把 `stats` 设为 `[]` |
| 花草树太多 / 太少 | `decor.trees`、`decor.flowers`（0～2 倍） |
| 电脑卡 | `"quality": "low"`（关泛光移轴、减少花草，建筑不变） |
| 小红书竖图 | `frameRatio: "3:4"`，页面按 F 出取景框，H 隐藏界面后截图 |
| 新的建筑造型 | 按 [积木手册](references/kits.md#新增积木) 加一个 `KITS.xxx` |
| 新的底座形状 | 按 [底座手册](references/bases.md#新增底座) 加一个 `BASES.xxx` |

## 第 4 步：交付

交付一个能直接打开的 HTML，并用几句话说清：
- 怎么打开（双击或本地服务器），需要联网（Three.js 和字体走 CDN）。
- 怎么玩：拖动旋转、滚轮缩放、点建筑看详情、P 漫步、D 巡游、T 换色、S 截图、F 取景框、H 隐藏界面、铅笔按钮编辑内容。
- 修改只存在当前浏览器，不会写回文件、不跨设备同步。
- 哪些内容是示例、哪些检查没做（例如“未在浏览器实测”）。

## 参考文档（按需读，一次读一个）

| 要做的事 | 读 |
|---|---|
| 每一步的详细操作、上下文不够时怎么续做 | [流程手册](references/workflow.md) |
| 配置里每个字段的含义、取值和坐标 | [配置手册](references/config-schema.md) |
| 16 种积木的样子和用法、怎么新增积木 | [积木手册](references/kits.md) |
| 3 种底座、怎么新增底座 | [底座手册](references/bases.md) |
| 7 套主题、怎么调自定义配色 | [配色手册](references/themes.md) |
| 这种风格的“基因”：比例、材质、灯光、后期，改代码前必读 | [风格基因](references/style-dna.md) |
| 白屏、穿模、太暗、卡顿等问题 | [排障手册](references/troubleshooting.md) |
| 交付前逐项核对 | [验收清单](references/acceptance.md) |
| 给用户/其他 agent 的提示词模板 | [提示词](references/prompts.md) |

模板代码按 `§1`～`§18` 分节，搜索 `§7` 就能跳到积木库，不需要通读全文件。
