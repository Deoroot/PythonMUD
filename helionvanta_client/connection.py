"""Telnet + GMCP connection handler for the Helion Vanta pygame client.

Ported directly from the Rust Belt MUD client (connection.py) — the protocol
layer is server-agnostic; only the GMCP module names differ.

Runs in a background thread.  Parses the Evennia telnet stream:
  - Text lines  → passed to on_text callback
  - GMCP blocks → dispatched by module name to registered handlers

Usage:
    conn = HelionVantaConnection(host="localhost", port=4000)
    conn.on_text = lambda line: text_panel.append(line)
    conn.register_gmcp("HelionVanta.World.Map", map_panel.on_map)
    conn.start()
    conn.send_command("go n")
"""
import socket
import threading
import json
import re

_ANSI_RE = re.compile(r'\x1b\[[0-9;]*[mGKHFABCDEJsurh]|\x1b\([AB]|\x1b[=>]')

# Telnet option codes
IAC  = 255
DO   = 253
DONT = 254
WILL = 251
WONT = 252
SB   = 250
SE   = 240
GMCP = 201


class HelionVantaConnection:
    def __init__(self, host: str = "localhost", port: int = 4000):
        self.host = host
        self.port = port
        self._sock   = None
        self._thread = None
        self._running = False
        self._gmcp_handlers: dict = {}  # module_name: [callable]
        self.on_text          = None   # callable(text_line: str)
        self.on_connect_error = None   # callable(error_str: str)
        self._gmcp_negotiated = False

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def register_gmcp(self, module: str, handler):
        self._gmcp_handlers.setdefault(module, []).append(handler)

    def start(self):
        """Begin connection attempt in a background thread — non-blocking."""
        self.stop()
        self._gmcp_negotiated = False
        print(f"[CONN] Connecting to {self.host}:{self.port}...", flush=True)
        self._thread = threading.Thread(target=self._connect_and_read, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        self._gmcp_negotiated = False
        if self._sock:
            print("[CONN] Closing socket.", flush=True)
            self._sock.close()

    def send_command(self, cmd: str):
        if self._sock:
            print(f"[CMD]  >> {cmd}", flush=True)
            try:
                self._sock.sendall((cmd + "\n").encode("utf-8"))
            except Exception as exc:
                print(f"[CONN] send_command failed: {exc}", flush=True)

    # ------------------------------------------------------------------ #
    # Internal
    # ------------------------------------------------------------------ #

    def _send_raw(self, data: bytes):
        try:
            if self._sock:
                self._sock.sendall(data)
        except Exception:
            pass

    def _connect_and_read(self):
        try:
            sock = socket.create_connection((self.host, self.port), timeout=6.0)
            sock.settimeout(None)
        except Exception as exc:
            print(f"[CONN] Connection failed: {exc}", flush=True)
            if self.on_connect_error:
                self.on_connect_error(str(exc))
            return
        self._sock = sock
        print("[CONN] Socket open.", flush=True)
        self._running = True
        self._read_loop()

    def _read_loop(self):
        buf = b""
        while self._running:
            try:
                chunk = self._sock.recv(4096)
                if not chunk:
                    print("[CONN] Server closed connection.", flush=True)
                    break
                buf += chunk
                buf = self._process(buf)
            except Exception as exc:
                if self._running:
                    print(f"[CONN] Read error: {exc}", flush=True)
                break
        print("[CONN] Read loop exited.", flush=True)

    def _process(self, buf: bytes) -> bytes:
        """Parse telnet stream, extract GMCP SB blocks and plain text lines."""
        out = []
        i   = 0
        while i < len(buf):
            b = buf[i]
            if b == IAC:
                if i + 1 >= len(buf):
                    break
                nxt = buf[i + 1]
                if nxt == SB:
                    end = buf.find(bytes([IAC, SE]), i + 2)
                    if end == -1:
                        break
                    self._handle_sb(buf[i + 2: end])
                    i = end + 2
                elif nxt in (DO, DONT, WILL, WONT):
                    if i + 2 >= len(buf):
                        break
                    option = buf[i + 2]
                    if nxt == WILL and option == GMCP:
                        if not self._gmcp_negotiated:
                            self._send_raw(bytes([IAC, DO, GMCP]))
                            self._gmcp_negotiated = True
                    elif nxt == DO and option == GMCP:
                        self._send_raw(bytes([IAC, WILL, GMCP]))
                    i += 3
                elif nxt == IAC:
                    out.append(b'\xff')
                    i += 2
                else:
                    i += 2
            else:
                out.append(buf[i:i+1])
                i += 1

        remaining = buf[i:]
        text  = b"".join(out).decode("utf-8", errors="replace")
        lines = text.split("\n")
        for line in lines[:-1]:
            raw = line.rstrip("\r")
            if self.on_text and _ANSI_RE.sub("", raw).strip():
                self.on_text(raw)
        text_tail = lines[-1].encode("utf-8") if lines[-1] else b""
        return text_tail + remaining

    def _handle_sb(self, sb_data: bytes):
        if not sb_data or sb_data[0] != GMCP:
            return
        payload = sb_data[1:].decode("utf-8", errors="replace").strip()
        space = payload.find(" ")
        if space == -1:
            return
        module = payload[:space]
        try:
            data = json.loads(payload[space + 1:])
        except json.JSONDecodeError as e:
            print(f"[GMCP] {module}  PARSE ERROR: {e}", flush=True)
            return
        _noisy = {"HelionVanta.World.Map", "HelionVanta.Char.Status"}
        if module in _noisy:
            keys = list(data.keys()) if isinstance(data, dict) else type(data).__name__
            print(f"[GMCP] {module}  keys={keys}", flush=True)
        else:
            print(f"[GMCP] {module}  {data}", flush=True)
        if not self._gmcp_handlers.get(module):
            print(f"[GMCP] WARNING: no handler for {module}", flush=True)
        for handler in self._gmcp_handlers.get(module, []):
            try:
                handler(data)
            except Exception as e:
                import traceback
                print(f"[GMCP] HANDLER ERROR {module}: {e}", flush=True)
                traceback.print_exc()
