/* 在浏览器里检查工作台运行状态（不改任何东西）。
   用法：页面加载完成后，把整段粘到开发者工具 Console，或交给浏览器工具的 “执行 JavaScript”。
   返回一个 JSON 报告；ok=false 时看 problems。 */
(() => {
  const W = window.__WB, problems = [], info = {};
  if (!W) return { ok: false, problems: ['没有 window.__WB：页面没加载完，或模板被改坏（看控制台第一条报错）'] };
  const S = W.SCENE();
  const pg = W.page ? W.page() : { cur: 0, total: 1, multi: false };
  const pageZones = pg.multi ? (S.pages[pg.cur].zones || []) : S.zones;
  info.ready = W.ready; info.base = S.base; info.theme = S.theme; info.zones = W.zones.length;
  info.page = pg.multi ? `${pg.cur + 1}/${pg.total}` : '1/1';
  info.loadingHidden = document.getElementById('loading').classList.contains('hide');
  if (!info.loadingHidden) problems.push('加载层还没消失（可能 CDN 加载失败或脚本报错）');
  if (W.zones.length !== pageZones.length) problems.push(`当前页配置 ${pageZones.length} 个区域，实际建出 ${W.zones.length} 个`);
  W.zones.forEach((z, i) => {
    if (![z.x, z.z, z.h, z.r].every(Number.isFinite)) problems.push(`区域 ${i} 坐标/尺寸不是数字`);
    if (!W.inside(z.x, z.z, -0.6)) problems.push(`区域 ${i}「${z.cfg.name}」中心在底座边缘外`);
    if (!z.group.children.length) problems.push(`区域 ${i} 没有任何模型`);
    W.zones.forEach((o, j) => { if (j > i) { const d = Math.hypot(z.x - o.x, z.z - o.z); if (d < (z.r + o.r) * 0.8) problems.push(`区域 ${i} 与 ${j} 重叠（距离 ${d.toFixed(1)}）`); } });
  });
  const labs = document.querySelectorAll('#labels .lab');
  if (labs.length !== W.zones.length) problems.push(`浮标 ${labs.length} 个，区域 ${W.zones.length} 个`);
  let tris = 0; W.scene.traverse(o => { if (o.isMesh && o.geometry) { const g = o.geometry; const n = g.index ? g.index.count / 3 : (g.attributes.position?.count || 0) / 3; tris += n * (o.isInstancedMesh ? o.count : 1); } });
  info.triangles = Math.round(tris); info.drawCalls = W.renderer.info.render.calls;
  if (tris > 3.5e6) problems.push('三角面过多，低端设备可能卡顿，考虑 quality: "low" 或降低 decor 密度');
  return { ok: problems.length === 0, info, problems };
})();
