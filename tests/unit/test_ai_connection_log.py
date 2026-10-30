import json
from src.services.ai_connection_log import log_connection_test


def test_logs_destination_and_fingerprint_without_secret(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_connection_test("primary", "https://user:password@example.com/v1?key=secret#token", "model", "test-secret-key", "submitted")
    row=json.loads((tmp_path / "logs/ai-connection-tests.jsonl").read_text("utf-8"))
    assert row["base_url"] == "https://example.com/v1"
    assert row["key_source"] == "submitted"
    assert row["key_length"] == 15
    assert len(row["key_sha256"]) == 16
    assert "test-secret-key" not in json.dumps(row)
    assert "password" not in json.dumps(row)
