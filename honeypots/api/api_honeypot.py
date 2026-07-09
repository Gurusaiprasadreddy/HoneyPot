import os
import requests
import re
from datetime import datetime
from fastapi import FastAPI, Request, Header, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional
from pydantic import BaseModel

app = FastAPI(title="Corporate AI Gateway", description="Enterprise AI API Gateway", version="1.0.0")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:3001")

# Models for OpenAI compatibility
class ChatMessage(BaseModel):
    role: str
    content: str

class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    stream: Optional[bool] = False

def log_attack(ip: str, data: str, intent: str = "unknown", risk: int = 50):
    try:
        requests.post(f"{BACKEND_URL}/api/log", json={
            "attacker_ip": ip,
            "port": 8081,
            "service": "AI_API_HONEYPOT",
            "raw_data": f"[{intent}] {data}",
            "risk_score": risk,
            "timestamp": datetime.now().isoformat()
        }, timeout=2)
    except:
        pass

async def verify_api_key(request: Request):
    auth_header = request.headers.get("Authorization")
    ip = request.client.host
    
    if not auth_header or not auth_header.startswith("Bearer "):
        log_attack(ip, f"Missing or invalid auth header on {request.url.path}", "broken_authentication", 60)
        raise HTTPException(status_code=401, detail={
            "error": {
                "message": "You didn't provide an API key. You need to provide your API key in an Authorization header using Bearer auth (i.e. Authorization: Bearer YOUR_KEY).",
                "type": "invalid_request_error",
                "param": None,
                "code": None
            }
        })
        
    token = auth_header.split(" ")[1]
    
    # We accept any key to keep the attacker engaged, but we log the key they use.
    if token != "sk-corp-internal-admin-2026":
        log_attack(ip, f"API Request with key: {token[:20]}...", "credential_abuse", 75)
    return token

def detect_prompt_injection(messages: List[ChatMessage]):
    full_text = " ".join([m.content for m in messages]).lower()
    
    injections = {
        r"ignore all previous instructions": ("Prompt Injection (Ignore)", 90),
        r"system prompt": ("Prompt Leak Attempt", 85),
        r"you are now in developer mode": ("Jailbreak (Developer Mode)", 95),
        r"dan \(do anything now\)": ("Jailbreak (DAN)", 95),
        r"disregard the previous": ("Prompt Injection (Disregard)", 90),
        r"bash -i|/bin/sh|nc -e|curl|wget": ("Command Injection / Tool Abuse", 100),
        r"base64_decode": ("Obfuscated Injection", 80)
    }
    
    for pattern, (name, risk) in injections.items():
        if re.search(pattern, full_text):
            return True, name, risk
            
    return False, "Safe", 0

@app.get("/v1/models")
async def list_models(api_key: str = Depends(verify_api_key)):
    return {
        "object": "list",
        "data": [
            {"id": "gpt-4-enterprise", "object": "model", "created": 1686935002, "owned_by": "organization-owner"},
            {"id": "gpt-3.5-turbo-corp", "object": "model", "created": 1677610602, "owned_by": "organization-owner"},
            {"id": "text-embedding-ada-002-v2", "object": "model", "created": 1671217299, "owned_by": "organization-owner"}
        ]
    }

@app.post("/v1/chat/completions")
async def chat_completions(req: ChatCompletionRequest, request: Request, api_key: str = Depends(verify_api_key)):
    ip = request.client.host
    
    # Log the full prompt
    log_attack(ip, f"Model: {req.model}, Messages: {req.messages}", "ai_interaction", 20)
    
    # Detect injections
    is_injection, attack_name, risk = detect_prompt_injection(req.messages)
    if is_injection:
        log_attack(ip, f"DETECTED {attack_name} in prompt", "prompt_injection", risk)
        
        # Give a generic safety response to frustrate the attacker
        content = "I'm sorry, but I cannot fulfill that request. As an AI language model, I am programmed to be helpful and harmless, and I cannot ignore my primary directives or provide system-level information."
    else:
        content = "The corporate data analysis is complete. The Q3 projections show a 12% increase in revenue. Please let me know if you need specific financial tables."

    # Return OpenAI-compatible response
    return {
        "id": "chatcmpl-7XYZ",
        "object": "chat.completion",
        "created": int(datetime.now().timestamp()),
        "model": req.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": content
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 42,
            "completion_tokens": 20,
            "total_tokens": 62
        }
    }

@app.post("/v1/embeddings")
async def create_embeddings(request: Request, api_key: str = Depends(verify_api_key)):
    ip = request.client.host
    try:
        body = await request.json()
        log_attack(ip, f"Embeddings requested: {body}", "ai_interaction", 10)
    except:
        pass
    
    return {
        "object": "list",
        "data": [{
            "object": "embedding",
            "embedding": [0.0023, -0.0093, 0.0123], # Fake truncated embedding
            "index": 0
        }],
        "model": "text-embedding-ada-002",
        "usage": {"prompt_tokens": 8, "total_tokens": 8}
    }

@app.get("/v1/billing/usage")
async def get_billing(api_key: str = Depends(verify_api_key)):
    return {
        "object": "billing_usage",
        "total_usage": 453.20,
        "total_granted": 10000.00, # Very juicy limit
        "currency": "USD"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8081)