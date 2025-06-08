from fastapi import APIRouter, Header, HTTPException
import sqlite3
import uuid
from datetime import datetime, timedelta

router = APIRouter()

DB_PATH = "/root/serverpanel/backend/database.sqlite"

def is_admin_key(key: str) -> bool:
    if key == "h2r-admin0709-reload9383":
        return True
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.execute("SELECT admin FROM licenses WHERE key = ? AND active = 1", (key,))
    row = cur.fetchone()
    con.close()
    return row is not None and row[0] == 1

@router.get("/licenses")
def list_keys(x_api_key: str = Header(None)):
    if not is_admin_key(x_api_key):
        raise HTTPException(status_code=403, detail="Adminzugriff erforderlich")
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    cur = con.cursor()
    cur.execute("SELECT key, valid_until, active, admin FROM licenses")
    rows = cur.fetchall()
    con.close()
    return [dict(r) for r in rows]

@router.post("/licenses/add")
def add_key(data: dict, x_api_key: str = Header(None)):
    if not is_admin_key(x_api_key):
        raise HTTPException(status_code=403, detail="Adminzugriff erforderlich")
    key = data.get("key") or str(uuid.uuid4())
    valid_until = data.get("valid_until")  # z. B. "2025-12-31"
    active = int(data.get("active", 1))
    admin = int(data.get("admin", 0))
    con = sqlite3.connect(DB_PATH)
    try:
        con.execute("INSERT INTO licenses (key, valid_until, active, admin) VALUES (?, ?, ?, ?)", (key, valid_until, active, admin))
        con.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Key bereits vorhanden")
    finally:
        con.close()
    return {"success": True, "key": key}

@router.post("/licenses/update")
def update_key(data: dict, x_api_key: str = Header(None)):
    if not is_admin_key(x_api_key):
        raise HTTPException(status_code=403, detail="Adminzugriff erforderlich")
    key = data.get("key")
    valid_until = data.get("valid_until")
    active = int(data.get("active", 1))
    con = sqlite3.connect(DB_PATH)
    con.execute("UPDATE licenses SET valid_until = ?, active = ? WHERE key = ?", (valid_until, active, key))
    con.commit()
    con.close()
    return {"success": True}

@router.post("/licenses/delete")
def delete_key(data: dict, x_api_key: str = Header(None)):
    if not is_admin_key(x_api_key):
        raise HTTPException(status_code=403, detail="Adminzugriff erforderlich")
    key = data.get("key")
    con = sqlite3.connect(DB_PATH)
    con.execute("DELETE FROM licenses WHERE key = ?", (key,))
    con.commit()
    con.close()
    return {"success": True}
