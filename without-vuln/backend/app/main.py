from __future__ import annotations

import hashlib
import hmac
import secrets
import sqlite3
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "uniman_secure.db"
UPLOAD_DIR = BASE_DIR / "uploads"
PASSWORD_ITERATIONS = 120000
TOKEN_SCHEME = HTTPBearer(auto_error=False)
TOKENS: dict[str, dict[str, Any]] = {}

app = FastAPI(
    title="UniMan API",
    description="高校后勤服务管理系统",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


class LoginPayload(BaseModel):
    username: str
    password: str


class ProfilePayload(BaseModel):
    name: str
    phone: str
    email: str
    department: str


class PasswordPayload(BaseModel):
    current_password: str
    next_password: str


class RepairPayload(BaseModel):
    reporter_id: int
    reporter_name: str
    repair_type: str
    campus: str
    building: str
    room: str
    description: str
    contact_phone: str
    image_url: str = ""
    status: str = "待受理"
    assignee_id: int | None = None
    assignee_name: str = "未分配"
    result: str = ""
    cancel_reason: str = ""
    cancel_source: str = ""


class ComplaintPayload(BaseModel):
    user_id: int
    user_name: str
    type: str
    title: str
    content: str
    image_url: str = ""
    status: str = "待处理"
    reply: str = ""


class NoticePayload(BaseModel):
    title: str
    content: str
    status: str
    publish_scope: str
    publisher_id: int
    publisher_name: str


class NoticeReadPayload(BaseModel):
    user_id: int


class UserPayload(BaseModel):
    username: str
    password: str
    name: str
    role: str
    phone: str
    email: str
    department: str
    status: str = "启用"


class RolePayload(BaseModel):
    name: str
    code: str
    description: str
    permissions: str
    status: str = "启用"


class BaseDataPayload(BaseModel):
    data_type: str
    name: str
    parent_name: str = ""
    status: str = "启用"
    extra: str = ""


class EvaluationPayload(BaseModel):
    repair_id: int
    user_id: int
    user_name: str
    assignee_id: int | None = None
    assignee_name: str = ""
    score: int
    comment: str


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def column_exists(cursor: sqlite3.Cursor, table: str, column: str) -> bool:
    info = cursor.execute(f"PRAGMA table_info({table})").fetchall()
    return any(row[1] == column for row in info)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), PASSWORD_ITERATIONS)
    return f"pbkdf2_sha256${PASSWORD_ITERATIONS}${salt}${digest.hex()}"


def verify_password(password: str, stored_password: str) -> bool:
    if stored_password.startswith("pbkdf2_sha256$"):
        _, iterations_text, salt, digest = stored_password.split("$", 3)
        check = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt.encode("utf-8"),
            int(iterations_text),
        ).hex()
        return hmac.compare_digest(check, digest)
    return hmac.compare_digest(password, stored_password)


def issue_token(user: dict[str, Any]) -> str:
    token = secrets.token_urlsafe(32)
    TOKENS[token] = user
    return token


def current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(TOKEN_SCHEME),
) -> dict[str, Any]:
    if not credentials or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已失效")
    session = TOKENS.get(credentials.credentials)
    if not session:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录或登录已失效")
    return session


def require_roles(*roles: str):
    def dependency(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
        if session["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该资源")
        return session

    return dependency


def seed_if_empty(cursor: sqlite3.Cursor, table: str, sql: str, rows: list[tuple[Any, ...]]) -> None:
    if cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0:
        cursor.executemany(sql, rows)


def next_order_no(cursor: sqlite3.Cursor) -> str:
    current = cursor.execute("SELECT COUNT(*) FROM repairs").fetchone()[0] + 1
    return f"BX{current:06d}"


def add_log(cursor: sqlite3.Cursor, username: str, action: str, detail: str) -> None:
    cursor.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        ("操作日志", username, action, "127.0.0.1", "低", detail),
    )


def user_notice_scopes(role: str) -> tuple[str, ...]:
    if role == "普通用户":
        return ("全校", "学生")
    if role == "后勤人员":
        return ("全校", "后勤人员")
    if role == "系统管理员":
        return ("全校", "管理员")
    return ("全校",)


