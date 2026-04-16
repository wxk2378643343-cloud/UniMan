from __future__ import annotations

import sqlite3
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "uniman_vuln.db"
UPLOAD_DIR = BASE_DIR / "uploads"

app = FastAPI(
    title="UniMan Vulnerable API",
    description="高校后勤服务管理系统漏洞研究版",
    version="0.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


class LoginPayload(BaseModel):
    username: str
    password: str


class RepairPayload(BaseModel):
    student_name: str
    location: str
    repair_type: str
    description: str
    contact_phone: str
    image_url: str = ""


class RepairUpdatePayload(BaseModel):
    student_name: str
    location: str
    repair_type: str
    description: str
    contact_phone: str
    image_url: str = ""
    status: str
    assignee: str


class NoticePayload(BaseModel):
    title: str
    category: str
    content: str
    publisher: str


class NoticeUpdatePayload(BaseModel):
    title: str
    category: str
    content: str
    publisher: str
    status: str


class ComplaintPayload(BaseModel):
    student_name: str
    category: str
    content: str
    contact_phone: str


class ComplaintUpdatePayload(BaseModel):
    category: str
    content: str
    status: str
    reply: str


class UserPayload(BaseModel):
    username: str
    password: str
    role: str
    display_name: str
    department: str
    status: str = "启用"


class RolePayload(BaseModel):
    name: str
    code: str
    permissions: str
    status: str = "启用"


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    info = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in info)


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    cursor = conn.cursor()

    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            display_name TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '启用'
        );

        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL,
            permissions TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '启用'
        );

        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            location TEXT NOT NULL,
            repair_type TEXT NOT NULL,
            description TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            image_url TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT '待受理',
            assignee TEXT NOT NULL DEFAULT '未分配',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            publisher TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '已发布',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            category TEXT NOT NULL,
            content TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '待处理',
            reply TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS security_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            log_type TEXT NOT NULL,
            username TEXT NOT NULL,
            action TEXT NOT NULL,
            ip_address TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            detail TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    if not column_exists(cursor, "users", "status"):
        cursor.execute("ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT '启用'")
    if not column_exists(cursor, "notices", "status"):
        cursor.execute("ALTER TABLE notices ADD COLUMN status TEXT NOT NULL DEFAULT '已发布'")

    if cursor.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO roles(name, code, permissions, status) VALUES (?, ?, ?, ?)",
            [
                ("系统管理员", "admin", "用户管理,角色管理,公告管理,工单管理,安全审计", "启用"),
                ("后勤工作人员", "worker", "工单处理,公告查看,投诉查看", "启用"),
                ("学生", "student", "报修提交,投诉建议,公告查看", "启用"),
                ("安全审计员", "auditor", "安全日志,漏洞研究展示", "启用"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO users(username, password, role, display_name, department, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("admin", "admin123", "系统管理员", "王老师", "信息中心", "启用"),
                ("repair01", "123456", "后勤工作人员", "李师傅", "维修中心", "启用"),
                ("student01", "123456", "学生", "张同学", "计算机学院", "启用"),
                ("audit01", "123456", "安全审计员", "周老师", "网信办", "启用"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM repairs").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO repairs(student_name, location, repair_type, description, contact_phone, status, assignee)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("张同学", "3号宿舍楼 402", "宿舍报修", "空调制冷效果差，夜间噪音较大。", "13800000001", "处理中", "李师傅"),
                ("陈同学", "一食堂 二层", "餐饮反馈", "窗口照明故障，晚间取餐区域较暗。", "13800000002", "待受理", "未分配"),
                ("刘同学", "图书馆东侧公共区域", "公共设施", "走廊饮水机无法加热。", "13800000003", "已完成", "周师傅"),
                ("何同学", "8号教学楼 203", "教学设备", "投影仪无法开机。", "13800000004", "已分配", "赵师傅"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO notices(title, category, content, publisher, status) VALUES (?, ?, ?, ?, ?)",
            [
                ("北校区停水通知", "后勤公告", "因主管网检修，4月18日 09:00-12:00 北校区部分宿舍暂停供水。", "后勤保障处", "已发布"),
                ("宿舍报修高峰提醒", "服务提醒", "近期空调集中检修，请同学提交工单时补充房间号与联系电话。", "维修中心", "已发布"),
                ("五一值班安排", "值班通知", "节假日期间维保热线保持畅通，值班表已同步到各楼宇。", "办公室", "草稿"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM complaints").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO complaints(student_name, category, content, contact_phone, status, reply)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("张同学", "服务态度", "晚间报修电话接听不及时，希望优化值班安排。", "13800000001", "待处理", ""),
                ("李同学", "环境卫生", "宿舍楼公共洗衣房排水口异味较重。", "13800000005", "处理中", "已转保洁组核查。"),
                ("孙同学", "餐饮建议", "建议晚餐高峰时段增加自助结算通道。", "13800000006", "已回复", "已提交食堂运营组评估。"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM security_logs").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("登录日志", "admin", "登录成功", "127.0.0.1", "低", "管理员登录后台。"),
                ("登录日志", "unknown", "登录失败", "10.10.1.23", "中", "同一 IP 30 秒内多次尝试弱口令。"),
                ("操作日志", "repair01", "更新工单状态", "127.0.0.1", "低", "将工单 #1 更新为处理中。"),
                ("异常请求", "guest", "访问用户列表", "10.10.2.88", "高", "未鉴权访问 /api/users 接口。"),
                ("异常请求", "guest", "跨域调用", "10.10.2.88", "中", "来自任意源的前端脚本可直接读取接口。"),
            ],
        )

    conn.commit()
    conn.close()


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/upload")
async def upload_image(file: UploadFile = File(...)) -> dict[str, str]:
    suffix = Path(file.filename or "").suffix or ".bin"
    file_name = f"{uuid.uuid4().hex}{suffix}"
    target = UPLOAD_DIR / file_name
    content = await file.read()
    target.write_bytes(content)
    return {
        "message": "上传成功",
        "file_name": file_name,
        "url": f"/uploads/{file_name}",
    }


@app.post("/api/auth/login")
def login(payload: LoginPayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    query = (
        "SELECT id, username, role, display_name, department, status FROM users "
        f"WHERE username = '{payload.username}' AND password = '{payload.password}'"
    )
    user = cursor.execute(query).fetchone()

    cursor.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "登录日志",
            payload.username,
            "登录成功" if user else "登录失败",
            "127.0.0.1",
            "低" if user else "中",
            "当前版本登录逻辑存在 SQL 注入和明文密码缺陷。",
        ),
    )
    conn.commit()
    conn.close()

    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    return {
        "message": "登录成功",
        "token": f"vuln-token-{user['id']}",
        "user": dict(user),
        "risk_note": "当前版本保留了研究用途的认证缺陷，请勿用于真实环境。",
    }


@app.get("/api/dashboard/summary")
def dashboard_summary() -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()

    total_repairs = cursor.execute("SELECT COUNT(*) FROM repairs").fetchone()[0]
    pending_repairs = cursor.execute(
        "SELECT COUNT(*) FROM repairs WHERE status IN ('待受理', '已分配', '处理中')"
    ).fetchone()[0]
    total_notices = cursor.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_complaints = cursor.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    high_risk_logs = cursor.execute(
        "SELECT COUNT(*) FROM security_logs WHERE risk_level = '高'"
    ).fetchone()[0]

    repair_status = dict_rows(
        cursor.execute(
            "SELECT status AS name, COUNT(*) AS value FROM repairs GROUP BY status ORDER BY COUNT(*) DESC"
        ).fetchall()
    )
    complaint_status = dict_rows(
        cursor.execute(
            "SELECT status AS name, COUNT(*) AS value FROM complaints GROUP BY status ORDER BY COUNT(*) DESC"
        ).fetchall()
    )
    notice_category = dict_rows(
        cursor.execute(
            "SELECT category AS name, COUNT(*) AS value FROM notices GROUP BY category ORDER BY COUNT(*) DESC"
        ).fetchall()
    )
    department_load = [
        {"name": "维修中心", "value": 18},
        {"name": "宿舍管理", "value": 12},
        {"name": "保洁服务", "value": 9},
        {"name": "餐饮中心", "value": 7},
    ]

    latest_repairs = dict_rows(
        cursor.execute(
            """
            SELECT id, student_name, location, repair_type, status, assignee, created_at
            FROM repairs ORDER BY id DESC LIMIT 6
            """
        ).fetchall()
    )
    latest_logs = dict_rows(
        cursor.execute(
            """
            SELECT id, log_type, username, action, risk_level, created_at
            FROM security_logs ORDER BY id DESC LIMIT 6
            """
        ).fetchall()
    )

    conn.close()
    return {
        "metrics": [
            {"label": "累计工单", "value": total_repairs, "accent": "sun"},
            {"label": "待处理事项", "value": pending_repairs, "accent": "alert"},
            {"label": "投诉建议", "value": total_complaints, "accent": "sky"},
            {"label": "系统用户", "value": total_users, "accent": "leaf"},
            {"label": "公告数量", "value": total_notices, "accent": "sea"},
            {"label": "高风险日志", "value": high_risk_logs, "accent": "danger"},
        ],
        "charts": {
            "repairStatus": repair_status,
            "complaintStatus": complaint_status,
            "noticeCategory": notice_category,
            "departmentLoad": department_load,
        },
        "repairs": latest_repairs,
        "logs": latest_logs,
        "security": {
            "status": "高风险研究环境",
            "open_risks": 5,
            "logs_today": len(latest_logs),
            "description": "该版本故意保留弱口令、宽松跨域、越权访问与敏感数据暴露，用于论文实验与修复对照。",
        },
    }


@app.get("/api/repairs")
def list_repairs() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(
        conn.execute(
            """
            SELECT id, student_name, location, repair_type, description, contact_phone, image_url,
                   status, assignee, created_at
            FROM repairs ORDER BY id DESC
            """
        ).fetchall()
    )
    conn.close()
    return rows


@app.post("/api/repairs")
def create_repair(payload: RepairPayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO repairs(student_name, location, repair_type, description, contact_phone, image_url)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.student_name,
            payload.location,
            payload.repair_type,
            payload.description,
            payload.contact_phone,
            payload.image_url,
        ),
    )
    cursor.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("操作日志", payload.student_name, "提交报修", "127.0.0.1", "低", "学生提交新的报修工单。"),
    )
    conn.commit()
    repair_id = cursor.lastrowid
    conn.close()
    return {"message": "报修提交成功", "id": repair_id}


@app.put("/api/repairs/{repair_id}")
def update_repair(repair_id: int, payload: RepairUpdatePayload) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE repairs
        SET student_name = ?, location = ?, repair_type = ?, description = ?, contact_phone = ?,
            image_url = ?, status = ?, assignee = ?
        WHERE id = ?
        """,
        (
            payload.student_name,
            payload.location,
            payload.repair_type,
            payload.description,
            payload.contact_phone,
            payload.image_url,
            payload.status,
            payload.assignee,
            repair_id,
        ),
    )
    conn.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("操作日志", payload.assignee or "未分配", "更新工单", "127.0.0.1", "低", f"更新工单 #{repair_id}。"),
    )
    conn.commit()
    conn.close()
    return {"message": "工单状态已更新"}


@app.get("/api/notices")
def list_notices() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(
        conn.execute(
            """
            SELECT id, title, category, content, publisher, status, created_at
            FROM notices ORDER BY id DESC
            """
        ).fetchall()
    )
    conn.close()
    return rows


@app.post("/api/notices")
def create_notice(payload: NoticePayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notices(title, category, content, publisher, status) VALUES (?, ?, ?, ?, ?)",
        (payload.title, payload.category, payload.content, payload.publisher, "已发布"),
    )
    cursor.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("操作日志", payload.publisher, "发布公告", "127.0.0.1", "低", "后台新增公告。"),
    )
    conn.commit()
    notice_id = cursor.lastrowid
    conn.close()
    return {"message": "公告发布成功", "id": notice_id}


@app.put("/api/notices/{notice_id}")
def update_notice(notice_id: int, payload: NoticeUpdatePayload) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        """
        UPDATE notices
        SET title = ?, category = ?, content = ?, publisher = ?, status = ?
        WHERE id = ?
        """,
        (payload.title, payload.category, payload.content, payload.publisher, payload.status, notice_id),
    )
    conn.commit()
    conn.close()
    return {"message": "公告状态已更新"}


@app.get("/api/complaints")
def list_complaints() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(
        conn.execute(
            """
            SELECT id, student_name, category, content, contact_phone, status, reply, created_at
            FROM complaints ORDER BY id DESC
            """
        ).fetchall()
    )
    conn.close()
    return rows


@app.post("/api/complaints")
def create_complaint(payload: ComplaintPayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO complaints(student_name, category, content, contact_phone)
        VALUES (?, ?, ?, ?)
        """,
        (payload.student_name, payload.category, payload.content, payload.contact_phone),
    )
    cursor.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("操作日志", payload.student_name, "提交投诉建议", "127.0.0.1", "低", "学生新增投诉建议。"),
    )
    conn.commit()
    complaint_id = cursor.lastrowid
    conn.close()
    return {"message": "投诉建议提交成功", "id": complaint_id}


@app.put("/api/complaints/{complaint_id}")
def update_complaint(complaint_id: int, payload: ComplaintUpdatePayload) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        "UPDATE complaints SET category = ?, content = ?, status = ?, reply = ? WHERE id = ?",
        (payload.category, payload.content, payload.status, payload.reply, complaint_id),
    )
    conn.commit()
    conn.close()
    return {"message": "投诉建议已处理"}


