import os
import requests
from datetime import datetime
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
import urllib.parse

app = FastAPI(title="Corporate Web Portal")

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")

def log_attack(ip: str, data: str):
    try:
        requests.post(f"{BACKEND_URL}/api/log", json={
            "attacker_ip": ip,
            "port": 80,
            "service": "WEB_HONEYPOT",
            "raw_data": data,
            "timestamp": datetime.now().isoformat()
        }, timeout=2)
    except:
        pass

def detect_attack(path: str, body: str = ""):
    combined = urllib.parse.unquote(path + " " + body).lower()
    if "<script" in combined or "javascript:" in combined or "onerror=" in combined:
        return "xss_attempt"
    if "union" in combined or "select" in combined or "1=1" in combined or "' or" in combined:
        return "sqli_attempt"
    if "../" in combined or "/etc/passwd" in combined or "windows/system32" in combined:
        return "directory_traversal"
    return None

@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    ip = request.client.host
    path = request.url.path
    query = request.url.query
    
    body_bytes = await request.body()
    body_str = body_bytes.decode(errors="ignore")
    
    full_path = f"{path}?{query}" if query else path
    
    # Simple attack detection in middleware
    attack_type = detect_attack(full_path, body_str)
    
    if attack_type or path not in ["/", "/login", "/admin"]:
        # Log anomalous behaviour
        log_data = f"{request.method} {full_path} BODY: {body_str}"
        log_attack(ip, log_data)
        
    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <html>
    <head><title>Corporate Intranet</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h1>Welcome to Corporate Intranet v2.1</h1>
        <p>Employees must <a href="/login">login here</a> to access the admin portal.</p>
    </body>
    </html>
    """

@app.get("/login", response_class=HTMLResponse)
async def login_get():
    return """
    <html>
    <head><title>Login - Corporate</title></head>
    <body style="font-family: Arial; display: flex; justify-content: center; align-items: center; height: 100vh;">
        <div style="border: 1px solid #ccc; padding: 30px; border-radius: 5px;">
            <h2>Admin Login</h2>
            <form method="POST" action="/login">
                <input type="text" name="username" placeholder="Username" style="width: 100%; margin-bottom: 10px; padding: 5px;"><br>
                <input type="password" name="password" placeholder="Password" style="width: 100%; margin-bottom: 10px; padding: 5px;"><br>
                <input type="submit" value="Login" style="width: 100%; padding: 5px; background: #0066cc; color: white; border: none;">
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/login", response_class=HTMLResponse)
async def login_post(request: Request):
    ip = request.client.host
    body = await request.body()
    body_str = body.decode("utf-8", errors="ignore")
    
    # Automatically log the login attempt
    log_attack(ip, f"LOGIN ATTEMPT: {body_str}")
    
    return """
    <html>
    <head><title>Login Failed</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h2 style="color: red;">Invalid credentials or database connection error</h2>
        <p><a href="/login">Try again</a></p>
        <p style="font-size: 10px; color: #888;">Error code: SQL_CONN_TIMEOUT</p>
    </body>
    </html>
    """

@app.get("/admin", response_class=HTMLResponse)
async def admin(request: Request):
    ip = request.client.host
    log_attack(ip, "ACCESSED ADMIN PORTAL UNAUTHENTICATED")
    return """
    <html>
    <head><title>Access Denied</title></head>
    <body style="font-family: Arial; text-align: center; margin-top: 50px;">
        <h1 style="color: red;">403 Forbidden</h1>
        <p>You do not have the required permissions to view this directory.</p>
    </body>
    </html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8082)
