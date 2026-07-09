import socket
import threading
import os
import requests
import sqlite3
import sqlparse
import re
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:3001")

# --- MySQL Wire Protocol Helpers ---

def lenenc_int(i):
    if i < 251: return bytes([i])
    if i < 65536: return b'\xfc' + i.to_bytes(2, 'little')
    if i < 16777216: return b'\xfd' + i.to_bytes(3, 'little')
    return b'\xfe' + i.to_bytes(8, 'little')

def lenenc_str(s):
    b = s.encode('utf-8')
    return lenenc_int(len(b)) + b

def make_packet(payload, seq):
    length = len(payload)
    return length.to_bytes(3, 'little') + bytes([seq]) + payload

def send_error(conn, seq, msg):
    payload = b'\xff\x15\x04#42000' + msg.encode()
    conn.sendall(make_packet(payload, seq))

def send_ok(conn, seq):
    payload = b'\x00\x00\x00\x02\x00\x00\x00'
    conn.sendall(make_packet(payload, seq))

def send_result_set(conn, seq_start, columns, rows):
    seq = seq_start
    # Column count
    conn.sendall(make_packet(lenenc_int(len(columns)), seq))
    seq += 1
    
    # Column definitions
    for col in columns:
        payload = (
            lenenc_str("def") + 
            lenenc_str("") + lenenc_str(col) + lenenc_str("") + lenenc_str(col) +
            b'\x0c\x08\x00\x00\x00\x00\x00\xfd\x00\x00\x00\x00\x00'
        )
        conn.sendall(make_packet(payload, seq))
        seq += 1
        
    # EOF packet
    conn.sendall(make_packet(b'\xfe\x00\x00\x02\x00', seq))
    seq += 1
    
    # Rows
    for row in rows:
        payload = b''
        for val in row:
            if val is None:
                payload += b'\xfb'
            else:
                payload += lenenc_str(str(val))
        conn.sendall(make_packet(payload, seq))
        seq += 1
        
    # EOF packet
    conn.sendall(make_packet(b'\xfe\x00\x00\x02\x00', seq))

# --- Fake Database & SQLi Detection ---

def setup_fake_db():
    conn = sqlite3.connect(':memory:')
    c = conn.cursor()
    c.execute("CREATE TABLE users (id INTEGER, username TEXT, password TEXT)")
    c.execute("INSERT INTO users VALUES (1, 'admin', 'SuperSecretAdmin123!')")
    c.execute("INSERT INTO users VALUES (2, 'john_doe', 'Password123')")
    c.execute("CREATE TABLE api_keys (service TEXT, api_key TEXT)")
    c.execute("INSERT INTO api_keys VALUES ('AWS', 'AKIAIOSFODNN7EXAMPLE')")
    c.execute("CREATE TABLE financial_records (account_id INTEGER, balance REAL)")
    c.execute("INSERT INTO financial_records VALUES (101, 54321.00)")
    c.execute("INSERT INTO financial_records VALUES (102, 1000000.00)")
    conn.commit()
    return conn

def log_attack(ip, data, attack_type="MySQL Access", risk_score=50):
    try:
        requests.post(f"{BACKEND_URL}/api/log", json={
            "attacker_ip": ip,
            "port": 3306,
            "service": "MYSQL_HONEYPOT",
            "raw_data": f"[{attack_type}] {data}",
            "timestamp": datetime.now().isoformat()
        }, timeout=2)
    except:
        pass

def analyze_sqli(query):
    q = query.lower()
    attack_type = "Generic SQL"
    risk = 20
    
    if "union" in q and "select" in q:
        attack_type = "Union SQLi"
        risk = 90
    elif re.search(r"(sleep|benchmark|waitfor\s+delay)\s*\(", q):
        attack_type = "Time-based SQLi"
        risk = 95
    elif re.search(r"(extractvalue|updatexml)\s*\(", q) or "floor(rand(" in q:
        attack_type = "Error-based SQLi"
        risk = 85
    elif re.search(r"(\b(and|or)\b\s+\d+=\d+|\b(and|or)\b\s+'.*'='.*')", q):
        attack_type = "Blind SQLi (Boolean)"
        risk = 80
    elif "sqlmap" in q:
        attack_type = "Automated SQLMap"
        risk = 95
        
    return attack_type, risk

# --- Server Logic ---

def handle_client(conn, addr):
    ip = addr[0]
    log_attack(ip, "Connection established to MySQL honeypot", "Connection")
    
    db = setup_fake_db()
    
    try:
        # 1. Server Greeting (MySQL 5.7)
        greeting = b'\x4a\x00\x00\x00\x0a\x35\x2e\x37\x2e\x33\x36\x2d\x6c\x6f\x67\x00\x0c\x00\x00\x00\x4f\x47\x55\x52\x3a\x42\x32\x53\x00\xff\xf7\x08\x02\x00\xff\x81\x15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x61\x47\x4c\x52\x58\x41\x59\x51\x32\x59\x68\x4d\x00\x6d\x79\x73\x71\x6c\x5f\x6e\x61\x74\x69\x76\x65\x5f\x70\x61\x73\x73\x77\x6f\x72\x64\x00'
        conn.sendall(greeting)

        # 2. Receive Auth
        auth = conn.recv(1024)
        if not auth: return
        
        # 3. Send OK
        send_ok(conn, 2)

        # 4. Command Loop
        while True:
            packet = conn.recv(4096)
            if not packet: break
            
            if len(packet) > 4:
                seq = packet[3]
                cmd = packet[4]
                
                if cmd == 0x03: # COM_QUERY
                    query = packet[5:].decode('utf-8', errors='ignore')
                    
                    # Intercept standard driver setup queries
                    if "@@" in query or query.strip().upper().startswith(("SET", "SHOW", "USE")):
                        send_ok(conn, seq + 1)
                        continue
                        
                    attack_type, risk = analyze_sqli(query)
                    log_attack(ip, query, attack_type, risk)
                    
                    try:
                        cursor = db.cursor()
                        cursor.execute(query)
                        if query.strip().upper().startswith(("SELECT", "PRAGMA", "EXPLAIN")):
                            rows = cursor.fetchall()
                            cols = [desc[0] for desc in cursor.description] if cursor.description else ["result"]
                            send_result_set(conn, seq + 1, cols, rows)
                        else:
                            db.commit()
                            send_ok(conn, seq + 1)
                    except sqlite3.Error as e:
                        send_error(conn, seq + 1, str(e))
                        
                elif cmd == 0x01: # COM_QUIT
                    break
                else:
                    send_ok(conn, seq + 1)
    except Exception as e:
        pass
    finally:
        db.close()
        conn.close()

def main():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", 3306))
    server.listen(5)
    print("Fake MySQL Honeypot (Vault-SQL) listening on port 3306")
    
    while True:
        conn, addr = server.accept()
        threading.Thread(target=handle_client, args=(conn, addr)).start()

if __name__ == "__main__":
    main()