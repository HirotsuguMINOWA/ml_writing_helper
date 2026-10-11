"""Local web UI to create ml_writing_helper.json.

Serves a single page on 127.0.0.1. The page posts the config back, which is validated with
``parse_config`` and written to ``save_path``. Only requests carrying the per-session token are accepted.
"""
import json
import secrets
import threading
import webbrowser
from collections.abc import Sequence
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from loguru import logger

from ml_writing_helper.config import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_OBSERVER,
    LOG_LEVELS,
    OUTPUT_FORMATS,
    ConfigError,
    parse_config,
)


@dataclass(frozen=True)
class WebUIResult:
    saved: bool
    start_watch: bool


_PAGE = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ML Writing Helper 設定</title>
<style>
:root {
  --bg: #f6f7f9; --panel: #ffffff; --text: #1d2330; --muted: #5f6b7a; --border: #d9dee5;
  --accent: #2f6fde; --accent-text: #ffffff; --danger: #c43c3c; --ok: #237a4b; --code: #f0f2f5;
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #15181d; --panel: #1e232a; --text: #e6e9ee; --muted: #9aa5b3; --border: #343b45;
    --accent: #5b8ff0; --accent-text: #0d1117; --danger: #ef6b6b; --ok: #5cc28a; --code: #161a20;
  }
}
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--text);
  font: 14px/1.5 -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Segoe UI", sans-serif; }
main { max-width: 860px; margin: 0 auto; padding: 24px 16px 64px; }
h1 { font-size: 20px; margin: 0 0 4px; }
h2 { font-size: 15px; margin: 0 0 12px; }
p.sub { color: var(--muted); margin: 0 0 20px; word-break: break-all; }
section { background: var(--panel); border: 1px solid var(--border); border-radius: 8px; padding: 16px; margin-bottom: 16px; }
.grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; }
label { display: flex; flex-direction: column; gap: 4px; font-size: 12px; color: var(--muted); }
label.check { flex-direction: row; align-items: center; gap: 6px; color: var(--text); font-size: 13px; }
input[type=text], input[type=number], select {
  font: inherit; color: var(--text); background: var(--bg); border: 1px solid var(--border);
  border-radius: 6px; padding: 6px 8px; width: 100%; }
.task { border: 1px solid var(--border); border-radius: 8px; padding: 12px; margin-bottom: 12px; }
.task-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
.badge { font-size: 12px; font-weight: 600; padding: 2px 8px; border-radius: 999px; background: var(--code); }
button { font: inherit; border-radius: 6px; padding: 7px 14px; cursor: pointer;
  border: 1px solid var(--border); background: var(--panel); color: var(--text); }
button.primary { background: var(--accent); border-color: var(--accent); color: var(--accent-text); font-weight: 600; }
button.link { border: none; background: none; color: var(--danger); padding: 2px 4px; }
.row { display: flex; gap: 8px; flex-wrap: wrap; }
pre { background: var(--code); border-radius: 6px; padding: 12px; overflow-x: auto; margin: 0; font-size: 12px; }
#msg { margin: 0 0 16px; white-space: pre-wrap; }
#msg.error { color: var(--danger); }
#msg.ok { color: var(--ok); }
.hint { color: var(--muted); font-size: 12px; margin: 8px 0 0; }
</style>
</head>
<body>
<main>
  <h1>ML Writing Helper 設定</h1>
  <p class="sub">保存先: <code id="savePath"></code></p>

  <section>
    <h2>全体設定</h2>
    <div class="grid">
      <label>root（相対パスの基準）<input type="text" id="root" value="."></label>
      <label>observer<select id="observer"></select></label>
      <label>sleep_sec<input type="number" id="sleep_sec" value="1" min="0.1" step="0.1"></label>
      <label>log_level<select id="log_level"></select></label>
    </div>
    <p class="hint">パスは json ファイルのあるフォルダ（root）からの相対パス、または絶対パスで指定します。</p>
  </section>

  <section>
    <h2>監視タスク</h2>
    <div id="tasks"></div>
    <div class="row">
      <button type="button" onclick="addTask('img_conv')">＋ 図の変換タスク</button>
      <button type="button" onclick="addTask('copy')">＋ コピータスク</button>
    </div>
  </section>

  <section>
    <h2>プレビュー</h2>
    <pre id="preview"></pre>
  </section>

  <p id="msg"></p>
  <div class="row">
    <button type="button" class="primary" onclick="save(true)">保存して監視開始</button>
    <button type="button" onclick="save(false)">保存のみ</button>
    <button type="button" onclick="cancel()">キャンセル</button>
  </div>
