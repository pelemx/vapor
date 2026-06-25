import os
import sys
import subprocess
import glob

base_dir = os.path.abspath(".venv/lib/python3.12/site-packages/nvidia")
lib_paths = glob.glob(os.path.join(base_dir, "*", "lib")) + glob.glob(os.path.join(base_dir, "*", "lib64"))

ld_path = ":".join(lib_paths)
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = f"{ld_path}:{env.get('LD_LIBRARY_PATH', '')}"

print("[*] Injecting CUDA Paths:")
for p in lib_paths: print(f" -> {p}")

with open("api.log", "w") as f:
    subprocess.Popen([".venv/bin/python", "batchvapor.py"], env=env, stdout=f, stderr=f, start_new_session=True)
print("[*] API launched in background.")
