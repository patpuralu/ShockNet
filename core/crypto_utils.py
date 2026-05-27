#  Cifrado AES-256-CBC 

import os, base64, json


def encrypt_payload(data: dict, key: str) -> dict:
    if not key:
        return data
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as P
        from cryptography.hazmat.backends import default_backend
        key_b = key.encode().ljust(32, b'\x00')[:32]
        iv    = os.urandom(16)
        raw   = json.dumps(data, ensure_ascii=False).encode()
        pad   = P.PKCS7(128).padder()
        padded= pad.update(raw) + pad.finalize()
        enc   = Cipher(algorithms.AES(key_b), modes.CBC(iv),
                       backend=default_backend()).encryptor()
        ct    = enc.update(padded) + enc.finalize()
        return {"_encrypted": True,
                "iv":   base64.b64encode(iv).decode(),
                "data": base64.b64encode(ct).decode()}
    except Exception as e:
        print(f"[ShockNet] Cifrado fallido: {e}")
        return data


def decrypt_payload(data: dict, key: str) -> dict:
    if not key or not data.get("_encrypted"):
        return data
    try:
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
        from cryptography.hazmat.primitives import padding as P
        from cryptography.hazmat.backends import default_backend
        key_b  = key.encode().ljust(32, b'\x00')[:32]
        iv     = base64.b64decode(data["iv"])
        ct     = base64.b64decode(data["data"])
        dec    = Cipher(algorithms.AES(key_b), modes.CBC(iv),
                        backend=default_backend()).decryptor()
        padded = dec.update(ct) + dec.finalize()
        unpad  = P.PKCS7(128).unpadder()
        raw    = unpad.update(padded) + unpad.finalize()
        return json.loads(raw.decode())
    except Exception as e:
        print(f"[ShockNet] Descifrado fallido: {e}")
        return {}
