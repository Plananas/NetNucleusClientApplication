import sys
import subprocess


def build_exe(python_script, exe_name, icon_file=None, admin_required=False):
    """
    Builds a standalone .exe from a Python script using PyInstaller.

    :param python_script: Name of the Python script to package.
    :param exe_name: Desired name of the resulting executable (without .exe).
    :param icon_file: Path to the icon file for the executable (optional).
    :param admin_required: Whether the executable requires admin privileges.
    """
    # Construct the PyInstaller command
    command = [
        sys.executable, '-m', 'PyInstaller',
        '--onefile',
        '--hidden-import=win32timezone',
        '--hidden-import=win32service',
        '--hidden-import=win32serviceutil',
        '--hidden-import=pywintypes',
        '--hidden-import=pythoncom',
        '--name', exe_name,
    ]

    # Add admin privileges if required
    if admin_required:
        command.append('--uac-admin')

    # Add the icon file if provided
    if icon_file:
        command.extend(['--icon', icon_file])

    # Append the Python script
    command.append(python_script)

    print(f"Building {exe_name}.exe from {python_script}...")
    print("Command: " + " ".join(command))

    # Run the PyInstaller command
    subprocess.run(command, check=True)
    print(f"Build for {exe_name}.exe finished! Check the 'dist' folder.")


if __name__ == '__main__':
    # Build the installer executable
    build_exe(
        python_script="Installer.py",
        exe_name="Installer",
        icon_file="",  # Replace with the path to the installer's icon file
        admin_required=True  # The installer usually requires admin privileges
    )

    # Build the main application executable
    # build_exe(
    #     python_script="NetworkAutomationService.py",
    #     exe_name="NetworkAutomationClient",
    #     icon_file="icon.ico"  # Replace with the path to the app's icon file
    # )
