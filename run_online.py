import subprocess
import time
import re
import urllib.request
import json
import webbrowser
import os
import sys

DIRECTORY = os.path.dirname(os.path.abspath(__file__))
os.chdir(DIRECTORY)

print("=" * 60)
print("  VIETNAM OCR BISTRO - ONLINE CLOUD LAUNCHER")
print("=" * 60)

# Check if server is already running on port 8080
server_running = False
try:
    with urllib.request.urlopen("http://127.0.0.1:8080/api/info", timeout=2) as res:
        if res.status == 200:
            server_running = True
            print("[INFO] Server is already running on port 8080.")
except Exception:
    pass

server_proc = None
if not server_running:
    print("[1/3] Starting python server.py...")
    server_proc = subprocess.Popen([sys.executable, "server.py"], cwd=DIRECTORY)
    time.sleep(1.5)

# Start Cloudflare Tunnel
cloudflared_path = os.path.join(DIRECTORY, "cloudflared.exe")
if not os.path.exists(cloudflared_path):
    print("[ERROR] cloudflared.exe not found.")
    sys.exit(1)

print("[2/3] Connecting to Cloudflare Global Edge Network...")
cf_proc = subprocess.Popen(
    [cloudflared_path, "tunnel", "--url", "http://127.0.0.1:8080"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
    errors="replace"
)

tunnel_url = None
start_time = time.time()
while time.time() - start_time < 30:
    line = cf_proc.stdout.readline()
    if not line and cf_proc.poll() is not None:
        break
    m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
    if m:
        tunnel_url = m.group(0)
        break

if tunnel_url:
    print(f"\n" + "=" * 60)
    print(f" [ONLINE SUCCESS] Public URL generated:")
    print(f" >> {tunnel_url}")
    print(f" Student join: {tunnel_url}/play")
    print("=" * 60 + "\n")
    
    # Update server.py with this custom public URL
    try:
        req = urllib.request.Request(
            "http://127.0.0.1:8080/api/set_public_url",
            data=json.dumps({"url": tunnel_url}).encode("utf-8"),
            headers={"Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=3)
        print("[3/3] QR Code updated to public Cloudflare URL automatically!")
    except Exception as e:
        print("[WARN] Failed to auto-update server public URL:", e)

    # Open teacher browser
    webbrowser.open("http://localhost:8080")
    print("\nTeacher View opened: http://localhost:8080")
    print("QR Code on screen is now 100% SCAN-READY FOR 4G & ANY WI-FI!")
    print("Press Ctrl+C to stop the online tunnel.\n")
    try:
        cf_proc.wait()
    except KeyboardInterrupt:
        print("\nStopping online tunnel...")
        cf_proc.terminate()
        if server_proc:
            server_proc.terminate()
else:
    print("[ERROR] Failed to obtain Cloudflare tunnel URL within 30 seconds.")
    if cf_proc:
        cf_proc.terminate()
    if server_proc:
        server_proc.terminate()
