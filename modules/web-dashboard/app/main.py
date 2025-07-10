# modules/web-dashboard/main.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import subprocess
from pathlib import Path

app = FastAPI()
templates = Jinja2Templates(directory="templates")

MODULE_LIST_PATH = "/app/shared/module.list"

def get_module_names():
    try:
        with open(MODULE_LIST_PATH, "r") as f:
            return [Path(line.strip()).name for line in f if line.strip()]
    except Exception:
        return []

def get_container_status(name):
    try:
        result = subprocess.check_output(["docker", "inspect", "-f", "{{.State.Status}}", name])
        return result.decode().strip()
    except subprocess.CalledProcessError:
        return "not found"

def get_container_logs(name, tail=100):
    try:
        result = subprocess.check_output(["docker", "logs", "--tail", str(tail), name])
        return result.decode()
    except subprocess.CalledProcessError:
        return "Logs unavailable"

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    modules = get_module_names()
    statuses = {name: get_container_status(name) for name in modules}
    return templates.TemplateResponse("index.html", {"request": request, "statuses": statuses})

@app.get("/logs/{container}", response_class=HTMLResponse)
async def logs(request: Request, container: str):
    logs = get_container_logs(container)
    return templates.TemplateResponse("logs.html", {"request": request, "container": container, "logs": logs})
