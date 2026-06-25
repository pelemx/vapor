import os
import signal
import sys

port_hex = "1CD8"
inodes = []

for file in ['/proc/net/tcp', '/proc/net/tcp6']:
    if os.path.exists(file):
        with open(file, 'r') as f:
            for line in f.readlines()[1:]:
                parts = line.split()
                if len(parts) > 9 and parts[1].endswith(f":{port_hex}"):
                    inodes.append(parts[9])

if not inodes:
    print("[*] Port 7384 is free. No locks detected.")
    sys.exit(0)

for p in os.listdir('/proc'):
    if p.isdigit():
        try:
            fd_dir = f"/proc/{p}/fd"
            if os.access(fd_dir, os.R_OK):
                for fd in os.listdir(fd_dir):
                    link = os.readlink(f"{fd_dir}/{fd}")
                    if any(f"socket:[{i}]" in link for i in inodes):
                        os.kill(int(p), signal.SIGKILL)
                        print(f"[+] Surgical strike: Terminated PID {p} holding port 7384")
        except Exception:
            pass
