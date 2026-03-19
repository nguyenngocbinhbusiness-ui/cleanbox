import os
import shutil
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, shell=True)
    if result.returncode != 0:
        print(f"Error executing command: {cmd}")
        sys.exit(1)

def cleanup():
    print("Cleaning up previous build artifacts...")
    dirs = ['build', 'dist', 'cleanbox.build', 'cleanbox.dist', 'cleanbox.onefile-build']
    for d in dirs:
        if os.path.exists(d):
            try:
                shutil.rmtree(d)
                print(f"Removed {d}")
            except Exception as e:
                print(f"Failed to remove {d}: {e}")

def build_nuitka():
    print("Starting Nuitka build (Standalone Mode)...")
    
    # Ensure dist directory exists
    os.makedirs("dist", exist_ok=True)
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--standalone",
        "--windows-disable-console",
        # "--onefile", # Disabled to fix AV issues and DLL errors
        "--enable-plugin=pyqt6",
        "--include-data-dir=src/assets=assets",
        "--windows-icon-from-ico=src/assets/icon.ico",
        "--company-name=CleanBox Team",
        "--product-name=CleanBox",
        "--file-version=1.0.17",
        "--product-version=1.0.17",
        "--output-dir=dist",
        "--output-filename=CleanBox.exe",
        "--assume-yes-for-downloads",
        "--show-progress",
        
        # Explicitly include packages that often cause DLL errors
        "--include-package=win32api",
        "--include-package=win32file",
        "--include-package=win32con",
        "--include-package=win32com",
        "--include-package=win11toast",
        "--include-package=winshell",
        
        "src/main.py"
    ]
    
    run_command(cmd)
    print("Nuitka build completed successfully.")

def build_installer():
    print("\nChecking for NSIS...")
    makensis_path = shutil.which("makensis")
    
    if not makensis_path:
        # Check default location
        default_path = Path(r"C:\Program Files (x86)\NSIS\makensis.exe")
        if default_path.exists():
            print(f"NSIS found at default location: {default_path}")
            makensis_path = str(default_path)
            
    if makensis_path:
        print("NSIS found. Building installer...")
        
        # Identify source directory (Nuitka output)
        possible_dirs = [
            Path("dist/CleanBox.dist"),
            Path("dist/main.dist"),
            Path("dist/CleanBox.exe") 
        ]
        
        dist_dir = None
        for d in possible_dirs:
            if d.exists() and d.is_dir():
                dist_dir = d
                break
                
        if not dist_dir:
            print("ERROR: Could not find build output directory for installer generation.")
            return

        print(f"Using source directory: {dist_dir}")
        
        # Run NSIS
        # Note: installer.nsi defines output as dist\CleanBox_Setup.exe
        # We pass absolute path for SRC_DIR to be safe
        cmd = f'"{makensis_path}" /DSRC_DIR="{dist_dir.absolute()}" installer.nsi'
        run_command(cmd)
        
    else:
        print("WARNING: 'makensis' not found. Skipping installer generation.")

def main():
    cleanup()
    build_nuitka()
    build_installer()
    
    # Verification
    print("\nVerifying artifacts...")
    artifacts = [
        Path("dist/CleanBox_Setup.exe"),
        Path("dist/CleanBox.dist/CleanBox.exe"),
        Path("dist/main.dist/CleanBox.exe")
    ]
    
    found_any = False
    for p in artifacts:
        if p.exists():
            print(f"[SUCCESS] Artifact found: {p}")
            found_any = True
            
    if not found_any:
        print("\n[FAILURE] No expected artifacts found in dist/.")
        sys.exit(1)

if __name__ == "__main__":
    main()
