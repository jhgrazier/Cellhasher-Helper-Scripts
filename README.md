# Cellhasher-Helper-Scripts
Cellhasher Helper Scripts

## XMRig Termux Builder for Cellhasher

This script installs and compiles XMRig inside Termux on Android devices connected through ADB. You run the script from Cellhasher using the Python Script option.

### Requirements

- ADB installed on your PC.
- Termux installed on each phone.
- USB debugging enabled and authorized.
- Cellhasher installed with ADB path configured.
- Python scripting enabled in Cellhasher.

### Prepare Termux on the phone

Open Termux once on the phone, then run:

termux-setup-storage
pkg update
pkg upgrade

This completes the one-time setup.

### Verify ADB connectivity

On your PC:

adb devices

Your device must appear with the status device.
If it shows unauthorized, unlock the phone and accept the debugging prompt.

### Verify Termux can run through ADB

Run:

adb -s DEVICE_ID shell run-as com.termux id

You should see uid and group information.
If it prints that the package is not debuggable, reinstall Termux from the GitHub release.

### Install the script into Cellhasher

1. Save the Python script as xmrig_setup_termux.py.
2. Open Cellhasher.
3. Go to Scripts.
4. Click Import Script.
5. Choose Python Script (.py).
6. Select the file.

The script will now appear in your script list inside Cellhasher.

### Running the script in Cellhasher

1. Select the target devices in the Devices panel.
2. Select the script.
3. Click Run.
4. Watch the output log for each command and return code.

### What the script does

Inside Termux, the script:

- Updates packages.
- Installs Git, Proot, CMake, and Figlet.
- Clones the XMRig repository.
- Creates the build directory.
- Runs CMake and Make to compile XMRig.
- Removes Figlet to clean up.
- Prints status messages for each step.

All commands execute using:

bash -l -c "command"

The -l flag loads the Termux login environment so apt, git, and other packages work.

### Troubleshooting

#### Commands fail with return code 1

Confirm Termux can run through ADB:

adb -s DEVICE_ID shell run-as com.termux id

If this fails, reinstall Termux.

#### apt or git not found

Check the executable paths:

adb -s DEVICE_ID shell run-as com.termux /data/data/com.termux/files/usr/bin/bash -l -c "which apt"

If no path prints, Termux is not initialized correctly.

#### Build directory already exists

The script skips cloning if the folder exists.
To rebuild from scratch, remove the directory:

rm -rf xmrig

Then rerun the script.

## Notes

- The script can run on multiple devices at once inside Cellhasher.
- Each device builds its own XMRig instance inside Termux.
- You can modify the commands to build other miners or tools.