</main>
<script>
const BOOT = __BOOT__;
const tasks = [];

function opt(sel, values, current) {
  sel.innerHTML = "";
  for (const v of values) {
    const o = document.createElement("option");
    o.value = v; o.textContent = v; o.selected = v === current;
    sel.appendChild(o);
  }
}

function addTask(type) {
  if (type === "img_conv") {
    tasks.push({type, src: "fig_src", dst: "fig_gen", ext: "pdf", gray: false, crop: true});
  } else {
    tasks.push({type, src: "", dst: "bib", exts: ["bib"], diff_sec: 10});
  }
  render();
}

function removeTask(i) { tasks.splice(i, 1); render(); }

function field(i, key, label, type, extra) {
  const t = tasks[i];
  if (type === "check") {
    return `<label class="check"><input type="checkbox" data-i="${i}" data-k="${key}" ${t[key] ? "checked" : ""}> ${label}</label>`;
  }
  if (type === "select") {
    const opts = extra.map(v => `<option ${v === t[key] ? "selected" : ""}>${v}</option>`).join("");
    return `<label>${label}<select data-i="${i}" data-k="${key}">${opts}</select></label>`;
  }
  const v = key === "exts" ? t.exts.join(", ") : t[key];
  return `<label>${label}<input type="${type}" data-i="${i}" data-k="${key}" value="${String(v).replace(/"/g, "&quot;")}" ${extra || ""}></label>`;
}

function render() {
  const box = document.getElementById("tasks");
  box.innerHTML = tasks.map((t, i) => {
    const title = t.type === "img_conv" ? "図の変換 (img_conv)" : "コピー (copy)";
    const body = t.type === "img_conv"
      ? field(i, "src", "src（監視フォルダ）", "text") + field(i, "dst", "dst（出力フォルダ）", "text")
        + field(i, "ext", "出力形式", "select", BOOT.formats)
        + `<div>${field(i, "gray", "グレー化", "check")}${field(i, "crop", "クロップ", "check")}</div>`
      : field(i, "src", "src（監視フォルダ）", "text") + field(i, "dst", "dst（コピー先）", "text")
        + field(i, "exts", "拡張子（カンマ区切り）", "text") + field(i, "diff_sec", "diff_sec", "number", 'min="0" step="1"');
    return `<div class="task"><div class="task-head"><span class="badge">${i + 1}. ${title}</span>`
      + `<button type="button" class="link" onclick="removeTask(${i})">削除</button></div>`
      + `<div class="grid">${body}</div></div>`;
  }).join("") || '<p class="hint">タスクがありません。下のボタンで追加してください。</p>';
  updatePreview();
}

function buildConfig() {
  return {
    root: document.getElementById("root").value.trim() || ".",
    observer: document.getElementById("observer").value,
    sleep_sec: Number(document.getElementById("sleep_sec").value),
    log_level: document.getElementById("log_level").value,
    tasks: tasks.map(t => ({...t})),
  };
}

function updatePreview() {
  document.getElementById("preview").textContent = JSON.stringify(buildConfig(), null, 2);
}

document.addEventListener("input", e => {
  const el = e.target;
  if (el.dataset.i !== undefined) {
    const t = tasks[Number(el.dataset.i)], k = el.dataset.k;
    if (el.type === "checkbox") t[k] = el.checked;
    else if (k === "exts") t[k] = el.value.split(",").map(s => s.trim()).filter(Boolean);
    else if (k === "diff_sec") t[k] = el.value === "" ? 0 : Math.trunc(Number(el.value));
    else t[k] = el.value;
  }
  updatePreview();
});
document.addEventListener("change", updatePreview);

function showMsg(text, cls) {
  const m = document.getElementById("msg");
  m.textContent = text; m.className = cls;
}

