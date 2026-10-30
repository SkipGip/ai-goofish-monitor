from src.services import ai_profiles


def test_backups_temporarily_disabled_without_erasing_saved_profiles(monkeypatch):
    saved = [{"id": "kept", "api_key": "test-only"}]
    monkeypatch.setattr(ai_profiles, "load_backups", lambda: saved)
    assert ai_profiles.active_backups() == []
    assert len(ai_profiles.ordered_profiles()) == 1
    assert ai_profiles.load_backups() == saved
