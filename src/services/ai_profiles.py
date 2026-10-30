"""Ordered fallback profiles. Secrets stay in the local environment file."""
import json
from urllib.parse import urlparse
from src.infrastructure.config.env_manager import env_manager

BACKUPS_KEY = "AI_BACKUP_PROFILES"


def load_backups():
    raw = env_manager.get_value(BACKUPS_KEY, "[]") or "[]"
    try:
        data = json.loads(raw)
        if not isinstance(data, list): raise ValueError()
        return data
    except (ValueError, TypeError):
        raise ValueError("备用 AI 配置格式无效，请重新保存") from None


def public_backups(profiles=None):
    return [{**p, "api_key": "", "api_key_set": bool(p.get("api_key"))} for p in (load_backups() if profiles is None else profiles)]


def prepare_backups(submitted, existing=None):
    if not isinstance(submitted, list) or len(submitted) > 10:
        raise ValueError("最多配置 10 个备用 AI")
    old = {p["id"]: p for p in (load_backups() if existing is None else existing)}
    result=[]
    seen=set()
    for raw in submitted:
        if not isinstance(raw, dict): raise ValueError("备用 AI 配置格式无效")
        p={k: str(raw.get(k) or "").strip() for k in ("id", "name", "base_url", "model", "api_key", "proxy_url")}
        if not p["id"] or p["id"] in seen: raise ValueError("备用 AI 标识不能重复或为空")
        seen.add(p["id"])
        if not p["name"] or not p["model"]: raise ValueError("请填写备用配置名称和模型名称")
        url=urlparse(p["base_url"])
        if url.scheme not in {"http", "https"} or not url.netloc or url.username or url.password or url.query or url.fragment:
            raise ValueError("备用 API 地址必须是有效 HTTP/HTTPS 地址，不能包含凭据或查询参数")
        if p["proxy_url"]:
            proxy=urlparse(p["proxy_url"])
            if proxy.scheme not in {"http", "https", "socks5", "socks5h"} or not proxy.netloc:
                raise ValueError("备用代理地址无效")
        previous=old.get(p["id"], {})
        if not p["api_key"]:
            if previous.get("base_url") == p["base_url"]:
                p["api_key"]=previous.get("api_key", "")
            else:
                raise ValueError("新增备用或更换中转地址时，请重新填写该配置的 API Key")
        if not p["api_key"]: raise ValueError("请填写备用 API Key")
        result.append(p)
    return result


def ordered_profiles():
    primary=dict(id="primary", name="主配置", base_url=env_manager.get_value("OPENAI_BASE_URL", ""), model=env_manager.get_value("OPENAI_MODEL_NAME", ""), api_key=env_manager.get_value("OPENAI_API_KEY", ""), proxy_url=env_manager.get_value("PROXY_URL", ""))
    return [primary, *load_backups()]
