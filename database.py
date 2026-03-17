import os
import sqlite3
from pathlib import Path
from typing import Optional


APP_NAME = "MISMain"
DEFAULT_DB_NAME = "mis_main.db"


def get_app_data_dir(custom_dir: Optional[str] = None) -> Path:
    """
    Determine the directory where the SQLite database will live.

    Priority:
    1. Explicit custom_dir argument
    2. MIS_MAIN_DB_DIR environment variable
    3. C:\\ProgramData\\MISMain
    4. ~/Documents/MISMain/Data
    """
    if custom_dir:
        base = Path(custom_dir)
    elif os.environ.get("MIS_MAIN_DB_DIR"):
        base = Path(os.environ["MIS_MAIN_DB_DIR"])
    else:
        if os.name == "nt":
            program_data = os.environ.get("PROGRAMDATA")
            if program_data:
                base = Path(program_data) / APP_NAME
            else:
                documents = Path.home() / "Documents"
                base = documents / APP_NAME / "Data"
        else:
            # Fallback for non-Windows environments
            base = Path.home() / f".{APP_NAME.lower()}"

    base.mkdir(parents=True, exist_ok=True)
    return base


def get_db_path(custom_dir: Optional[str] = None) -> Path:
    return get_app_data_dir(custom_dir) / DEFAULT_DB_NAME


def get_connection(custom_dir: Optional[str] = None) -> sqlite3.Connection:
    db_path = get_db_path(custom_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


def init_db(custom_dir: Optional[str] = None) -> None:
    """
    Initialize database schema if it does not exist.
    Creates default admin user (username: admin, password: admin) if no users exist.
    """
    conn = get_connection(custom_dir)
    cur = conn.cursor()

    # Visitors table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS visitors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            nin TEXT UNIQUE NOT NULL,
            district TEXT,
            sub_county TEXT,
            village TEXT
        )
        """
    )

    # Visits table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_id INTEGER NOT NULL,
            reason TEXT,
            person_visited TEXT NOT NULL,
            items_brought TEXT,
            time_in TEXT NOT NULL,
            time_out TEXT,
            visit_date TEXT NOT NULL,
            FOREIGN KEY (visitor_id) REFERENCES visitors(id)
        )
        """
    )

    # Users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('ADMIN', 'RECORDING_USER'))
        )
        """
    )

    conn.commit()

    # Ensure at least one admin user exists
    cur.execute("SELECT COUNT(*) AS c FROM users")
    row = cur.fetchone()
    if row and row["c"] == 0:
        from hashlib import sha256

        default_password = "admin"
        password_hash = sha256(default_password.encode("utf-8")).hexdigest()
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            ("admin", password_hash, "ADMIN"),
        )
        conn.commit()

    conn.close()


def verify_user(username: str, password: str, custom_dir: Optional[str] = None):
    """Return user row (dict-like) if credentials are valid, else None."""
    from hashlib import sha256

    conn = get_connection(custom_dir)
    cur = conn.cursor()

    cur.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cur.fetchone()
    if not user:
        conn.close()
        return None

    password_hash = sha256(password.encode("utf-8")).hexdigest()
    if user["password_hash"] != password_hash:
        conn.close()
        return None

    # Convert to simple dict for easier use in GUI
    result = {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"],
    }
    conn.close()
    return result


def create_user(username: str, password: str, role: str, custom_dir: Optional[str] = None):
    from hashlib import sha256

    conn = get_connection(custom_dir)
    cur = conn.cursor()
    password_hash = sha256(password.encode("utf-8")).hexdigest()
    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, password_hash, role),
    )
    conn.commit()
    conn.close()

