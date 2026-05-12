"""
Seed a super-admin account — ZimAgriTrust.

Interactive usage (run inside the backend container):
    python -m scripts.seed_super_admin

Non-interactive / scripted usage:
    python -m scripts.seed_super_admin \
        --first-name Tatenda \
        --surname Moyo \
        --username tatenda.moyo \
        --email tatenda@zimagritrust.co.zw \
        --phone 0771234567 \
        --password "Strong-Pass-1!" \
        --enroll-totp

The TOTP secret is printed ONCE as an otpauth URI.
Scan it into Google/Microsoft Authenticator immediately — it is NOT stored in
plain text and cannot be recovered.
"""
from __future__ import annotations

import argparse
import getpass
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.super_admin_security import generate_totp_secret, totp_provisioning_uri  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services.super_admin_service import (  # noqa: E402
    get_super_admin_by_username,
    seed_super_admin,
)

# ── ANSI helpers ──────────────────────────────────────────────────────────────
_BOLD  = "\033[1m"
_GREEN = "\033[32m"
_CYAN  = "\033[36m"
_RED   = "\033[31m"
_DIM   = "\033[2m"
_RESET = "\033[0m"

def _h(text: str) -> str:
    return f"{_BOLD}{_CYAN}{text}{_RESET}"

def _ok(text: str) -> str:
    return f"{_GREEN}{text}{_RESET}"

def _err(text: str) -> str:
    return f"{_RED}{text}{_RESET}"


# ── Input helpers ─────────────────────────────────────────────────────────────

def _ask(label: str, default: str | None = None, required: bool = True) -> str:
    """Prompt the user for a single value."""
    hint = f" [{default}]" if default else ""
    while True:
        value = input(f"  {label}{hint}: ").strip()
        if value:
            return value
        if default:
            return default
        if not required:
            return ""
        print(f"  {_err('✗')} {label} is required. Please enter a value.")


def _ask_password() -> str:
    """Prompt for password with confirmation."""
    while True:
        pw = getpass.getpass("  Password: ")
        if len(pw) < 8:
            print(f"  {_err('✗')} Password must be at least 8 characters.")
            continue
        confirm = getpass.getpass("  Confirm password: ")
        if pw != confirm:
            print(f"  {_err('✗')} Passwords do not match. Try again.")
            continue
        return pw


def _validate_email(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email))


def _normalize_phone(phone: str) -> str | None:
    if not phone:
        return None
    value = re.sub(r"\s+", "", phone)
    if value.startswith("+"):
        return value
    if value.startswith("0"):
        return f"+263{value[1:]}"
    if value.startswith("263"):
        return f"+{value}"
    return f"+263{value}"


