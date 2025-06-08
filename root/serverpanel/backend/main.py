from fastapi import APIRouter, FastAPI, Request, HTTPException, Depends, Header, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from auth import verify_license
from services import list_services, control_service, get_logs, list_server_names
from licenses_api import router as license_router
import sqlite3
from filemanager import router as filemanager_router

app = FastAPI()
router = APIRouter()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Gibt alle Servernamen zurück (für Dropdown)
@app.get("/servers")
def get_servers(api_key: str = Depends(verify_license)):
    return list_server_names()

# Gibt nur den Status für einen bestimmten Server zurück
@app.get("/status")
def status(
    name: str = Query(None),
    api_key: str = Depends(verify_license)
):
    all_status = list_services()
    if name:
        unit = f"minecraft@{name}"
        if unit not in all_status:
            raise HTTPException(status_code=404, detail="Server nicht gefunden")
        return {unit: all_status[unit]}
    return all_status

@app.post("/control")
async def control(data: dict, api_key: str = Depends(verify_license)):
    return control_service(data)

@app.get("/logs")
async def logs(service: str, api_key: str = Depends(verify_license)):
    return get_logs(service)

@app.get("/me")
def get_license_info(x_api_key: str = Header(...)):
    conn = sqlite3.connect("/root/serverpanel/backend/database.sqlite")
    cursor = conn.cursor()
    cursor.execute("SELECT key, active, admin, valid_until, license_type FROM licenses WHERE key = ?", (x_api_key,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=403, detail="Ungültiger Schlüssel")
    return {
    "key": row[0],
    "active": row[1],
    "admin": row[2],
    "valid_until": row[3],
    "license_type": row[4] or "basic"
    }

app.include_router(license_router)
app.include_router(filemanager_router)

class DeleteRequest(BaseModel):
    server: str
    paths: list[str]

@router.post("/files/delete")
def delete_files(data: DeleteRequest, api_key: str = Depends(verify_license)):
    base_path = f"/home/mc/{data.server}"
    deleted = []
    for rel in data.paths:
        abs_path = os.path.abspath(os.path.join(base_path, rel))
        if not abs_path.startswith(base_path):
            raise HTTPException(status_code=400, detail="Pfad nicht erlaubt")
        try:
            if os.path.isdir(abs_path):
                os.rmdir(abs_path)
            else:
                os.remove(abs_path)
            deleted.append(rel)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Löschen: {rel}: {str(e)}")
    return {"deleted": deleted}