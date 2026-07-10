# Grafana Performance Dashboard: Setup & Usage Guide

## 1. What is the Grafana Dashboard?
In this AI-Driven Deceptive Security Framework, there are **two** distinct dashboards, each serving a critical but different purpose:

1. **The React SOC Dashboard (`localhost:3000`):** Focuses on **Threat Intelligence**. It shows who is attacking, what their intent is, where they are from, and their MITRE ATT&CK categorization.
2. **The Grafana Dashboard (`localhost:3003`):** Focuses on **Infrastructure & Performance**. It acts as the "health monitor" for the entire honeypot system. It tracks how much stress the system is under (Throughput) and how fast the AI and Blockchain are responding to attacks (Latency).

---

## 2. How to Access and Log In
Grafana runs as an isolated Docker container within the project's secure network.

1. **URL:** Open your web browser and go to [http://localhost:3003](http://localhost:3003)
2. **Login Credentials:**
   - **Username:** `admin`
   - **Password:** `admin`
3. *Note: Upon first login, Grafana will ask you to change your password. You can enter a new one or click **Skip**.*

---

## 3. Connecting the Data Source (Prometheus)
Grafana is purely a visualization tool; it needs a database to pull metrics from. The project uses **Prometheus** (running in the background) to scrape metrics from the backend every 5 seconds.

**To connect them:**
1. In Grafana, go to the left sidebar menu and click **Connections** (or the ⚙️ Gear icon) > **Data Sources**.
2. Click the blue **Add data source** button and select **Prometheus**.
3. In the **Connection URL** field, enter: `http://prometheus:9090` *(This works because both containers are on the same `honeypot-net` Docker network).*
4. Scroll to the bottom and click **Save & test**. A green checkmark will confirm the connection.

---

## 4. How to View Live Metrics
Once connected, click the **Explore** tab (🧭 compass icon on the left). Ensure the switch in the top right is set to **Code** (not Builder). You can paste the following PromQL (Prometheus Query Language) commands to visualize system performance:

### A. System Throughput (Requests Per Second)
Tracks the raw volume of attacks hitting the honeypots and backend API.
> **Query:** `rate(honeypot_requests_total[1m])`
> **Usage:** If this graph spikes massively (e.g., thousands of requests per second), it indicates an attacker is attempting a **DDoS (Distributed Denial of Service)** attack to crash the honeypot framework.

### B. Backend API Latency
Tracks how fast the backend FastAPI server processes incoming attack logs.
> **Query:** `rate(honeypot_request_latency_seconds_sum[1m]) / rate(honeypot_request_latency_seconds_count[1m])`
> **Usage:** Ensures the central brain of the system is not bottlenecking under heavy attack loads. 

### C. AI Inference Latency
Tracks exactly how many milliseconds the Python classification engine (and Llama3) takes to parse a raw payload and map it to a MITRE ATT&CK category.
> **Query:** `rate(honeypot_ai_inference_seconds_sum[1m]) / rate(honeypot_ai_inference_seconds_count[1m])`
> **Usage:** Critical for proving that the AI evaluation happens in near real-time, allowing the framework to respond to attackers before they realize they are in a honeypot.

### D. Blockchain Anchoring Latency
Tracks the time taken to hash the attack log and wait for the local Ethereum (Ganache) blockchain to confirm the transaction block.
> **Query:** `rate(honeypot_blockchain_tx_seconds_sum[1m]) / rate(honeypot_blockchain_tx_seconds_count[1m])`
> **Usage:** Demonstrates the performance cost of cryptographic security. If this is too high, the system might lag behind live attacks.

*(Tip: You can click "Add to dashboard" in the Explore tab to save these graphs permanently into a beautiful, multi-panel dashboard!)*

---

## 5. Why is this Dashboard Important for the Project?
While the React Dashboard shows *what* the attackers are doing, the Grafana dashboard proves *how well* your framework is surviving the attacks. 

In a real Enterprise SOC (Security Operations Center), security tools are often targeted first by hackers trying to blind the defenders. By including Grafana, this project demonstrates **production-grade observability**, proving that the Honeypot Framework is resilient, scalable, and actively monitored for performance degradation during high-intensity cyber warfare.
