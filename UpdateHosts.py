import os

HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
ENTRIES = [
    "127.0.0.1 onsite.local"
]

def ensure_admin():
    try:
        is_admin = os.getuid() == 0
    except AttributeError:
        # Windows-only check using ctypes
        import ctypes
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

def add_entries():
    with open(HOSTS_PATH, "r") as file:
        lines = file.read().splitlines()

    modified = False
    with open(HOSTS_PATH, "a") as file:
        for entry in ENTRIES:
            if not any(entry in line for line in lines):
                print(f"Adding: {entry}")
                file.write(f"\n{entry}")
                modified = True
            else:
                print(f"Already present: {entry}")

    if modified:
        print("Hosts file updated.")
    else:
        print("No changes needed.")

if __name__ == "__main__":
    if not ensure_admin():
        print("Please run this script as Administrator.")
    else:
        add_entries()