@app.get("/api/users")
def list_users() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(
        conn.execute(
            """
            SELECT id, username, password, role, display_name, department, status
            FROM users ORDER BY id ASC
            """
        ).fetchall()
    )
    conn.close()
    return rows


@app.post("/api/users")
def create_user(payload: UserPayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users(username, password, role, display_name, department, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payload.username,
            payload.password,
            payload.role,
            payload.display_name,
            payload.department,
            payload.status,
        ),
    )
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"message": "用户新增成功", "id": user_id}


@app.put("/api/users/{user_id}")
def update_user(user_id: int, payload: UserPayload) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        """
        UPDATE users
        SET username = ?, password = ?, role = ?, display_name = ?, department = ?, status = ?
        WHERE id = ?
        """,
        (
            payload.username,
            payload.password,
            payload.role,
            payload.display_name,
            payload.department,
            payload.status,
            user_id,
        ),
    )
    conn.commit()
    conn.close()
    return {"message": "用户更新成功"}


@app.get("/api/roles")
def list_roles() -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(conn.execute("SELECT * FROM roles ORDER BY id ASC").fetchall())
    conn.close()
    return rows


@app.post("/api/roles")
def create_role(payload: RolePayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO roles(name, code, permissions, status) VALUES (?, ?, ?, ?)",
        (payload.name, payload.code, payload.permissions, payload.status),
    )
    conn.commit()
    role_id = cursor.lastrowid
    conn.close()
    return {"message": "角色新增成功", "id": role_id}


