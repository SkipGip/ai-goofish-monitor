# Repository Guidelines

## 项目结构与模块组织
- 后端位于 `src/`，入口 `src/app.py`，API 路由在 `src/api/routes/`，服务层在 `src/services/`，领域模型在 `src/domain/`，基础设施在 `src/infrastructure/`。
- 前端在 `web-ui/`（Vue 3 + Vite），视图放于 `web-ui/src/views/`，组件在 `web-ui/src/components/`，构建产物会复制到根目录 `dist/`。
- 测试位于 `tests/`，命名遵循 `test_*.py` 或 `tests/*/test_*.py`。
- 运行数据与资源：`prompts/`、`jsonl/`、`logs/`、`images/`、`static/`、`state/`，配置文件 `config.json` 与 `.env` 位于仓库根目录。

## 构建、测试与本地开发
- 后端开发：`python -m src.app` 或 `uvicorn src.app:app --host 0.0.0.0 --port 8000 --reload`。
- 爬虫任务：`python spider_v2.py --task-name "MacBook Air M1" --debug-limit 3`（可用 `--config` 指定自定义配置）。
- 前端开发：`cd web-ui && npm install && npm run dev`；构建：`cd web-ui && npm run build`（产物复制到根目录 `dist/`）。
- 一键本地启动：`bash start.sh`（自动安装依赖、前端构建并启动后端）。
- Docker：`docker compose up --build -d`，查看日志 `docker compose logs -f app`，停止 `docker compose down`。

## 编码风格与命名约定
- 保持分层：API → services → domain → infrastructure，避免跨层耦合，模块保持精简。
- Python 测试函数命名为 `test_*`，文件与路径遵循上述测试目录规范。
- 使用描述性、任务导向的命名（如爬虫任务名、配置键），与业务含义对应。

## 架构与运行时
- 后端使用 FastAPI 提供 API 与静态资源，爬虫与 AI 推理在独立任务进程中协作，前后端通过 HTTP/Web UI 交互。
- 任务运行会在 `jsonl/` 写入结果、在 `logs/` 留存运行日志、在 `images/` 下载图片，前端监控页面依赖这些数据。
- 默认监听 8000 端口，前端构建后静态文件可由后端或 Docker 镜像直接提供。

## 测试指南
- 测试框架：`pytest`（默认同步测试，无需 `pytest-asyncio`）。
- 运行全部测试：`pytest`；覆盖率：`pytest --cov=src` 或 `coverage run -m pytest`；定向测试：`pytest tests/test_utils.py::test_safe_get`。
- 优先覆盖核心服务、爬虫管道的异常分支与重试逻辑，避免回归。
- PR 前请运行相关测试，新增逻辑补充针对性用例。

## 提交与 PR 规范
- Commit 采用类 Conventional Commits：`feat(...)`、`fix(...)`、`refactor(...)`、`chore(...)`、`docs(...)` 等。
- PR 需说明变更范围与影响模块；UI 变更在 `web-ui/` 提供截图；关联相关 Issue；提及配置或迁移步骤。

## 安全与配置提示
- 复制 `.env.example` 为 `.env`，设置必填项 `OPENAI_API_KEY`、`OPENAI_BASE_URL`、`OPENAI_MODEL_NAME` 等。
- 不要提交真实凭据或 cookies（如 `state.json`）；Playwright 需本地浏览器，Docker 镜像已预装 Chromium。
- Web 认证默认 `admin/admin123`，生产环境务必修改，推荐启用 HTTPS 并限制访问来源。

## 本地工作区位置（用户要求）

- 本地项目、克隆仓库和新工作区统一放在 `D:\Codex\Workspaces`，不要放在 C 盘；用户指定其他 D 盘位置时遵从指定位置。
- 当前工作区：`D:\Codex\Workspaces\xianyu-helper-mail`；商品监控位于其 `ai-goofish-monitor` 子目录。
- 同级 `xianyu-mailer`、`xianyu-helper-mail-repo` 保持相对路径关系。
- 项目虚拟环境、node_modules、构建产物、日志和数据均保存在 D 盘项目内。
- C 盘旧目录仅作为迁移提示，后续命令和编辑使用 D 盘真实路径。
- 不擅自移动应用安装目录、用户凭据或系统配置。

## 自动提交与远端推送（用户要求）

- 本项目每次完成代码、文档或项目规则修改后，执行与改动相关的检查，然后自动提交并 push 到用户的远端仓库，无需重复询问是否提交或推送；用户明确要求暂不提交时例外。
- 目标仓库为 https://github.com/SkipGip/ai-goofish-monitor；推送前确认远端与当前分支，禁止误推上游 Usagi-org 仓库。
- 仅提交本次任务相关的源代码和文档；不得提交 .env、API Key、账号登录态、cookies、数据库、私人监控配置、日志或其他运行数据。
- 提交使用 Conventional Commits；不要强制推送，不覆盖或丢弃用户已有改动。
- 若目录缺少 Git 元数据、认证不可用或推送失败，明确报告未推送及原因；保留本地修改，不将本地保存或提交报告成远端推送成功。需要恢复 Git 工作区时使用 D 盘，并保留现有运行数据。
