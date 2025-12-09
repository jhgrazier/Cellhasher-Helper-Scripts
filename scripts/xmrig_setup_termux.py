import subprocess

ADB = "adb"
BASH = "/data/data/com.termux/files/usr/bin/bash"


def list_device_serials():
    out = subprocess.check_output([ADB, "devices"], text=True).splitlines()
    serials = []
    for line in out[1:]:
        parts = line.split()
        if len(parts) == 2 and parts[1] == "device":
            serials.append(parts[0])
    return serials


def run_in_termux(serial, cmd):
    full_cmd = f'{BASH} -l -c "{cmd}"'
    full = [
        ADB,
        "-s",
        serial,
        "shell",
        "run-as",
        "com.termux",
        full_cmd,
    ]

    print(f"[{serial}] > {cmd}")
    proc = subprocess.run(full, capture_output=True, text=True)
    print(f"[{serial}] return code: {proc.returncode}")

    if proc.stdout:
        print(f"[{serial}] STDOUT:\n{proc.stdout}")
    if proc.stderr:
        print(f"[{serial}] STDERR:\n{proc.stderr}")

    return proc.returncode


def setup_xmrig(serial):
    commands = [
        "echo 'Testing Termux environment'",
        "apt update -y",
        "apt upgrade -y",
        "apt install git proot cmake figlet -y",
        "figlet -f small 'Cloning repository'",
        "git clone https://github.com/xmrig/xmrig || true",
        "mkdir -p xmrig/build",
        "cd xmrig/build && figlet -f small 'Compiling xmrig' && cmake -DWITH_HWLOC=OFF .. && make -j$(nproc)",
        "figlet -f small 'Done compiling'",
        "apt remove figlet -y",
        "echo 'Removed extra packages'",
    ]

    for cmd in commands:
        rc = run_in_termux(serial, cmd)
        if rc != 0:
            print(f"[{serial}] Command failed with code {rc}")


def main():
    serials = list_device_serials()
    if not serials:
        print("No devices found by adb")
        return

    for serial in serials:
        print(f"Running xmrig setup on {serial}")
        setup_xmrig(serial)


if __name__ == "__main__":
    main()