@app.put("/api/roles/{role_id}")
def update_role(role_id: int, payload: RolePayload) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        """
        UPDATE roles
        SET name = ?, code = ?, permissions = ?, status = ?
        WHERE id = ?
        """,
        (payload.name, payload.code, payload.permissions, payload.status, role_id),
    )
    conn.commit()
    conn.close()
    return {"message": "角色更新成功"}


@app.get("/api/security/overview")
def security_overview() -> dict[str, Any]:
    conn = get_conn()
    items = [
        {"name": "登录认证", "status": "存在缺陷", "detail": "密码明文存储，登录查询拼接 SQL。"},
        {"name": "接口鉴权", "status": "存在缺陷", "detail": "后台数据接口未统一校验身份。"},
        {"name": "跨域策略", "status": "存在缺陷", "detail": "允许任意来源访问接口。"},
        {"name": "数据暴露", "status": "存在缺陷", "detail": "用户列表直接返回密码字段。"},
        {"name": "日志审计", "status": "部分实现", "detail": "已记录日志，但未限制未授权访问。"},
    ]
    logs = dict_rows(
        conn.execute(
            """
            SELECT id, log_type, username, action, ip_address, risk_level, detail, created_at
            FROM security_logs ORDER BY id DESC
            """
        ).fetchall()
    )
    conn.close()
    return {"version": "with-vuln", "level": "高风险", "items": items, "logs": logs}
