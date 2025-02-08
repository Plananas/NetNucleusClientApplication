import os
import sys
import subprocess
import time
import tkinter as tk
from tkinter import messagebox
import win32serviceutil

SERVICE_NAME = "NetworkAutomationClient"
DISPLAY_NAME = "Network Automation Client"
CONFIG_DIR = os.path.join(os.environ.get("ProgramData", ""), "NetworkAutomationClient")
CONFIG_FILE = os.path.join(CONFIG_DIR, "client.config")

def save_ip_address(ip_address):
    if not os.path.exists(CONFIG_DIR):
        os.makedirs(CONFIG_DIR)
    with open(CONFIG_FILE, "w") as f:
        f.write(f"IP_ADDRESS={ip_address}\n")

def is_service_installed(service_name):
    try:
        win32serviceutil.QueryServiceStatus(service_name)
        return True
    except Exception:
        return False

#TODO why wont this run
def install_service():
    try:
        script = sys.argv[0]
        subprocess.check_call([sys.executable, script, 'install'])
        print("Service installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to install service. Error: {e}")

def uninstall_service():
    try:
        script = sys.argv[0]
        subprocess.check_call([sys.executable, script, 'remove'])
        print("Service uninstalled successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to uninstall service. Error: {e}")

def start_service():
    try:
        script = sys.argv[0]
        subprocess.check_call([sys.executable, script, 'start'])
        print("Service started successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to start service. Error: {e}")

def stop_service():
    try:
        script = sys.argv[0]
        subprocess.check_call([sys.executable, script, 'stop'])
        print("Service stopped successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to stop service. Error: {e}")

def install_and_run_service(root):
    try:
        install_service()
        time.sleep(5)
        start_service()
        messagebox.showinfo("Success", "Service installed and started.")
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to install and start.\n\n{e}")

def uninstall_service_gui(root):
    try:
        stop_service()
        uninstall_service()
        messagebox.showinfo("Success", "Service stopped/uninstalled.")
        root.destroy()
    except Exception as e:
        messagebox.showerror("Error", f"Failed to uninstall.\n\n{e}")

def validate_ip(ip_address):
    parts = ip_address.split(".")
    if len(parts) != 4:
        return False
    for part in parts:
        try:
            if not (0 <= int(part) <= 255):
                return False
        except ValueError:
            return False
    return True

def set_ip_address_gui(ip_entry):
    ip_address = ip_entry.get().strip()
    if not ip_address:
        messagebox.showerror("Error", "Please enter an IP address.")
        return

    if not validate_ip(ip_address):
        messagebox.showerror("Error", "Invalid IP address format.")
        return

    save_ip_address(ip_address)
    messagebox.showinfo("Success", f"IP address set to {ip_address}")

def main_window():
    root = tk.Tk()
    root.title("Service Manager")
    root.geometry("400x300")

    tk.Label(root, text="Enter the server IP address:", font=("Arial", 12)).pack(pady=10)
    ip_entry = tk.Entry(root, font=("Arial", 12), width=30)
    ip_entry.pack(pady=5)

    tk.Button(root,
              text="Set IP Address",
              command=lambda: set_ip_address_gui(ip_entry)
              ).pack(pady=10)

    tk.Button(root,
              text="Install and Start Service",
              command=lambda: install_and_run_service(root)
              ).pack(pady=10)

    tk.Button(root,
              text="Uninstall and Stop Service",
              command=lambda: uninstall_service_gui(root)
              ).pack(pady=10)

    tk.Button(root, text="Exit", command=root.destroy).pack(pady=20)
    root.mainloop()

def main():
    # Check if the user gave any of the service arguments
    service_commands = {"install", "start", "stop", "remove"}
    # Intersect the service_commands set with arguments provided (excluding the script name)
    if service_commands.intersection(sys.argv[1:]):
        # If there's a service command, don't open the GUI window.
        # Just handle any normal or advanced service logic here if needed.
        pass
    else:
        # If no service command is given, open the GUI
        main_window()

if __name__ == "__main__":
    main()
