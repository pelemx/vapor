import os
import subprocess
import sys
import glob

LOCAL_ROOT = os.path.join(os.getcwd(), "vs_hijack")
os.makedirs(LOCAL_ROOT, exist_ok=True)

def run_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)

print("[*] 1. Locating VapourSynth packages...")
out = run_cmd(["apt-cache", "depends", "libvapoursynth-dev"])
deps = ["vapoursynth", "libvapoursynth-dev"]

# Dynamically find the versioned library (e.g., libvapoursynth-60)
for line in out.stdout.split('\n'):
    if "Depends:" in line and "libvapoursynth" in line:
        pkg = line.split("Depends:")[1].strip()
        if pkg not in deps: deps.append(pkg)

print(f"[*] 2. Downloading packages locally: {deps}")
for pkg in deps:
    subprocess.run(["apt-get", "download", pkg])

print("[*] 3. Extracting shared objects (.so) and headers...")
for deb in glob.glob("*.deb"):
    subprocess.run(["dpkg", "-x", deb, LOCAL_ROOT])

print("[*] 4. Forcing compiler paths...")
lib_paths = glob.glob(f"{LOCAL_ROOT}/usr/lib/*linux-gnu*")
lib_path = lib_paths[0] if lib_paths else f"{LOCAL_ROOT}/usr/lib"
inc_path = f"{LOCAL_ROOT}/usr/include"

env = os.environ.copy()
env["C_INCLUDE_PATH"] = inc_path
env["CPLUS_INCLUDE_PATH"] = inc_path
env["LIBRARY_PATH"] = lib_path
env["LD_LIBRARY_PATH"] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}"

print("[*] 5. Compiling VapourSynth Wheel...")
subprocess.run([sys.executable, "-m", "pip", "install", "vapoursynth"], env=env)

print("\n[+] Hijack complete.")
