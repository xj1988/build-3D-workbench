# 流程手册

给所有模型用的逐步操作。能力强的模型照做会更快，能力弱或上下文小的模型照做也不会走偏。

## 目录
1. 总路线
2. 阶段 A：理解需求 → 写配置
3. 阶段 B：生成与静态检查
4. 阶段 C：浏览器实测
5. 阶段 D：微调
6. 阶段 E：扩展（新积木 / 新底座 / 新主题）
7. 上下文不够时怎么续做

## 1. 总路线

```
需求 ──▶ 选预设 ──▶ 改配置 JSON ──▶ build ──▶ validate ──▶（有浏览器）实测 ──▶ 交付
                         ▲                                        │
                         └──────────── 发现问题，只改一处 ◀─────────┘
```

默认路线不写任何 JavaScript。只有用户要的造型 16 个积木都表达不了，才进入阶段 E。

## 2. 阶段 A：理解需求 → 写配置

1. 从用户的话里摘出：主题/用途、喜欢的颜色、想要的模块清单、要显示的数字、需要的进度步骤。没提到的全部用默认值。
2. 按 SKILL.md 第 0 步的四张表选 `base`、`theme`、每个模块的 `kit`。
3. 选最接近的预设，复制成 `OUT/config.json`：
   ```bash
   cp "SKILL_DIR/assets/presets/island-dream.json" "OUT/config.json"
   ```
4. 改 `config.json`：
   - 改 `title`、`subtitle`、`nickname`。
   - 改 `zones`：增删条目，每条至少有 `kit` 和 `name`；不写 `pos`，让引擎自动摆。
   - 每个区域的 `panel` 填用户给的内容；用户没给就写一句 `lead` 说明这个区域是干什么的，加 2～3 条示例 `items`，并在交付时说明是示例。
   - `stats`、`track`、`modes` 按用户的数字和流程改；用不上就删掉。
   - 删掉 `storageKey`（脚本会自动生成）。
5. 用户只说“做一个这样的工作台”、没有任何内容时：直接用 `island-dream` 预设，不需要写配置。

## 3. 阶段 B：生成与静态检查

```bash
python3 "SKILL_DIR/scripts/build_workbench.py" --config "OUT/config.json" --output "OUT/workbench.html"
python3 "SKILL_DIR/scripts/validate_workbench.py" "OUT/workbench.html"
```

- 生成失败会打印“生成失败：原因”，按原因改 JSON（最常见：多了逗号、少了引号、kit 名拼错、value 超出 0～1）。
- 出现“提醒”要处理：重叠就去掉 `pos` 或拉开距离；书脊太近就把 x 移到 |x| ≥ 1.3；文字过长就缩短。
- 全部 PASS 才进入下一步。

## 4. 阶段 C：浏览器实测

<a id="浏览器实测"></a>
有浏览器工具时必须做；没有就跳过，但交付时写明“未在浏览器实测”。

1. 起本地服务（后台运行，不要阻塞）：
   ```bash
   python3 -m http.server 8000 --bind 127.0.0.1 --directory "OUT"
   ```
   然后打开 `http://127.0.0.1:8000/workbench.html`。如果浏览器工具和命令行不在同一台机器（例如浏览器在用户电脑、命令行在云端），localhost 打不开，换用工具支持的方式（例如发布成 artifact，或让用户自己打开截图）。
2. 等加载层消失后再等 3 秒（入场镜头动画）。
3. 在页面里执行 `SKILL_DIR/scripts/browser_check.js` 的全部内容，读返回的 JSON：
   - `ok: true` → 通过。
   - `problems` 里有内容 → 逐条修。
   - 拿不到 `window.__WB` → 看控制台第一条红色错误，查 troubleshooting.md。
4. 截图检查（至少 3 张）：
   - 全景：底座完整在画面内，没有建筑互相穿插或悬空，浮标不互相盖住。
   - 按数字键 1～9 任选一个区域：特写清楚，右侧面板内容正确。
   - 点月亮按钮：夜景里窗户、路灯、串灯亮起，道路仍能看清。
5. 交互抽查：拖动旋转不误开面板；按 P 漫步，WASD 能走、能过桥、靠近建筑出现“按 E 进入”；按 T 换色；按 Esc 回全景。

## 5. 阶段 D：微调

每次只改一项，改完重新 build + validate（+ 实测）：

1. 文字 → 2. 配色 → 3. 区域位置/大小 → 4. 装饰密度 → 5. 画质。

常用对照表见 SKILL.md 第 3 步。位置微调时一次只移一个区域，每次移动 0.5～1.5。

## 6. 阶段 E：扩展

| 要扩展 | 读 | 改哪里 |
|---|---|---|
| 新建筑造型 | kits.md 第 3 节 | 模板 `§7` 加 `KITS.xxx`，`KIT_NAMES` 加名字，`catalog.json` 加说明 |
| 新底座形状 | bases.md 第 3 节 | 模板 `§6` 加 `BASES.xxx`，`normalize()` 白名单，`catalog.json` |
| 新配色 | themes.md 第 3 节 | 用 `--palette`，或写进 `THEMES` |

扩展规则：
- **改模板前先复制一份**（`workbench-template.backup.html`），改坏了能回退。
- 只在指定位置加代码，不重排、不“顺手优化”其他部分。
- 改完先 `node --check`（validate 脚本会做），再生成一个只含新积木的测试配置实测。
- 风格必须符合 style-dna.md。

## 7. 上下文不够时怎么续做

模板约 1000 行，不要整个读进上下文。需要看代码时：
- 用搜索跳转：`§6` 底座、`§7` 积木、`§9` 装饰、`§11` 昼夜、`§14` 界面、`§17` 漫步。
- 只读要改的那个函数。

快到上下文上限时，在 `OUT/PROGRESS.md` 记下：
```
已完成：配置 / 生成 / 校验 / 实测（哪些）
当前文件：OUT/workbench.html（可用）、OUT/config.json
未解决：第一条问题是什么、在哪个函数
下一步：具体要做的一件事
```
续做时先读这个文件和 `config.json`，不要重新生成已经可用的部分，不要在聊天里输出整份 HTML。
