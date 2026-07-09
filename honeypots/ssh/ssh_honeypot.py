import asyncio
import asyncssh
import os
import sys
import aiohttp
import json
import httpx
from datetime import datetime

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:3001")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

sys.path.insert(0, "/app")

async def send_log(attacker_ip, command, response):
    payload = {
        "attacker_ip": attacker_ip,
        "port": 2222,
        "service": "SSH",
        "raw_data": command,
        "response": response,
        "timestamp": datetime.now().isoformat()
    }
    try:
        async with aiohttp.ClientSession() as s:
            await s.post(f"{BACKEND_URL}/api/log", json=payload)
    except Exception as e:
        print(f"Log send failed: {e}")

class VirtualFileSystem:
    def __init__(self):
        self.cwd = "/home/dbadmin"
        self.files = {
            "/home/dbadmin/.bash_history": "ssh root@192.168.1.200\nmysql -u root -p\npg_dump -U postgres corporate_db\n",
            "/home/dbadmin/.ssh/id_rsa": "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEAz/q0QWzK7pL5wO+r+VwL...\n-----END RSA PRIVATE KEY-----",
            "/home/dbadmin/.ssh/authorized_keys": "ssh-rsa AAAAB3NzaC1yc2E... admin@corp",
            "/home/dbadmin/db_scripts/backup.sh": "#!/bin/bash\npg_dump -U postgres corporate_db > /tmp/backup.sql\n",
            "/etc/passwd": "root:x:0:0:root:/root:/bin/bash\ndaemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\nubuntu:x:1000:1000:Ubuntu:/home/ubuntu:/bin/bash\ndbadmin:x:1001:1001:DB Admin:/home/dbadmin:/bin/bash\npostgres:x:1002:1002::/var/lib/postgresql:/bin/bash",
            "/etc/shadow": "root:$6$fakehash123$abc:19700:0:99999:7:::\ndbadmin:$6$fakehash456$xyz:19700:0:99999:7:::",
            "/etc/environment": "AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE\nAWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY\nDB_PASS=SuperSecretDBPass123!\n",
            "/etc/hosts": "127.0.0.1 localhost\n192.168.1.200 db-primary.corp.internal\n",
            "/etc/os-release": "NAME=\"Ubuntu\"\nVERSION=\"22.04.3 LTS (Jammy Jellyfish)\"\nID=ubuntu\n",
            "/var/log/auth.log": "Jun 23 14:30:00 corp-prod-db-01 sshd[1234]: Accepted publickey for dbadmin from 10.0.0.55\n",
            "/tmp/backup_20250620.tar.gz": "<binary data>"
        }
        self.dirs = [
            "/", "/bin", "/boot", "/dev", "/etc", "/home", "/home/dbadmin", 
            "/home/dbadmin/.ssh", "/home/dbadmin/db_scripts", "/home/ubuntu", 
            "/lib", "/opt", "/proc", "/root", "/run", "/sys", "/tmp", "/usr", 
            "/var", "/var/log"
        ]

    def resolve(self, path):
        if not path:
            return self.cwd
        if path.startswith("/"):
            res = path
        else:
            res = os.path.normpath(os.path.join(self.cwd, path)).replace("\\", "/")
        if res.endswith("/") and len(res) > 1:
            res = res[:-1]
        return res

    def get_contents(self, target):
        contents = set()
        for d in self.dirs:
            if d.startswith(target + "/") and len(d.split("/")) == len(target.split("/")) + 1:
                contents.add(d.split("/")[-1])
        for f in self.files:
            if f.startswith(target + "/") and len(f.split("/")) == len(target.split("/")) + 1:
                contents.add(f.split("/")[-1])
        return contents

    def execute(self, cmd_line):
        parts = cmd_line.strip().split()
        if not parts:
            return ""
        
        cmd = parts[0]
        args = parts[1:]

        if cmd == "pwd":
            return self.cwd
        
        if cmd == "cd":
            target = self.resolve(args[0] if args else "/home/dbadmin")
            if target in self.dirs or self.get_contents(target):
                self.cwd = target
                return ""
            return f"bash: cd: {args[0]}: No such file or directory"
        
        if cmd == "ls":
            target = self.resolve(args[-1] if args and not args[-1].startswith("-") else self.cwd)
            contents = self.get_contents(target)
            if not contents and target not in self.dirs:
                if target in self.files:
                    return args[-1]
                return f"ls: cannot access '{args[-1]}': No such file or directory"
            return "  ".join(sorted(contents))
            
        if cmd == "cat":
            if not args:
                return ""
            target = self.resolve(args[0])
            if target in self.files:
                if "shadow" in target or "root" in target:
                    return f"cat: {args[0]}: Permission denied"
                return self.files[target]
            if target in self.dirs:
                return f"cat: {args[0]}: Is a directory"
            return f"cat: {args[0]}: No such file or directory"
            
        if cmd == "touch":
            if not args: return "touch: missing file operand"
            target = self.resolve(args[0])
            if target not in self.files and target not in self.dirs:
                self.files[target] = ""
            return ""
            
        if cmd == "rm":
            if not args: return "rm: missing operand"
            target = self.resolve(args[-1])
            if target in self.files:
                del self.files[target]
                return ""
            if target in self.dirs:
                return f"rm: cannot remove '{args[-1]}': Is a directory"
            return f"rm: cannot remove '{args[-1]}': No such file or directory"
            
        if cmd == "mkdir":
            if not args: return "mkdir: missing operand"
            target = self.resolve(args[0])
            if target not in self.dirs:
                self.dirs.append(target)
            return ""

        if cmd == "whoami": return "dbadmin"
        if cmd == "id": return "uid=1001(dbadmin) gid=1001(dbadmin) groups=1001(dbadmin),27(sudo)"
        if cmd == "hostname": return "corp-prod-db-01"
        if cmd == "env" or cmd == "printenv": return self.files["/etc/environment"] + f"\nPWD={self.cwd}\nUSER=dbadmin\nHOME=/home/dbadmin"
        if cmd == "history": return self.files["/home/dbadmin/.bash_history"]
        if cmd == "uname": return "Linux corp-prod-db-01 5.15.0-91-generic #101-Ubuntu SMP x86_64 GNU/Linux"
        if cmd == "ifconfig" or cmd == "ip": return "eth0: inet 192.168.1.105 netmask 255.255.255.0\nlo: inet 127.0.0.1"
        
        return None # signal to use LLM

