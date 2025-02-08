from Crypto.Cipher import AES
import secrets
import hashlib
import base64


class MessageCipherHandler:
    GENERATOR = 2
    PRIME_MODULUS = int(
        'FFFFFFFFFFFFFFFFC90FDAA22168C234C4C6628B80DC1CD1'
        '29024E088A67CC74020BBEA63B139B22514A08798E3404DD'
        'EF9519B3CD3A431B302B0A6DF25F14374FE1356D6D51C245'
        'E485B576625E7EC6F44C42E9A637ED6B0BFF5CB6F406B7ED'
        'EE386BFB5A899FA5AE9F24117C4B1FE649', 16
    )


    def __init__(self):
        self.private_key = secrets.randbits(256)
        self.public_key = self._generate_public_key()
        self.shared_encryption_key = None


    def get_public_key(self):
        return base64.b64encode(self.public_key.to_bytes((self.public_key.bit_length() + 7) // 8, byteorder='big')).decode()


    def set_peer_public_key(self, key):
        try:
            peer_key = int.from_bytes(base64.b64decode(key), byteorder='big')
            self.shared_encryption_key = self._compute_shared_key(peer_key)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid peer public key: {e}")


    def encrypt(self, msg):
        """
        Encrypts a message using AES encryption.
        :param msg: The plaintext message to encrypt.
        :return: A string containing Base64-encoded nonce, ciphertext, and tag separated by '|'.
        """
        cipher = AES.new(self.shared_encryption_key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(msg.encode('utf-8'))
        nonce = cipher.nonce

        # Base64 encode each component
        b64_nonce = base64.b64encode(nonce).decode('utf-8')
        b64_ciphertext = base64.b64encode(ciphertext).decode('utf-8')
        b64_tag = base64.b64encode(tag).decode('utf-8')

        # Combine the Base64-encoded components with the '|' separator
        return f"{b64_nonce}|{b64_ciphertext}|{b64_tag}"


    def decrypt(self, encoded_message):
        """
        Decrypts a message using AES decryption.
        :param encoded_message: A string containing Base64-encoded nonce, ciphertext, and tag separated by '|'.
        :return: Decrypted plaintext message, or None if decryption fails.
        """
        try:
            # Split the message into Base64 components
            b64_nonce, b64_ciphertext, b64_tag = encoded_message.split('|')

            # Decode each component from Base64
            nonce = base64.b64decode(b64_nonce)
            ciphertext = base64.b64decode(b64_ciphertext)
            tag = base64.b64decode(b64_tag)

            # Create the AES cipher with the shared encryption key and nonce
            cipher = AES.new(self.shared_encryption_key, AES.MODE_EAX, nonce=nonce)

            # Decrypt and verify
            plaintext = cipher.decrypt(ciphertext)
            cipher.verify(tag)
            return plaintext.decode('utf-8')

        except ValueError as e:
            print(f"[DECRYPT ERROR] Decryption failed: {e}")
            return None
        except Exception as e:
            print(f"[DECRYPT ERROR] Unexpected error: {e}")
            return None

    def _generate_public_key(self):
        return pow(self.GENERATOR, self.private_key, self.PRIME_MODULUS)


    def _compute_shared_key(self, other_public_key):
        shared_secret = pow(other_public_key, self.private_key, self.PRIME_MODULUS)
        shared_secret_bytes = shared_secret.to_bytes((shared_secret.bit_length() + 7) // 8, byteorder='big')
        return hashlib.sha256(shared_secret_bytes).digest()[:16]
