import hashlib
import time
import random
import string


def generate_did():
    return "web_" + "".join(random.choices(string.hexdigits.lower(), k=32))


def generate_kwssectoken():
    return "".join(random.choices(string.ascii_letters + string.digits, k=32))


def md5(text):
    return hashlib.md5(text.encode()).hexdigest()


def timestamp_ms():
    return int(time.time() * 1000)
