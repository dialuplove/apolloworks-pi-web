# gen_url.py
import os, time, hmac, hashlib, base64, urllib.parse

SECRET = os.environ["EDGE_SIGNING_SECRET"]
PATH = "/live/stream.m3u8"  # change to a specific .ts to test segments
TTL = 30                    # seconds

def b64url_nopad(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip("=")

exp = int(time.time()) + TTL
msg = (PATH.lower() + str(exp)).encode()
sig = hmac.new(SECRET.encode(), msg, hashlib.sha256).digest()
sig_b64 = b64url_nopad(sig)

qs = f"exp={exp}&sig={urllib.parse.quote(sig_b64)}"
print(f"{PATH}?{qs}")
