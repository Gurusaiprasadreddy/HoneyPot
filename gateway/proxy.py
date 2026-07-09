import asyncio, os, aiohttp, json
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")

ROUTES = {
    2222: ("shadow-shell", 2223),
    8080: ("oracle-ai",    8081),
    3306: ("vault-sql",    3306),
    80:   ("web-honeypot", 8082),
    9090: ("forge-ci",     9091),
    8545: ("ledger-trap",  8545),
}

async def log_connection(ip, port):
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json={
                "attacker_ip": ip, "port": port,
                "service": "PROXY",
                "raw_data": f"New connection on port {port}",
                "timestamp": datetime.now().isoformat()
            })
    except:
        pass

async def pipe(reader, writer):
    try:
        while True:
            data = await reader.read(4096)
            if not data:
                break
            writer.write(data)
            await writer.drain()
    except:
        pass
    finally:
        try:
            writer.close()
        except:
            pass

async def handle(reader, writer, listen_port):
    ip = writer.get_extra_info("peername")[0]
    target_host, target_port = ROUTES.get(listen_port, ("localhost", 9999))
    asyncio.create_task(log_connection(ip, listen_port))
    try:
        dr, dw = await asyncio.open_connection(target_host, target_port)
        await asyncio.gather(pipe(reader, dw), pipe(dr, writer))
    except:
        pass
    finally:
        try:
            writer.close()
        except:
            pass

async def main():
    for port in ROUTES:
        await asyncio.start_server(
            lambda r, w, p=port: handle(r, w, p),
            "0.0.0.0", port
        )
        print(f"[PROXY] Listening on port {port}")
    await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())