#!/usr/bin/env python3
"""把一份 JSON 配置（或内置预设）注入通用 3D 工作台模板，生成可直接打开的 HTML。

用法示例：
  python3 build_workbench.py --list
  python3 build_workbench.py --preset island-dream --output out/dream.html
  python3 build_workbench.py --preset book-creator --theme sakura --title "我的手账" --output out/a.html
  python3 build_workbench.py --config my.json --output out/b.html
  python3 build_workbench.py --config my.json --palette my-palette.json --output out/c.html

只做两件事：校验配置 → 替换模板里 SCENE_BEGIN/END（以及可选的 THEMES_BEGIN/END）之间的 JSON。
不会修改模板本身，不联网，不读取任何个人文件。
"""
import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'assets' / 'workbench-template.html'
CATALOG = json.loads((ROOT / 'assets' / 'catalog.json').read_text(encoding='utf-8'))
PRESETS = ROOT / 'assets' / 'presets'
RATIOS = ['3:4', '4:3', '16:9', '9:16', '1:1']
PALETTE_KEYS = ['paper', 'paperEdge', 'cover', 'grass', 'grass2', 'rock', 'rock2', 'water', 'waterLight', 'accent', 'accent2',
                'butter', 'lav', 'mist', 'sage', 'sage2', 'sage3', 'wood', 'wood2', 'stone', 'stone2', 'soil', 'soil2',
                'roof', 'roof2', 'cream', 'ink', 'metal', 'skin']
CSS_KEYS = ['paper', 'paper2', 'accent', 'accent2', 'olive', 'ink', 'ink2']
HEX = re.compile(r'^#[0-9A-Fa-f]{6}$')
warnings = []


class ConfigError(ValueError):
    pass


def need(cond, msg):
    if not cond:
        raise ConfigError(msg)


def block(html, name):
    m = re.search(r'/\* ' + name + r'_BEGIN \*/(.*?)/\* ' + name + r'_END \*/', html, re.S)
    need(m, '模板缺少标记 ' + name + '_BEGIN/END')
    return m


def encode(value):
    text = json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    # 防止 JSON 中的文字提前结束 <script>
    return (text.replace('&', '\\u0026').replace('<', '\\u003c').replace('>', '\\u003e')
            .replace('\u2028', '\\u2028').replace('\u2029', '\\u2029'))


def replace_block(html, name, value):
    pattern = r'(/\* ' + name + r'_BEGIN \*/).*?(/\* ' + name + r'_END \*/)'
    out, n = re.subn(pattern, lambda m: m[1] + encode(value) + m[2], html, flags=re.S)
    need(n == 1, '模板标记缺失或重复：' + name)
    return out