def list_visible_notices(cursor: sqlite3.Cursor, role: str, user_id: int) -> list[dict[str, Any]]:
    scopes = user_notice_scopes(role)
    placeholders = ",".join("?" for _ in scopes)
    rows = dict_rows(
        cursor.execute(
            f"""
            SELECT n.id, n.title, n.content, n.publish_scope, n.publisher_id, n.publisher_name,
                   n.published_at, n.created_at,
                   CASE WHEN nr.id IS NULL THEN '未读' ELSE '已读' END AS read_status,
                   nr.read_at
            FROM notices n
            LEFT JOIN notice_reads nr ON nr.notice_id = n.id AND nr.user_id = ?
            WHERE n.status = '已发布' AND n.publish_scope IN ({placeholders})
            ORDER BY n.id DESC
            """,
            (user_id, *scopes),
        ).fetchall()
    )
    return rows


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
            name TEXT NOT NULL,
            role TEXT NOT NULL,
            phone TEXT NOT NULL,
            email TEXT NOT NULL,
            department TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '启用',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS roles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            code TEXT NOT NULL,
            description TEXT NOT NULL,
            permissions TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '启用'
        );

        CREATE TABLE IF NOT EXISTS repairs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_no TEXT NOT NULL,
            reporter_id INTEGER NOT NULL,
            reporter_name TEXT NOT NULL,
            repair_type TEXT NOT NULL,
            campus TEXT NOT NULL,
            building TEXT NOT NULL,
            room TEXT NOT NULL,
            description TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            image_url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '待受理',
            assignee_id INTEGER,
            assignee_name TEXT NOT NULL DEFAULT '未分配',
            result TEXT NOT NULL DEFAULT '',
            cancel_reason TEXT NOT NULL DEFAULT '',
            cancel_source TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            type TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '待处理',
            reply TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            replied_at TEXT
        );

        CREATE TABLE IF NOT EXISTS notices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '草稿',
            publish_scope TEXT NOT NULL,
            publisher_id INTEGER NOT NULL,
            publisher_name TEXT NOT NULL,
            published_at TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS notice_reads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            notice_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            read_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(notice_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS base_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_type TEXT NOT NULL,
            name TEXT NOT NULL,
            parent_name TEXT NOT NULL DEFAULT '',
            status TEXT NOT NULL DEFAULT '启用',
            extra TEXT NOT NULL DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repair_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            user_name TEXT NOT NULL,
            assignee_id INTEGER,
            assignee_name TEXT NOT NULL DEFAULT '',
            score INTEGER NOT NULL,
            comment TEXT NOT NULL,
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

    if not column_exists(cursor, "repairs", "cancel_reason"):
        cursor.execute("ALTER TABLE repairs ADD COLUMN cancel_reason TEXT NOT NULL DEFAULT ''")
    if not column_exists(cursor, "repairs", "cancel_source"):
        cursor.execute("ALTER TABLE repairs ADD COLUMN cancel_source TEXT NOT NULL DEFAULT ''")

    legacy_users = cursor.execute("SELECT id, password FROM users").fetchall()
    for user in legacy_users:
        if not str(user["password"]).startswith("pbkdf2_sha256$"):
            cursor.execute(
                "UPDATE users SET password = ? WHERE id = ?",
                (hash_password(user["password"]), user["id"]),
            )

    seed_if_empty(
        cursor,
        "roles",
        "INSERT INTO roles(name, code, description, permissions, status) VALUES (?, ?, ?, ?, ?)",
        [
            ("普通用户", "user", "师生服务申请角色", "报修提交,投诉建议,公告查看,评价服务", "启用"),
            ("后勤人员", "worker", "后勤工单处理角色", "工单处理,结果反馈,公告查看", "启用"),
            ("系统管理员", "admin", "平台业务管理角色", "用户管理,角色管理,公告管理,工单管理,基础数据", "启用"),
        ],
    )

    seed_if_empty(
        cursor,
        "users",
        """
        INSERT INTO users(username, password, name, role, phone, email, department, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("admin", hash_password("admin123"), "王老师", "系统管理员", "13800000000", "admin@uniman.local", "信息中心", "启用"),
            ("logis01", hash_password("123456"), "李师傅", "后勤人员", "13800000011", "logis01@uniman.local", "维修中心", "启用"),
            ("logis02", hash_password("123456"), "周师傅", "后勤人员", "13800000012", "logis02@uniman.local", "后勤保障处", "启用"),
            ("user01", hash_password("123456"), "张同学", "普通用户", "13800000021", "user01@uniman.local", "计算机学院", "启用"),
            ("user02", hash_password("123456"), "李同学", "普通用户", "13800000022", "user02@uniman.local", "外国语学院", "启用"),
        ],
    )

    seed_if_empty(
        cursor,
        "base_data",
        "INSERT INTO base_data(data_type, name, parent_name, status, extra) VALUES (?, ?, ?, ?, ?)",
        [
            ("repair_type", "水电维修", "", "启用", ""),
            ("repair_type", "门窗维修", "", "启用", ""),
            ("repair_type", "网络设备", "", "启用", ""),
            ("repair_type", "空调设备", "", "启用", ""),
            ("repair_type", "公共设施", "", "启用", ""),
            ("complaint_type", "食堂服务", "", "启用", ""),
            ("complaint_type", "宿舍管理", "", "启用", ""),
            ("complaint_type", "维修服务", "", "启用", ""),
            ("complaint_type", "校园环境", "", "启用", ""),
            ("campus", "东校区", "", "启用", ""),
            ("campus", "西校区", "", "启用", ""),
            ("building", "1号宿舍楼", "东校区", "启用", ""),
            ("building", "3号教学楼", "东校区", "启用", ""),
            ("building", "图书馆", "西校区", "启用", ""),
            ("department", "信息中心", "", "启用", ""),
            ("department", "维修中心", "", "启用", ""),
            ("department", "后勤保障处", "", "启用", ""),
        ],
    )

    if cursor.execute("SELECT COUNT(*) FROM repairs").fetchone()[0] == 0:
        workers = dict_rows(cursor.execute("SELECT id, name FROM users WHERE role = '后勤人员'").fetchall())
        cursor.executemany(
            """
            INSERT INTO repairs(order_no, reporter_id, reporter_name, repair_type, campus, building, room,
            description, contact_phone, image_url, status, assignee_id, assignee_name, result)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("BX000001", 4, "张同学", "空调设备", "东校区", "1号宿舍楼", "402", "空调制冷效果差，夜间噪音较大。", "13800000021", "", "处理中", workers[0]["id"], workers[0]["name"], "已上门检测，等待更换零件。"),
                ("BX000002", 5, "李同学", "公共设施", "西校区", "图书馆", "二层", "饮水机无法加热。", "13800000022", "", "待受理", None, "未分配", ""),
                ("BX000003", 4, "张同学", "网络设备", "东校区", "3号教学楼", "203", "投影无法连接校园网。", "13800000021", "", "待确认", workers[1]["id"], workers[1]["name"], "线路已恢复，请确认。"),
            ],
        )

    seed_if_empty(
        cursor,
        "complaints",
        """
        INSERT INTO complaints(user_id, user_name, type, title, content, image_url, status, reply, replied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (4, "张同学", "食堂服务", "晚高峰排队较长", "建议在晚餐高峰时段增加窗口开放数量。", "", "处理中", "已反馈食堂运营组优化。", "2026-04-17 09:00:00"),
            (5, "李同学", "宿舍管理", "洗衣房卫生需要改善", "洗衣房地面积水较多，希望加强保洁频次。", "", "待处理", "", None),
        ],
    )

    seed_if_empty(
        cursor,
        "notices",
        """
        INSERT INTO notices(title, content, status, publish_scope, publisher_id, publisher_name, published_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            ("北校区停水通知", "因主管网检修，4月18日 09:00-12:00 北校区部分楼栋暂停供水。", "已发布", "全校", 1, "王老师", "2026-04-17 08:00:00"),
            ("空调检修安排", "本周末开展宿舍空调集中巡检，请同学提前整理阳台区域。", "已发布", "学生", 1, "王老师", "2026-04-16 14:00:00"),
            ("假期值班提醒", "节假日期间维修热线保持畅通，值班表已同步到各部门。", "草稿", "后勤人员", 1, "王老师", None),
        ],
    )

    seed_if_empty(
        cursor,
        "evaluations",
        """
        INSERT INTO evaluations(repair_id, user_id, user_name, assignee_id, assignee_name, score, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [(1, 4, "张同学", 2, "李师傅", 5, "响应及时，处理态度很好。")],
    )

    seed_if_empty(
        cursor,
        "security_logs",
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            ("登录日志", "guest", "登录失败", "127.0.0.1", "中", "当前版本保留 SQL 注入与明文密码问题。"),
            ("异常请求", "guest", "访问用户列表", "10.10.2.88", "高", "未鉴权访问后台数据接口。"),
        ],
    )

    conn.commit()
    conn.close()


def summary_metrics(cursor: sqlite3.Cursor, role: str, user_id: int | None) -> dict[str, Any]:
    if role == "普通用户" and user_id:
        visible_notices = list_visible_notices(cursor, role, user_id)
        my_repairs = cursor.execute("SELECT COUNT(*) FROM repairs WHERE reporter_id = ?", (user_id,)).fetchone()[0]
        completed_repairs = cursor.execute(
            "SELECT COUNT(*) FROM repairs WHERE reporter_id = ? AND status IN ('待确认', '已完成')",
            (user_id,),
        ).fetchone()[0]
        complaints = cursor.execute("SELECT COUNT(*) FROM complaints WHERE user_id = ?", (user_id,)).fetchone()[0]
        notices = len(visible_notices)
        recent_repairs = dict_rows(
            cursor.execute(
                """
                SELECT id, order_no, repair_type, campus, building, room, status, assignee_name, created_at
                FROM repairs WHERE reporter_id = ? ORDER BY id DESC LIMIT 5
                """,
                (user_id,),
            ).fetchall()
        )
        recent_notices = visible_notices[:4]
        recent_complaints = dict_rows(
            cursor.execute(
                """
                SELECT id, type, title, status, created_at, reply
                FROM complaints WHERE user_id = ? ORDER BY id DESC LIMIT 4
                """,
                (user_id,),
            ).fetchall()
        )
        return {
            "mode": "user",
            "metrics": [
                {"label": "我的报修", "value": my_repairs},
                {"label": "待确认/已完成", "value": completed_repairs},
                {"label": "我的投诉建议", "value": complaints},
                {"label": "可查看公告", "value": notices},
            ],
            "recent_repairs": recent_repairs,
            "recent_notices": recent_notices,
            "recent_complaints": recent_complaints,
        }

    repairs_total = cursor.execute("SELECT COUNT(*) FROM repairs").fetchone()[0]
    pending_repairs = cursor.execute(
        "SELECT COUNT(*) FROM repairs WHERE status IN ('待受理', '已分派', '处理中', '待确认')"
    ).fetchone()[0]
    complaints_total = cursor.execute("SELECT COUNT(*) FROM complaints").fetchone()[0]
    notice_total = cursor.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    user_total = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    base_total = cursor.execute("SELECT COUNT(*) FROM base_data").fetchone()[0]
    repairs_by_status = dict_rows(
        cursor.execute(
            "SELECT status AS name, COUNT(*) AS value FROM repairs GROUP BY status ORDER BY COUNT(*) DESC"
        ).fetchall()
    )
    complaints_by_status = dict_rows(
        cursor.execute(
            "SELECT status AS name, COUNT(*) AS value FROM complaints GROUP BY status ORDER BY COUNT(*) DESC"
        ).fetchall()
    )
    latest_repairs = dict_rows(
        cursor.execute(
            """
            SELECT id, order_no, reporter_name, repair_type, status, assignee_name, updated_at
            FROM repairs ORDER BY id DESC LIMIT 6
            """
        ).fetchall()
    )
    return {
        "mode": "admin",
        "metrics": [
            {"label": "报修总量", "value": repairs_total},
            {"label": "待处理工单", "value": pending_repairs},
            {"label": "投诉建议", "value": complaints_total},
            {"label": "公告数量", "value": notice_total},
            {"label": "系统用户", "value": user_total},
            {"label": "基础数据", "value": base_total},
        ],
        "charts": {"repairs": repairs_by_status, "complaints": complaints_by_status},
        "latest_repairs": latest_repairs,
    }


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/options")
def get_options(_: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    options = {
        "repair_types": [row["name"] for row in cursor.execute("SELECT name FROM base_data WHERE data_type = 'repair_type' AND status = '启用'").fetchall()],
        "complaint_types": [row["name"] for row in cursor.execute("SELECT name FROM base_data WHERE data_type = 'complaint_type' AND status = '启用'").fetchall()],
        "campuses": [row["name"] for row in cursor.execute("SELECT name FROM base_data WHERE data_type = 'campus' AND status = '启用'").fetchall()],
        "buildings": dict_rows(cursor.execute("SELECT name, parent_name FROM base_data WHERE data_type = 'building' AND status = '启用'").fetchall()),
        "departments": [row["name"] for row in cursor.execute("SELECT name FROM base_data WHERE data_type = 'department' AND status = '启用'").fetchall()],
        "workers": dict_rows(cursor.execute("SELECT id, name FROM users WHERE role = '后勤人员' AND status = '启用' ORDER BY id ASC").fetchall()),
        "roles": [row["name"] for row in cursor.execute("SELECT name FROM roles WHERE status = '启用' ORDER BY id ASC").fetchall()],
        "repair_statuses": ["待受理", "已分派", "处理中", "待确认", "已完成", "已取消"],
        "complaint_statuses": ["待处理", "处理中", "已回复", "已关闭", "已撤销"],
        "notice_statuses": ["草稿", "已发布", "已下线"],
        "notice_scopes": ["全校", "学生", "后勤人员", "管理员"],
    }
    conn.close()
    return options


@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    _: dict[str, Any] = Depends(current_session),
) -> dict[str, str]:
    suffix = (Path(file.filename or "").suffix or "").lower()
    allowed_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
    if suffix not in allowed_suffixes:
        raise HTTPException(status_code=400, detail="仅支持 png/jpg/jpeg/webp 图片")
    content = await file.read()
    if len(content) > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")
    target_name = f"{uuid.uuid4().hex}{suffix}"
    target = UPLOAD_DIR / target_name
    target.write_bytes(content)
    return {"message": "上传成功", "url": f"/uploads/{target_name}"}


@app.post("/api/auth/login")
def login(payload: LoginPayload) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    user = cursor.execute(
        """
        SELECT id, username, password, name, role, phone, email, department, status
        FROM users WHERE username = ?
        """,
        (payload.username,),
    ).fetchone()
    is_valid = bool(user and verify_password(payload.password, user["password"]))
    cursor.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            "登录日志",
            payload.username,
            "登录成功" if is_valid else "登录失败",
            "127.0.0.1",
            "低" if is_valid else "中",
            "无漏洞版本已启用参数化查询、密码哈希与服务端鉴权。",
        ),
    )
    conn.commit()
    conn.close()
    if not is_valid:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    safe_user = {
        "id": user["id"],
        "username": user["username"],
        "name": user["name"],
        "role": user["role"],
        "phone": user["phone"],
        "email": user["email"],
        "department": user["department"],
        "status": user["status"],
    }
    return {"message": "登录成功", "token": issue_token(safe_user), "user": safe_user}


@app.get("/api/dashboard/summary")
def dashboard_summary(session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    conn = get_conn()
    data = summary_metrics(conn.cursor(), session["role"], session["id"])
    conn.close()
    return data


@app.put("/api/profile/{user_id}")
def update_profile(user_id: int, payload: ProfilePayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, str]:
    if session["id"] != user_id and session["role"] != "系统管理员":
        raise HTTPException(status_code=403, detail="无权修改该用户信息")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE users
        SET name = ?, phone = ?, email = ?, department = ?
        WHERE id = ?
        """,
        (payload.name, payload.phone, payload.email, payload.department, user_id),
    )
    add_log(cursor, payload.name, "更新个人信息", f"用户 #{user_id} 修改了个人资料。")
    conn.commit()
    conn.close()
    return {"message": "个人信息已更新"}


