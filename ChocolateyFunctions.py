import subprocess
import re

"""
Chocolatey Functions:
This file contains the original functionality for my client app, the processes were all completed client side instead of server side.

Just in case these are ever needed again, I will keep them here.
"""

def get_updatable_software_chocolatey():
    print("Getting Updatable Software...")

    # Run the choco outdated command to get the list of outdated packages
    result = subprocess.run(['choco', 'outdated', '--all'], capture_output=True, text=True)

    # Initialize an empty list to store software update details
    updatable_software = []

    # Check if the command was successful
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return updatable_software

    # Parse the output assuming it is a pipe-separated list
    try:
        # Split the output into lines
        lines = result.stdout.splitlines()
        # Iterate over each line to parse package details
        for line in lines:
            # Skip header lines or invalid data
            if not line.strip() or '|' not in line:
                continue

            # Split the line by the pipe separator
            parts = line.split('|')

            # Ensure there are enough parts to parse
            if len(parts) < 4:
                continue

            # Extract package details
            name = parts[0].strip()
            current_version = parts[1].strip()
            available_version = parts[2].strip()

            # Append the parsed data to the updatable_software list
            updatable_software.append({
                'name': name,
                'current_version': current_version,
                'available_version': available_version
            })
    except Exception as e:
        print(f"Failed to parse the output: {e}")

    updatable_software.pop(0)
    print(updatable_software)
    return updatable_software


def get_all_software_chocolatey():
    print("Getting all installed software...")
    try:
        result = subprocess.run(['choco', 'list'], capture_output=True, text=True, encoding='utf-8')
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

    print("got all the software")
    installedSoftware = []
    outputLines = result.stdout.splitlines()

    for line in outputLines:
        if not line or '---' in line:
            continue

        softwareDetails = re.split(' ', line.strip())  # 2 or more spaces

        # In case the line has 2 parts (Package, Version)
        if len(softwareDetails) == 2:
            name, version = softwareDetails
            softwareEntry = {
                'name': name,
                'current_version': version,
            }
            installedSoftware.append(softwareEntry)

    installedSoftware.pop(0)
    print(installedSoftware)
    return installedSoftware


def update_software_chocolatey(program_name):
    try:
        # Run the Chocolatey command to install the program
        subprocess.run(['choco', 'upgrade', program_name, '-y', '--force'], check=True)
        return f"Successfully upgraded {program_name}"
    except subprocess.CalledProcessError:
        return f"Failed to upgrade {program_name}"
    except FileNotFoundError:
        return "Chocolatey is not installed or available on this system."

def update_all_software_chocolatey():
    try:
        # Run the Chocolatey command to install the program
        subprocess.run(['choco', 'upgrade', 'all', '-y', '--force'], check=True)
        return f"Successfully upgraded all software"
    except subprocess.CalledProcessError:
        return f"Failed to upgrade"
    except FileNotFoundError:
        return "Chocolatey is not installed or available on this system."


def install_program_chocolatey(program_name):
    try:
        # Run the Chocolatey command to install the program
        subprocess.run(['choco', 'install', program_name, '-y', '--force'], check=True)
        return f"Successfully installed {program_name}"
    except subprocess.CalledProcessError:
        return f"Failed to install {program_name}"
    except FileNotFoundError:
        return "Chocolatey is not installed or available on this system."


def uninstall_program_chocolatey(program_name):
    try:
        # Run the Chocolatey command to uninstall the program with automatic 'Yes' input
        process = subprocess.run(
            ['choco', 'uninstall', program_name, '-y'],
            input='y\n',  # Automatically answers 'Yes' to prompts
            text=True,
            check=True
        )
        return f"Successfully uninstalled {program_name}."
    except subprocess.CalledProcessError as e:
        return f"Failed to uninstall {program_name}. Error: {e}"
    except FileNotFoundError:
        return "Chocolatey is not installed or available on this system."


def ensure_chocolatey_installed():
    """
    Checks if Chocolatey (choco) is installed on the system. If it is not installed,
    installs it using a PowerShell script.
    """

    # Step 1: Check if choco is installed
    try:
        # "choco --version" will throw FileNotFoundError if `choco` is not on PATH
        # or CalledProcessError if there's another execution problem
        subprocess.run(["choco", "--version"], check=True, capture_output=True)
        print("Chocolatey is already installed.")
        return
    except FileNotFoundError:
        print("Chocolatey not found.")
    except subprocess.CalledProcessError:
        # We got a return code != 0; this may mean Chocolatey is not properly installed
        # or something else went wrong
        print("Chocolatey detected but could not run. Attempting to reinstall.")

    # Step 2: Install Chocolatey using PowerShell
    # Using the official Chocolatey installation script from https://community.chocolatey.org/install.ps1
    print("Installing Chocolatey. This may take a few moments...")
    install_cmd = (
        r"Set-ExecutionPolicy Bypass -Scope Process -Force; "
        r"[System.Net.ServicePointManager]::SecurityProtocol = "
        r"[System.Net.ServicePointManager]::SecurityProtocol -bor 3072; "
        r"iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
    )
    try:
        subprocess.run(
            ["powershell", "-Command", install_cmd],
            check=True
        )
    except subprocess.CalledProcessError as e:
        print("Installation of Chocolatey failed with an error:")
        print(e)
        return

    # Step 3: Verify installation
    try:
        subprocess.run(["choco", "--version"], check=True, capture_output=True)
        print("Chocolatey installation successful.")
    except Exception as e:
        print("Chocolatey installation was attempted but verification failed.")
        print(e)