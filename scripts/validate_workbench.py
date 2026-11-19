#!/usr/bin/env python3
"""静态检查生成的工作台 HTML：标记、配置、积木名、外部域名、隐私痕迹、JS 语法。
不打开浏览器，不能代替画面检查。用法：python3 validate_workbench.py out.html
"""
import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_workbench as bw  # noqa: E402

REQUIRED_IDS = ['c', 'labels', 'brand', 'stats', 'tools', 'track', 'panel', 'pBody', 'modal', 'fJson', 'loading', 'frame', 'toast', 'pageNav', 'pgPrev', 'pgNext', 'pgChip']
ALLOWED_HOSTS = {'fonts.googleapis.com', 'fonts.gstatic.com', 'cdn.jsdelivr.net'}


class Doc(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.modules, self.external, self._in = [], [], [], False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if 'id' in a:
            self.ids.append(a['id'])
        if tag == 'script' and a.get('type') == 'module':
            self._in = True
        for k in ['src', 'href']:
            if (a.get(k) or '').startswith('http'):
                self.external.append(a[k])

    def handle_endtag(self, tag):
        if tag == 'script':
            self._in = False

    def handle_data(self, data):
        if self._in:
            self.modules.append(data)


def validate(path):
    text = Path(path).read_text(encoding='utf-8')
    d = Doc(); d.feed(text)
    errors, notes = [], []
    def check(ok, msg):
        if not ok:
            errors.append(msg)
    check(len(d.ids) == len(set(d.ids)), 'HTML id 重复')
    for i in REQUIRED_IDS:
        check(i in d.ids, '缺少界面元素 #' + i)
    check(len(d.modules) == 1, '应只有一个 ES module 脚本')
    themes = {}
    try:
        themes = json.loads(bw.block(text, 'THEMES').group(1))
        for k, t in themes.items():
            bw.validate_palette(t, 'THEMES.' + k)
    except Exception as e:
        errors.append('THEMES 无效：' + str(e))
    try:
        scene = json.loads(bw.block(text, 'SCENE').group(1))
        bw.validate_scene(scene, themes)
        zone_lists = ([p.get('zones') or [] for p in scene['pages']] if isinstance(scene.get('pages'), list) and len(scene['pages']) > 1
                      else [scene['zones']])
        for zs in zone_lists:
            for z in zs:
                check(('KITS.' + z['kit'] + '=') in text, '模板里没有积木 ' + z['kit'])
    except Exception as e:
        errors.append('SCENE 无效：' + str(e))
    check('three@0.169.0/build/three.module.js' in text and 'three@0.169.0/examples/jsm/' in text, 'Three.js 核心与 addons 必须固定为同一版本 0.169.0')
    for u in d.external + re.findall(r'https://[^\s"\'`)]+', ''.join(d.modules)):
        host = urlsplit(u).hostname
        check(host in ALLOWED_HOSTS, '出现未审核的外部域名：' + str(host))
    check(not re.search(r'(/Users/|/home/|C:\\\\Users|file://|xsec_token|X-Amz-Signature|Bearer\s+[A-Za-z0-9])', text), '发现本机路径或凭据痕迹')
    check('data:image/jpeg;base64' not in text and 'data:image/png;base64' not in text, '内嵌了位图，请确认来源与隐私')
    for m in ['SCENE_BEGIN', 'SCENE_END', 'THEMES_BEGIN', 'THEMES_END']:
        check(text.count('/* ' + m + ' */') == 1, '标记缺失或重复：' + m)
    if d.modules and shutil.which('node'):
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'm.mjs'; f.write_text(d.modules[0], encoding='utf-8')
            r = subprocess.run(['node', '--check', str(f)], capture_output=True, text=True)
            check(r.returncode == 0, 'JS 语法错误：' + r.stderr[:600])
    else:
        notes.append('没有 Node.js，跳过 JS 语法检查')
    return errors, notes + ['提醒：' + w for w in bw.warnings]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('html', type=Path)
    a = ap.parse_args()
    errors, notes = validate(a.html)
    for n in notes:
        print('NOTE:', n)
    for e in errors:
        print('FAIL:', e)
    if errors:
        return 1
    print('PASS：结构、配置、外部域名、语法检查通过。画面、点击、帧率仍需在浏览器里看。')
    return 0


if __name__ == '__main__':
    sys.exit(main())
