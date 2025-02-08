import os
import json
import socket
import time
from getmac import get_mac_address
import SystemFunctions
from MessageHandler import MessageHandler
import servicemanager


class Client:
    CONFIG_DIR = os.path.join(os.environ["ProgramData"], "NetworkAutomationClient")
    CONFIG_FILE = os.path.join(CONFIG_DIR, "client.config")  # Full path to the config file
    SERVICE_NAME = "NetworkAutomationClient"


    def __init__(self):
        self.ensure_dependencies()
        self.PORT = 50000

        #FIXME this static address only works after installation
        # change this back before final product
        #self.SERVER = self.get_server_ip()
        self.SERVER = socket.gethostbyname(socket.gethostname())
        self.ADDR = (self.SERVER, self.PORT)
        self.message_controller = MessageHandler(object)
        self.connected = False
        self.mac_address = get_mac_address()
        self.client = self.configure_socket()


    def ensure_dependencies(self):
        """
        Ensure that required dependencies are installed.
        :return:
        """
        SystemFunctions.ensure_scoop_installed()


    def configure_socket(self):
        """
        Create and configure the client socket.
        :return:
        """
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 65536)
        client.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        return client


    def get_server_ip(self):
        """
        Retrieve the server IP from a configuration file.
        :return:
        """
        try:
            with open(self.CONFIG_FILE, "r") as f:
                for line in f:
                    if line.startswith("IP_ADDRESS="):
                        return line.strip().split("=")[1]
        except FileNotFoundError:
            print("Configuration file not found.")
        return None


    def run(self):
        """
        Start the client and connect to the server.
        :return:
        """
        self.connect_to_server()
        self.initialise_message_controller()
        servicemanager.LogInfoMsg(f"{self.SERVICE_NAME}: Service is now running.")
        self.handle_server()


    def connect_to_server(self):
        """
        Attempt to connect to the server.
        :return:
        """
        while not self.connected:
            try:
                print(f"Attempting to connect to {self.ADDR}...")
                self.client.connect(self.ADDR)
                print("[CONNECTION SUCCESS] Connected to host.")
                self.connected = True
            except Exception as e:
                print(f"[CONNECTION ERROR] Could not connect to host: {e}")
                print("Retrying in 30 seconds...")
                time.sleep(30)


    def initialise_message_controller(self):
        """
        Initialise the message controller.
        :return:
        """
        try:
            self.message_controller = MessageHandler(self.client)
            print("[MESSAGE CONTROLLER] Successfully created.")
            self.message_controller.send_initial_message()
            print("[MESSAGE CONTROLLER] Successfully Encrypted Connection.")
        except Exception as e:
            print(f"[MESSAGE CONTROLLER ERROR] Error creating the message handler: {e}")
            self.connected = False


    def handle_server(self):
        """
        Handle messages from the server.
        :return:
        """
        print("\n[LISTENING FOR MESSAGES]")
        while self.connected: 
            try:
                msg = self.message_controller.read()
                if msg:
                    print("[READING MESSAGE]", msg)
                    self.send(self.process_message(msg))
            except (socket.timeout, socket.error) as e:
                print(f"\n[CONNECTION ERROR] {e}. Reconnecting...")
                self.connected = False
                self.reconnect()
                break
            except Exception as e:
                print(f"\n[UNKNOWN ERROR] {e}. Disconnecting.")
                self.connected = False
                break


    def send(self, message):
        """
        Send a message to the server.
        :param message:
        :return:
        """
        if not message:
            message = "No response"
            return
        print("Sending Message")
        print(message)
        self.message_controller.write({self.mac_address: message})
        time.sleep(0.5)


    def get_file(self, file_name):
        """
        Get a file from the server.
        :return:
        """
        try:
            print("Getting File")
            self.message_controller.read_file(file_name)

            return SystemFunctions.install_program(file_name)

        except Exception as e:
            return "Unable to install program"


    def reconnect(self):
        """
        Attempt to reconnect to the server.
        """
        print("Reconnecting in 30 seconds...")
        time.sleep(30)
        self.client.close()
        self.client = self.configure_socket()
        self.connected = False
        self.connect_to_server()
        self.initialise_message_controller()
        self.handle_server()


    def process_message(self, message):
        """
        Process a message from the server.
        :param message:
        :return:
        """
        print("\n[MESSAGE PROCESSING]")
        print(message)
        commands = {
            "shutdown": SystemFunctions.shutdown,
            "statistics": SystemFunctions.get_system_statistics,
            #"upgrades": SystemFunctions.get_updatable_software,
            "software": SystemFunctions.get_all_software,
            #"upgrade": SystemFunctions.update_all_software
        }

        if message.lower() in commands:
            return commands[message.lower()]()

        split_message = message.split()
        print(split_message)
        print("split message section")
        if len(split_message) == 2:
            command, argument = split_message
            command_map = {
                "uninstall": SystemFunctions.uninstall_program,
                #"upgrade": SystemFunctions.update_software,
                "install": self.get_file,
            }
            if command.lower() in command_map:
                return command_map[command.lower()](argument)


    def cleanup(self):
        """
        Clean up the connection and release resources.
        """
        print("[CLEANUP] Closing the connection...")
        try:
            self.client.close()
        except Exception as e:
            print(f"[CLEANUP ERROR] {e}")



if __name__ == "__main__":
    client = Client()
    client.run()
