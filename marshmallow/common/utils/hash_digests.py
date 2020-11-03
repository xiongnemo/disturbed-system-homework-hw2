import hashlib


def sha512_digest_hexstring(input_string: str) -> str:
    sha512 = hashlib.sha512()
    sha512.update(input_string.encode())
    return sha512.hexdigest()


def sha512_module(input_string: str, mod: int) -> int:
    sha512 = hashlib.sha512()
    sha512.update(input_string.encode())
    module = int(sha512.hexdigest(), 16) % mod
    return module
