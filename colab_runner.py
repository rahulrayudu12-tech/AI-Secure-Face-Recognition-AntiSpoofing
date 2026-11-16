"""
Google Colab Launch Helper for AuraID Face Recognition & Anti-Spoofing System
Exposes the local Flask server to the internet using localtunnel or Colab native port forwarding.
"""
import subprocess
import time
import threading
import sys
import os

def start_server():
    os.environ["HOST"] = "127.0.0.1"
    os.environ["PORT"] = "5000"
    from backend.app import create_app
    app = create_app()
    app.run(host="127.0.0.1", port=5000, debug=False, use_reloader=False)

def run_colab():
    print("=" * 70)
    print("🚀 AURAID AI SECURE FACE RECOGNITION & ANTI-SPOOFING SYSTEM")
    print("=" * 70)
    print("[*] Starting backend service on port 5000...")
    
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(3)
    
    print("[✓] Backend server is running!")
    print("\n" + "=" * 70)
    print("🌐 EXPOSING PUBLIC TUNNEL FOR GOOGLE COLAB WEBCAM ACCESS")
    print("=" * 70)
    
    # Try localtunnel
    try:
        print("[*] Launching localtunnel...")
        tunnel_proc = subprocess.Popen(
            ["npx", "localtunnel", "--port", "5000"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        for line in tunnel_proc.stdout:
            if "your url is:" in line.lower():
                print(f"\n👉 OPEN YOUR AURAID UI HERE: {line.strip()}\n")
                break
    except Exception as e:
        print(f"[!] Localtunnel note: {e}")
        print("[*] Alternatively, in Google Colab use:")
        print("    from google.colab.output import eval_js")
        print("    print(eval_js(\"google.colab.kernel.proxyPort(5000)\"))")

    print("[*] Press Ctrl+C in Colab to terminate server.")
    while True:
        time.sleep(1)

if __name__ == "__main__":
    run_colab()
