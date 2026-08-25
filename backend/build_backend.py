import sys
import os
import subprocess
import shutil

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
TARGET_BINARIES_DIR = os.path.join(PROJECT_ROOT, "desktop", "src-tauri", "binaries")

def build_standalone_sidecar():
    """Package backend into standalone executable binary using PyInstaller."""
    os.makedirs(TARGET_BINARIES_DIR, exist_ok=True)
    is_mac = sys.platform == "darwin"
    is_win = sys.platform == "win32"

    # Define platform triple for Tauri sidecar naming
    if is_mac:
        sidecar_name = "friday-core-aarch64-apple-darwin" if "arm" in sys.version.lower() or os.uname().machine == "arm64" else "friday-core-x86_64-apple-darwin"
    elif is_win:
        sidecar_name = "friday-core-x86_64-pc-windows-msvc.exe"
    else:
        sidecar_name = "friday-core-x86_64-unknown-linux-gnu"

    entry_point = os.path.join(BACKEND_DIR, "run_backend.py")
    dist_dir = os.path.join(BACKEND_DIR, "dist")
    build_dir = os.path.join(BACKEND_DIR, "build")

    pyinstaller_bin = os.path.join(BACKEND_DIR, "venv", "bin", "pyinstaller")
    if is_win:
        pyinstaller_bin = os.path.join(BACKEND_DIR, "venv", "Scripts", "pyinstaller.exe")
    if not os.path.exists(pyinstaller_bin):
        pyinstaller_bin = "pyinstaller"

    cmd = [
        pyinstaller_bin,
        "--onefile",
        "--name", "friday-core",
        "--distpath", dist_dir,
        "--workpath", build_dir,
        "--clean",
        "--paths", PROJECT_ROOT,
        entry_point
    ]

    print(f"[PyInstaller] Compiling backend into standalone executable: {' '.join(cmd)}")
    subprocess.run(cmd, check=True)

    # Copy output binary to Tauri binaries directory
    source_binary = os.path.join(dist_dir, "friday-core.exe" if is_win else "friday-core")
    target_path = os.path.join(TARGET_BINARIES_DIR, sidecar_name)
    shutil.copy2(source_binary, target_path)

    print(f"[PyInstaller] Standalone backend binary successfully created at: {target_path}")

if __name__ == "__main__":
    build_standalone_sidecar()
