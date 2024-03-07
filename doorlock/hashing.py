import hashlib


def sha512(str):
    try:
        digest = hashlib.sha512(str.encode()).hexdigest()
        return digest
    except Exception as e:
        return None
