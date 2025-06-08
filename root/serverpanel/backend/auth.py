import sqlite3
from fastapi import HTTPException, Header

def verify_license(x_api_key: str = Header(...)):
    import sqlite3
    conn = sqlite3.connect("/root/serverpanel/backend/database.sqlite")
    cur = conn.cursor()
    cur.execute("SELECT valid_until, active FROM licenses WHERE key=?", (x_api_key,))
    row = cur.fetchone()
    conn.close()
    if not row or row[1] != 1:
        raise HTTPException(status_code=403, detail="Invalid or inactive license key")
    return x_api_key
