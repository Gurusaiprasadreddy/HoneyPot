import os
import requests
import json
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI(title="Ethereum JSON-RPC Node", description="Web3 API", version="1.0")

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:3001")

def log_attack(ip: str, data: str, intent: str, risk: int):
    try:
        requests.post(f"{BACKEND_URL}/api/log", json={
            "attacker_ip": ip,
            "port": 8545,
            "service": "LEDGER_TRAP",
            "raw_data": f"[{intent}] {data}",
            "risk_score": risk,
            "timestamp": datetime.now().isoformat()
        }, timeout=2)
    except:
        pass

@app.post("/")
async def json_rpc(request: Request):
    ip = request.client.host
    try:
        body = await request.json()
    except Exception:
        log_attack(ip, "Malformed JSON Payload", "rpc_fuzzing", 80)
        return JSONResponse(status_code=400, content={"error": "Parse error", "id": None})

    # Handle batched requests
    if isinstance(body, list):
        reqs = body
    else:
        reqs = [body]

    responses = []
    
    for req in reqs:
        method = req.get("method", "unknown")
        req_id = req.get("id", 1)
        params = req.get("params", [])

        if method == "eth_blockNumber":
            # Fake high block number (e.g. block 19,000,000)
            log_attack(ip, "Queried Block Number", "web3_recon", 20)
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": "0x121eac0"})
            
        elif method == "eth_getBalance":
            # Return a massive fake balance (e.g., 500 ETH)
            log_attack(ip, f"Queried Balance for {params}", "web3_recon", 30)
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": "0x1b1ae4d6e2ef500000"})
            
        elif method == "eth_accounts":
            # Return juicy fake addresses
            log_attack(ip, "Enumerated Wallets", "web3_recon", 40)
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": [
                "0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B",
                "0x4B0897b0513fdC7C541B6d9D7E929C4e5364D2dB"
            ]})
            
        elif method == "eth_sendTransaction" or method == "eth_sendRawTransaction":
            # Capture the malicious transaction attempt
            log_attack(ip, f"Attempted Transaction: {params}", "crypto_theft", 100)
            # Fake a transaction hash response
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": "0x8a3c8bf08db5e9e09d13e316a3bc5f778d94e2e28892f39d56488bc11425d5d6"})
            
        elif method == "net_version":
            responses.append({"jsonrpc": "2.0", "id": req_id, "result": "1"})
            
        else:
            # Fallback for fuzzing or unknown methods
            log_attack(ip, f"Unknown/Fuzzing Method: {method}", "rpc_fuzzing", 60)
            responses.append({"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}})

    if isinstance(body, list):
        return JSONResponse(content=responses)
    else:
        return JSONResponse(content=responses[0])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8545)
