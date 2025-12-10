import os, time, subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed

ADB = os.environ.get("adb_path", "adb")
devices = os.environ.get("devices", "").split()
wallet_address = os.environ.get("wallet_address", "")
pool_url = os.environ.get("pool_url", "")
threads = os.environ.get("threads", "8")
algorithm = os.environ.get("algorithm", "")  # Optional algorithm
password = os.environ.get("password", "")  # Optional password/worker name
cpu_max_threads_hint = os.environ.get("cpu_max_threads_hint", "")  # Optional % CPU usage
xmrig_algorithm = os.environ.get("xmrig_algorithm", "")  # XMRIG-specific algorithm (-a flag)
custom_flags = os.environ.get("custom_flags", "")  # Additional custom XMRIG flags
additional_flags = os.environ.get("additional_flags", "")

def run_mining_on_device(device_id):
    """Start XMRIG mining on a single device"""
    try:
        print(f"[{device_id}] Starting XMRIG mining...")

        # Construct the mining command
        mining_cmd = f"./xmrig -o {pool_url} -u {wallet_address} -k -t {threads}"

        # Add XMRIG-specific algorithm if specified (takes precedence over general algorithm)
        if xmrig_algorithm:
            mining_cmd += f" -a {xmrig_algorithm}"
        elif algorithm:
            mining_cmd += f" -a {algorithm}"

        # Add CPU max threads hint only if specified (XMRIG defaults to 100% if not set)
        if cpu_max_threads_hint:
            mining_cmd += f" --cpu-max-threads-hint={cpu_max_threads_hint}"

        # Add password/worker name if provided
        if password:
            mining_cmd += f" -p {password}"

        # Add custom flags if provided
        if custom_flags:
            mining_cmd += f" {custom_flags}"

        print(f"[{device_id}] Mining command: {mining_cmd}")

        print(f"[{device_id}] Force stopping Termux...")
        subprocess.run(f"{ADB} -s {device_id} shell am force-stop com.termux", shell=True)
        time.sleep(2)

        print(f"[{device_id}] Launching Termux...")
        subprocess.run(f"{ADB} -s {device_id} shell am start -n com.termux/com.termux.app.TermuxActivity", shell=True)
        time.sleep(10)  # Wait 10 seconds for Termux to fully initialize

        print(f"[{device_id}] Navigating to xmrig directory...")
        # First navigate to the xmrig directory
        cd_cmd = "cd%sxmrig"
        subprocess.run(f"{ADB} -s {device_id} shell input text \"{cd_cmd}\"", shell=True)
        time.sleep(1)
        subprocess.run(f"{ADB} -s {device_id} shell input keyevent 66", shell=True)
        time.sleep(2)

        # Now run the mining command (without the ~/xmrig/ prefix since we're already in the directory)
        escaped_cmd = mining_cmd.replace(" ", "%s")
        subprocess.run(f"{ADB} -s {device_id} shell input text \"{escaped_cmd}\"", shell=True)
        time.sleep(1)
        subprocess.run(f"{ADB} -s {device_id} shell input keyevent 66", shell=True)

        print(f"[{device_id}] Keeping device screen on...")
        subprocess.run(f"{ADB} -s {device_id} shell svc power stayon true", shell=True)

        print(f"[{device_id}] XMRIG mining initiated successfully!")
        return f"[{device_id}] Mining started"
    except Exception as e:
        print(f"[{device_id}] Error starting mining: {e}")
        return f"[{device_id}] Error: {e}"

print("=== Starting XMRIG Mining (Parallel) ===")

if not devices:
    print("No devices specified in $devices environment variable")
elif not wallet_address:
    print("No wallet address specified in $wallet_address environment variable")
elif not pool_url:
    print("No pool URL specified in $pool_url environment variable")
else:
    # Process all devices in parallel
    with ThreadPoolExecutor(max_workers=len(devices)) as executor:
        future_to_device = {executor.submit(run_mining_on_device, device_id): device_id for device_id in devices}

        for future in as_completed(future_to_device):
            device_id = future_to_device[future]
            try:
                result = future.result()
                print(result)
            except Exception as exc:
                print(f"[{device_id}] Generated an exception: {exc}")

    print("XMRIG mining started on all devices. Check the devices to see the progress.")
