import os
import subprocess
import shutil
import platform
import time
import urllib.request

BASE_URL = "https://github.com/Ultimaker/Cura/releases/download/5.9.0"

def find_cura_path():
    system = platform.system()

    if system == "Windows":
        program_files_dirs = [os.getenv("PROGRAMFILES"), os.getenv("PROGRAMFILES(X86)")]
        for base_dir in program_files_dirs:
            if base_dir:
                for folder in os.listdir(base_dir):
                    if "cura" in folder.lower():
                        return os.path.join(base_dir, folder)
        return None

    elif system == "Darwin":
        return next((os.path.join("/Applications", folder) for folder in os.listdir("/Applications") if "cura" in folder.lower()), None)

    return None

def uninstall_cura(cura_path):
    system = platform.system()

    if system == "Windows":
        uninstall_exe = os.path.join(cura_path, "uninstall.exe")
        if os.path.exists(uninstall_exe):
            subprocess.run([uninstall_exe, "/S"], shell=True)
        else:
            print("Uninstall executable not found. Skipping uninstall.")
    elif system == "Darwin":  # macOS
        if os.path.exists(cura_path):
            subprocess.run(["rm", "-rf", cura_path], check=True)

def download_cura_installer(system):
    print("Downloading Cura installer...")
    if system == "Windows":
        installer_name = "UltiMaker-Cura-5.9.0-win64-X64.exe"
    elif system == "Darwin":
        arch = subprocess.check_output(["uname", "-m"]).strip().decode()
        if arch == "arm64":
            installer_name = "UltiMaker-Cura-5.9.0-macos-ARM64.dmg"
        else:
            installer_name = "UltiMaker-Cura-5.9.0-macos-X64.dmg"
    else:
        print("Unsupported operating system.")
        exit(1)

    url = f"{BASE_URL}/{installer_name}"
    installer_path = os.path.join(os.path.expanduser('~'), 'Downloads', installer_name)
    urllib.request.urlretrieve(url, installer_path)
    print("Download completed.")
    return installer_path

def install_cura(system):
    print("Installing Cura...")
    installer_path = download_cura_installer(system)

    if system == "Windows":
        result = subprocess.run([installer_path, "/S"], shell=True)  # Silent install
        if result.returncode != 0:
            print("Installation failed.")
            exit(1)

        # Verify installation
        cura_path = find_cura_path()
        if not cura_path:
            print("Installation verification failed. Cura is not detected after installation.")
            exit(1)
        print("Done.")
        return cura_path

    elif system == "Darwin":  # macOS
        subprocess.run(["hdiutil", "attach", installer_path], check=True)
        subprocess.run(["cp", "-r", "/Volumes/Ultimaker Cura/Ultimaker Cura.app", "/Applications"], check=True)
        subprocess.run(["hdiutil", "detach", "/Volumes/Ultimaker Cura"], check=True)

        # Verify installation
        cura_path = find_cura_path()
        if not cura_path:
            print("Installation verification failed. Cura is not detected after installation.")
            exit(1)
        print("Done.")
        return cura_path

def clean_old_versions():
    system = platform.system()

    if system == "Windows":
        appdata_path = os.path.expandvars(r"%APPDATA%\cura")
        local_appdata_path = os.path.expandvars(r"%LOCALAPPDATA%\cura")
    elif system == "Darwin":  # macOS
        appdata_path = os.path.expanduser("~/Library/Application Support/cura")
        local_appdata_path = None

    # Remove entire Cura folders
    if os.path.exists(appdata_path):
        shutil.rmtree(appdata_path)
    if local_appdata_path and os.path.exists(local_appdata_path):
        shutil.rmtree(local_appdata_path)

def open_cura(cura_path):
    system = platform.system()
    if system == "Windows":
        cura_exe_path = os.path.join(cura_path, "UltiMaker-Cura.exe")
        if not os.path.exists(cura_exe_path):
            print("Could not find Cura executable.")
            exit(1)
        subprocess.Popen([cura_exe_path], shell=True)
    elif system == "Darwin":
        if not os.path.exists(cura_path):
            print("Could not find Cura application.")
            exit(1)
        subprocess.Popen(["open", "-a", cura_path])

def open_cura_with_file(file_path, cura_path):
    system = platform.system()
    if system == "Windows":
        cura_exe_path = os.path.join(cura_path, "UltiMaker-Cura.exe")
        if not os.path.exists(cura_exe_path):
            print("Could not find Cura executable.")
            exit(1)
        subprocess.Popen([cura_exe_path, file_path], shell=True)
    elif system == "Darwin":
        if not os.path.exists(cura_path):
            print("Could not find Cura application.")
            exit(1)
        subprocess.Popen(["open", "-a", cura_path, file_path])

def wait_for_cura_to_close():
    system = platform.system()
    cura_process_name = "Cura" if system == "Darwin" else "Cura.exe"

    while True:
        if system == "Windows":
            result = subprocess.run(["tasklist"], capture_output=True, text=True)
            if cura_process_name not in result.stdout:
                break
        elif system == "Darwin":
            result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
            if cura_process_name not in result.stdout:
                break
        time.sleep(5)

def upgrade_cura_windows():
    print("Upgrading Cura using winget...")
    result = subprocess.run(["winget", "upgrade", "--id", "Ultimaker.Cura", "--silent"], shell=True)
    if result.returncode != 0:
        print("Upgrade failed. (Or up to date)")
        exit(1)

if __name__ == "__main__":
    print("\n\nWARNING: This script will remove all of your Cura metadata and replace it with the defaults and the SEP environment. Do you want to continue? (y/n)")
    choice = input().strip().lower()
    if choice != 'y':
        print("Aborting script.")
        exit(0)

    print("Accept all OS dialogs. Then, this script will open Cura three times. First time you will need to add a random offline printer, and get through the welcome dialogs. Do not upgrade Cura if asked. Then exit Cura to continue. The following times, select 'Import as project' when the dialog asks if you would like to import all settings and models from the project file, then close Cura.")
    input("\nPress any key to continue...\n")

    first_file = "AquilaEmptyProjectToImportPrinterAndProfile.3mf"
    second_file = "Cr10EmptyProjectToImportPrinterAndProfile.3mf"

    if not os.path.exists(first_file):
        print(f"File {first_file} not found in the current directory.")
        exit(1)

    if not os.path.exists(second_file):
        print(f"File {second_file} not found in the current directory.")
        exit(1)

    cura_path = find_cura_path()
    if cura_path:
        uninstall_cura(cura_path)
        clean_old_versions()

    system = platform.system()
    cura_path = install_cura(system)

    open_cura(cura_path)
    wait_for_cura_to_close()

    open_cura_with_file(os.path.join(os.getcwd(), first_file), cura_path)
    wait_for_cura_to_close()

    open_cura_with_file(os.path.join(os.getcwd(), second_file), cura_path)
    wait_for_cura_to_close()

    if system == "Windows":
        upgrade_cura_windows()
