import os, time, subprocess, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

ADB = os.environ.get("adb_path", "adb")
devices = os.environ.get("devices", "").split()

install_script = r'''#!/data/data/com.termux/files/usr/bin/bash
set -e

HOME="/data/data/com.termux/files/home"
LOG="$HOME/xmrig_build.log"

echo "===== XMRIG INSTALL START $(date) =====" | tee "$LOG"
echo "[*] HOME = $HOME" | tee -a "$LOG"

echo "[*] Forcing repo refresh (non-interactive)" | tee -a "$LOG"
yes | pkg update -y 2>&1 | tee -a "$LOG" || true
yes | pkg upgrade -y 2>&1 | tee -a "$LOG" || true

echo "[*] Installing dependencies..." | tee -a "$LOG"
pkg install -y git clang make cmake openssl libuv 2>&1 | tee -a "$LOG"

mkdir -p "$HOME"

cd "$HOME"

if [ -d "$HOME/xmrig" ]; then
    echo "[*] Updating existing xmrig repo" | tee -a "$LOG"
    cd "$HOME/xmrig"
    git pull 2>&1 | tee -a "$LOG" || true
else
    echo "[*] Cloning xmrig..." | tee -a "$LOG"
    git clone https://github.com/lukewrightmain/xmrig "$HOME/xmrig" 2>&1 | tee -a "$LOG"
    cd "$HOME/xmrig"
fi

mkdir -p build
cd build

echo "[*] Running cmake..." | tee -a "$LOG"
cmake -DWITH_HWLOC=OFF .. 2>&1 | tee -a "$LOG"

echo "[*] Building xmrig (this takes time)..." | tee -a "$LOG"
make -j"$(nproc)" 2>&1 | tee -a "$LOG"

if [ -f "$HOME/xmrig/build/xmrig" ]; then
    echo "[OK] Build complete, installing binary" | tee -a "$LOG"
    cp "$HOME/xmrig/build/xmrig" "$HOME/xmrig/xmrig"
    chmod +x "$HOME/xmrig/xmrig"
else
    echo "[ERROR] Build failed – xmrig binary missing" | tee -a "$LOG"
fi

echo "[*] Creating xmrig_start.sh" | tee -a "$LOG"
cat > "$HOME/xmrig_start.sh" <<EOF
#!/data/data/com.termux/files/usr/bin/bash
cd ~/xmrig
./xmrig -o stratum+tcp://pool.hashvault.pro:443 -u YOUR_WALLET -k -t 8 -a RandomX -p x
EOF

chmod +x "$HOME/xmrig_start.sh"

echo "===== XMRIG INSTALL END $(date) =====" | tee -a "$LOG"
'''

def install_on_device(device_id, script_path):
    try:
        print(f"[{device_id}] Starting xmrig installer")

        subprocess.run(f"{ADB} -s {device_id} shell am force-stop com.termux", shell=True)
        time.sleep(1)

        remote = "/data/local/tmp/xmrig_install.sh"
        subprocess.run(f'{ADB} -s {device_id} push "{script_path}" "{remote}"', shell=True, check=True)
        subprocess.run(f"{ADB} -s {device_id} shell chmod 755 {remote}", shell=True, check=True)

        subprocess.run(f"{ADB} -s {device_id} shell am start -n com.termux/com.termux.app.TermuxActivity", shell=True)
        time.sleep(4)

        cmd = "bash%s/data/local/tmp/xmrig_install.sh"
        subprocess.run(f'{ADB} -s {device_id} shell input text "{cmd}"', shell=True)
        time.sleep(1)
        subprocess.run(f"{ADB} -s {device_id} shell input keyevent 66", shell=True)

        return f"[{device_id}] INSTALL STARTED"

    except Exception as e:
        return f"[{device_id}] ERROR: {e}"

with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="\n", delete=False, suffix=".sh") as f:
    f.write(install_script)
    local_path = f.name

if not devices:
    print("No devices defined in $devices")
else:
    print(f"Installer saved to {local_path}")
    with ThreadPoolExecutor(max_workers=len(devices)) as exe:
        futures = {exe.submit(install_on_device, d, local_path): d for d in devices}
        for fut in as_completed(futures):
            print(fut.result())

os.unlink(local_path)
print("All installer commands sent.")
