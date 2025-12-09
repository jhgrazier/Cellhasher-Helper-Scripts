import subprocess
from pathlib import Path

ADB = "adb"

TERMUX_PREFIX = "/data/data/com.termux/files/usr"
TERMUX_HOME = f"{TERMUX_PREFIX}/home"
BASH = f"{TERMUX_PREFIX}/bin/bash"

APT = f"{TERMUX_PREFIX}/bin/apt"
GIT = f"{TERMUX_PREFIX}/bin/git"
CMAKE = f"{TERMUX_PREFIX}/bin/cmake"
MAKE = f"{TERMUX_PREFIX}/bin/make"
FIGLET = f"{TERMUX_PREFIX}/bin/figlet"


def list_device_serials():
    out = subprocess.check_output([ADB, "devices"], text=True).splitlines()
    serials = []
    for line in out[1:]:
        parts = line.split()
        if len(parts) == 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def run_in_termux(serial, cmd):
    full_cmd = f'{BASH} -c "{cmd}"'
    args = [
        ADB,
        "-s",
        serial,
        "shell",
        "run-as",
        "com.termux",
        full_cmd,
    ]

    print(f"[{serial}] > {cmd}")
    proc = subprocess.run(args, capture_output=True, text=True)
    rc = proc.returncode

    print(f"[{serial}] return code: {rc}")
    if proc.stdout:
        print(f"[{serial}] STDOUT:\n{proc.stdout}")
    if proc.stderr:
        print(f"[{serial}] STDERR:\n{proc.stderr}")

    log_path = Path(f"xmrig_setup_{serial}.log")
    with log_path.open("a", encoding="utf-8") as fh:
        fh.write("===== COMMAND START =====\n")
        fh.write(f"CMD: {cmd}\n")
        fh.write(f"RETURN CODE: {rc}\n")
        if proc.stdout:
            fh.write("STDOUT:\n" + proc.stdout + "\n")
        if proc.stderr:
            fh.write("STDERR:\n" + proc.stderr + "\n")
        fh.write("===== COMMAND END =====\n\n")

    return rc


def setup_xmrig(serial):
    # Check binaries first
    check_cmd = (
        f"for f in '{APT}' '{GIT}' '{CMAKE}' '{MAKE}' '{FIGLET}'; do "
        "  if [ ! -x \"$f\" ]; then echo \"MISSING_BINARY:$f\"; exit 2; fi; "
        "done; echo 'BINARIES_OK'"
    )
    rc = run_in_termux(serial, check_cmd)
    if rc != 0:
        print(f"[{serial}] One or more required binaries are missing")
        return

    full_script = (
        f"export HOME='{TERMUX_HOME}'; "
        f"export TERMUX_PREFIX='{TERMUX_PREFIX}'; "
        "export PATH=\"$TERMUX_PREFIX/bin:$TERMUX_PREFIX/bin/applets:$PATH\"; "
        "cd \"$HOME\" && "
        f"'{APT}' update -y && "
        f"'{APT}' upgrade -y && "
        f"'{APT}' install -y git proot cmake figlet && "
        f"'{GIT}' clone https://github.com/xmrig/xmrig || true && "
        "cd xmrig && mkdir -p build && cd build && "
        f"'{FIGLET}' Compiling || true && "
        f"'{CMAKE}' -DWITH_HWLOC=OFF .. && "
        f"'{MAKE}' -j\"$(nproc)\" && "
        f"'{FIGLET}' Done || true && "
        f"'{APT}' remove -y figlet || true && "
        "echo 'Build complete'"
    )

    rc = run_in_termux(serial, full_script)
    if rc != 0:
        print(f"[{serial}] XMRig setup FAILED with code {rc}")
    else:
        print(f"[{serial}] XMRig setup completed successfully")


def main():
    serials = list_device_serials()
    if not serials:
        print("No devices detected")
        return

    print("Found devices: " + ", ".join(serials))
    for serial in serials:
        print(f"\n--- Running XMRig setup on {serial} ---")
        setup_xmrig(serial)


if __name__ == "__main__":
    main()
