import asyncio
from types import SimpleNamespace
from src.services import round_email_service as module


def test_round_message_includes_all_results_and_marks_errors():
    records = [{"商品信息": {"商品链接": "https://example.test/item"}, "ai_analysis": a} for a in [
        {"is_recommended": True, "reason": "good"},
        {"is_recommended": False, "reason": "bad"},
        {"is_recommended": False, "reason": "待确认配置"},
        {"is_recommended": False, "error": "timeout"},
    ]]
    msg = module.build_round_message("task", "run1", records, True)
    assert "这是汇总的内容" in msg.content
    for label in ["推荐", "不推荐", "待确认", "分析失败", "https://example.test/item"]:
        assert label in msg.content
    assert "4 条" in msg.content
    empty = module.build_round_message("task", "run2", [], False)
    assert "部分结果" in empty.content
    assert "example.test" not in empty.content


def test_send_failure_does_not_fail_scraping(monkeypatch):
    class Client:
        def __init__(self, settings): pass
        def is_enabled(self): return True
        def _send_sync(self, message): raise RuntimeError("private")
    monkeypatch.setattr(module, "SmtpClient", Client)
    monkeypatch.setattr(module, "load_notification_settings", lambda: None)
    assert asyncio.run(module.send_round_summary("t", "r", [])) is False


def test_scrape_wrapper_sends_once_and_isolates_runs(monkeypatch):
    import src.scraper as scraper
    sent = []
    async def run(config, limit, records):
        records.append({"商品信息": {"商品ID": config["task_name"]}})
        return 1
    async def send(name, run_id, records, completed):
        sent.append((name, records, completed))
    monkeypatch.setattr(scraper, "_scrape_xianyu_run", run)
    monkeypatch.setattr(module, "send_round_summary", send)
    async def check():
        await scraper.scrape_xianyu({"task_name": "one"})
        await scraper.scrape_xianyu({"task_name": "two"})
    asyncio.run(check())
    assert len(sent) == 2
    assert sent[0][1] == [{"商品信息": {"商品ID": "one"}}]
    assert sent[1][1] == [{"商品信息": {"商品ID": "two"}}]
