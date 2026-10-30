"""Local, redacted connection-test diagnostics."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit
from threading import Lock

_LOCK = Lock()


def log_connection_test(channel, base_url, model, api_key, key_source):
    try:
        url = urlsplit(base_url or "")
        authority = url.netloc.rsplit("@", 1)[-1]
        safe_url = urlunsplit((url.scheme, authority, url.path, "", ""))
        key = api_key or ""
        row = dict(timestamp=datetime.now(timezone.utc).isoformat(), channel=channel,
                   base_url=safe_url, model=model, key_source=key_source,
                   key_length=len(key), key_sha256=hashlib.sha256(key.encode()).hexdigest()[:16] if key else "")
        line = json.dumps(row, ensure_ascii=False)
        with _LOCK:
            path = Path("logs/ai-connection-tests.jsonl")
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as output:
                output.write(line + "\n")
        print("[AI连接测试] " + line, flush=True)
    except Exception:
        print("[AI连接测试] 诊断日志写入失败", flush=True)
