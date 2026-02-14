"""
HTML report: single self-contained file (inline CSS + inline Chart.js).
Works when opened as file:// in browser; no CDN. Chart animations on load.
"""

import html
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import markdown
from jinja2 import BaseLoader, Environment

from . import __version__
from .git_utils import get_commit_info, get_diff_numstat

_CHART_JS_URL = "https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"
_USER_AGENT = "Mozilla/5.0 (compatible; SmartDiff/1.0)"


def _fetch_chart_js() -> str:
    """Fetch Chart.js UMD bundle for inlining (so file:// works). Escape </script> in source."""
    try:
        req = Request(_CHART_JS_URL, headers={"User-Agent": _USER_AGENT})
        with urlopen(req, timeout=15) as r:
            raw = r.read().decode("utf-8", errors="replace")
            return raw.replace("</script>", "<\\/script>")
    except Exception:
        return "/* Chart.js load failed */ window.Chart = { register: function(){}, getChart: function(){ return null; } };"


def _open_in_browser(path: Path) -> None:
    path = path.resolve()
    if not path.exists():
        return
    try:
        if os.name == "nt":
            os.startfile(path.as_uri())
        elif sys.platform == "darwin":
            subprocess.run(["open", str(path)], check=False, timeout=2)
        else:
            subprocess.run(["xdg-open", str(path)], check=False, timeout=2)
    except Exception:
        pass


def _inline_styles() -> str:
    """Full inline CSS so file works without CDN (file:// in browser, Quick Look, etc.)."""
    return r"""
* { box-sizing: border-box; }
body { margin: 0; font-family: system-ui, -apple-system, Segoe UI, sans-serif; background: #f8fafc; color: #1e293b; min-height: 100vh; line-height: 1.5; -webkit-font-smoothing: antialiased; }
.report-wrap { max-width: 64rem; margin: 0 auto; padding: 2rem 1rem; }
.gradient-head { background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%); border-radius: 1rem; padding: 2rem; margin-bottom: 2rem; color: #fff; box-shadow: 0 10px 25px -5px rgb(0 0 0 / 0.1); }
.gradient-head h1 { margin: 0; font-size: 1.875rem; font-weight: 700; letter-spacing: -0.025em; }
.gradient-head .sub { margin-top: 0.5rem; color: rgba(255,255,255,0.9); font-size: 1.125rem; }
.gradient-head .meta { margin-top: 1rem; font-size: 0.875rem; color: rgba(255,255,255,0.8); }
.stats-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.75rem; margin-top: 1rem; }
@media (min-width: 640px) { .stats-row { grid-template-columns: repeat(4, 1fr); } }
.stat-box { background: rgba(255,255,255,0.15); border-radius: 0.5rem; padding: 0.75rem; text-align: center; }
.stat-box .n { font-size: 1.25rem; font-weight: 700; display: block; }
.stat-box .l { font-size: 0.7rem; color: rgba(255,255,255,0.85); text-transform: uppercase; letter-spacing: 0.05em; }
.stat-box.add .n { color: #6ee7b7; }
.stat-box.del .n { color: #fda4af; }
.section { margin-bottom: 2rem; }
.section h2 { font-size: 1.25rem; font-weight: 600; color: #1e293b; margin: 0 0 0.75rem 0; display: flex; align-items: center; gap: 0.5rem; }
.card { background: #fff; border: 1px solid #e2e8f0; border-radius: 0.75rem; padding: 1.5rem; box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.05); }
.grid-2-1 { display: grid; gap: 1.5rem; }
@media (min-width: 1024px) { .grid-2-1 { grid-template-columns: 2fr 1fr; } }
.table-wrap { overflow-x: auto; }
table { width: 100%; font-size: 0.875rem; border-collapse: collapse; }
th, td { padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #f1f5f9; }
th { background: #f8fafc; font-weight: 600; color: #475569; font-size: 0.8rem; }
.text-right { text-align: right; }
.add-num { color: #059669; font-weight: 500; }
.del-num { color: #e11d48; font-weight: 500; }
.truncate { max-width: 18rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.font-mono { font-family: ui-monospace, monospace; }
.prose-sm a { color: #6366f1; text-decoration: underline; }
.prose-sm ul { list-style: disc; padding-left: 1.25rem; margin: 0.5em 0; }
.prose-sm ol { list-style: decimal; padding-left: 1.25rem; margin: 0.5em 0; }
.prose-sm strong { font-weight: 600; }
.prose-sm pre { background: #1e1e2e; color: #cdd6f4; padding: 1rem; border-radius: 0.5rem; overflow-x: auto; font-size: 0.8rem; }
.prose-sm code { background: #e2e8f0; color: #701a75; padding: 0.15rem 0.35rem; border-radius: 0.25rem; font-size: 0.85em; }
.diff-block { background: #0f172a; color: #cbd5e1; padding: 1rem; border-radius: 0.75rem; overflow: auto; max-height: 24rem; font-size: 0.875rem; font-family: ui-monospace, monospace; white-space: pre; }
.footer { text-align: center; color: #94a3b8; font-size: 0.875rem; padding-top: 2rem; }
.footer a { color: #6366f1; text-decoration: none; }
.footer a:hover { text-decoration: underline; }
.chart-wrap { display: flex; align-items: center; justify-content: center; min-height: 200px; }
@keyframes sd-fade { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: translateY(0); } }
.section.animate-in { animation: sd-fade 0.5s ease-out both; }
"""