async function post(path, body) {
  const res = await fetch(path, {
    method: "POST",
    headers: {"Content-Type": "application/json", "X-Token": BOOT.token},
    body: JSON.stringify(body),
  });
  return res.json();
}

async function save(start) {
  try {
    const r = await post("/api/save", {config: buildConfig(), start});
    if (r.ok) {
      showMsg(start ? "保存しました。ターミナルで監視を開始しました。このタブは閉じて構いません。"
                    : "保存しました。このタブは閉じて構いません。", "ok");
      document.querySelectorAll("button").forEach(b => b.disabled = true);
    } else {
      showMsg("保存できませんでした:\n- " + r.errors.join("\n- "), "error");
    }
  } catch (e) {
    showMsg("サーバーに接続できません: " + e, "error");
  }
}

async function cancel() {
  try { await post("/api/cancel", {}); } catch (e) {}
  showMsg("キャンセルしました。このタブは閉じて構いません。", "ok");
  document.querySelectorAll("button").forEach(b => b.disabled = true);
}

document.getElementById("savePath").textContent = BOOT.savePath;
opt(document.getElementById("observer"), BOOT.observers, BOOT.defaultObserver);
opt(document.getElementById("log_level"), BOOT.logLevels, BOOT.defaultLogLevel);
addTask("img_conv");
</script>
</body>
</html>
"""


def run_webui(
        save_path: Path,
        available_observers: Sequence[str],
        host: str = "127.0.0.1",
        port: int = 0,
        open_browser: bool = True,
) -> WebUIResult:
    """Serve the config editor until the user saves or cancels. Blocks."""
    token = secrets.token_urlsafe(16)
    result: dict[str, bool] = {"saved": False, "start_watch": False}
    boot = {
        "token": token,
        "savePath": save_path.as_posix(),
        "formats": OUTPUT_FORMATS,
        "observers": list(available_observers),
        "logLevels": LOG_LEVELS,
        "defaultObserver": DEFAULT_OBSERVER,
        "defaultLogLevel": DEFAULT_LOG_LEVEL,
    }
    page = _PAGE.replace("__BOOT__", json.dumps(boot, ensure_ascii=False)).encode("utf-8")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
            logger.debug("webui: " + format % args)

        def _send(self, code: int, body: bytes, content_type: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def _send_json(self, code: int, obj: dict[str, Any]) -> None:
            self._send(code, json.dumps(obj, ensure_ascii=False).encode("utf-8"), "application/json")

        def do_GET(self) -> None:
            if self.path.split("?")[0] in ("/", "/index.html"):
                self._send(200, page, "text/html; charset=utf-8")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self) -> None:
            if self.headers.get("X-Token") != token:
                self._send_json(403, {"ok": False, "errors": ["invalid token"]})
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                body = json.loads(self.rfile.read(length) or b"{}")
            except (ValueError, json.JSONDecodeError):
                self._send_json(400, {"ok": False, "errors": ["invalid request body"]})
                return

            if self.path == "/api/cancel":
                self._send_json(200, {"ok": True})
                _shutdown()
                return
            if self.path != "/api/save":
                self._send_json(404, {"ok": False, "errors": ["not found"]})
                return

            config = body.get("config")
            try:
                _ = parse_config(config, base_dir=save_path.parent, available_observers=available_observers)
            except ConfigError as e:
                self._send_json(200, {"ok": False, "errors": e.errors})
                return
            save_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            logger.info(f"Saved: {save_path}")
            result["saved"] = True
            result["start_watch"] = bool(body.get("start"))
            self._send_json(200, {"ok": True})
            _shutdown()

    server = ThreadingHTTPServer((host, port), Handler)

    def _shutdown() -> None:
        threading.Thread(target=server.shutdown, daemon=True).start()

    url = f"http://{host}:{server.server_address[1]}/"
    logger.info(f"{save_path.name} が見つからないため、設定用 Web UI を起動しました: {url}")
    logger.info("ブラウザで設定を保存してください（中止: Ctrl+C）")
    if open_browser:
        _ = webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Web UI を中止しました")
    finally:
        server.server_close()
    return WebUIResult(saved=result["saved"], start_watch=result["start_watch"])
