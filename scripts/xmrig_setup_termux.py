import os
import time
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed

# ADB binary and device list provided by CellHasher env
ADB = os.environ.get("adb_path", "adb")
devices = os.environ.get("devices", "").split()

# Bash script that runs inside Termux
install_script_content = r'''#!/data/data/com.termux/files/usr/bin/bash
set -e

# Termux real home
export HOME="/data/data/com.termux/files/home"
LOG="$HOME/xmrig_build.log"

mkdir -p "$HOME"

echo "===== XMRIG INSTALL START $(date) =====" | tee "$LOG"
echo "[*] Using HOME=$HOME" | tee -a "$LOG"

echo "[*] Updating Termux packages..." | tee -a "$LOG"
yes '' | pkg upgrade -y 2>&1 | tee -a "$LOG" || true
pkg update -y 2>&1 | tee -a "$LOG"
pkg upgrade -y 2>&1 | tee -a "$LOG" || true

echo "[*] Installing dependencies..." | tee -a "$LOG"
pkg install -y clang make cmake git libuv openssl 2>&1 | tee -a "$LOG" || true

cd "$HOME"

if [ -d "$HOME/xmrig" ]; then
  echo "[*] xmrig exists, pulling latest changes..." | tee -a "$LOG"
  cd "$HOME/xmrig"
  git pull 2>&1 | tee -a "$LOG" || true
else
  echo "[*] Cloning xmrig..." | tee -a "$LOG"
  git clone https://github.com/xmrig/xmrig "$HOME/xmrig" 2>&1 | tee -a "$LOG"
  cd "$HOME/xmrig"
fi

mkdir -p build
cd build

echo "[*] Running cmake WITHOUT hwloc..." | tee -a "$LOG"
cmake -DWITH_HWLOC=OFF .. 2>&1 | tee -a "$LOG"

echo "[*] Building xmrig..." | tee -a "$LOG"
make -j"$(nproc)" 2>&1 | tee -a "$LOG"

BIN_BUILD="$HOME/xmrig/build/xmrig"
BIN_TARGET="$HOME/xmrig/xmrig"

if [ -x "$BIN_BUILD" ]; then
  echo "[OK] xmrig binary built at $BIN_BUILD" | tee -a "$LOG"
  ls -l "$BIN_BUILD" | tee -a "$LOG"

  # Copy binary to ~/xmrig/xmrig
  cp "$BIN_BUILD" "$BIN_TARGET"
  chmod +x "$BIN_TARGET"
  echo "[OK] Copied xmrig to $BIN_TARGET" | tee -a "$LOG"
  ls -l "$BIN_TARGET" | tee -a "$LOG"
else
  echo "[ERROR] Binary not found after build: $BIN_BUILD" | tee -a "$LOG"
fi

echo "===== XMRIG INSTALL END $(date) =====" | tee -a "$LOG"
'''

def install_on_device(device_id: str, script_path: str) -> str:
    try:
        print(f"[{device_id}] Starting xmrig installer...")

        # Stop Termux so we get a clean session
        subprocess.run(
            f"{ADB} -s {device_id} shell am force-stop com.termux",
            shell=True
        )
        time.sleep(1)

        # Push installer script
        remote = "/data/local/tmp/xmrig_install.sh"
        print(f"[{device_id}] Uploading script to {remote}...")
        subprocess.run(
            f'{ADB} -s {device_id} push "{script_path}" "{remote}"',
            shell=True,
            check=True,
        )
        subprocess.run(
            f"{ADB} -s {device_id} shell chmod 755 {remote}",
            shell=True,
            check=True,
        )

        # Launch Termux UI
        print(f"[{device_id}] Launching Termux...")
        subprocess.run(
            f"{ADB} -s {device_id} shell am start -n com.termux/com.termux.app.TermuxActivity",
            shell=True,
        )
        time.sleep(3)

        # Type and run the bash command inside Termux
        # CellHasher uses %s trick to send a space
        cmd = "bash%s/data/local/tmp/xmrig_install.sh"
        print(f"[{device_id}] Executing script inside Termux...")
        subprocess.run(
            f'{ADB} -s {device_id} shell input text "{cmd}"',
            shell=True,
        )
        time.sleep(1)
        subprocess.run(
            f"{ADB} -s {device_id} shell input keyevent 66",  # ENTER
            shell=True,
        )

        print(f"[{device_id}] Install started.")
        return f"[{device_id}] OK"

    except Exception as e:
        print(f"[{device_id}] ERROR: {e}")
        return f"[{device_id}] ERROR: {e}"

# Write bash script to a temp file
with tempfile.NamedTemporaryFile(
    mode="w",
    encoding="utf-8",
    newline="\n",
    delete=False,
    suffix=".sh",
) as f:
    f.write(install_script_content)
    local_script_path = f.name

if not devices:
    print("No devices provided in $devices")
else:
    print(f"Saved xmrig installer to {local_script_path}")
    print("=== Deploying XMRIG Installers ===")

    with ThreadPoolExecutor(max_workers=max(1, len(devices))) as executor:
        futures = {
            executor.submit(install_on_device, d, local_script_path): d
            for d in devices
        }
        for fut in as_completed(futures):
            print(fut.result())

# Cleanup temp file
os.unlink(local_script_path)
print("All installation commands dispatched.")
