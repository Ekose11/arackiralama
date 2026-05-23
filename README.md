# Rent A Car Panel

Render + GitHub uyumlu Flask araç kiralama paneli.

## Local çalıştırma
```bash
pip install -r requirements.txt
python app.py
```

## Render ayarları
Build Command:
```bash
pip install -r requirements.txt
```

Start Command:
```bash
gunicorn app:app
```

Not: Render ücretsiz planda SQLite ve yüklenen resimler yeniden deploy/sleep sonrası kalıcı olmayabilir. Gerçek kullanımda PostgreSQL ve cloud storage önerilir.
