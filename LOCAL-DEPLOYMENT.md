# Windows 本地部署

此 fork 增加 Windows 本机启动入口，默认只监听 `127.0.0.1:18080`。

## 安装

需要 Python 3.11+、Node.js 22.12+ 和 Microsoft Edge。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-local.lock.txt
Copy-Item .env.example .env
npm --prefix web-ui ci
npm --prefix web-ui run build
```

前端构建产物直接写入根目录 `dist/`。`requirements-local.lock.txt` 记录本次 Windows/Python 3.11 部署验证过的依赖版本；升级依赖后应重新验证。

## 配置与启动

编辑本地 `.env`：

- 设置 `WEB_USERNAME` 和自选的 `WEB_PASSWORD`，不要保留示例密码。
- 设置 `SERVER_PORT=18080`，与本地启动入口保持一致；修改端口时同时修改 `run-local.py`。
- 设置 `LOGIN_IS_EDGE=true`，使用本机 Edge。
- 如需 AI 判断，配置 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL_NAME`；也可先使用关键词判断。
- 在管理页面的账号管理中导入闲鱼登录态；通知渠道按需配置。

双击 `start-local.cmd`，访问 http://127.0.0.1:18080 。用 Ctrl+C 停止服务；不注册开机自启，不要重复启动。

`run-local.py` 先导入应用再初始化 Uvicorn 日志，避免上游 Windows 模块重设标准输出流后，日志处理器继续使用已分离的输出流。

## 验证范围

本次部署已验证前端构建、`pip check`、健康检查、管理后台登录和 Edge 页面加载。真实商品抓取、AI 调用与通知送达需在配置账号和服务后单独验收。

## 不要提交本地数据

`.env`、账号登录态、数据库、图片、日志、`.venv/`、`.runtime/`、`node_modules/` 和构建产物不应上传。仓库只包含源码、依赖清单和说明，不包含可用密码或密钥。
