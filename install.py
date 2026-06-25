import os
import sys
import subprocess
import urllib.request

# Configuration
MODEL_URL = "https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/inswapper_128.onnx"
MODEL_FILENAME = "inswapper_128.onnx"

def install_requirements():
    print("[*] Phase 1: Installing dependencies from requirements.txt...")
    if not os.path.exists("requirements.txt"):
        print("[!] requirements.txt not found! Please create it first.")
        sys.exit(1)
        
    try:
        # Calls the pip binary bound to the current Python environment safely
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("[+] Dependencies installed successfully.\n")
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to install dependencies. Error: {e}")
        sys.exit(1)

def download_model():
    print("[*] Phase 2: Checking ONNX Model...")
    if os.path.exists(MODEL_FILENAME):
        print(f"[+] {MODEL_FILENAME} already exists. Skipping download.\n")
        return

    print(f"[*] Downloading {MODEL_FILENAME} from HuggingFace...")
    print("[*] File is ~528MB. Please wait...")
    
    try:
        # Safe HTTP request without relying on external curl/wget binaries
        def reporthook(count, block_size, total_size):
            if total_size > 0:
                percent = int(count * block_size * 100 / total_size)
                # Keep it at 100% max
                if percent > 100: percent = 100
                sys.stdout.write(f"\r    -> Downloading: {percent}% ")
                sys.stdout.flush()

        urllib.request.urlretrieve(MODEL_URL, MODEL_FILENAME, reporthook)
        print(f"\n[+] Successfully downloaded {MODEL_FILENAME}.\n")
    except Exception as e:
        print(f"\n[!] Failed to download model: {e}")
        sys.exit(1)

if __name__ == "__main__":
    print("========================================")
    print("   VapourSynth Pipeline Setup Engine    ")
    print("========================================")
    
    install_requirements()
    download_model()
    
    print("========================================")
    print(" [+] Environment Setup Complete!        ")
    print("========================================")
