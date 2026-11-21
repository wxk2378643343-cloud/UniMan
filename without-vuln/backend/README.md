# UniMan 修订版后端

使用 FastAPI 与 SQLite，为高校后勤管理界面提供 API。

在 `without-vuln/backend/` 创建并激活 Python 虚拟环境后执行以下命令。

```sh
python -m pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

服务启动时初始化本地 SQLite 数据库。应用入口和数据库文件位置定义在 [app/main.py](app/main.py)。启动后可在本机访问 `http://127.0.0.1:8000/docs` 查看接口。
