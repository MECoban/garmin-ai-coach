"""Garmin girişi — şifreyi gizli (getpass) sorar, cloudscraper ile Cloudflare'i geçer.

ÖN KOŞUL: 2FA KAPALI olmalı. Şifre ekrana yazılmaz, hiçbir yere kaydedilmez.
Başarınca token ~/.garminconnect'e (~1 yıl). Kendi terminalinde çalıştır:
    cd /path/to/garmin-ai-coach && venv/bin/python scripts/login_garmin.py
"""
from __future__ import annotations
import getpass
import os
from pathlib import Path
from dotenv import load_dotenv
import cloudscraper
from garminconnect import Garmin

load_dotenv(str(Path(__file__).resolve().parent / ".env"))


def main() -> int:
    email = os.getenv("GARMIN_EMAIL") or input("Garmin e-posta: ").strip()
    pw = getpass.getpass(f"{email} için Garmin şifresi (gizli): ")
    if not pw:
        print("Şifre boş.")
        return 1
    ts = str(os.getenv("GARMINTOKENS") or Path.home() / ".garminconnect")
    Path(ts).mkdir(parents=True, exist_ok=True)

    print("Giriş yapılıyor (cloudscraper → Cloudflare bypass)...")
    try:
        client = Garmin(email, pw)
        client.garth.sess = cloudscraper.create_scraper()
        client.login()
        client.garth.dump(ts)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc).lower()
        print(f"\nGiriş başarısız: {type(exc).__name__}: {str(exc)[:250]}")
        if "401" in msg or "unauthorized" in msg or "credential" in msg:
            print("→ Şifre yanlış. Tarayıcıda giriş yaptığın şifreyle birebir aynı mı? Tekrar dene.")
        elif "mfa" in msg or "2fa" in msg:
            print("→ 2FA hâlâ açık. Security Center'da E-mail+SMS ikisini de OFF yap.")
        elif any(k in msg for k in ("cloudflare", "403", "captcha", "no profile")):
            print("→ Cloudflare/sunucu geçici engeli. Birkaç dk bekle, tekrar dene.")
        return 1

    # doğrula
    try:
        name = client.get_full_name()
        print(f"\n✓ BAŞARILI! Giriş: {name}")
    except Exception:
        print("\n✓ Token kaydedildi.")
    print(f"Token: {ts} (~1 yıl). Artık otomatik veri çekimi giriş gerektirmez.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
