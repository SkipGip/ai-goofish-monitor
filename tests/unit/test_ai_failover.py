import asyncio
import json
from types import SimpleNamespace
import pytest
from src.services import ai_failover as module
from src.services.ai_profiles import prepare_backups, public_backups


def profile(name):
    return dict(id=name, name=name, base_url="https://"+name+".example/v1", model=name, api_key="secret-"+name, proxy_url="")


def test_switch_after_five_and_next_request_starts_primary(monkeypatch):
    calls=[]
    closed=[]
    class Client:
        async def close(self): closed.append(self.name)
    def factory(p):
        c=Client(); c.name=p["name"]; return c
    async def create(c, mode, params):
        calls.append(c.name)
        if c.name=="primary": raise TimeoutError("private-secret")
        return SimpleNamespace(output_text="valid")
    monkeypatch.setattr(module,"make_client",factory)
    monkeypatch.setattr(module,"create_ai_response_async",create)
    async def run():
        for _ in range(2):
            assert await module.request_with_failover([], [profile("primary"),profile("backup")], retry_delay=0)=="valid"
    asyncio.run(run())
    assert calls==(["primary"]*5+["backup"])*2
    assert closed==["primary","backup"]*2


def test_invalid_results_fail_over_and_exhaustion_is_bounded(monkeypatch):
    calls=[]
    class Client:
        async def close(self): pass
    monkeypatch.setattr(module,"make_client",lambda p:Client())
    async def create(c, mode, params):
        calls.append(params["model"])
        return SimpleNamespace(output_text="not json")
    monkeypatch.setattr(module,"create_ai_response_async",create)
    with pytest.raises(RuntimeError,match="全部"):
        asyncio.run(module.request_with_failover([], [profile("primary"),profile("backup")], validate=json.loads,retry_delay=0))
    assert calls==["primary"]*5+["backup"]*5


def test_masked_keys_survive_reorder_but_not_destination_change():
    original=[profile("a"),profile("b")]
    visible=public_backups(original)
    assert all(p["api_key"]=="" and p["api_key_set"] for p in visible)
    saved=prepare_backups(visible[::-1],original)
    assert saved[0]["api_key"]=="secret-b"
    visible[0]["base_url"]="https://different.example/v1"
    with pytest.raises(ValueError): prepare_backups(visible,original)
    assert prepare_backups([],original)==[]


def test_sdk_retries_disabled(monkeypatch):
    options={}
    monkeypatch.setattr(module,"AsyncOpenAI",lambda **kwargs: options.update(kwargs))
    module.make_client(profile("a"))
    assert options["max_retries"]==0


def test_product_analysis_uses_backups_when_primary_client_unavailable(monkeypatch, tmp_path):
    import src.ai_handler as handler
    from src.services import ai_profiles
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(handler, "client", None)
    monkeypatch.setattr(ai_profiles, "load_backups", lambda:[profile("backup")])
    monkeypatch.setattr(ai_profiles, "ordered_profiles", lambda:[profile("primary"),profile("backup")])
    expected={"is_recommended":False,"reason":"test","criteria_analysis":{}}
    async def fake(messages, profiles, **kwargs):
        assert len(profiles)==2
        assert "validate" in kwargs
        return expected
    monkeypatch.setattr(module, "request_with_failover", fake)
    assert asyncio.run(handler.get_ai_analysis({"商品信息":{"商品ID":"1"}},prompt_text="test"))==expected


def test_concurrent_requests_do_not_share_failover_state(monkeypatch):
    class Client:
        async def close(self): pass
    monkeypatch.setattr(module,"make_client",lambda p: Client())
    calls={"one":[],"two":[]}
    async def create(c, mode, params):
        tag=params["messages"][0]["content"]
        calls[tag].append(params["model"])
        await asyncio.sleep(0)
        if tag=="one" and params["model"]=="primary": raise TimeoutError()
        return SimpleNamespace(output_text="ok")
    monkeypatch.setattr(module,"create_ai_response_async",create)
    async def run():
        await asyncio.gather(*(module.request_with_failover([{"role":"user","content":tag}], [profile("primary"),profile("backup")],retry_delay=0) for tag in calls))
    asyncio.run(run())
    assert calls["one"]==["primary"]*5+["backup"]
    assert calls["two"]==["primary"]


def test_primary_read_timeout_180_backup_60(monkeypatch):
    captured = []
    monkeypatch.setattr(module.httpx, "AsyncClient", lambda **kwargs: object())
    monkeypatch.setattr(module, "AsyncOpenAI", lambda **kwargs: captured.append(kwargs))
    module.make_client(profile("primary"))
    module.make_client(profile("backup"))
    assert [c["timeout"].read for c in captured] == [180.0, 60.0]
    assert all(c["timeout"].connect == 15.0 for c in captured)
    assert all(c["max_retries"] == 0 for c in captured)