def is_num(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def check_text(v, label, maxlen=200):
    need(isinstance(v, str), label + ' 必须是文字')
    if len(v) > maxlen:
        warnings.append(f'{label} 超过 {maxlen} 字，界面可能放不下')


def validate_palette(p, label):
    need(isinstance(p, dict), label + ' 必须是对象')
    need(isinstance(p.get('c'), dict), label + '.c（3D 颜色）必须是对象')
    for k, v in p['c'].items():
        need(k in PALETTE_KEYS, f'{label}.c 有未知键 {k}，可用：{", ".join(PALETTE_KEYS)}')
        need(isinstance(v, str) and HEX.match(v), f'{label}.c.{k} 必须是 #RRGGBB')
    missing = [k for k in ['paper', 'grass', 'water', 'accent', 'accent2', 'sage', 'roof'] if k not in p['c']]
    if missing:
        warnings.append(f'{label} 缺少 {missing}，会回退到 cream 的颜色')
    for k, v in (p.get('css') or {}).items():
        need(k in CSS_KEYS and isinstance(v, str) and HEX.match(v), f'{label}.css.{k} 无效（可用 {CSS_KEYS}，值为 #RRGGBB）')
    sky = p.get('sky')
    if sky is not None:
        for m in ['morning', 'afternoon', 'night']:
            arr = sky.get(m)
            need(isinstance(arr, list) and len(arr) == 4 and all(isinstance(x, str) and HEX.match(x) for x in arr),
                 f'{label}.sky.{m} 必须是 4 个 #RRGGBB：[天顶, 地平线, 地面, 太阳光晕]')


def validate_scene(s, themes):
    need(isinstance(s, dict), '配置必须是 JSON 对象')
    for k in ['title', 'zones']:
        need(k in s, '缺少字段 ' + k)
    check_text(s['title'], 'title', 24)
    if 'subtitle' in s:
        check_text(s['subtitle'], 'subtitle', 60)
    if 'nickname' in s:
        check_text(s['nickname'], 'nickname', 12)
    need(s.get('base', 'island') in CATALOG['bases'], 'base 只能是：' + ' / '.join(CATALOG['bases']))
    need(s.get('theme', 'cream') in themes, 'theme 只能是：' + ' / '.join(themes))
    need(s.get('quality', 'standard') in ['standard', 'low'], 'quality 只能是 standard 或 low')
    need(s.get('frameRatio', '3:4') in RATIOS, 'frameRatio 只能是：' + ' / '.join(RATIOS))
    if 'pageNotes' in s:
        need(isinstance(s['pageNotes'], list) and all(isinstance(x, str) for x in s['pageNotes']), 'pageNotes 必须是文字数组')
    river = s.get('river', {})
    need(isinstance(river, dict), 'river 必须是对象')
    if 'points' in river:
        pts = river['points']
        need(isinstance(pts, list) and len(pts) >= 3 and all(isinstance(p, list) and len(p) == 2 and all(is_num(v) for v in p) for p in pts),
             'river.points 至少 3 个 [x, z] 点')
    if 'bridges' in river:
        need(isinstance(river['bridges'], list) and all(is_num(t) and 0.05 <= t <= 0.95 for t in river['bridges']),
             'river.bridges 是 0.05~0.95 之间的数（沿河位置比例）')
    decor = s.get('decor', {})
    need(isinstance(decor, dict), 'decor 必须是对象')
    for k in ['trees', 'flowers']:
        if k in decor:
            need(is_num(decor[k]) and 0 <= decor[k] <= 2, f'decor.{k} 是 0~2 的密度倍数')
    for k in ['walkers', 'planes', 'boats']:
        if k in decor:
            need(isinstance(decor[k], int) and 0 <= decor[k] <= 16, f'decor.{k} 是 0~16 的整数')
    modes = s.get('modes', {})
    need(isinstance(modes, dict), 'modes 必须是对象')
    for m, v in modes.items():
        need(m in ['morning', 'afternoon', 'night'], 'modes 只能有 morning / afternoon / night')
        need(isinstance(v, dict), f'modes.{m} 必须是对象')
        for f in ['name', 'sub']:
            if f in v:
                check_text(v[f], f'modes.{m}.{f}', 40)
        if 'focus' in v:
            need(isinstance(v['focus'], list) and all(isinstance(i, int) and 0 <= i < 9 for i in v['focus']), f'modes.{m}.focus 是区域序号数组（从 0 开始）')
    stats = s.get('stats', [])
    need(isinstance(stats, list) and len(stats) <= 4, 'stats 最多 4 个')
    for i, st in enumerate(stats):
        need(isinstance(st, dict) and isinstance(st.get('k'), str) and (is_num(st.get('v')) or isinstance(st.get('v'), str)),
             f'stats[{i}] 需要 {{"k": 文字, "v": 数字或文字}}')
    tr = s.get('track')
    if tr is not None:
        need(isinstance(tr, dict) and isinstance(tr.get('steps'), list) and 2 <= len(tr['steps']) <= 7 and all(isinstance(x, str) for x in tr['steps']),
             'track.steps 需要 2~7 个文字步骤（不要底部进度条就删掉 track）')
        need(isinstance(tr.get('current', 1), int) and 1 <= tr.get('current', 1) <= len(tr['steps']), 'track.current 从 1 开始，不能超过步骤数')
    zones = s['zones']
    need(isinstance(zones, list) and 1 <= len(zones) <= CATALOG['limits']['zones_max'], f'zones 需要 1~{CATALOG["limits"]["zones_max"]} 个')
    ids = set()
    lim = CATALOG['limits']
    placed = []
    for i, z in enumerate(zones):
        lab = f'zones[{i}]'
        need(isinstance(z, dict), lab + ' 必须是对象')
        need(z.get('kit') in CATALOG['kits'], f'{lab}.kit 只能是：' + ' / '.join(CATALOG['kits']))
        check_text(z.get('name', ''), lab + '.name', 10)
        need(z.get('name'), lab + '.name 不能为空')
        if 'info' in z:
            check_text(z['info'], lab + '.info', 14)
        zid = z.get('id', f'zone{i}')
        need(zid not in ids, f'{lab}.id 重复：{zid}')
        ids.add(zid)
        if 'value' in z:
            need(is_num(z['value']) and 0 <= z['value'] <= 1, f'{lab}.value 是 0~1 的小数')
        if 'scale' in z:
            need(is_num(z['scale']) and 0.5 <= z['scale'] <= 1.6, f'{lab}.scale 是 0.5~1.6')
        if 'rot' in z:
            need(is_num(z['rot']), f'{lab}.rot 是角度（数字）')
        if 'pos' in z:
            p = z['pos']
            need(isinstance(p, list) and len(p) == 2 and all(is_num(v) for v in p), f'{lab}.pos 是 [x, z]')
            need(lim['x'][0] <= p[0] <= lim['x'][1] and lim['z'][0] <= p[1] <= lim['z'][1],
                 f'{lab}.pos 超出范围：x 在 {lim["x"]}，z 在 {lim["z"]}')
            if s.get('base') == 'book' and abs(p[0]) < 1.3:
                warnings.append(f'{lab} 太靠近书脊（|x|<1.3），建筑会压在折缝上')
        panel = z.get('panel', {})
        need(isinstance(panel, dict), lab + '.panel 必须是对象')
        for f in ['lead', 'text', 'itemsTitle', 'checklistTitle']:
            if f in panel:
                check_text(panel[f], f'{lab}.panel.{f}', 600)
        if 'chips' in panel:
            need(isinstance(panel['chips'], list) and all(isinstance(c, dict) and isinstance(c.get('k'), str) for c in panel['chips']), lab + '.panel.chips 是 [{k, v}]')
        if 'items' in panel:
            need(isinstance(panel['items'], list) and all(isinstance(c, dict) and isinstance(c.get('t'), str) for c in panel['items']), lab + '.panel.items 是 [{t, s}]')
        if 'checklist' in panel:
            need(isinstance(panel['checklist'], list) and all(isinstance(c, dict) and isinstance(c.get('t'), str) and isinstance(c.get('done', False), bool) for c in panel['checklist']), lab + '.panel.checklist 是 [{t, done:true/false}]')
        if 'progress' in panel:
            pr = panel['progress']
            need(isinstance(pr, dict) and is_num(pr.get('value')) and 0 <= pr['value'] <= 1, lab + '.panel.progress.value 是 0~1')
        if 'tags' in panel:
            need(isinstance(panel['tags'], list) and all(isinstance(t, str) for t in panel['tags']), lab + '.panel.tags 是文字数组')
        placed.append((z, i))
    # 粗略检查显式坐标的重叠
    exp = [(z, i) for z, i in placed if 'pos' in z]
    for a in range(len(exp)):
        for b in range(a + 1, len(exp)):
            za, ia = exp[a]
            zb, ib = exp[b]
            d = math.dist(za['pos'], zb['pos'])
            ra = CATALOG['kits'][za['kit']]['r'] * za.get('scale', 1)
            rb = CATALOG['kits'][zb['kit']]['r'] * zb.get('scale', 1)
            if d < ra + rb:
                warnings.append(f'zones[{ia}] 和 zones[{ib}] 距离 {d:.1f}，小于占地半径之和 {ra + rb:.1f}，可能重叠')


def load_json(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except json.JSONDecodeError as e:
        raise ConfigError(f'{path} 不是合法 JSON：第 {e.lineno} 行第 {e.colno} 列 {e.msg}')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--list', action='store_true', help='列出预设、底座、主题、积木')
    ap.add_argument('--preset', help='assets/presets 里的预设名（不带 .json）')
    ap.add_argument('--config', type=Path, help='完整配置 JSON 路径（字段见 references/config-schema.md）')
    ap.add_argument('--palette', type=Path, help='自定义配色 JSON（结构同模板里的一个主题），会以 custom 名称加入并启用')
    ap.add_argument('--output', type=Path, help='输出 HTML 路径')
    ap.add_argument('--title'); ap.add_argument('--subtitle'); ap.add_argument('--nickname')
    ap.add_argument('--base', choices=list(CATALOG['bases']))
    ap.add_argument('--theme')
    ap.add_argument('--quality', choices=['standard', 'low'])
    ap.add_argument('--frame-ratio', choices=RATIOS)
    ap.add_argument('--storage-key', help='浏览器本地存储名；不填则按配置内容自动生成')
    ap.add_argument('--force', action='store_true', help='允许覆盖已存在的输出文件')
    a = ap.parse_args()

    html = TEMPLATE.read_text(encoding='utf-8')
    themes = json.loads(block(html, 'THEMES').group(1))

    if a.list:
        print('预设：', ', '.join(sorted(p.stem for p in PRESETS.glob('*.json'))))
        print('底座：'); [print(f'  {k:8} {v["label"]} — {v["good_for"]}') for k, v in CATALOG['bases'].items()]
        print('主题：'); [print(f'  {k:9} {v}') for k, v in CATALOG['themes'].items()]
        print('积木：'); [print(f'  {k:12} {v["label"]} — {v["means"]}') for k, v in CATALOG['kits'].items()]
        return 0

    need(a.output, '请用 --output 指定输出文件')
    need(not (a.preset and a.config), '--preset 和 --config 只能选一个')
    if a.config:
        scene = load_json(a.config)
    else:
        name = a.preset or 'island-dream'
        f = PRESETS / (name + '.json')
        need(f.exists(), f'没有预设 {name}，可用：' + ', '.join(sorted(p.stem for p in PRESETS.glob('*.json'))))
        scene = load_json(f)

    if a.palette:
        pal = load_json(a.palette)
        validate_palette(pal, 'palette')
        pal.setdefault('label', '自定义')
        themes['custom'] = pal
        scene['theme'] = 'custom'
    for flag, key in [('title', 'title'), ('subtitle', 'subtitle'), ('nickname', 'nickname'), ('base', 'base'),
                      ('theme', 'theme'), ('quality', 'quality'), ('frame_ratio', 'frameRatio')]:
        v = getattr(a, flag)
        if v is not None:
            scene[key] = v
    for name, t in themes.items():
        validate_palette(t, 'THEMES.' + name)
    validate_scene(scene, themes)

    if a.storage_key:
        need(re.fullmatch(r'[A-Za-z0-9_-]{3,80}', a.storage_key), 'storage-key 只能用字母、数字、横线、下划线（3~80 位）')
        scene['storageKey'] = a.storage_key
    else:
        digest = hashlib.sha1(json.dumps(scene, ensure_ascii=False, sort_keys=True).encode()).hexdigest()[:10]
        scene['storageKey'] = 'wb-' + digest

    need(not a.output.exists() or a.force, f'{a.output} 已存在；换个文件名，或确认后加 --force 覆盖')
    html = replace_block(html, 'SCENE', scene)
    if a.palette:
        html = replace_block(html, 'THEMES', themes)
    html = re.sub(r'<title>.*?</title>', '<title>' + scene['title'].replace('<', '').replace('>', '') + '</title>', html, count=1)
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(html, encoding='utf-8')
    for w in warnings:
        print('提醒：', w)
    print('已生成：', a.output.resolve())
    print(f'底座 {scene.get("base", "island")} · 主题 {scene.get("theme", "cream")} · {len(scene["zones"])} 个区域 · 存储名 {scene["storageKey"]}')
    print('依赖：Three.js 与字体来自公开 CDN，需要联网打开；修改只保存在浏览器本地。')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except ConfigError as e:
        print('生成失败：', e, file=sys.stderr)
        sys.exit(1)