def _suggest_username(first: str, surname: str, email: str) -> str:
    clean = lambda s: re.sub(r"[^a-z0-9]", "", s.lower())
    if first and surname:
        return f"{clean(first)}.{clean(surname)}"
    if first:
        return clean(first)
    if email:
        return email.split("@")[0].lower()
    return "superadmin"


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    p = argparse.ArgumentParser(description="Seed a ZimAgriTrust super-admin account.")
    p.add_argument("--first-name",   default=None)
    p.add_argument("--surname",      default=None)
    p.add_argument("--username",     default=None)
    p.add_argument("--email",        default=None)
    p.add_argument("--phone",        default=None, help="Zimbabwe number, e.g. 0771234567 or +263771234567")
    p.add_argument("--password",     default=None)
    p.add_argument("--ip-whitelist", default=None, help="Comma-separated IPs allowed to log in")
    p.add_argument("--enroll-totp",  action="store_true", help="Generate a TOTP secret for 2FA")
    p.add_argument("--yubikey-public-id", default=None, help="First 12 modhex chars of your YubiKey OTP")
    args = p.parse_args()

    print()
    print(_h("═══════════════════════════════════════════════"))
    print(_h("   ZimAgriTrust — Super Admin Account Setup    "))
    print(_h("═══════════════════════════════════════════════"))
    print()

    # ── Personal details ──────────────────────────────────────────────────────
    print(_BOLD + "  Step 1 of 4 — Personal details" + _RESET)
    print()
    first_name = _ask("First name", args.first_name)
    surname    = _ask("Surname",    args.surname)
    full_name  = f"{first_name} {surname}".strip()

    print()

    # ── Contact details ───────────────────────────────────────────────────────
    print(_BOLD + "  Step 2 of 4 — Contact details" + _RESET)
    print()

    while True:
        email = _ask("Email address", args.email)
        if _validate_email(email):
            break
        print(f"  {_err('✗')} That does not look like a valid email address.")
        args.email = None  # clear so _ask prompts again

    raw_phone = _ask("Phone number (Zimbabwe)", args.phone, required=False)
    phone = _normalize_phone(raw_phone) if raw_phone else None
    print()

    # ── Login credentials ─────────────────────────────────────────────────────
    print(_BOLD + "  Step 3 of 4 — Login credentials" + _RESET)
    print()

    suggested = _suggest_username(first_name, surname, email)
    username  = _ask("Username", args.username or suggested)

    if args.password:
        password = args.password
    else:
        print(f"  {_DIM}Password must be at least 8 characters with upper, lower, digit and special char.{_RESET}")
        password = _ask_password()

    print()

    # ── Security options ──────────────────────────────────────────────────────
    print(_BOLD + "  Step 4 of 4 — Security options" + _RESET)
    print()

    enroll_totp = args.enroll_totp
    if not enroll_totp:
        ans = input("  Enroll TOTP (Google/Microsoft Authenticator)? [Y/n]: ").strip().lower()
        enroll_totp = ans not in ("n", "no")

    totp_secret = generate_totp_secret() if enroll_totp else None
    ip_wl = [ip.strip() for ip in args.ip_whitelist.split(",")] if args.ip_whitelist else None
    print()

    # ── Preview ───────────────────────────────────────────────────────────────
    print(_h("  ── Account preview ──────────────────────────"))
    print(f"  {'Full name:':<18} {full_name}")
    print(f"  {'Username:':<18} {username}")
    print(f"  {'Email:':<18} {email}")
    print(f"  {'Phone:':<18} {phone or '(not set)'}")
    print(f"  {'2FA (TOTP):':<18} {'Yes — QR code will be shown' if totp_secret else 'No'}")
    print(f"  {'YubiKey ID:':<18} {args.yubikey_public_id or '(none)'}")
    print(f"  {'IP whitelist:':<18} {', '.join(ip_wl) if ip_wl else '(all IPs allowed)'}")
    print()

    confirm = input("  Confirm and create this account? [Y/n]: ").strip().lower()
    if confirm in ("n", "no"):
        print(f"\n  {_err('Aborted.')} No account was created.\n")
        return 1

    # ── Create ────────────────────────────────────────────────────────────────
    print()
    print("  Creating account…")
    try:
        with SessionLocal() as db:
            if get_super_admin_by_username(db, username):
                print(f"\n  {_err('ERROR:')} A super-admin with username '{username}' already exists.", file=sys.stderr)
                return 2
            account = seed_super_admin(
                db,
                username=username,
                email=email,
                password=password,
                hardware_mfa_secret=totp_secret,
                yubikey_public_id=args.yubikey_public_id,
                phone_number=phone,
                ip_whitelist=ip_wl,
            )
    except Exception as exc:
        print(f"\n  {_err('ERROR:')} {exc}", file=sys.stderr)
        return 3

    print(_ok(f"\n  ✓ Super-admin '{account.username}' created successfully (id={account.id})."))

    if totp_secret:
        uri = totp_provisioning_uri(totp_secret, account_name=account.email)
        print()
        print(_h("  ── TOTP Enrolment ────────────────────────────"))
        print(f"  {_DIM}Scan the QR code below OR copy the otpauth URI into your Authenticator app.{_RESET}")
        print(f"  {_DIM}This secret is shown ONLY ONCE and cannot be recovered.{_RESET}")
        print()
        try:
            import qrcode
            qr = qrcode.QRCode(border=2)
            qr.add_data(uri)
            qr.make(fit=True)
            qr.print_ascii(invert=True)
        except Exception:
            print(f"  (Install the 'qrcode' package for QR rendering)")
        print(f"\n  otpauth URI:     {uri}")
        print(f"  Secret (base32): {totp_secret}")
        print()

    print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
