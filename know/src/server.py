"""
HTTP server for spec-dashboard.

Responsibilities:
- Serve static dashboard files from know/www/dashboard/
- REST API for reading graph data (in-process, no subprocess)
- REST API for mutations (proxied through know CLI via subprocess)
- Undo stack for reverting mutations (snapshot-based)
- History endpoint for reading diff-graph.jsonl
- AI chat via claude CLI (execPath auth passthrough)
- SSE file-watch for hot updates when graph changes externally
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import webbrowser
from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, unquote

WWW_DIR = Path(__file__).parent.parent / "www" / "dashboard"
KNOW_PY = Path(__file__).parent.parent / "know.py"

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*m')


def _strip_ansi(text):
    """Remove ANSI escape codes from CLI output."""
    return _ANSI_RE.sub('', text).strip()


def _find_claude():
    """Find the claude CLI executable."""
    return shutil.which('claude')


class UndoStack:
    """Thread-safe stack of graph snapshots for undo support."""

    def __init__(self, max_size=30):
        self._stack = deque(maxlen=max_size)
        self._lock = threading.Lock()

    def push(self, snapshot, description):
        with self._lock:
            self._stack.append({"graph": snapshot, "description": description})

    def pop(self):
        with self._lock:
            return self._stack.pop() if self._stack else None

    def peek(self):
        with self._lock:
            return self._stack[-1] if self._stack else None

    def entries(self):
        with self._lock:
            return [{"description": e["description"]} for e in reversed(self._stack)]

    def __len__(self):
        with self._lock:
            return len(self._stack)


class FileWatcher:
    """Watches a file for mtime changes and notifies SSE clients."""

    def __init__(self, path, poll_interval=0.5):
        self.path = Path(path)
        self.poll_interval = poll_interval
        self._last_mtime = self._get_mtime()
        self._clients = []
        self._lock = threading.Lock()
        self._running = False

    def _get_mtime(self):
        try:
            return self.path.stat().st_mtime
        except FileNotFoundError:
            return 0

    def add_client(self, wfile):
        with self._lock:
            self._clients.append(wfile)

    def remove_client(self, wfile):
        with self._lock:
            self._clients = [c for c in self._clients if c is not wfile]

    def _notify_clients(self, event_data):
        msg = f"data: {json.dumps(event_data)}\n\n"
        with self._lock:
            dead = []
            for wfile in self._clients:
                try:
                    wfile.write(msg.encode('utf-8'))
                    wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    dead.append(wfile)
            for d in dead:
                self._clients.remove(d)

    def start(self):
        self._running = True
        t = threading.Thread(target=self._poll_loop, daemon=True)
        t.start()

    def stop(self):
        self._running = False

    def _poll_loop(self):
        while self._running:
            mtime = self._get_mtime()
            if mtime != self._last_mtime:
                self._last_mtime = mtime
                self._notify_clients({"type": "graph-updated", "ts": time.time()})
            time.sleep(self.poll_interval)


# Shared state — one per server process
_undo_stack = UndoStack()
_file_watcher = None  # Set by serve()
_claude_path = None  # Set by serve()


class DashboardHandler(BaseHTTPRequestHandler):
    """HTTP handler for the spec-dashboard."""

    graph_path = ""
    project_cwd = Path(".")

    def log_message(self, fmt, *args):
        pass

    # --- Helpers ---

    def _read_graph(self):
        try:
            with open(self.graph_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {"error": str(e)}

    def _write_graph(self, data):
        graph_path = Path(self.graph_path)
        with tempfile.NamedTemporaryFile(
            mode='w', dir=str(graph_path.parent), suffix='.tmp', delete=False
        ) as tmp:
            json.dump(data, tmp, indent=2)
            tmp_path = tmp.name
        os.replace(tmp_path, str(graph_path))

    def _json_response(self, data, status=200):
        body = json.dumps(data, indent=2).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(body)

    def _read_body(self):
        length = int(self.headers.get('Content-Length', 0))
        if length == 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, ValueError):
            return {}

    def _run_know(self, args):
        cmd = [sys.executable, str(KNOW_PY), '-g', str(self.graph_path)] + args
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True,
                cwd=str(self.project_cwd), timeout=15
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"

    def _mutation_response(self, args, description="mutation"):
        before = self._read_graph()
        if "error" not in before:
            _undo_stack.push(before, description)
        ok, stdout, stderr = self._run_know(args)
        if ok:
            graph = self._read_graph()
            self._json_response({
                "ok": True, "graph": graph,
                "undo_available": len(_undo_stack) > 0
            })
        else:
            _undo_stack.pop()
            clean = _strip_ansi(stderr)
            self._json_response({"ok": False, "error": clean or stdout}, status=422)

    def _extract_entity_id(self, path, prefix):
        return unquote(path[len(prefix):])

    def _read_history(self, limit=50):
        diff_path = Path(self.graph_path).parent / 'diff-graph.jsonl'
        if not diff_path.exists():
            return []
        entries = []
        with open(diff_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return list(reversed(entries[-limit:]))

    def _build_chat_context(self):
        """Build a system prompt with current graph context for the AI chat."""
        graph = self._read_graph()
        if "error" in graph:
            return "The spec-graph could not be loaded."

        features = list(graph.get('entities', {}).get('feature', {}).keys())
        actions = list(graph.get('entities', {}).get('action', {}).keys())
        components = list(graph.get('entities', {}).get('component', {}).keys())
        horizons = list(graph.get('meta', {}).get('horizons', {}).keys())

        return (
            f"You are a helpful assistant embedded in the spec-dashboard for a project "
            f"using the 'know' spec-graph tool. The current spec-graph has:\n"
            f"- Features: {', '.join(features[:15]) or 'none'}\n"
            f"- Actions: {', '.join(actions[:15]) or 'none'}\n"
            f"- Components: {', '.join(components[:15]) or 'none'}\n"
            f"- Horizons: {', '.join(horizons) or 'none'}\n\n"
            f"The graph file is at: {self.graph_path}\n"
            f"Project root: {self.project_cwd}\n\n"
            f"You can help users understand the spec-graph, suggest new entities, "
            f"explain relationships, and advise on architecture. "
            f"Keep responses concise. Use the know CLI for graph operations."
        )

    # --- Routes ---

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == '/api/graph':
            graph = self._read_graph()
            if "error" in graph and isinstance(graph.get("error"), str):
                self._json_response(graph, status=500)
            else:
                self._json_response(graph)
            return

        if path == '/api/rules':
            rules_path = self.project_cwd / '.ai' / 'know' / 'config' / 'dependency-rules.json'
            if not rules_path.exists():
                rules_path = Path(__file__).parent.parent / 'config' / 'dependency-rules.json'
            try:
                with open(rules_path, 'r') as f:
                    self._json_response(json.load(f))
            except FileNotFoundError:
                self._json_response({"error": "Rules file not found"}, status=404)
            return

        if path == '/api/history':
            entries = self._read_history()
            self._json_response({
                "entries": entries,
                "undo_available": len(_undo_stack) > 0,
                "undo_stack": _undo_stack.entries()
            })
            return

        # SSE endpoint for file-watch hot updates
        if path == '/api/events':
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Connection', 'keep-alive')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            # Send initial heartbeat
            try:
                self.wfile.write(b"data: {\"type\": \"connected\"}\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                return
            # Register with file watcher
            if _file_watcher:
                _file_watcher.add_client(self.wfile)
                # Keep connection alive until client disconnects
                try:
                    while True:
                        time.sleep(15)
                        self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, OSError):
                    pass
                finally:
                    _file_watcher.remove_client(self.wfile)
            return

        if path == '/api/chat/status':
            self._json_response({"available": _claude_path is not None})
            return

        # Static files
        if path == '/' or path == '':
            path = '/index.html'

        file_path = (WWW_DIR / path.lstrip('/')).resolve()
        if not str(file_path).startswith(str(WWW_DIR.resolve())):
            self.send_error(403, "Forbidden")
            return

        if file_path.exists() and file_path.is_file():
            content_types = {
                '.html': 'text/html', '.js': 'application/javascript',
                '.css': 'text/css', '.json': 'application/json',
                '.svg': 'image/svg+xml', '.png': 'image/png',
            }
            content_type = content_types.get(file_path.suffix, 'application/octet-stream')
            body = file_path.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_error(404, f"File not found: {path}")

    def do_POST(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path == '/api/undo':
            entry = _undo_stack.pop()
            if not entry:
                self._json_response({"ok": False, "error": "Nothing to undo"}, status=400)
                return
            self._write_graph(entry["graph"])
            graph = self._read_graph()
            self._json_response({
                "ok": True, "graph": graph,
                "undone": entry["description"],
                "undo_available": len(_undo_stack) > 0
            })
            return

        # AI Chat — streams claude CLI output via SSE
        if path == '/api/chat':
            if not _claude_path:
                self._json_response({"ok": False, "error": "claude CLI not found"}, status=503)
                return
            message = body.get('message', '')
            if not message:
                self._json_response({"ok": False, "error": "message is required"}, status=400)
                return

            context = self._build_chat_context()
            cmd = [
                _claude_path,
                '-p',
                '--output-format', 'stream-json',
                '--no-session-persistence',
                '--system-prompt', context,
                message
            ]

            # Stream the response as SSE
            self.send_response(200)
            self.send_header('Content-Type', 'text/event-stream')
            self.send_header('Cache-Control', 'no-cache')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()

            try:
                proc = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    cwd=str(self.project_cwd)
                )
                for line in proc.stdout:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        event = json.loads(line)
                        self.wfile.write(f"data: {json.dumps(event)}\n\n".encode('utf-8'))
                        self.wfile.flush()
                    except json.JSONDecodeError:
                        pass
                proc.wait(timeout=120)
                self.wfile.write(b"data: {\"type\": \"done\"}\n\n")
                self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError, OSError):
                if proc.poll() is None:
                    proc.terminate()
            except subprocess.TimeoutExpired:
                proc.terminate()
                self.wfile.write(b"data: {\"type\": \"error\", \"message\": \"Timeout\"}\n\n")
                self.wfile.flush()
            return

        if path == '/api/entity':
            etype = body.get('type', '')
            key = body.get('key', '')
            data = {}
            if body.get('name'):
                data['name'] = body['name']
            if body.get('description'):
                data['description'] = body['description']
            if not etype or not key:
                self._json_response({"ok": False, "error": "type and key are required"}, status=400)
                return
            self._mutation_response(['add', etype, key, json.dumps(data)], f"Add {etype}:{key}")
            return

        if path == '/api/link':
            frm = body.get('from', '')
            to = body.get('to', '')
            if not frm or not to:
                self._json_response({"ok": False, "error": "from and to are required"}, status=400)
                return
            to_list = to if isinstance(to, list) else [to]
            self._mutation_response(['link', frm] + to_list, f"Link {frm} → {', '.join(to_list)}")
            return

        if path == '/api/horizon':
            entity_id = body.get('entity_id', '')
            horizon = body.get('horizon', '')
            if not entity_id or not horizon:
                self._json_response({"ok": False, "error": "entity_id and horizon are required"}, status=400)
                return
            before = self._read_graph()
            if "error" not in before:
                _undo_stack.push(before, f"Move {entity_id} → horizon {horizon}")
            ok, stdout, stderr = self._run_know(['horizons', 'move', entity_id, horizon])
            if not ok and 'not found in any horizon' in stderr:
                ok, stdout, stderr = self._run_know(['horizons', 'add', horizon, entity_id])
            if ok and body.get('status'):
                self._run_know(['horizons', 'status', entity_id, body['status']])
            graph = self._read_graph()
            if ok:
                self._json_response({"ok": True, "graph": graph, "undo_available": len(_undo_stack) > 0})
            else:
                _undo_stack.pop()
                self._json_response({"ok": False, "error": _strip_ansi(stderr)}, status=422)
            return

        self.send_error(404, f"Unknown POST endpoint: {path}")

    def do_PUT(self):
        parsed = urlparse(self.path)
        path = parsed.path
        body = self._read_body()

        if path.startswith('/api/entity/'):
            entity_id = self._extract_entity_id(path, '/api/entity/')
            data = {}
            if body.get('name'):
                data['name'] = body['name']
            if body.get('description'):
                data['description'] = body['description']
            if not data:
                self._json_response({"ok": False, "error": "Nothing to update"}, status=400)
                return
            self._mutation_response(['nodes', 'update', entity_id, json.dumps(data)], f"Update {entity_id}")
            return
        self.send_error(404, f"Unknown PUT endpoint: {path}")

    def do_DELETE(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path.startswith('/api/entity/'):
            entity_id = self._extract_entity_id(path, '/api/entity/')
            self._mutation_response(['nodes', 'delete', entity_id, '-y'], f"Delete {entity_id}")
            return

        if path == '/api/link':
            body = self._read_body()
            frm = body.get('from', '')
            to = body.get('to', '')
            if not frm or not to:
                self._json_response({"ok": False, "error": "from and to are required"}, status=400)
                return
            self._mutation_response(['unlink', frm, to, '-y'], f"Unlink {frm} → {to}")
            return
        self.send_error(404, f"Unknown DELETE endpoint: {path}")


def serve(graph_path, port=5173, open_browser=True, project_cwd=None):
    """Start the dashboard HTTP server."""
    global _file_watcher, _claude_path

    graph_path = Path(graph_path).resolve()
    if not graph_path.exists():
        print(f"Error: Graph file not found: {graph_path}", file=sys.stderr)
        sys.exit(1)

    if project_cwd is None:
        project_cwd = graph_path.parent.parent.parent
    project_cwd = Path(project_cwd).resolve()

    # Find claude CLI for AI chat
    _claude_path = _find_claude()
    if _claude_path:
        print(f"  AI chat: enabled (claude at {_claude_path})")
    else:
        print(f"  AI chat: disabled (claude CLI not found)")

    # Start file watcher for hot updates
    _file_watcher = FileWatcher(graph_path)
    _file_watcher.start()

    DashboardHandler.graph_path = str(graph_path)
    DashboardHandler.project_cwd = project_cwd

    server = ThreadingHTTPServer(('127.0.0.1', port), DashboardHandler)
    url = f"http://127.0.0.1:{port}"

    print(f"spec-dashboard serving {graph_path.name}")
    print(f"  → {url}")
    print(f"  Press Ctrl+C to stop")

    if open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        _file_watcher.stop()
        print("\nStopped.")
        server.server_close()
