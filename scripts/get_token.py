"""Garmin token alıcı — cloudscraper ile Cloudflare'i geçer (kanıtlanmış reçete).

Kaynak: freakyflow/garminskill — garminconnect 0.2.38 (garth) + cloudscraper.
ÖN KOŞUL: Garmin'de 2FA (Two-Step Verification) TAMAMEN KAPALI olmalı —
garminconnect 2FA desteklemez; kapalıyken cloudscraper Cloudflare'i geçince
kod sorulmadan giriş yapar.

Şifre .env'den okunur (GARMIN_EMAIL / GARMIN_PASSWORD). Token ~/.garminconnect'e,
~1 yıl geçerli. Başarınca fetch_data.py / dashboard giriş yapmadan bu token'ı kullanır.
"""
from __future__ import annotations
import os
from pathlib import Path
from dotenv import load_dotenv
import cloudscraper
from garminconnect import Garmin

load_dotenv(str(Path(__file__).resolve().parent / ".env"))


def main() -> int:
    email = os.getenv("GARMIN_EMAIL")
    pw = os.getenv("GARMIN_PASSWORD")
    if not email or not pw:
        print("HATA: .env'de GARMIN_EMAIL / GARMIN_PASSWORD yok.")
        return 1
    ts = str(os.getenv("GARMINTOKENS") or Path.home() / ".garminconnect")
    Path(ts).mkdir(parents=True, exist_ok=True)

    print(f"Giriş yapılıyor (cloudscraper → Cloudflare bypass): {email[:3]}***")
    try:
        client = Garmin(email, pw)
        # KRİTİK: garth'ın HTTP oturumunu cloudscraper ile değiştir → Cloudflare geçilir.
        client.garth.sess = cloudscraper.create_scraper()
        client.login()
        client.garth.dump(ts)
    except Exception as exc:  # noqa: BLE001
        msg = str(exc)
        print(f"\nGiriş başarısız: {type(exc).__name__}: {msg[:300]}")
        low = msg.lower()
        if any(k in low for k in ("mfa", "2fa", "credential", "401", "unauthorized")):
            print("\n→ 2FA hâlâ açık olabilir. Garmin → Security Center →\n"
                  "  Two-Step Verification → E-mail ve SMS ikisini de OFF yap, tekrar dene.")
        elif any(k in low for k in ("cloudflare", "captcha", "403", "no profile")):
            print("\n→ Cloudflare/sunucu geçici engeli. Birkaç dk bekleyip tekrar dene "
                  "(üst üste deneme).")
        return 1

    print(f"\n✓ BAŞARILI. Token kaydedildi: {ts}")
    print("Artık günlük otomatik veri çekimi giriş gerektirmez (~1 yıl).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
