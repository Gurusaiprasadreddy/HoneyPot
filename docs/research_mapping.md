# Research Objectives Mapping

This document directly maps the final-year project academic research claims to the actual technical implementation within the `Deceptive-HoneyPot` framework. It serves as proof of implementation for academic evaluation.

## 1. Dynamic AI Deception & Context Awareness
**Research Claim:** Traditional honeypots use static responses (e.g., cowrie). Our framework uses an LLM to dynamically generate context-aware responses to attacker inputs, keeping them engaged longer.
**Implementation Evidence:**
- **File:** `honeypots/ssh/ssh_honeypot.py`
- **Mechanism:** When an attacker enters a command over SSH (e.g., `cat /etc/passwd`), the payload is intercepted and forwarded to the local `ollama` container. The LLM generates a realistic, dynamic terminal output which is streamed back to the attacker's terminal.
- **Status:** ✅ Successfully Implemented.

## 2. Immutable Forensic Logging (Blockchain Integration)
**Research Claim:** Logs stored on central servers can be tampered with if an attacker achieves a breakout. We utilize Blockchain technology to ensure forensic integrity.
**Implementation Evidence:**
- **File:** `backend/blockchain/ledger.py` and `contracts/HoneypotLogger.sol`
- **Mechanism:** As soon as an attack payload is analyzed, the FastAPI backend computes a SHA-256 hash of the JSON log. This hash is instantly anchored to a local Ethereum network (Ganache) via a Smart Contract.
- **Status:** ✅ Successfully Implemented (Includes UI Verification).

## 3. Real-Time Threat Intelligence & MITRE ATT&CK Mapping
**Research Claim:** The system automatically categorizes unknown attacks into the industry-standard MITRE ATT&CK framework using Behavioral Intent Analysis.
**Implementation Evidence:**
- **File:** `backend/main.py` (`classify_intent_and_risk` function)
- **Mechanism:** A classification algorithm analyzes raw payloads in real-time. If it detects `union select`, it maps to `T1190` (Exploit Public-Facing Application). If it detects `wget`, it maps to `T1105` (Ingress Tool Transfer).
- **Status:** ✅ Successfully Implemented.

## 4. Multi-Vector Attack Surface (Zero-Trust Simulation)
**Research Claim:** Modern attackers don't just attack SSH. The framework simulates a complete corporate enterprise network.
**Implementation Evidence:**
- **Files:** `honeypots/web`, `honeypots/ssh`, `honeypots/database`, `honeypots/ethereum`, `honeypots/cicd`
- **Mechanism:** 5 totally distinct containerized services run concurrently. A Smart Proxy (`gateway/proxy.py`) intelligently routes external traffic on ports (2222, 3306, 8080, 8545, 9091) to the respective isolated honeypots on the `honeypot-net` bridge network.
- **Status:** ✅ Successfully Implemented.

## 5. Live Dashboard with Session Correlated Metrics
**Research Claim:** Data is visualized in a live SOC (Security Operations Center) dashboard without requiring page reloads.
**Implementation Evidence:**
- **Files:** `frontend/src/components/ThreatAnalytics.jsx`
- **Mechanism:** Uses WebSockets in FastAPI to push newly anchored logs directly to the React frontend. Recharts renders the Live Threat Velocity and MITRE tactics distribution in real-time.
- **Status:** ✅ Successfully Implemented.
