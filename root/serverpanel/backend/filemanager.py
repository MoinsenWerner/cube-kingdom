import os
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.responses import FileResponse
from auth import verify_license

router = APIRouter()

BASE_DIR = "/home/mc"

def get_safe_path(server: str, path: str = ""):
    safe_base = os.path.abspath(os.path.join(BASE_DIR, server))
    target = os.path.abspath(os.path.join(safe_base, path))
    if not target.startswith(safe_base):
        raise HTTPException(status_code=400, detail="Pfad außerhalb des Servers")
    return safe_base, target

@router.get("/files/list")
def list_files(server: str, path: str = "", api_key: str = Depends(verify_license)):
    base, full_path = get_safe_path(server, path)
    if not os.path.isdir(full_path):
        raise HTTPException(status_code=404, detail="Verzeichnis nicht gefunden")

    items = []
    for name in os.listdir(full_path):
        p = os.path.join(full_path, name)
        items.append({
            "name": name,
            "type": "dir" if os.path.isdir(p) else "file"
        })
    return {"items": items, "path": path}

@router.post("/files/upload")
def upload_file(server: str = Form(...), path: str = Form(""), file: UploadFile = File(...), api_key: str = Depends(verify_license)):
    _, full_path = get_safe_path(server, path)
    if not os.path.isdir(full_path):
        raise HTTPException(status_code=400, detail="Ungültiger Zielordner")
    target_file = os.path.join(full_path, file.filename)
    with open(target_file, "wb") as f:
        f.write(file.file.read())
    return {"success": True}

@router.get("/files/download")
def download_file(server: str, path: str, api_key: str = Depends(verify_license)):
    _, full_path = get_safe_path(server, path)
    if not os.path.isfile(full_path):
        raise HTTPException(status_code=404, detail="Datei nicht gefunden")
    return FileResponse(full_path, filename=os.path.basename(full_path))

@router.post("/files/delete")
def delete_files(server: str = Form(...), paths: list[str] = Form(...), api_key: str = Depends(verify_license)):
    base, _ = get_safe_path(server)
    for relative in paths:
        _, full = get_safe_path(server, relative)
        if os.path.isdir(full):
            try:
                os.rmdir(full)  # Nur leere Verzeichnisse löschen
            except:
                raise HTTPException(status_code=400, detail=f"Kann Ordner nicht löschen: {relative}")
        else:
            os.remove(full)
    return {"success": True}

@router.post("/files/mkdir")
def make_dir(server: str = Form(...), path: str = Form(...), name: str = Form(...), api_key: str = Depends(verify_license)):
    _, full_path = get_safe_path(server, path)
    new_dir = os.path.join(full_path, name)
    if not new_dir.startswith(os.path.abspath(os.path.join(BASE_DIR, server))):
        raise HTTPException(status_code=400, detail="Ungültiger Pfad")
    os.makedirs(new_dir, exist_ok=True)
    return {"success": True}
