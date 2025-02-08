import os
import subprocess
import re
import shutil
import sys


def shutdown():
    #os.system('shutdown -s')#
    #TODO set shutdown status
    return "Shutdown is deactivated"

#Scoop Functions
def get_all_software():
    print("Getting all installed software...")

    try:
        result = subprocess.run('scoop list', shell=True, check=True, capture_output=True, text=True)
    except Exception as e:
        # Catch any other exceptions that might occur
        print(f"An unexpected error occurred: {str(e)}")
        return []

    # Check if the command was successful
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        print(f"Exit code: {result.returncode}")
        return []

    # Print the stdout for debugging
    print("Command Output:")
    print(result.stdout)

    # Check if Scoop reports no installed apps
    if "There aren't any apps installed." in result.stdout:
        print("No software is installed.")
        return []

    installedSoftware = []
    outputLines = result.stdout.splitlines()

    process_software = False

    for line in outputLines:
        if '---' in line:
            process_software = True  # Start processing after this line
            continue

        if not process_software or not line.strip():
            continue  # Ignore lines before the separator or empty lines

        # Example output line: 7zip 22.01  main
        softwareDetails = re.split(r'\s+', line.strip())  # Split by whitespace

        # Ensure the line has at least 2 parts (Package, Version)
        if len(softwareDetails) >= 2:
            name, version = softwareDetails[:2]
            softwareEntry = {
                'name': name,
                'current_version': version,
            }
            installedSoftware.append(softwareEntry)

    print(installedSoftware)
    return installedSoftware


def ensure_scoop_installed():
    """
    Checks if Scoop is installed on the system. If it is not installed or not functioning,
    exits the program with an error message.
    """
    try:
        # "scoop --version" will throw FileNotFoundError if `scoop` is not on PATH,
        # or CalledProcessError if there's another execution problem.
        subprocess.run("scoop --version", shell=True, check=True, capture_output=True, text=True)
        print("Scoop is already installed.")
    except FileNotFoundError:
        print("Scoop not found: Please contact your administrator. Exiting program.")
        sys.exit(1)
    except subprocess.CalledProcessError:
        # We got a non-zero return code; this may mean Scoop is not properly installed.
        print("Scoop detected but could not run. Exiting program.")
        sys.exit(1)


def install_program(program_full_name):
    file_path = os.path.join(os.getcwd(), "client_installers")
    program_path = os.path.join(file_path, program_full_name)
    # /{user}/scoop/cache
    user_home = os.path.expanduser("~")
    scoop_cache_path = os.path.join(user_home, "scoop", "cache")

    # Ensure the Scoop cache directory exists
    if not os.path.exists(scoop_cache_path):
        print("Error: Scoop cache directory not found.")
        return False

    # Move the program installer to the Scoop cache directory
    destination_path = os.path.join(scoop_cache_path, program_full_name)
    try:
        shutil.copy(program_path, destination_path)
        print(f"Copied {program_full_name} to {scoop_cache_path}")
    except Exception as e:
        print(f"Error copying file: {e}")
        return False

    # 2) run the scoop install and somehow install the new file
    try:
        program_name = program_full_name.split("#")[0]
        print(f"installing {program_name}")
        result = subprocess.run(f'scoop install {program_name}', shell=True, check=True, capture_output=True, text=True)
        return f"Successfully installed {program_name}"
    except Exception as e:
        # Catch any other exceptions that might occur
        print(f"An unexpected error occurred: {str(e)}")
        return []


def uninstall_program(program_name):
    """
    Uninstalls the specified program using Scoop and returns a success status.
    """

    scoop_command = f"scoop uninstall {program_name}"
    try:
        result = subprocess.run(
            scoop_command,
            shell=True,
            check=True,
            capture_output=True,
            text=True
        )
        # Check for a success message in the command output
        if "Successfully uninstalled" in result.stdout:
            print(f"{program_name} was successfully uninstalled.")
            return f"{program_name} was successfully uninstalled."
        else:
            # If no explicit success message, we assume it executed correctly.
            print(f"Uninstall command executed. Output:\n{result.stdout}")
            return f"Uninstall command executed. Output:\n{result.stdout}"
    except subprocess.CalledProcessError as e:
        print(f"Error uninstalling {program_name}: {e.stderr}")
        return f"Error uninstalling {program_name}: {e.stderr}"


import wmi
import platform
import getpass


def get_active_user():
    """
    Return the currently active user.
    In a real-world scenario you might use a more advanced method.
    """
    return getpass.getuser()


