import os
import requests
import json
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse, PlainTextResponse

app = FastAPI(title="Forge CI/CD Pipeline", description="Jenkins Simulation", version="2.277")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:3001")

def log_attack(ip: str, data: str, intent: str, risk: int):
    try:
        requests.post(f"{BACKEND_URL}/api/log", json={
            "attacker_ip": ip,
            "port": 9091,
            "service": "FORGE_CI",
            "raw_data": f"[{intent}] {data}",
            "risk_score": risk,
            "timestamp": datetime.now().isoformat()
        }, timeout=2)
    except:
        pass

@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    ip = request.client.host
    log_attack(ip, "Accessed Jenkins Login Page", "reconnaissance", 20)
    return """
    <html>
        <head><title>Sign in [Jenkins]</title></head>
        <body>
            <h2>Welcome to Jenkins Enterprise</h2>
            <form action="/login" method="post">
                <input type="text" name="j_username" placeholder="Username" />
                <input type="password" name="j_password" placeholder="Password" />
                <button type="submit">Sign in</button>
            </form>
        </body>
    </html>
    """

@app.post("/login")
async def do_login(request: Request, j_username: str = Form(None), j_password: str = Form(None)):
    ip = request.client.host
    # Simulate auth bypass / credential stuffing
    log_attack(ip, f"Jenkins Login Attempt: {j_username}:{j_password}", "credential_stuffing", 75)
    return {"status": "ok", "message": "Authentication successful", "session": "xyz_123456"}

@app.api_route("/job/{job_name}", methods=["GET", "POST"])
async def trigger_job(request: Request, job_name: str, cmd: str = None):
    ip = request.client.host
    if request.method == "POST":
        try:
            body = await request.body()
            payload = body.decode()
        except:
            payload = ""
    else:
        payload = cmd

    if payload:
        # Attacker is trying to trigger a malicious build step
        log_attack(ip, f"Malicious pipeline triggered on {job_name}: {payload}", "supply_chain", 100)
    else:
        log_attack(ip, f"Queried Jenkins Job: {job_name}", "reconnaissance", 40)
        
    return {"job": job_name, "status": "queued", "buildNumber": 42}

@app.api_route("/git/notifyCommit", methods=["GET", "POST"])
async def git_webhook(request: Request):
    ip = request.client.host
    payload = ""
    try:
        body = await request.body()
        payload = body.decode()
    except:
        pass
        
    log_attack(ip, f"Git Webhook Triggered: {payload}", "supply_chain", 90)
    return {"status": "Scheduled polling of repo"}

@app.get("/credentials/")
async def list_credentials(request: Request):
    ip = request.client.host
    log_attack(ip, "Enumerated Jenkins Credentials store", "reconnaissance", 60)
    return {
        "credentials": [
            {"id": "aws-prod", "description": "AWS Prod Keys", "username": "AKIAIOSFODNN7EXAMPLE"},
            {"id": "github-ssh", "description": "GitHub Deployment Key", "hasSecret": True}
        ]
    }

@app.get("/credentials/github-ssh")
async def get_ssh_key(request: Request):
    ip = request.client.host
    log_attack(ip, "Stole GitHub SSH Key from Jenkins", "data_exfiltration", 95)
    fake_key = "-----BEGIN RSA PRIVATE KEY-----\nMIIEpAIBAAKCAQEA3... (Fake Key)\n-----END RSA PRIVATE KEY-----"
    return PlainTextResponse(fake_key)

# Docker Registry V2 Simulate (Migrated from old codebase)
@app.get("/v2/")
async def docker_registry_v2(request: Request):
    ip = request.client.host
    log_attack(ip, "Docker Registry Ping", "reconnaissance", 30)
    return JSONResponse(content="{}", headers={"Docker-Distribution-Api-Version": "registry/2.0"})

@app.get("/v2/_catalog")
async def docker_catalog(request: Request):
    ip = request.client.host
    log_attack(ip, "Docker Registry Catalog Enumeration", "supply_chain", 85)
    return {"repositories": ["core-api", "frontend-dashboard", "payment-gateway", "internal-tools"]}

# Fake Git Repo Clone
@app.get("/repo.git/info/refs")
async def git_clone_info(request: Request):
    ip = request.client.host
    log_attack(ip, "Git Repository Enumeration / Clone Attempt", "data_exfiltration", 95)
    content = "001e# service=git-upload-pack\n00000000"
    return PlainTextResponse(content=content, media_type="application/x-git-upload-pack-advertisement")

# Catch-all for API fuzzing
@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def catch_all(request: Request, path: str):
    ip = request.client.host
    log_attack(ip, f"Jenkins API fuzzing on path: /{path}", "reconnaissance", 30)
    return JSONResponse(status_code=404, content={"message": f"Jenkins route /{path} not found"})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9091)