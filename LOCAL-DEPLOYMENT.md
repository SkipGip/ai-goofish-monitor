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

## SMTP 邮件通知

系统设置 → 通知设置 → SMTP 邮箱：填写服务器、端口（SSL 465 或 STARTTLS 587）、发件邮箱、收件邮箱及邮箱授权码；登录账号留空时使用发件邮箱。保存后可发送测试邮件。授权码保存在本地 .env，接口只返回是否已配置，不返回授权码。只有被判为推荐的商品触发通知。SMTP 接收成功不代表最终进入收件箱，请检查收件箱或垃圾邮件。清空该渠道并保存可禁用。

## 多 AI 配置与自动切换

系统设置 → AI 模型：原设置为主配置，下方可添加最多 10 个备用（地址、Key、模型、代理各自独立），用上移/下移调整顺序。保存时 Key 留空保留旧值，更换地址必须重填 Key。Key 不回显，只保存于本地 .env。每条商品从主配置开始，每组最多 5 次尝试（含兼容性重试）；失败切换下一组，成功结束当前分析，下一条恢复主配置。全部失败则保留分析失败结果，不无限循环。备用成功不重复调用主配置。各商品独立计数，SDK 自动重试关闭；多配置流程每次请求读取超时为 60 秒，连接超时 15 秒。备用也用于生成任务分析标准。修改后重启运行任务。连接测试只测试所选备用，不自动切换。

## AI 连接测试日志

点击主配置或备用的测试按钮时，实际选用的地址、模型、Key 来源、长度与 SHA-256 前 16 位指纹写入 `logs/ai-connection-tests.jsonl`，同时输出到服务标准日志。submitted 表示本次输入，saved_primary/saved_backup 表示使用已保存的对应 Key。不会记录完整 Key，URL 查询参数与凭据会移除。日志为本地运行数据，不提交到远端。