def _template() -> str:
    return r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Smart Diff Report — {{ scope_label }}</title>
  <style>{{ inline_css }}</style>
</head>
<body>
  <div class="report-wrap">
    <header class="gradient-head">
      <h1>Smart Diff Report</h1>
      <p class="sub">{{ scope_label }}</p>
      <p class="meta">Model: <strong>{{ model }}</strong> · {{ generated_at }}</p>
      <div class="stats-row">
        <div class="stat-box"><span class="n">{{ files_count }}</span><span class="l">Files</span></div>
        <div class="stat-box add"><span class="n">+{{ total_added }}</span><span class="l">Added</span></div>
        <div class="stat-box del"><span class="n">−{{ total_deleted }}</span><span class="l">Deleted</span></div>
        <div class="stat-box"><span class="n">{{ total_added - total_deleted }}</span><span class="l">Net</span></div>
      </div>
    </header>

    {% if commit_info %}
    <section class="section animate-in">
      <h2>Commit</h2>
      <div class="card">
        <table>
          <tr><td style="color:#64748b;width:5rem;">Hash</td><td><code class="font-mono">{{ commit_info.hash }}</code></td></tr>
          <tr><td style="color:#64748b;">Author</td><td>{{ commit_info.author }}</td></tr>
          <tr><td style="color:#64748b;">Date</td><td>{{ commit_info.date }}</td></tr>
          <tr><td style="color:#64748b;">Subject</td><td>{{ commit_info.subject }}</td></tr>
        </table>
        {% if commit_info.body %}
        <div style="margin-top:1rem;padding-top:1rem;border-top:1px solid #e2e8f0;"><span style="font-size:0.8rem;color:#64748b;">Body</span><pre style="margin:0.25rem 0 0 0;white-space:pre-wrap;font-size:0.85rem;">{{ commit_info.body }}</pre></div>
        {% endif %}
      </div>
    </section>
    {% endif %}

    <section class="section animate-in" style="animation-delay: 0.05s;">
      <h2>Analysis</h2>
      <div class="card prose-sm">
        {{ analysis_html | safe }}
      </div>
    </section>

    {% if file_stats %}
    <section class="section animate-in" style="animation-delay: 0.1s;">
      <h2>Changed files</h2>
      <div class="grid-2-1">
        <div class="card">
          <div class="table-wrap">
            <table>
              <thead><tr><th>File</th><th class="text-right add-num">+</th><th class="text-right del-num">−</th></tr></thead>
              <tbody>
                {% for f in file_stats %}
                <tr><td class="truncate font-mono" title="{{ f.path }}">{{ f.path }}</td><td class="text-right add-num">{{ f.added }}</td><td class="text-right del-num">{{ f.deleted }}</td></tr>
                {% endfor %}
              </tbody>
            </table>
          </div>
        </div>
        <div class="card chart-wrap"><canvas id="chartFiles" height="220"></canvas></div>
      </div>
      <div class="card chart-wrap" style="margin-top:1rem;"><canvas id="chartLines" height="120"></canvas></div>
    </section>
    {% endif %}

    {% if ext_labels %}
    <section class="section animate-in" style="animation-delay: 0.15s;">
      <h2>By extension</h2>
      <div class="card chart-wrap"><canvas id="chartExt" height="200"></canvas></div>
    </section>
    {% endif %}

    {% if file_stats %}
    <section class="section animate-in" style="animation-delay: 0.2s;">
      <h2>Add / Del per file (top 10)</h2>
      <div class="card chart-wrap"><canvas id="chartPerFile" height="280"></canvas></div>
    </section>
    <section class="section animate-in" style="animation-delay: 0.25s;">
      <h2>Net change per file</h2>
      <div class="card chart-wrap"><canvas id="chartNet" height="260"></canvas></div>
    </section>
    {% endif %}

    <section class="section animate-in" style="animation-delay: 0.3s;">
      <h2>Diff</h2>
      <div class="card"><pre class="diff-block">{{ diff_escaped }}</pre></div>
    </section>

    <footer class="footer">
      Generated by <a href="https://github.com/YOUR_USERNAME/smart-diff">Smart Diff</a> · {{ version }} · {{ generated_at }}
    </footer>
  </div>

  <script>{{ chart_js_inline }}</script>
  <script>
    (function(){
      var fileStats = {{ file_stats_json | safe }};
      var labels = fileStats.map(function(f){ return f.path.split('/').pop() || f.path; });
      var added = fileStats.map(function(f){ return f.added; });
      var deleted = fileStats.map(function(f){ return f.deleted; });
      var ANIM_MS = 1000;
      var DELAY = 220;
      var opts = { responsive: true, maintainAspectRatio: false, animation: { duration: ANIM_MS } };

      function mk(id, fn) {
        var el = document.getElementById(id);
        if (!el || typeof Chart === 'undefined') return;
        fn(el);
      }
      function chartFiles(el) {
        new Chart(el, {
          type: 'bar',
          data: { labels: labels, datasets: [
            { label: 'Added', data: added, backgroundColor: 'rgba(16, 185, 129, 0.7)', borderColor: 'rgb(16, 185, 129)', borderWidth: 1 },
            { label: 'Deleted', data: deleted, backgroundColor: 'rgba(244, 63, 94, 0.7)', borderColor: 'rgb(244, 63, 94)', borderWidth: 1 }
          ]},
          options: Object.assign({}, opts, { indexAxis: 'y', plugins: { legend: { position: 'top' } }, scales: { x: { stacked: true }, y: { stacked: true } } })
        });
      }
      function chartLines(el) {
        var ta = added.reduce(function(a,b){ return a+b; }, 0);
        var td = deleted.reduce(function(a,b){ return a+b; }, 0);
        new Chart(el, {
          type: 'doughnut',
          data: { labels: ['Lines added', 'Lines deleted'], datasets: [{ data: [ta, td], backgroundColor: ['rgba(16, 185, 129, 0.8)', 'rgba(244, 63, 94, 0.8)'], borderWidth: 0 }]},
          options: Object.assign({}, opts, { plugins: { legend: { position: 'bottom' } } })
        });
      }
      var delay = 0;
      mk('chartFiles', function(el){ setTimeout(function(){ chartFiles(el); }, delay); delay += DELAY; });
      mk('chartLines', function(el){ setTimeout(function(){ chartLines(el); }, delay); delay += DELAY; });
      {% if ext_labels %}
      mk('chartExt', function(el){ setTimeout(function(){
        new Chart(el, { type: 'doughnut', data: { labels: {{ ext_labels | safe }}, datasets: [{ data: {{ ext_data | safe }}, backgroundColor: {{ ext_colors | safe }}, borderWidth: 0 }]}, options: Object.assign({}, opts, { plugins: { legend: { position: 'right' } } }) });
      }, delay); delay += DELAY; });
      {% endif %}
      var top10 = fileStats.slice(0, 10);
      var topLabels = top10.map(function(f){ return f.path.split('/').pop() || f.path; });
      mk('chartPerFile', function(el){ setTimeout(function(){
        new Chart(el, { type: 'bar', data: { labels: topLabels, datasets: [
          { label: '+ Added', data: top10.map(function(f){ return f.added; }), backgroundColor: 'rgba(16, 185, 129, 0.7)', borderColor: 'rgb(16, 185, 129)', borderWidth: 1 },
          { label: '− Deleted', data: top10.map(function(f){ return f.deleted; }), backgroundColor: 'rgba(244, 63, 94, 0.7)', borderColor: 'rgb(244, 63, 94)', borderWidth: 1 }
        ]}, options: Object.assign({}, opts, { indexAxis: 'y', plugins: { legend: { position: 'top' } }, scales: { x: { stacked: true }, y: { stacked: true } } }) });
      }, delay); delay += DELAY; });
      var netValues = top10.map(function(f){ return f.added - f.deleted; });
      var netColors = netValues.map(function(v){ return v >= 0 ? 'rgba(16, 185, 129, 0.7)' : 'rgba(244, 63, 94, 0.7)'; });
      mk('chartNet', function(el){ setTimeout(function(){
        new Chart(el, { type: 'bar', data: { labels: topLabels, datasets: [{ label: 'Net', data: netValues, backgroundColor: netColors, borderWidth: 1 }]}, options: Object.assign({}, opts, { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { ticks: { callback: function(v){ return v >= 0 ? '+' + v : v; } } } } }) });
      }, delay); });
    })();
  </script>