class HoneypotSession(asyncssh.SSHServerSession):
    def __init__(self, peer_addr):
        self.peer_addr = peer_addr
        self.vfs = VirtualFileSystem()
        self.history = []
        self.buffer = ""

    def shell_requested(self):
        return True

    def connection_made(self, chan):
        self._chan = chan
        chan.write("\r\nWelcome to Ubuntu 22.04.3 LTS (GNU/Linux 5.15.0-91-generic x86_64)\r\n")
        chan.write(f"Last login: {datetime.now().strftime('%a %b %d %H:%M:%S %Y')} from {self.peer_addr}\r\n")
        chan.write(f"dbadmin@corp-prod-db-01:{self.vfs.cwd}$ ")

    def data_received(self, data, datatype):
        self.buffer += data
        if "\n" in self.buffer or "\r" in self.buffer:
            cmd = self.buffer.strip()
            self.buffer = ""
            if cmd:
                asyncio.create_task(self._process(cmd))
            else:
                self._chan.write(f"\r\ndbadmin@corp-prod-db-01:{self.vfs.cwd}$ ")

    async def get_llm_response(self, command):
        try:
            prompt = f"You are an Ubuntu 22.04 terminal. User is dbadmin. Current directory is {self.vfs.cwd}. Reply ONLY with the terminal output for the command: {command}"
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(f"{OLLAMA_HOST}/api/generate", json={
                    "model": "llama3",
                    "prompt": prompt,
                    "stream": False,
                    "options": {"temperature": 0.2, "num_predict": 200}
                })
                return resp.json().get("response", f"bash: {command}: command not found")
        except:
            return f"bash: {command}: command not found"

    async def _process(self, command):
        if command in ("exit", "logout", "quit"):
            self._chan.write("\r\nlogout\r\n")
            self._chan.close()
            return
            
        # Append to fake bash history
        self.vfs.files["/home/dbadmin/.bash_history"] += command + "\n"

        # Check VFS first
        response = self.vfs.execute(command)
        
        # Fallback to LLM if VFS doesn't handle it
        if response is None:
            # Check for output redirection
            if ">" in command:
                parts = command.split(">", 1)
                cmd_part = parts[0].strip()
                file_part = parts[1].strip().split()[0]
                llm_out = await self.get_llm_response(cmd_part)
                self.vfs.files[self.vfs.resolve(file_part)] = llm_out
                response = ""
            else:
                response = await self.get_llm_response(command)
        
        # Clean up response for terminal display
        if response:
            response = response.replace("\n", "\r\n")
            self._chan.write(f"\r\n{response}")
            
        await send_log(self.peer_addr, command, response)
        self._chan.write(f"\r\ndbadmin@corp-prod-db-01:{self.vfs.cwd}$ ")

    def connection_lost(self, exc):
        print(f"[SSH] Session ended: {self.peer_addr}")

class HoneypotServer(asyncssh.SSHServer):
    def connection_made(self, conn):
        self._conn = conn
        self._peer = conn.get_extra_info("peername")[0]
        print(f"[SSH] Connection from {self._peer}")

    def begin_auth(self, username):
        return True

    def password_auth_supported(self):
        return True

    async def validate_password(self, username, password):
        print(f"[SSH] Auth attempt: {username}:{password} from {self._peer}")
        await send_log(self._peer, f"LOGIN:{username}:{password}", "accepted")
        return True

    def session_requested(self):
        return HoneypotSession(self._peer)

async def main():
    key_dir  = "/app/keys"
    key_path = f"{key_dir}/ssh_host_key"
    os.makedirs(key_dir, exist_ok=True)

    if not os.path.exists(key_path):
        key = asyncssh.generate_private_key("ssh-rsa", key_size=2048)
        key.write_private_key(key_path)
        print("[SSH] New host key generated and saved.")

    await asyncssh.create_server(
        HoneypotServer, "", 2223,
        server_host_keys=[key_path]
    )
    print("[SSH] Shadow-Shell honeypot running on port 2223")
    await asyncio.get_event_loop().create_future()

if __name__ == "__main__":
    asyncio.run(main())