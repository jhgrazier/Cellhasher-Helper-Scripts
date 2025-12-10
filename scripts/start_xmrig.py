import os, time, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

ADB = os.environ.get("adb_path", "adb")
devices = os.environ.get("devices", "").split()

start_script_content = r'''#!/data/data/com.termux/files/usr/bin/bash
set -e

export HOME="/data/data/com.termux/files/home"
cd "$HOME"

LOG="$HOME/xmrig_start.log"

echo "===== XMRIG START $(date) =====" | tee "$LOG"
echo "[*] HOME=$HOME" | tee -a "$LOG"

if [ ! -d "$HOME/xmrig" ]; then
  echo "[!] ~/xmrig directory not found" | tee -a "$LOG"
  exit 1
fi

cd "$HOME/xmrig"

BIN=""
if [ -x "$HOME/xmrig/xmrig" ]; then
  BIN="$HOME/xmrig/xmrig"
  echo "[*] Using binary: $BIN" | tee -a "$LOG"
elif [ -x "$HOME/xmrig/build/xmrig" ]; then
  BIN="$HOME/xmrig/build/xmrig"
  echo "[*] Using binary: $BIN" | tee -a "$LOG"
else
  echo "[!] No xmrig binary found in ./ or ./build" | tee -a "$LOG"
  exit 1
fi

echo "[*] Starting miner..." | tee -a "$LOG"
echo "[*] Command:" | tee -a "$LOG"
echo "$BIN -o stratum+tcp://<POOL> -u <WALLET_ADDRESS> -k -t 8 -a RandomX -p x" | tee -a "$LOG"

exec "$BIN" -o stratum+tcp://<POOL> \
  -u <WALLET_ADDRESS> \
  -k -t 8 -a RandomX -p x
'''

def start_on_device(device_id, script_path):
    try:
        print(f"[{device_id}] Preparing to start xmrig...")

        remote = "/data/local/tmp/xmrig_start.sh"
        print(f"[{device_id}] Pushing start script...")
        subprocess.run(f'{ADB} -s {device_id} push "{script_path}" "{remote}"', shell=True, check=True)
        subprocess.run(f"{ADB} -s {device_id} shell chmod 755 {remote}", shell=True, check=True)

        print(f"[{device_id}] Launching Termux...")
        subprocess.run(f"{ADB} -s {device_id} shell am start -n com.termux/com.termux.app.TermuxActivity", shell=True)
        time.sleep(3)

        typed = "bash%s/data/local/tmp/xmrig_start.sh"
        print(f"[{device_id}] Executing xmrig_start.sh inside Termux...")
        subprocess.run(f'{ADB} -s {device_id} shell input text "{typed}"', shell=True)
        time.sleep(1)
        subprocess.run(f"{ADB} -s {device_id} shell input keyevent 66", shell=True)

        print(f"[{device_id}] Start command sent.")
        return f"[{device_id}] OK"

    except Exception as e:
        print(f"[{device_id}] ERROR: {e}")
        return f"[{device_id}] ERROR: {e}"

with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", delete=False, suffix=".sh") as f:
    f.write(start_script_content)
    local_script_path = f.name

if not devices:
    print("No devices in $devices")
else:
    print(f"Saved xmrig start script to {local_script_path}")
    print("=== Starting XMRIG on Devices ===")

    with ThreadPoolExecutor(max_workers=max(1, len(devices))) as executor:
        futures = {executor.submit(start_on_device, d, local_script_path): d for d in devices}
        for fut in as_completed(futures):
            print(fut.result())

os.unlink(local_script_path)
print("All start commands dispatched.")