def get_firewall_status():
    """
    Return a map of firewall statuses for Domain, Private, and Public profiles,
    using the 'netsh advfirewall show allprofiles' command.
    It returns 1 if the profile is enabled ("ON") and 0 if disabled ("OFF").
    """
    try:
        # Run the netsh command and capture its output.
        output = subprocess.check_output("netsh advfirewall show allprofiles",
                                           shell=True, text=True)
        # Prepare a dictionary for the profiles.
        profiles = {"Domain": None, "Private": None, "Public": None}
        # The output typically includes lines like:
        #   Domain Profile Settings:
        #       State                                 ON
        #   Private Profile Settings:
        #       State                                 OFF
        #   Public Profile Settings:
        #       State                                 ON
        #
        # We'll use regex to capture the state (ON/OFF) for each profile.
        for profile in profiles.keys():
            pattern = rf"{profile} Profile Settings:.*?State\s+(\w+)"
            match = re.search(pattern, output, re.IGNORECASE | re.DOTALL)
            if match:
                state_str = match.group(1).strip().lower()
                profiles[profile] = 1 if state_str == "on" else 0
            else:
                profiles[profile] = None  # Could not determine status for this profile

        return profiles

    except Exception as e:
        return {"error": f"Error accessing firewall status via netsh: {e}"}


def get_storage():
    """
    Return a map with storage statistics for the main drive.
    For Windows, it uses the SYSTEMDRIVE environment variable (usually 'C:').
    For other operating systems, it defaults to the root ('/').

    Returns:
        dict: {
            "max": total storage in GB (rounded),
            "current": used storage in GB (rounded)
        }
    """
    # Determine the main drive path: use SYSTEMDRIVE for Windows or '/' for other OS
    main_drive = os.getenv("SYSTEMDRIVE", "/")
    if os.name == "nt" and not main_drive.endswith("\\"):
        main_drive += "\\"

    # Get disk usage statistics (returns total, used, free in bytes)
    usage = shutil.disk_usage(main_drive)

    # Convert bytes to gigabytes (GB)
    total_gb = usage.total / (1024 ** 3)
    used_gb = usage.used / (1024 ** 3)

    return {"max": round(total_gb), "current": round(used_gb)}


def get_operating_system_information():
    """
    Return a map with operating system information.
    Using the platform module to retrieve basic details.
    """
    # platform.release() might return '10' on Windows 10.
    # platform.version() gives a more detailed version string.
    return {
        "windows": platform.release(),
        "windows_version_number": platform.version()
    }


def get_bitlocker_status():
    """
    Connects to the BitLocker WMI namespace and returns an array of maps.
    Each map contains details for one encryptable volume.
    Instead of returning the raw device ID (e.g. "\\?\Volume{...}\"),
    this function attempts to return the drive letter if available.
    """
    # First, build a mapping from the volume DeviceID to its DriveLetter
    volume_lookup = {}
    # Query the default WMI namespace (root\CIMV2) for volumes.
    c_vol = wmi.WMI()
    for vol in c_vol.Win32_Volume():
        if vol.DriveLetter:
            # Normalize by stripping whitespace and converting to uppercase.
            device_id = vol.DeviceID.strip().upper()
            volume_lookup[device_id] = vol.DriveLetter

    # Mapping Protection Status to human-readable names
    protection_status_map = {
        0: "Off (Not Protected)",
        1: "On (Protected)"
    }

    # Mapping Encryption Methods to readable names
    encryption_method_map = {
        0: "None",
        1: "AES 128-bit",
        2: "AES 256-bit",
        3: "Hardware Encryption",
        4: "XTS-AES 128-bit",
        5: "XTS-AES 256-bit"
    }

    # Connect to the BitLocker WMI namespace
    c_bitlocker = wmi.WMI(namespace='root\\CIMV2\\Security\\MicrosoftVolumeEncryption')
    bitlocker_data = []  # List to hold the results

    for vol in c_bitlocker.Win32_EncryptableVolume():
        # Normalize the device ID from BitLocker query
        device_id = vol.DeviceID.strip().upper()
        # Look up the drive letter; if not found, fallback to the raw DeviceID.
        drive_letter = volume_lookup.get(device_id, device_id)
        bitlocker_data.append({
            "DeviceID": drive_letter,
            "ProtectionStatus": protection_status_map.get(vol.ProtectionStatus, f"Unknown ({vol.ProtectionStatus})"),
            "Encryption": encryption_method_map.get(vol.EncryptionMethod, f"Unknown ({vol.EncryptionMethod})")
        })

    return bitlocker_data


def get_system_statistics():

    return {
        "user": get_active_user(),
        "firewall_status": get_firewall_status(),
        "storage": get_storage(),
        "operating_system_information": get_operating_system_information(),
        "bitlocker_status": get_bitlocker_status()
    }


# Example usage:
if __name__ == "__main__":
    #Main for testing methods
    import json

    stats = get_system_statistics()
    print(json.dumps(stats, indent=4))
