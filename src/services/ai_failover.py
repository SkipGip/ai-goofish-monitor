"""Per-request failover: five explicit attempts per endpoint, always start primary."""
import asyncio
import httpx
from openai import AsyncOpenAI
from src.services.ai_request_compat import (
    CHAT_COMPLETIONS_API_MODE, RESPONSES_API_MODE, build_ai_request_params,
    create_ai_response_async, is_chat_completions_api_unsupported_error,
    is_responses_api_unsupported_error, is_json_output_unsupported_error,
    is_temperature_unsupported_error, remove_temperature_param,
)
from src.services.ai_response_parser import extract_ai_response_content


def make_client(profile):
    from urllib.parse import urlparse
    url = urlparse(profile.get("base_url") or "")
    if url.scheme not in {"http", "https"} or not url.netloc or not profile.get("model"):
        raise ValueError("AI 地址或模型未配置")
    options=dict(api_key=profile.get("api_key") or "not-required", base_url=profile["base_url"], max_retries=0, timeout=httpx.Timeout(60.0, connect=15.0, read=180.0 if profile.get("id") == "primary" else 60.0))
    # Explicit per-profile transport avoids cross-request proxy mutation.
    options["http_client"]=httpx.AsyncClient(proxy=profile.get("proxy_url") or None, trust_env=False)
    try:
        return AsyncOpenAI(**options)
    except Exception:
        # Construction normally cannot fail after settings validation.
        raise RuntimeError("AI 客户端初始化失败，请检查地址和代理") from None


async def request_with_failover(messages, profiles, *, temperature=0.1, max_output_tokens=4000, enable_json_output=True, enable_thinking=False, validate=None, attempts=5, retry_delay=1):
    for index, profile in enumerate(profiles):
        mode=CHAT_COMPLETIONS_API_MODE
        use_json=enable_json_output
        use_temperature=True
        client=None
        label=f"主配置" if index == 0 else f"备用 {index}"
        try:
            client=make_client(profile)
            for attempt in range(1, attempts+1):
                try:
                    params=build_ai_request_params(mode,model=profile["model"],messages=messages,temperature=temperature,max_output_tokens=max_output_tokens,enable_json_output=use_json)
                    if not use_temperature: params=remove_temperature_param(params)
                    if enable_thinking: params["extra_body"]={"enable_thinking":False}
                    response=await create_ai_response_async(client,mode,params)
                    text=extract_ai_response_content(response)
                    result=validate(text) if validate else text
                    if result is None or result is False: raise ValueError("Invalid response")
                    print(f"[AI切换] {label} 第 {attempt}/{attempts} 次成功；下一条重新优先使用主配置")
                    return result
                except Exception as exc:
                    if mode==CHAT_COMPLETIONS_API_MODE and is_chat_completions_api_unsupported_error(exc): mode=RESPONSES_API_MODE
                    elif mode==RESPONSES_API_MODE and is_responses_api_unsupported_error(exc): mode=CHAT_COMPLETIONS_API_MODE
                    if is_json_output_unsupported_error(exc): use_json=False
                    if is_temperature_unsupported_error(exc): use_temperature=False
                    code=getattr(exc,"status_code",None)
                    print(f"[AI切换] {label} 第 {attempt}/{attempts} 次失败：{type(exc).__name__}，状态码 {code}")
                    if attempt < attempts: await asyncio.sleep(retry_delay)
        except Exception as exc:
            print(f"[AI切换] {label} 无法初始化：{type(exc).__name__}")
        finally:
            if client is not None:
                try: await client.close()
                except Exception: pass
        if index+1 < len(profiles): print(f"[AI切换] {label} 失败，切换至备用 {index+1}")
    raise RuntimeError("全部 AI 配置均调用失败，请检查日志中的配置顺序和状态码")
