import base64
import io
import hashlib
import secrets
import pyotp
import qrcode


def generate_secret() -> str:
    return pyotp.random_base32()


def build_qr_code_base64(secret: str, username: str, issuer: str = "Cloudflare DDNS Panel") -> tuple[str, str]:
    """Devuelve (otpauth_url, qr_code_base64_png)."""
    totp = pyotp.TOTP(secret)
    otpauth_url = totp.provisioning_uri(name=username, issuer_name=issuer)

    img = qrcode.make(otpauth_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    qr_base64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return otpauth_url, f"data:image/png;base64,{qr_base64}"


def verify_totp_code(secret: str, code: str) -> bool:
    if not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code.strip(), valid_window=1)


# ---------- Códigos de recuperación ----------
def generate_recovery_codes(count: int = 10) -> list[str]:
    """Genera códigos legibles tipo 'ABCD-1234'."""
    alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin caracteres ambiguos (0/O, 1/I/L)
    codes = []
    for _ in range(count):
        part1 = "".join(secrets.choice(alphabet) for _ in range(4))
        part2 = "".join(secrets.choice(alphabet) for _ in range(4))
        codes.append(f"{part1}-{part2}")
    return codes


def normalize_recovery_code(code: str) -> str:
    return code.strip().upper().replace(" ", "")


def hash_recovery_code(code: str) -> str:
    normalized = normalize_recovery_code(code)
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
