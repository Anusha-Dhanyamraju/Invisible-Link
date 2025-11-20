import os
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# We use AES-GCM (Galois/Counter Mode) because it provides both confidentiality (encryption)
# and integrity (ensures the message hasn't been tampered with).

def derive_key(password: str, salt: bytes) -> bytes:
    """
    Derives a strong cryptographic key from a user password.
    
    Why? Passwords are often weak (e.g., "password123"). 
    KDF (Key Derivation Function) stretches them into a secure 32-byte key.
    We use PBKDF2 with SHA256 and 100,000 iterations to make it slow for attackers to guess.
    """
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    return kdf.derive(password.encode())

def encrypt(message: str, password: str) -> str:
    """
    Encrypts a text message using the password.
    
    Returns a base64 string containing:
    [Salt] + [Nonce] + [Ciphertext]
    """
    # 1. Generate a random salt. This ensures that even if two users have the same password,
    #    their derived keys will be different.
    salt = os.urandom(16)
    key = derive_key(password, salt)
    
    # 2. Generate a nonce (Number used ONCE). AES-GCM requires a unique nonce for every encryption
    #    to be secure.
    nonce = os.urandom(12)
    aesgcm = AESGCM(key)
    
    # 3. Encrypt the data.
    data = message.encode()
    ciphertext = aesgcm.encrypt(nonce, data, None)
    
    # 4. Pack everything together so we can decrypt it later.
    #    We need the salt to recreate the key, and the nonce to initialize AES-GCM.
    combined = salt + nonce + ciphertext
    
    # 5. Encode as Base64 so it's safe to treat as a string if needed, 
    #    though for steganography we'll eventually need binary.
    return base64.b64encode(combined).decode('utf-8')

def decrypt(encrypted_str: str, password: str) -> str:
    """
    Decrypts the base64 string back into the original message.
    """
    try:
        # 1. Decode the base64 string back to raw bytes.
        combined = base64.b64decode(encrypted_str)
        
        # 2. Extract the parts we packed earlier.
        #    Salt is 16 bytes, Nonce is 12 bytes.
        salt = combined[:16]
        nonce = combined[16:28]
        ciphertext = combined[28:]
        
        # 3. Re-derive the same key using the salt and password.
        key = derive_key(password, salt)
        
        # 4. Decrypt.
        aesgcm = AESGCM(key)
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        
        return plaintext.decode('utf-8')
    except Exception as e:
        # If the password is wrong or data is corrupted, AES-GCM will fail.
        raise ValueError("Decryption failed. Wrong password or corrupted data.") from e
