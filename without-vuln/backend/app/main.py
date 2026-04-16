from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, File, Header, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field


BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "uniman_secure.db"
UPLOAD_DIR = BASE_DIR / "uploads"
TOKEN_SECRET = os.getenv("UNIMAN_TOKEN_SECRET", "uniman-secure-demo-secret")
TOKEN_EXPIRE_SECONDS = 60 * 60 * 8
MAX_UPLOAD_SIZE = 2 * 1024 * 1024
ALLOWED_UPLOAD_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
ALLOWED_UPLOAD_TYPES = {"image/png", "image/jpeg", "image/webp"}

ROLE_ADMIN = "系统管理员"
ROLE_WORKER = "后勤工作人员"
ROLE_STUDENT = "学生"

app = FastAPI(
    title="UniMan Secure API",
    description="高校后勤服务管理系统修复版",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT"],
    allow_headers=["Authorization", "Content-Type"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")


class LoginPayload(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=128)


class RepairPayload(BaseModel):
    location: str = Field(min_length=2, max_length=100)
    repair_type: str = Field(min_length=2, max_length=30)
    description: str = Field(min_length=2, max_length=500)
    contact_phone: str = Field(min_length=6, max_length=20)
    image_url: str = Field(default="", max_length=255)


class RepairAdminUpdatePayload(RepairPayload):
    student_name: str = Field(min_length=2, max_length=30)
    status: str = Field(min_length=2, max_length=20)
    assignee: str = Field(min_length=2, max_length=30)


class RepairStudentUpdatePayload(BaseModel):
    description: str = Field(min_length=2, max_length=500)
    contact_phone: str = Field(min_length=6, max_length=20)
    image_url: str = Field(default="", max_length=255)


class RepairWorkerUpdatePayload(BaseModel):
    status: str


class NoticePayload(BaseModel):
    title: str = Field(min_length=2, max_length=100)
    category: str = Field(min_length=2, max_length=30)
    content: str = Field(min_length=2, max_length=1000)
    publisher: str = Field(min_length=2, max_length=30)
    status: str = Field(min_length=2, max_length=20)


class ComplaintPayload(BaseModel):
    category: str = Field(min_length=2, max_length=30)
    content: str = Field(min_length=2, max_length=500)
    contact_phone: str = Field(min_length=6, max_length=20)


class ComplaintUpdatePayload(BaseModel):
    category: str = Field(min_length=2, max_length=30)
    content: str = Field(min_length=2, max_length=500)
    status: str = Field(min_length=2, max_length=20)
    reply: str = Field(default="", max_length=500)


class UserPayload(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(default="", max_length=128)
    role: str = Field(min_length=2, max_length=20)
    display_name: str = Field(min_length=2, max_length=30)
    department: str = Field(min_length=2, max_length=30)
    status: str = Field(min_length=2, max_length=20)


class RolePayload(BaseModel):
    name: str = Field(min_length=2, max_length=20)
    code: str = Field(min_length=2, max_length=20)
    permissions: str = Field(min_length=2, max_length=255)
    status: str = Field(min_length=2, max_length=20)


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def dict_rows(rows: list[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def now_ts() -> int:
    return int(time.time())


def hash_password(password: str, salt_hex: str | None = None) -> str:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return f"{salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    try:
      salt_hex, digest_hex = stored.split("$", 1)
    except ValueError:
      return False
    expected = hash_password(password, salt_hex).split("$", 1)[1]
    return hmac.compare_digest(expected, digest_hex)


def create_token(user_id: int, role: str) -> str:
    expires = str(now_ts() + TOKEN_EXPIRE_SECONDS)
    payload = f"{user_id}:{role}:{expires}"
    signature = hmac.new(TOKEN_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    return base64.urlsafe_b64encode(f"{payload}:{signature}".encode("utf-8")).decode("utf-8")


def parse_token(token: str) -> tuple[int, str]:
    try:
        raw = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        user_id_str, role, expires_str, signature = raw.split(":", 3)
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效") from exc
    payload = f"{user_id_str}:{role}:{expires_str}"
    expected = hmac.new(TOKEN_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效")
    if int(expires_str) < now_ts():
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录已过期")
    return int(user_id_str), role


def user_public_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"],
        "display_name": row["display_name"],
        "department": row["department"],
        "status": row["status"],
    }


def log_event(conn: sqlite3.Connection, log_type: str, username: str, action: str, risk_level: str, detail: str) -> None:
    conn.execute(
        """
        INSERT INTO security_logs(log_type, username, action, ip_address, risk_level, detail)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (log_type, username, action, "127.0.0.1", risk_level, detail),
    )


def get_current_user(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="请先登录")
    token = authorization.split(" ", 1)[1]
    user_id, role = parse_token(token)
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE id = ? AND status = '启用'", (user_id,)).fetchone()
    conn.close()
    if not user or user["role"] != role:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="登录状态无效")
    return user_public_dict(user)


def require_roles(*roles: str):
    def dependency(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
        if current_user["role"] not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="无权访问该资源")
        return current_user

    return dependency


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = get_conn()
    cursor = conn.cursor()
    cursor.executescript(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
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
            student_username TEXT NOT NULL,
            student_name TEXT NOT NULL,
            location TEXT NOT NULL,
            repair_type TEXT NOT NULL,
            description TEXT NOT NULL,
            contact_phone TEXT NOT NULL,
            image_url TEXT DEFAULT '',
            status TEXT NOT NULL DEFAULT '待受理',
            assignee_username TEXT NOT NULL DEFAULT '',
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
            student_username TEXT NOT NULL,
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

    if cursor.execute("SELECT COUNT(*) FROM roles").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO roles(name, code, permissions, status) VALUES (?, ?, ?, ?)",
            [
                (ROLE_ADMIN, "admin", "用户管理,角色管理,工单管理,投诉建议,公告管理,统计分析", "启用"),
                (ROLE_WORKER, "worker", "工单处理,投诉处理,公告查看,统计分析", "启用"),
                (ROLE_STUDENT, "student", "报修提交,投诉建议,公告查看", "启用"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO users(username, password_hash, role, display_name, department, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                ("admin", hash_password("admin123"), ROLE_ADMIN, "王老师", "信息中心", "启用"),
                ("repair01", hash_password("123456"), ROLE_WORKER, "李师傅", "维修中心", "启用"),
                ("student01", hash_password("123456"), ROLE_STUDENT, "张同学", "计算机学院", "启用"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM repairs").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO repairs(student_username, student_name, location, repair_type, description, contact_phone, status, assignee_username, assignee)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("student01", "张同学", "3号宿舍楼 402", "宿舍报修", "空调制冷效果差，夜间噪音较大。", "13800000001", "处理中", "repair01", "李师傅"),
                ("student01", "张同学", "一食堂 二层", "餐饮反馈", "窗口照明故障，晚间取餐区域较暗。", "13800000001", "待受理", "", "未分配"),
                ("student01", "张同学", "图书馆东侧公共区域", "公共设施", "走廊饮水机无法加热。", "13800000001", "已完成", "repair01", "李师傅"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM notices").fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO notices(title, category, content, publisher, status) VALUES (?, ?, ?, ?, ?)",
            [
                ("北校区停水通知", "后勤公告", "因主管网检修，4月18日 09:00-12:00 北校区部分宿舍暂停供水。", "后勤保障处", "已发布"),
                ("宿舍报修高峰提醒", "服务提醒", "近期空调集中检修，请同学提交工单时补充房间号与联系电话。", "维修中心", "已发布"),
            ],
        )

    if cursor.execute("SELECT COUNT(*) FROM complaints").fetchone()[0] == 0:
        cursor.executemany(
            """
            INSERT INTO complaints(student_username, student_name, category, content, contact_phone, status, reply)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            [
                ("student01", "张同学", "服务态度", "晚间报修电话接听不及时，希望优化值班安排。", "13800000001", "待处理", ""),
                ("student01", "张同学", "餐饮建议", "建议晚餐高峰时段增加自助结算通道。", "13800000001", "已回复", "已提交食堂运营组评估。"),
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


@app.post("/api/auth/login")
def login(payload: LoginPayload) -> dict[str, Any]:
    conn = get_conn()
    user = conn.execute("SELECT * FROM users WHERE username = ?", (payload.username,)).fetchone()
    ok = bool(user and verify_password(payload.password, user["password_hash"]) and user["status"] == "启用")
    log_event(conn, "登录日志", payload.username, "登录成功" if ok else "登录失败", "低" if ok else "中", "安全版登录审计。")
    conn.commit()
    conn.close()
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    return {
        "message": "登录成功",
        "token": create_token(user["id"], user["role"]),
        "user": user_public_dict(user),
    }


@app.get("/api/dashboard/summary")
def dashboard_summary(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()

    if current_user["role"] == ROLE_ADMIN:
        repair_scope = ""
        repair_params: tuple[Any, ...] = ()
        complaint_scope = ""
        complaint_params: tuple[Any, ...] = ()
    elif current_user["role"] == ROLE_STUDENT:
        repair_scope = "WHERE student_username = ?"
        repair_params = (current_user["username"],)
        complaint_scope = "WHERE student_username = ?"
        complaint_params = (current_user["username"],)
    else:
        repair_scope = "WHERE assignee_username = ?"
        repair_params = (current_user["username"],)
        complaint_scope = ""
        complaint_params = ()

    total_repairs = cursor.execute(f"SELECT COUNT(*) FROM repairs {repair_scope}", repair_params).fetchone()[0]
    pending_repairs = cursor.execute(
        f"SELECT COUNT(*) FROM repairs {repair_scope + (' AND' if repair_scope else ' WHERE')} status IN ('待受理', '已分配', '处理中')",
        repair_params,
    ).fetchone()[0]
    total_notices = cursor.execute("SELECT COUNT(*) FROM notices").fetchone()[0]
    total_users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    total_complaints = cursor.execute(f"SELECT COUNT(*) FROM complaints {complaint_scope}", complaint_params).fetchone()[0]

    repair_status = dict_rows(
        cursor.execute(
            f"SELECT status AS name, COUNT(*) AS value FROM repairs {repair_scope} GROUP BY status ORDER BY COUNT(*) DESC",
            repair_params,
        ).fetchall()
    )
    complaint_status = dict_rows(
        cursor.execute(
            f"SELECT status AS name, COUNT(*) AS value FROM complaints {complaint_scope} GROUP BY status ORDER BY COUNT(*) DESC",
            complaint_params,
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
            f"""
            SELECT id, student_name, location, repair_type, status, assignee, created_at
            FROM repairs {repair_scope}
            ORDER BY id DESC LIMIT 6
            """,
            repair_params,
        ).fetchall()
    )
    conn.close()
    return {
        "metrics": [
            {"label": "累计工单", "value": total_repairs, "accent": "sun"},
            {"label": "待处理事项", "value": pending_repairs, "accent": "alert"},
            {"label": "投诉建议", "value": total_complaints, "accent": "sky"},
            {"label": "系统用户", "value": total_users, "accent": "leaf"},
        ],
        "charts": {
            "repairStatus": repair_status,
            "complaintStatus": complaint_status,
            "noticeCategory": notice_category,
            "departmentLoad": department_load,
        },
        "repairs": latest_repairs,
    }


@app.get("/api/repairs")
def list_repairs(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    conn = get_conn()
    if current_user["role"] == ROLE_ADMIN:
        rows = conn.execute("SELECT * FROM repairs ORDER BY id DESC").fetchall()
    elif current_user["role"] == ROLE_STUDENT:
        rows = conn.execute(
            "SELECT * FROM repairs WHERE student_username = ? ORDER BY id DESC",
            (current_user["username"],),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM repairs WHERE assignee_username = ? ORDER BY id DESC",
            (current_user["username"],),
        ).fetchall()
    conn.close()
    return dict_rows(rows)


@app.post("/api/repairs")
def create_repair(payload: RepairPayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_STUDENT))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO repairs(student_username, student_name, location, repair_type, description, contact_phone, image_url, status, assignee_username, assignee)
        VALUES (?, ?, ?, ?, ?, ?, ?, '待受理', '', '未分配')
        """,
        (
            current_user["username"],
            current_user["display_name"],
            payload.location,
            payload.repair_type,
            payload.description,
            payload.contact_phone,
            payload.image_url,
        ),
    )
    log_event(conn, "操作日志", current_user["username"], "提交报修", "低", "新增报修工单。")
    conn.commit()
    repair_id = cursor.lastrowid
    conn.close()
    return {"message": "报修提交成功", "id": repair_id}


@app.put("/api/repairs/{repair_id}")
def update_repair(
    repair_id: int,
    payload: dict[str, Any],
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, str]:
    conn = get_conn()
    current = conn.execute("SELECT * FROM repairs WHERE id = ?", (repair_id,)).fetchone()
    if not current:
        conn.close()
        raise HTTPException(status_code=404, detail="工单不存在")

    if current_user["role"] == ROLE_ADMIN:
        data = RepairAdminUpdatePayload(**payload)
        assignee_username = ""
        if data.assignee != "未分配":
            assignee_user = conn.execute(
                "SELECT username FROM users WHERE display_name = ? AND role = ?",
                (data.assignee, ROLE_WORKER),
            ).fetchone()
            assignee_username = assignee_user["username"] if assignee_user else ""
        conn.execute(
            """
            UPDATE repairs
            SET student_name = ?, location = ?, repair_type = ?, description = ?, contact_phone = ?,
                image_url = ?, status = ?, assignee = ?, assignee_username = ?
            WHERE id = ?
            """,
            (
                data.student_name,
                data.location,
                data.repair_type,
                data.description,
                data.contact_phone,
                data.image_url,
                data.status,
                data.assignee,
                assignee_username,
                repair_id,
            ),
        )
    elif current_user["role"] == ROLE_STUDENT:
        if current["student_username"] != current_user["username"]:
            conn.close()
            raise HTTPException(status_code=403, detail="无权修改该工单")
        data = RepairStudentUpdatePayload(**payload)
        conn.execute(
            "UPDATE repairs SET description = ?, contact_phone = ?, image_url = ? WHERE id = ?",
            (data.description, data.contact_phone, data.image_url, repair_id),
        )
    elif current_user["role"] == ROLE_WORKER:
        if current["assignee_username"] != current_user["username"]:
            conn.close()
            raise HTTPException(status_code=403, detail="无权修改该工单")
        data = RepairWorkerUpdatePayload(**payload)
        if data.status not in {"已完成", "已关闭"}:
            conn.close()
            raise HTTPException(status_code=400, detail="状态不合法")
        conn.execute("UPDATE repairs SET status = ? WHERE id = ?", (data.status, repair_id))
    else:
        conn.close()
        raise HTTPException(status_code=403, detail="无权修改该工单")

    log_event(conn, "操作日志", current_user["username"], "更新工单", "低", f"更新工单 #{repair_id}。")
    conn.commit()
    conn.close()
    return {"message": "工单状态已更新"}


@app.get("/api/notices")
def list_notices(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(conn.execute("SELECT * FROM notices ORDER BY id DESC").fetchall())
    conn.close()
    return rows


@app.post("/api/notices")
def create_notice(payload: NoticePayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO notices(title, category, content, publisher, status) VALUES (?, ?, ?, ?, ?)",
        (payload.title, payload.category, payload.content, payload.publisher, payload.status),
    )
    log_event(conn, "操作日志", current_user["username"], "发布公告", "低", "后台新增公告。")
    conn.commit()
    notice_id = cursor.lastrowid
    conn.close()
    return {"message": "公告发布成功", "id": notice_id}


@app.put("/api/notices/{notice_id}")
def update_notice(notice_id: int, payload: NoticePayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        """
        UPDATE notices
        SET title = ?, category = ?, content = ?, publisher = ?, status = ?
        WHERE id = ?
        """,
        (payload.title, payload.category, payload.content, payload.publisher, payload.status, notice_id),
    )
    log_event(conn, "操作日志", current_user["username"], "编辑公告", "低", f"更新公告 #{notice_id}。")
    conn.commit()
    conn.close()
    return {"message": "公告状态已更新"}


@app.get("/api/complaints")
def list_complaints(current_user: dict[str, Any] = Depends(get_current_user)) -> list[dict[str, Any]]:
    conn = get_conn()
    if current_user["role"] == ROLE_STUDENT:
        rows = conn.execute(
            "SELECT * FROM complaints WHERE student_username = ? ORDER BY id DESC",
            (current_user["username"],),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM complaints ORDER BY id DESC").fetchall()
    conn.close()
    return dict_rows(rows)


@app.post("/api/complaints")
def create_complaint(payload: ComplaintPayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_STUDENT))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO complaints(student_username, student_name, category, content, contact_phone)
        VALUES (?, ?, ?, ?, ?)
        """,
        (current_user["username"], current_user["display_name"], payload.category, payload.content, payload.contact_phone),
    )
    log_event(conn, "操作日志", current_user["username"], "提交投诉建议", "低", "新增投诉建议。")
    conn.commit()
    complaint_id = cursor.lastrowid
    conn.close()
    return {"message": "投诉建议提交成功", "id": complaint_id}


@app.put("/api/complaints/{complaint_id}")
def update_complaint(
    complaint_id: int,
    payload: ComplaintUpdatePayload,
    current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_WORKER)),
) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        "UPDATE complaints SET category = ?, content = ?, status = ?, reply = ? WHERE id = ?",
        (payload.category, payload.content, payload.status, payload.reply, complaint_id),
    )
    log_event(conn, "操作日志", current_user["username"], "处理投诉建议", "低", f"更新投诉 #{complaint_id}。")
    conn.commit()
    conn.close()
    return {"message": "投诉建议已处理"}


@app.get("/api/users")
def list_users(current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = conn.execute(
        "SELECT id, username, role, display_name, department, status FROM users ORDER BY id ASC"
    ).fetchall()
    conn.close()
    return dict_rows(rows)


@app.post("/api/users")
def create_user(payload: UserPayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    password_value = payload.password or "123456"
    cursor.execute(
        """
        INSERT INTO users(username, password_hash, role, display_name, department, status)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (payload.username, hash_password(password_value), payload.role, payload.display_name, payload.department, payload.status),
    )
    log_event(conn, "操作日志", current_user["username"], "新增用户", "低", f"新增用户 {payload.username}。")
    conn.commit()
    user_id = cursor.lastrowid
    conn.close()
    return {"message": "用户新增成功", "id": user_id}


@app.put("/api/users/{user_id}")
def update_user(user_id: int, payload: UserPayload, current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, str]:
    conn = get_conn()
    target = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not target:
        conn.close()
        raise HTTPException(status_code=404, detail="用户不存在")

    if current_user["role"] == ROLE_ADMIN:
        password_hash = target["password_hash"] if not payload.password else hash_password(payload.password)
        conn.execute(
            """
            UPDATE users
            SET username = ?, password_hash = ?, role = ?, display_name = ?, department = ?, status = ?
            WHERE id = ?
            """,
            (payload.username, password_hash, payload.role, payload.display_name, payload.department, payload.status, user_id),
        )
    elif current_user["id"] == user_id:
        password_hash = target["password_hash"] if not payload.password else hash_password(payload.password)
        conn.execute(
            """
            UPDATE users
            SET display_name = ?, department = ?, password_hash = ?
            WHERE id = ?
            """,
            (payload.display_name, payload.department, password_hash, user_id),
        )
    else:
        conn.close()
        raise HTTPException(status_code=403, detail="无权修改该用户")

    log_event(conn, "操作日志", current_user["username"], "更新用户", "低", f"更新用户 #{user_id}。")
    conn.commit()
    conn.close()
    return {"message": "用户更新成功"}


@app.get("/api/roles")
def list_roles(current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> list[dict[str, Any]]:
    conn = get_conn()
    rows = dict_rows(conn.execute("SELECT * FROM roles ORDER BY id ASC").fetchall())
    conn.close()
    return rows


@app.post("/api/roles")
def create_role(payload: RolePayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> dict[str, Any]:
    conn = get_conn()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO roles(name, code, permissions, status) VALUES (?, ?, ?, ?)",
        (payload.name, payload.code, payload.permissions, payload.status),
    )
    log_event(conn, "操作日志", current_user["username"], "新增角色", "低", f"新增角色 {payload.name}。")
    conn.commit()
    role_id = cursor.lastrowid
    conn.close()
    return {"message": "角色新增成功", "id": role_id}


@app.put("/api/roles/{role_id}")
def update_role(role_id: int, payload: RolePayload, current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN))) -> dict[str, str]:
    conn = get_conn()
    conn.execute(
        """
        UPDATE roles
        SET name = ?, code = ?, permissions = ?, status = ?
        WHERE id = ?
        """,
        (payload.name, payload.code, payload.permissions, payload.status, role_id),
    )
    log_event(conn, "操作日志", current_user["username"], "编辑角色", "低", f"更新角色 #{role_id}。")
    conn.commit()
    conn.close()
    return {"message": "角色更新成功"}


@app.post("/api/upload")
async def upload_image(
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(require_roles(ROLE_ADMIN, ROLE_STUDENT)),
) -> dict[str, str]:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_UPLOAD_SUFFIXES or file.content_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(status_code=400, detail="仅支持 png、jpg、jpeg、webp 图片")
    content = await file.read()
    if len(content) > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="图片大小不能超过 2MB")
    file_name = f"{uuid.uuid4().hex}{suffix}"
    target = UPLOAD_DIR / file_name
    target.write_bytes(content)
    return {"message": "上传成功", "file_name": file_name, "url": f"/uploads/{file_name}"}
