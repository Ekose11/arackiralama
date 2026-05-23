# Araç Kiralama Server

Render ayarları:

Build Command:
python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt

Start Command:
gunicorn app:app --bind 0.0.0.0:$PORT

Önemli: Render'da servis tipi **Web Service**, runtime **Python** olmalı. GitHub'a zip dosyasını değil, zip içindeki dosyaları yükleyin.