@app.put("/api/profile/{user_id}/password")
def update_password(user_id: int, payload: PasswordPayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, str]:
    if session["id"] != user_id and session["role"] != "系统管理员":
        raise HTTPException(status_code=403, detail="无权修改该用户密码")
    conn = get_conn()
    cursor = conn.cursor()
    row = cursor.execute("SELECT password, name FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    if session["role"] != "系统管理员" and not verify_password(payload.current_password, row["password"]):
        conn.close()
        raise HTTPException(status_code=400, detail="当前密码不正确")
    cursor.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (hash_password(payload.next_password), user_id),
    )
    add_log(cursor, row["name"], "修改密码", f"用户 #{user_id} 修改了登录密码。")
    conn.commit()
    conn.close()
    return {"message": "密码已更新"}


@app.get("/api/repairs")
def list_repairs(session: dict[str, Any] = Depends(current_session)) -> list[dict[str, Any]]:
    conn = get_conn()
    cursor = conn.cursor()
    if session["role"] == "普通用户":
        rows = dict_rows(
            cursor.execute(
                """
                SELECT id, order_no, reporter_id, reporter_name, repair_type, campus, building, room,
                       description, contact_phone, image_url, status, assignee_id, assignee_name,
                       result, cancel_reason, cancel_source, created_at, updated_at
                FROM repairs WHERE reporter_id = ? ORDER BY id DESC
                """,
                (session["id"],),
            ).fetchall()
        )
    elif session["role"] == "后勤人员":
        rows = dict_rows(
            cursor.execute(
                """
                SELECT id, order_no, reporter_id, reporter_name, repair_type, campus, building, room,
                       description, contact_phone, image_url, status, assignee_id, assignee_name,
                       result, cancel_reason, cancel_source, created_at, updated_at
                FROM repairs WHERE assignee_id = ? ORDER BY id DESC
                """,
                (session["id"],),
            ).fetchall()
        )
    else:
        rows = dict_rows(
            cursor.execute(
            """
            SELECT id, order_no, reporter_id, reporter_name, repair_type, campus, building, room,
                   description, contact_phone, image_url, status, assignee_id, assignee_name,
                   result, cancel_reason, cancel_source, created_at, updated_at
            FROM repairs ORDER BY id DESC
            """
            ).fetchall()
        )
    conn.close()
    return rows


