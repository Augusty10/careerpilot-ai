import os
import sys
import time
import subprocess
import socket

def wait_for_port(port, timeout=25):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=1):
                return True
        except (socket.timeout, ConnectionRefusedError, OSError):
            time.sleep(0.5)
    return False

def main():
    print("=" * 60)
    print("CareerPilot AI - Automated Walkthrough Orchestrator")
    print("=" * 60)

    env = os.environ.copy()
    env["USE_MOCK_DB"] = "true"
    env["FLASK_DEBUG"] = "False"
    env["PYTHONUNBUFFERED"] = "1"

    # 1. Start backend with virtualenv python
    py_exec = os.path.abspath(".venv/Scripts/python.exe")
    backend_cmd = [py_exec, "backend/app.py"]
    print("Starting Flask backend on port 5000...")
    backend_proc = subprocess.Popen(
        backend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        env=env
    )

    if not wait_for_port(5000, timeout=25):
        print("ERROR: Backend failed to start on port 5000")
        backend_proc.terminate()
        try:
            out, _ = backend_proc.communicate(timeout=3)
            print("Backend output:\n", out)
        except Exception:
            pass
        sys.exit(1)
    print("Backend is ready on http://127.0.0.1:5000")

    # 2. Start frontend dev server
    frontend_cmd = ["npm.cmd", "run", "dev", "--prefix", "frontend", "--", "--port", "5173", "--host"]
    print("Starting Vite frontend on port 5173...")
    frontend_proc = subprocess.Popen(
        frontend_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )

    if not wait_for_port(5173, timeout=25):
        print("ERROR: Frontend failed to start on port 5173")
        if frontend_proc.poll() is not None:
            out, _ = frontend_proc.communicate()
            print("Frontend output:", out)
        backend_proc.terminate()
        frontend_proc.terminate()
        sys.exit(1)
    print("Frontend is ready on http://127.0.0.1:5173")
    time.sleep(2)

    # 3. Run walkthrough script
    if "--m1" in sys.argv:
        walkthrough_file = "frontend/run_walkthrough.js"
    elif "--m2" in sys.argv:
        walkthrough_file = "frontend/run_walkthrough_m2.js"
    elif "--m3" in sys.argv:
        walkthrough_file = "frontend/run_walkthrough_m3.js"
    elif "--m4" in sys.argv:
        walkthrough_file = "frontend/run_walkthrough_m4.js"
    else:
        walkthrough_file = "frontend/run_walkthrough_m5.js"

    print(f"\nRunning Puppeteer Browser Walkthrough ({walkthrough_file})...")
    walkthrough_cmd = ["node", walkthrough_file]
    res = subprocess.run(walkthrough_cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print("STDERR:", res.stderr)

    # 4. Clean up processes
    print("\nShutting down dev servers...")
    backend_proc.terminate()
    frontend_proc.terminate()
    try:
        backend_proc.wait(timeout=3)
    except Exception:
        backend_proc.kill()
    try:
        frontend_proc.wait(timeout=3)
    except Exception:
        frontend_proc.kill()

    if res.returncode == 0:
        print("\nAll Walkthrough Steps & Screenshots Completed Successfully!")
    else:
        print("\nWalkthrough exited with errors.")
        sys.exit(res.returncode)

if __name__ == "__main__":
    main()