</body>
</html>
"""


def build_report_data(
    *,
    diff: str,
    analysis_md: str,
    staged: bool,
    ref: str | None,
    model: str,
    lang: str = "auto",
    theme: str = "dark",
    cwd: Path | None = None,
) -> dict:
    cwd = cwd or Path.cwd()
    commit_info = None
    if ref:
        commit_info = get_commit_info(ref, cwd=cwd)
    elif staged:
        commit_info = get_commit_info("HEAD", cwd=cwd)

    scope_label = "Working tree changes"
    if ref:
        scope_label = f"Commit {ref}"
    elif staged:
        scope_label = "Staged changes"

    file_stats = get_diff_numstat(staged=staged, ref=ref, cwd=cwd)
    total_added = sum(f["added"] for f in file_stats)
    total_deleted = sum(f["deleted"] for f in file_stats)

    ext_counter = Counter()
    for f in file_stats:
        ext = Path(f["path"]).suffix or "(no ext)"
        ext_counter[ext] += 1
    ext_counts = ext_counter.most_common(12)
    ext_colors = [
        "rgba(99, 102, 241, 0.8)",
        "rgba(16, 185, 129, 0.8)",
        "rgba(244, 63, 94, 0.8)",
        "rgba(234, 179, 8, 0.8)",
        "rgba(168, 85, 247, 0.8)",
        "rgba(6, 182, 212, 0.8)",
        "rgba(249, 115, 22, 0.8)",
        "rgba(132, 204, 22, 0.8)",
        "rgba(236, 72, 153, 0.8)",
        "rgba(20, 184, 166, 0.8)",
        "rgba(99, 102, 241, 0.6)",
        "rgba(244, 63, 94, 0.6)",
    ]
    ext_labels = json.dumps([html.escape(ext) for ext, _ in ext_counts])
    ext_data = json.dumps([c for _, c in ext_counts])
    ext_colors_json = json.dumps([ext_colors[i % len(ext_colors)] for i in range(len(ext_counts))])

    analysis_html = markdown.markdown(analysis_md, extensions=["extra", "nl2br"])
    diff_escaped = html.escape(diff)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "commit_info": commit_info,
        "scope_label": scope_label,
        "analysis_html": analysis_html,
        "file_stats": file_stats,
        "file_stats_json": json.dumps(
            [{"path": f["path"], "added": f["added"], "deleted": f["deleted"]} for f in file_stats]
        ),
        "diff_escaped": diff_escaped,
        "model": model,
        "lang": lang,
        "theme": theme,
        "version": __version__,
        "generated_at": generated_at,
        "files_count": len(file_stats),
        "total_added": total_added,
        "total_deleted": total_deleted,
        "ext_labels": ext_labels if ext_counts else None,
        "ext_data": ext_data if ext_counts else None,
        "ext_colors": ext_colors_json if ext_counts else None,
        "inline_css": _inline_styles(),
    }


def render_report(data: dict) -> str:
    env = Environment(loader=BaseLoader())
    return env.from_string(_template()).render(**data)


def write_report(report_path: Path, data: dict, auto_open: bool = True) -> Path:
    """Write HTML report to the given file path (single file, no folder structure). Self-contained: inline CSS + Chart.js so file:// works."""
    report_path = report_path.resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    data["chart_js_inline"] = _fetch_chart_js()
    report_path.write_text(render_report(data), encoding="utf-8")
    if auto_open:
        _open_in_browser(report_path)
    return report_path