@app.post("/api/repairs")
def create_repair(payload: RepairPayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    if session["role"] not in {"普通用户", "系统管理员"}:
        raise HTTPException(status_code=403, detail="无权创建报修工单")
    conn = get_conn()
    cursor = conn.cursor()
    reporter_id = session["id"] if session["role"] == "普通用户" else payload.reporter_id
    reporter = cursor.execute(
        "SELECT id, name, phone, role FROM users WHERE id = ? AND status = '启用'",
        (reporter_id,),
    ).fetchone()
    if not reporter or reporter["role"] != "普通用户":
        conn.close()
        raise HTTPException(status_code=400, detail="报修人信息无效")
    assignee_id = payload.assignee_id if session["role"] == "系统管理员" else None
    assignee_name = "未分配"
    if assignee_id:
        assignee = cursor.execute(
            "SELECT id, name FROM users WHERE id = ? AND role = '后勤人员' AND status = '启用'",
            (assignee_id,),
        ).fetchone()
        if not assignee:
            conn.close()
            raise HTTPException(status_code=400, detail="处理人信息无效")
        assignee_name = assignee["name"]
    order_no = next_order_no(cursor)
    cursor.execute(
        """
        INSERT INTO repairs(order_no, reporter_id, reporter_name, repair_type, campus, building, room,
        description, contact_phone, image_url, status, assignee_id, assignee_name, result, cancel_reason, cancel_source, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            order_no,
            reporter["id"],
            reporter["name"],
            payload.repair_type,
            payload.campus,
            payload.building,
            payload.room,
            payload.description,
            payload.contact_phone or reporter["phone"],
            payload.image_url,
            "已分派" if assignee_id else "待受理",
            assignee_id,
            assignee_name,
            "",
            "",
            "",
        ),
    )
    add_log(cursor, session["name"], "新增报修", f"提交工单 {order_no}。")
    conn.commit()
    repair_id = cursor.lastrowid
    conn.close()
    return {"message": "报修提交成功", "id": repair_id, "order_no": order_no}


@app.put("/api/repairs/{repair_id}")
def update_repair(repair_id: int, payload: RepairPayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    current = cursor.execute("SELECT * FROM repairs WHERE id = ?", (repair_id,)).fetchone()
    if not current:
        conn.close()
        raise HTTPException(status_code=404, detail="工单不存在")

    current_data = dict(current)
    next_data = current_data.copy()

    if session["role"] == "普通用户":
        if current["reporter_id"] != session["id"]:
            conn.close()
            raise HTTPException(status_code=403, detail="无权修改该工单")
        if payload.status == "已取消":
            if current["status"] not in {"待受理", "已分派"}:
                conn.close()
                raise HTTPException(status_code=400, detail="当前状态不可撤回")
            next_data["status"] = "已取消"
            next_data["cancel_reason"] = (payload.cancel_reason or "").strip()
            next_data["cancel_source"] = "user"
        else:
            if current["status"] != "待受理":
                conn.close()
                raise HTTPException(status_code=400, detail="当前状态不可编辑")
            next_data.update(
                {
                    "repair_type": payload.repair_type,
                    "campus": payload.campus,
                    "building": payload.building,
                    "room": payload.room,
                    "description": payload.description,
                    "contact_phone": payload.contact_phone,
                    "image_url": payload.image_url,
                }
            )
    elif session["role"] == "后勤人员":
        if current["assignee_id"] != session["id"]:
            conn.close()
            raise HTTPException(status_code=403, detail="无权处理该工单")
        if payload.status == "处理中" and current["status"] == "已分派":
            next_data["status"] = "处理中"
        elif payload.status == "待确认" and current["status"] == "处理中":
            next_data["status"] = "待确认"
            next_data["result"] = payload.result.strip()
        elif payload.status == "待受理" and current["status"] in {"已分派", "处理中"}:
            next_data["status"] = "待受理"
            next_data["assignee_id"] = None
            next_data["assignee_name"] = "未分配"
            next_data["cancel_reason"] = (payload.cancel_reason or "").strip()
            next_data["cancel_source"] = "worker"
            next_data["result"] = ""
        else:
            conn.close()
            raise HTTPException(status_code=400, detail="不支持的工单状态流转")
    else:
        next_data.update(
            {
                "repair_type": payload.repair_type,
                "campus": payload.campus,
                "building": payload.building,
                "room": payload.room,
                "description": payload.description,
                "contact_phone": payload.contact_phone,
                "image_url": payload.image_url,
                "status": payload.status,
                "result": payload.result,
                "cancel_reason": payload.cancel_reason,
                "cancel_source": payload.cancel_source,
            }
        )
        reporter = cursor.execute(
            "SELECT id, name, phone, role FROM users WHERE id = ? AND status = '启用'",
            (payload.reporter_id,),
        ).fetchone()
        if not reporter or reporter["role"] != "普通用户":
            conn.close()
            raise HTTPException(status_code=400, detail="报修人信息无效")
        next_data["reporter_id"] = reporter["id"]
        next_data["reporter_name"] = reporter["name"]
        if payload.assignee_id:
            assignee = cursor.execute(
                "SELECT id, name FROM users WHERE id = ? AND role = '后勤人员' AND status = '启用'",
                (payload.assignee_id,),
            ).fetchone()
            if not assignee:
                conn.close()
                raise HTTPException(status_code=400, detail="处理人信息无效")
            next_data["assignee_id"] = assignee["id"]
            next_data["assignee_name"] = assignee["name"]
        else:
            next_data["assignee_id"] = None
            next_data["assignee_name"] = "未分配"

    cursor.execute(
        """
        UPDATE repairs
        SET reporter_id = ?, reporter_name = ?, repair_type = ?, campus = ?, building = ?, room = ?,
            description = ?, contact_phone = ?, image_url = ?, status = ?, assignee_id = ?,
            assignee_name = ?, result = ?, cancel_reason = ?, cancel_source = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (
            next_data["reporter_id"],
            next_data["reporter_name"],
            next_data["repair_type"],
            next_data["campus"],
            next_data["building"],
            next_data["room"],
            next_data["description"],
            next_data["contact_phone"],
            next_data["image_url"],
            next_data["status"],
            next_data["assignee_id"],
            next_data["assignee_name"],
            next_data["result"],
            next_data["cancel_reason"],
            next_data["cancel_source"],
            repair_id,
        ),
    )
    add_log(cursor, session["name"], "更新报修", f"更新工单 #{repair_id}。")
    conn.commit()
    conn.close()
    return {"message": "报修工单已更新"}


@app.delete("/api/repairs/{repair_id}")
def delete_repair(repair_id: int, _: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    conn.execute("DELETE FROM repairs WHERE id = ?", (repair_id,))
    conn.commit()
    conn.close()
    return {"message": "报修工单已删除"}


@app.get("/api/complaints")
def list_complaints(session: dict[str, Any] = Depends(current_session)) -> list[dict[str, Any]]:
    conn = get_conn()
    cursor = conn.cursor()
    if session["role"] == "普通用户":
        rows = dict_rows(
            cursor.execute(
                """
                SELECT id, user_id, user_name, type, title, content, image_url, status, reply, created_at, replied_at
                FROM complaints WHERE user_id = ? ORDER BY id DESC
                """,
                (session["id"],),
            ).fetchall()
        )
    elif session["role"] == "系统管理员":
        rows = dict_rows(
            cursor.execute(
            """
            SELECT id, user_id, user_name, type, title, content, image_url, status, reply, created_at, replied_at
            FROM complaints ORDER BY id DESC
            """
            ).fetchall()
        )
    else:
        conn.close()
        raise HTTPException(status_code=403, detail="后勤人员无权查看投诉建议")
    conn.close()
    return rows


@app.post("/api/complaints")
def create_complaint(payload: ComplaintPayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    if session["role"] != "普通用户":
        raise HTTPException(status_code=403, detail="仅普通用户可提交投诉建议")
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO complaints(user_id, user_name, type, title, content, image_url, status, reply, replied_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            session["id"],
            session["name"],
            payload.type,
            payload.title,
            payload.content,
            payload.image_url,
            "待处理",
            "",
            None,
        ),
    )
    add_log(cursor, session["name"], "新增投诉建议", f"新增投诉建议《{payload.title}》。")
    conn.commit()
    complaint_id = cursor.lastrowid
    conn.close()
    return {"message": "投诉建议提交成功", "id": complaint_id}


@app.put("/api/complaints/{complaint_id}")
def update_complaint(complaint_id: int, payload: ComplaintPayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    current = cursor.execute("SELECT * FROM complaints WHERE id = ?", (complaint_id,)).fetchone()
    if not current:
        conn.close()
        raise HTTPException(status_code=404, detail="投诉建议不存在")
    if session["role"] == "普通用户":
        if current["user_id"] != session["id"]:
            conn.close()
            raise HTTPException(status_code=403, detail="无权修改该投诉建议")
        if payload.status == "已撤销":
            if current["status"] != "待处理":
                conn.close()
                raise HTTPException(status_code=400, detail="当前状态不可撤销")
            cursor.execute(
                """
                UPDATE complaints
                SET type = ?, title = ?, content = ?, image_url = ?, status = ?, reply = ''
                WHERE id = ?
                """,
                (current["type"], current["title"], current["content"], current["image_url"], "已撤销", complaint_id),
            )
        else:
            if current["status"] != "待处理":
                conn.close()
                raise HTTPException(status_code=400, detail="当前状态不可编辑")
            cursor.execute(
                """
                UPDATE complaints
                SET type = ?, title = ?, content = ?, image_url = ?
                WHERE id = ?
                """,
                (payload.type, payload.title, payload.content, payload.image_url, complaint_id),
            )
    elif session["role"] == "系统管理员":
        cursor.execute(
            """
            UPDATE complaints
            SET type = ?, title = ?, content = ?, image_url = ?, status = ?, reply = ?,
                replied_at = CASE WHEN ? = '' THEN replied_at ELSE CURRENT_TIMESTAMP END
            WHERE id = ?
            """,
            (
                payload.type,
                payload.title,
                payload.content,
                payload.image_url,
                payload.status,
                payload.reply,
                payload.reply,
                complaint_id,
            ),
        )
    else:
        conn.close()
        raise HTTPException(status_code=403, detail="后勤人员无权处理投诉建议")
    add_log(cursor, session["name"], "更新投诉建议", f"更新投诉建议 #{complaint_id}。")
    conn.commit()
    conn.close()
    return {"message": "投诉建议已更新"}


@app.delete("/api/complaints/{complaint_id}")
def delete_complaint(complaint_id: int, _: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    conn.execute("DELETE FROM complaints WHERE id = ?", (complaint_id,))
    conn.commit()
    conn.close()
    return {"message": "投诉建议已删除"}


@app.get("/api/notices")
def list_notices(session: dict[str, Any] = Depends(current_session)) -> list[dict[str, Any]]:
    conn = get_conn()
    cursor = conn.cursor()
    if session["role"] == "系统管理员":
        rows = dict_rows(
            cursor.execute(
                """
                SELECT id, title, content, status, publish_scope, publisher_id, publisher_name, published_at, created_at
                FROM notices ORDER BY id DESC
                """
            ).fetchall()
        )
    else:
        rows = list_visible_notices(cursor, session["role"], session["id"])
    conn.close()
    return rows


@app.post("/api/notices/{notice_id}/read")
def mark_notice_read(
    notice_id: int,
    _: NoticeReadPayload,
    session: dict[str, Any] = Depends(current_session),
) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    notice = cursor.execute("SELECT id FROM notices WHERE id = ?", (notice_id,)).fetchone()
    if not notice:
        conn.close()
        raise HTTPException(status_code=404, detail="公告不存在")
    cursor.execute(
        """
        INSERT OR IGNORE INTO notice_reads(notice_id, user_id)
        VALUES (?, ?)
        """,
        (notice_id, session["id"]),
    )
    conn.commit()
    conn.close()
    return {"message": "公告已标记为已读"}


@app.post("/api/notices")
def create_notice(payload: NoticePayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO notices(title, content, status, publish_scope, publisher_id, publisher_name, published_at)
        VALUES (?, ?, ?, ?, ?, ?, CASE WHEN ? = '已发布' THEN CURRENT_TIMESTAMP ELSE NULL END)
        """,
        (
            payload.title,
            payload.content,
            payload.status,
            payload.publish_scope,
            session["id"],
            session["name"],
            payload.status,
        ),
    )
    add_log(cursor, session["name"], "新增公告", f"发布公告《{payload.title}》。")
    conn.commit()
    notice_id = cursor.lastrowid
    conn.close()
    return {"message": "公告已保存", "id": notice_id}


@app.put("/api/notices/{notice_id}")
def update_notice(notice_id: int, payload: NoticePayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE notices
        SET title = ?, content = ?, status = ?, publish_scope = ?, publisher_id = ?, publisher_name = ?,
            published_at = CASE WHEN ? = '已发布' THEN COALESCE(published_at, CURRENT_TIMESTAMP) ELSE published_at END
        WHERE id = ?
        """,
        (
            payload.title,
            payload.content,
            payload.status,
            payload.publish_scope,
            session["id"],
            session["name"],
            payload.status,
            notice_id,
        ),
    )
    add_log(cursor, session["name"], "更新公告", f"更新公告 #{notice_id}。")
    conn.commit()
    conn.close()
    return {"message": "公告已更新"}


@app.delete("/api/notices/{notice_id}")
def delete_notice(notice_id: int, _: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    conn.execute("DELETE FROM notices WHERE id = ?", (notice_id,))
    conn.commit()
    conn.close()
    return {"message": "公告已删除"}


@app.get("/api/users")
def list_users(_: dict[str, Any] = Depends(require_roles("系统管理员"))) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(
        conn.execute(
            """
            SELECT id, username, name, role, phone, email, department, status, created_at
            FROM users ORDER BY id ASC
            """
        ).fetchall()
    )
    conn.close()
    return rows


@app.post("/api/users")
def create_user(payload: UserPayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users(username, password, name, role, phone, email, department, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.username,
            hash_password(payload.password or "123456"),
            payload.name,
            payload.role,
            payload.phone,
            payload.email,
            payload.department,
            payload.status,
        ),
    )
    add_log(cursor, session["name"], "新增用户", f"新增账号 {payload.username}。")
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"message": "用户新增成功", "id": user_id}


@app.put("/api/users/{user_id}")
def update_user(user_id: int, payload: UserPayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    existing = cursor.execute("SELECT password FROM users WHERE id = ?", (user_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")
    cursor.execute(
        """
        UPDATE users
        SET username = ?, password = ?, name = ?, role = ?, phone = ?, email = ?, department = ?, status = ?
        WHERE id = ?
        """,
        (
            payload.username,
            hash_password(payload.password) if payload.password else existing["password"],
            payload.name,
            payload.role,
            payload.phone,
            payload.email,
            payload.department,
            payload.status,
            user_id,
        ),
    )
    add_log(cursor, session["name"], "更新用户", f"更新用户 #{user_id}。")
    conn.commit()
    conn.close()
    return {"message": "用户信息已更新"}


@app.delete("/api/users/{user_id}")
def delete_user(user_id: int, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    if user_id == session["id"]:
        conn.close()
        raise HTTPException(status_code=400, detail="不能删除当前登录账号")
    conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return {"message": "用户已删除"}


@app.get("/api/roles")
def list_roles(_: dict[str, Any] = Depends(require_roles("系统管理员"))) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(conn.execute("SELECT * FROM roles ORDER BY id ASC").fetchall())
    conn.close()
    return rows


@app.post("/api/roles")
def create_role(payload: RolePayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO roles(name, code, description, permissions, status)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload.name, payload.code, payload.description, payload.permissions, payload.status),
    )
    add_log(cursor, session["name"], "新增角色", f"新增角色 {payload.code}。")
    conn.commit()
    role_id = cursor.lastrowid
    conn.close()
    return {"message": "角色新增成功", "id": role_id}


@app.put("/api/roles/{role_id}")
def update_role(role_id: int, payload: RolePayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE roles
        SET name = ?, code = ?, description = ?, permissions = ?, status = ?
        WHERE id = ?
        """,
        (payload.name, payload.code, payload.description, payload.permissions, payload.status, role_id),
    )
    add_log(cursor, session["name"], "更新角色", f"更新角色 #{role_id}。")
    conn.commit()
    conn.close()
    return {"message": "角色已更新"}


@app.delete("/api/roles/{role_id}")
def delete_role(role_id: int, _: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    conn.execute("DELETE FROM roles WHERE id = ?", (role_id,))
    conn.commit()
    conn.close()
    return {"message": "角色已删除"}


@app.get("/api/base-data")
def list_base_data(_: dict[str, Any] = Depends(require_roles("系统管理员"))) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(conn.execute("SELECT * FROM base_data ORDER BY id DESC").fetchall())
    conn.close()
    return rows


@app.post("/api/base-data")
def create_base_data(payload: BaseDataPayload, session: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO base_data(data_type, name, parent_name, status, extra)
        VALUES (?, ?, ?, ?, ?)
        """,
        (payload.data_type, payload.name, payload.parent_name, payload.status, payload.extra),
    )
    add_log(cursor, session["name"], "新增基础数据", f"新增 {payload.data_type}：{payload.name}。")
    conn.commit()
    item_id = cursor.lastrowid
    conn.close()
    return {"message": "基础数据新增成功", "id": item_id}


@app.put("/api/base-data/{item_id}")
def update_base_data(
    item_id: int,
    payload: BaseDataPayload,
    session: dict[str, Any] = Depends(require_roles("系统管理员")),
) -> dict[str, str]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE base_data
        SET data_type = ?, name = ?, parent_name = ?, status = ?, extra = ?
        WHERE id = ?
        """,
        (payload.data_type, payload.name, payload.parent_name, payload.status, payload.extra, item_id),
    )
    add_log(cursor, session["name"], "更新基础数据", f"更新基础数据 #{item_id}。")
    conn.commit()
    conn.close()
    return {"message": "基础数据已更新"}


@app.delete("/api/base-data/{item_id}")
def delete_base_data(item_id: int, _: dict[str, Any] = Depends(require_roles("系统管理员"))) -> dict[str, str]:
    conn = get_conn()
    conn.execute("DELETE FROM base_data WHERE id = ?", (item_id,))
    conn.commit()
    conn.close()
    return {"message": "基础数据已删除"}


@app.get("/api/evaluations")
def list_evaluations(session: dict[str, Any] = Depends(current_session)) -> list[dict[str, Any]]:
    conn = get_conn()
    cursor = conn.cursor()
    if session["role"] == "普通用户":
        rows = dict_rows(
            cursor.execute(
                """
                SELECT id, repair_id, user_id, user_name, assignee_id, assignee_name, score, comment, created_at
                FROM evaluations WHERE user_id = ? ORDER BY id DESC
                """,
                (session["id"],),
            ).fetchall()
        )
    elif session["role"] == "系统管理员":
        rows = dict_rows(
            cursor.execute(
            """
            SELECT id, repair_id, user_id, user_name, assignee_id, assignee_name, score, comment, created_at
            FROM evaluations ORDER BY id DESC
            """
            ).fetchall()
        )
    else:
        rows = []
    conn.close()
    return rows


@app.post("/api/evaluations")
def create_evaluation(payload: EvaluationPayload, session: dict[str, Any] = Depends(current_session)) -> dict[str, Any]:
    if session["role"] != "普通用户":
        raise HTTPException(status_code=403, detail="仅普通用户可提交评价")
    conn = get_conn()
    cursor = conn.cursor()
    existing = cursor.execute(
        "SELECT id FROM evaluations WHERE repair_id = ? AND user_id = ?",
        (payload.repair_id, session["id"]),
    ).fetchone()
    if existing:
        conn.close()
        raise HTTPException(status_code=400, detail="该工单已评价")
    repair = cursor.execute(
        """
        SELECT id, reporter_id, assignee_id, assignee_name, status
        FROM repairs WHERE id = ?
        """,
        (payload.repair_id,),
    ).fetchone()
    if not repair or repair["reporter_id"] != session["id"]:
        conn.close()
        raise HTTPException(status_code=403, detail="无权评价该工单")
    if repair["status"] != "已完成":
        conn.close()
        raise HTTPException(status_code=400, detail="仅已完成工单可评价")
    cursor.execute(
        """
        INSERT INTO evaluations(repair_id, user_id, user_name, assignee_id, assignee_name, score, comment)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.repair_id,
            session["id"],
            session["name"],
            repair["assignee_id"],
            repair["assignee_name"],
            payload.score,
            payload.comment,
        ),
    )
    add_log(cursor, session["name"], "提交评价", f"对工单 #{payload.repair_id} 进行了评分。")
    conn.commit()
    evaluation_id = cursor.lastrowid
    conn.close()
    return {"message": "评价提交成功", "id": evaluation_id}
