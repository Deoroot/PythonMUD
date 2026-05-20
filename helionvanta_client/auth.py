"""Credential storage for the Helion Vanta client.

Uses the OS keyring (Windows Credential Manager on Windows, libsecret on
Linux) — credentials are encrypted by the OS and tied to the current user
account.  Nothing is stored in plaintext on disk.

If keyring is unavailable the functions return None / do nothing gracefully;
the login panel will simply appear every session.
"""
import os
import json

import paths as _paths

_SERVICE   = "HelionVantaMUD"
_META_PATH = os.path.join(_paths.data_dir(), ".login_meta.json")


# ------------------------------------------------------------------ #
# Public API
# ------------------------------------------------------------------ #

def save_credentials(username: str, password: str, host: str, port: int) -> bool:
    """Store username+password in OS keyring.  Returns True on success."""
    try:
        import keyring
        keyring.set_password(_SERVICE, _svc_key(host, port),
                             f"{username}\x00{password}")
        _write_meta(username, host, port)
        return True
    except Exception:
        return False


def load_credentials(host: str, port: int):
    """Return (username, password) from OS keyring, or None if not found."""
    meta = _read_meta()
    if not meta:
        return None
    if meta.get("host") != host or meta.get("port") != port:
        return None
    try:
        import keyring
        raw = keyring.get_password(_SERVICE, _svc_key(host, port))
        if raw and "\x00" in raw:
            username, password = raw.split("\x00", 1)
            return username, password
    except Exception:
        pass
    return None


def clear_credentials(host: str, port: int):
    """Remove saved credentials for this server."""
    try:
        import keyring
        keyring.delete_password(_SERVICE, _svc_key(host, port))
    except Exception:
        pass
    if os.path.exists(_META_PATH):
        try:
            os.remove(_META_PATH)
        except Exception:
            pass


def saved_username(host: str, port: int) -> str:
    """Return the saved username for display, or empty string."""
    creds = load_credentials(host, port)
    return creds[0] if creds else ""


# ------------------------------------------------------------------ #
# Internal helpers
# ------------------------------------------------------------------ #

def _svc_key(host: str, port: int) -> str:
    return f"{host}:{port}"


def _write_meta(username: str, host: str, port: int):
    os.makedirs(os.path.dirname(_META_PATH), exist_ok=True)
    try:
        with open(_META_PATH, "w") as f:
            json.dump({"username": username, "host": host, "port": port}, f)
    except Exception:
        pass


def _read_meta() -> dict:
    try:
        with open(_META_PATH) as f:
            return json.load(f)
    except Exception:
        return {}
