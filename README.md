# UniMan 高校后勤服务管理系统

UniMan 面向高校后勤业务，包含 Vue 用户界面、FastAPI 后端和 SQLite 数据层。业务范围和角色定义见 [需求设计](doc/高校后勤服务管理系统需求设计.md)。

| 路径 | 内容 |
| --- | --- |
| [without-vuln/backend](without-vuln/backend/README.md) | 修订版后端、应用入口和本地数据 |
| [without-vuln/frontend](without-vuln/frontend/README.md) | 修订版前端依赖、开发服务和构建 |
| [docs/paper.md](docs/paper.md) | 系统设计与实现说明 |
| `with-vuln/` | 供防御性对照审阅的历史实现 |

## 本地使用

从修订版后端文档开始，按前端文档启动 Web 界面。修订版 Vite 开发服务器将 API 请求代理到本机的后端 8000 端口。修改后端端口时，同步更新 [Vite 代理配置](without-vuln/frontend/vite.config.js)。

演示环境应使用独立的 SQLite 文件和虚构数据。


后端入口为 `python -m uvicorn app.main:app --reload --port 8000`，在 `without-vuln/backend/` 中运行。前端在 `without-vuln/frontend/` 中执行 `npm ci` 和 `npm run dev`。
