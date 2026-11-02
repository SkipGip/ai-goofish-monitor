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


def test_image_attachment_and_link_fallback(monkeypatch):
    import httpx
    original = httpx.AsyncClient
    def handler(request):
        assert request.url.scheme == "https"
        return httpx.Response(200, headers={"content-type":"image/jpeg"}, content=b"test-image")
    monkeypatch.setattr(httpx, "AsyncClient", lambda **kw: original(transport=httpx.MockTransport(handler), **kw))
    records = [{"商品信息":{"商品图片列表":["http://img.alicdn.com/a.jpg", "http://127.0.0.1/private"]}}]
    message = module.build_round_message("t", "r", records, True)
    asyncio.run(module.attach_round_images(message, records))
    assert message.attachments == [("item-1-photo-1.jpg", "image/jpeg", b"test-image")]
    assert "未附带" in message.content
    assert "这是汇总的内容" in message.content


def test_summary_batches_five_without_losing_items(monkeypatch):
    calls = []
    async def send(name, run_id, records, completed, index, count):
        calls.append((list(records), index, count))
        return True
    monkeypatch.setattr(module, "_send_round_batch", send)
    assert asyncio.run(module.send_round_summary("t", "r", list(range(19))))
    assert [len(c[0]) for c in calls] == [5, 5, 5, 4]
    assert [x for c in calls for x in c[0]] == list(range(19))
    assert all(c[2] == 4 for c in calls)
