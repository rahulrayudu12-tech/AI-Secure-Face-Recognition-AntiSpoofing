"""
AuraID Secure Biometric Facial Authentication Platform
One-Click Local Launcher
"""
import os
import sys
import time
import webbrowser
import threading

def open_browser():
    time.sleep(1.5)
    url = "http://localhost:5000"
    print(f"\n[🚀] Opening AuraID UI in browser: {url}")
    webbrowser.open(url)

def main():
    print("=" * 70)
    print("   🛡️  AURAID SECURE FACE RECOGNITION & ANTI-SPOOFING SYSTEM")
    print("   Next-Generation Biometric Cybersecurity Platform")
    print("=" * 70)
    print("   • Zero-Trust Access Rule: Identity_Match AND Liveness_Verified")
    print("   • Anti-Spoofing: MultiFTNet (2D-FFT) + MiniFASNet + LSTM Temporal")
    print("   • Local Address: http://localhost:5000")
    print("   • Admin Console: http://localhost:5000/dashboard")
    print("   • API Reference: http://localhost:5000/docs")
    print("=" * 70)

    # Launch browser automatically in background
    browser_thread = threading.Thread(target=open_browser, daemon=True)
    browser_thread.start()

    from backend.app import create_app
    from backend.config import Config

    app = create_app()
    app.run(host=Config.HOST, port=Config.PORT, debug=False)

if __name__ == "__main__":
    main()
