import uuid
import os

from ClientApplication import SystemFunctions
from ClientApplication.MessageCipherHandler import MessageCipherHandler


class MessageHandler:
    FORMAT = 'utf-8'
    HEADER = 64
    BUFFER_SIZE = 1024

    def __init__(self):
        # prevent instances
        pass


    def __init__(self, connection):
        self.connection = connection
        self.message_id = str(uuid.uuid4())[:8]
        self.message_cipher_handler = MessageCipherHandler()
        self.encryption_enabled = False  # Track if encryption is active

    def send_initial_message(self):
        """
        Sends an initial message to set up the encryption keys.
        """
        # Send the public key to the peer
        initial_message = self.message_cipher_handler.get_public_key()
        self.write_unencrypted(initial_message)  # Initial message is unencrypted

        # Receive the peer's public key and generate the encryption key
        peer_key = self.read_unencrypted()
        self.message_cipher_handler.set_peer_public_key(peer_key)
        self.encryption_enabled = True

    def read(self):
        """
        Read an encrypted message from the client.
        """
        message_length = self._read_header()
        if message_length is None:
            return None

        full_message = self._read_message_body(message_length)
        if not full_message:
            return None

        if self.encryption_enabled:
            full_message = self.message_cipher_handler.decrypt(full_message)

        sender_id, content = self._parse_message(full_message)
        if sender_id != self.message_id:
            return content
        return None

    def write(self, message):
        """
        Write an encrypted message to the client.
        """
        # Add message ID and prepare for encryption
        message = f"{self.message_id}:{message}"

        if self.encryption_enabled:
            message = self.message_cipher_handler.encrypt(message)

        # Ensure the message is encoded for transmission
        encoded_message = message.encode(self.FORMAT)
        message_length = len(encoded_message)

        self._send_header(message_length)  # Send the length of the message as a header

        # Send the entire message
        sent_bytes = 0
        while sent_bytes < message_length:
            sent = self.connection.send(encoded_message[sent_bytes:])
            if sent == 0:
                raise RuntimeError("Socket connection broken while sending data")
            sent_bytes += sent

    def read_unencrypted(self):
        """
        Read an unencrypted message (used for initial key exchange).
        """
        message_length = self._read_header()
        if message_length is None:
            return None

        full_message = self._read_message_body(message_length)
        if not full_message:
            return None

        sender_id, content = self._parse_message(full_message)
        if sender_id != self.message_id:
            return content

    def write_unencrypted(self, message):
        """
        Write an unencrypted message (used for initial key exchange).
        """
        full_message = f"{self.message_id}:{message}"
        encoded_message = full_message.encode(self.FORMAT)
        message_length = len(encoded_message)

        self._send_header(message_length)
        self.connection.sendall(encoded_message)


    def read_file(self, file_name):
        """
        Read a ZIP file from the client and save it.
        """
        print("[DEBUG] Reading file from client")

        # Read total file length
        total_file_length = self._read_header()
        if total_file_length is None:
            print("[ERROR] No file length received")
            return None

        print(f"[DEBUG] Expecting {total_file_length} bytes")
        received_data = self.save_file(total_file_length, file_name)

        if not received_data:
            print("[ERROR] No file data received")
            return None



    def save_file(self, file_size, file_name):
        """
        Receives a binary file from the connection and saves it to the given file path.
        """
        received_bytes = 0
        file_parts = []

        print(f"[DEBUG] Receiving file of size {file_size} bytes...")

        while received_bytes < file_size:
            chunk_size = min(self.BUFFER_SIZE, file_size - received_bytes)
            part = self.connection.recv(chunk_size)

            if not part:
                print("[ERROR] Connection closed unexpectedly")
                return False  # Indicate failure

            file_parts.append(part)
            received_bytes += len(part)
            #print(f"[DEBUG] Received {received_bytes}/{file_size} bytes")

        # Move the ZIP to the local 'installers' directory
        file_path = os.path.join(os.getcwd(), "client_installers")
        os.makedirs(file_path, exist_ok=True)
        file_path = os.path.join(file_path, file_name)
        # Write received data to file
        with open(file_path, "wb") as file:
            file.write(b"".join(file_parts))

        print(f"[DEBUG] File successfully saved as {file_path}")
        return True  # Indicate success


    def write_file(self, file_path):
        """
        Send a ZIP file to the server.
        """
        print(f"[DEBUG] Sending file {file_path}")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        file_size = os.path.getsize(file_path)
        print(f"[DEBUG] File size: {file_size} bytes")

        # Send file length first
        self._send_header(file_size)

        with open(file_path, "rb") as file:
            while chunk := file.read(self.BUFFER_SIZE):
                self.connection.sendall(chunk)

        print("[DEBUG] File upload completed successfully")


    def _read_header(self):
        """
        Read and parse the message length header.
        """
        try:
            header_data = self.connection.recv(self.HEADER).decode(self.FORMAT).strip()
            return int(header_data)
        except ValueError:
            return None

    def _read_message_body(self, message_length):
        """
        Read the full message body based on the given length.
        """
        print("[DEBUG] Reading message body")
        received_bytes = 0
        message_parts = []
        print("read body:")
        while received_bytes < message_length:
            #print("received bytes:", received_bytes)
            part = self.connection.recv(min(self.BUFFER_SIZE, message_length - received_bytes))
            if not part:
                return None
            message_parts.append(part)
            received_bytes += len(part)

        try:
            return b''.join(message_parts).decode(self.FORMAT)
        except UnicodeDecodeError:
            return None

    def _parse_message(self, full_message):
        """
        Parse the sender ID and content from the full message.
        """
        try:
            sender_id, content = full_message.split(":", 1)
            return sender_id, content
        except ValueError:
            return None, None

    def _send_header(self, message_length):
        """
        Send the message length header.
        """
        header = str(message_length).encode(self.FORMAT)
        padded_header = header + b' ' * (self.HEADER - len(header))
        self.connection.send(padded_header)