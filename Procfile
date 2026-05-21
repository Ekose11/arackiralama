import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from werkzeug.utils import secure_filename

APP_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(APP_DIR, "static", "uploads")
DB_PATH = os.path.join(APP_DIR, "rentacar.db")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "degistirilecek-gizli-anahtar")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    with db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cars (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT NOT NULL,
                model TEXT NOT NULL,
                year INTEGER,
                plate TEXT,
                daily_price REAL NOT NULL,
                status TEXT NOT NULL DEFAULT 'Müsait',
                image TEXT,
                notes TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reservations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                car_id INTEGER NOT NULL,
                customer_name TEXT NOT NULL,
                phone TEXT,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                total_price REAL,
                status TEXT NOT NULL DEFAULT 'Aktif',
                created_at TEXT NOT NULL,
                FOREIGN KEY(car_id) REFERENCES cars(id)
            )
            """
        )


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def dashboard():
    with db() as conn:
        cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
        total = conn.execute("SELECT COUNT(*) c FROM cars").fetchone()["c"]
        available = conn.execute("SELECT COUNT(*) c FROM cars WHERE status='Müsait'").fetchone()["c"]
        rented = conn.execute("SELECT COUNT(*) c FROM cars WHERE status='Kirada'").fetchone()["c"]
        reservations = conn.execute(
            """
            SELECT r.*, c.brand, c.model, c.plate
            FROM reservations r
            JOIN cars c ON c.id = r.car_id
            ORDER BY r.id DESC LIMIT 8
            """
        ).fetchall()
    return render_template("dashboard.html", cars=cars, total=total, available=available, rented=rented, reservations=reservations)


@app.route("/cars/add", methods=["GET", "POST"])
def add_car():
    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        year = request.form.get("year") or None
        plate = request.form.get("plate", "").strip().upper()
        daily_price = request.form.get("daily_price") or 0
        status = request.form.get("status", "Müsait")
        notes = request.form.get("notes", "").strip()
        image_name = None

        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Sadece PNG, JPG, JPEG veya WEBP resim yükleyebilirsin.", "error")
                return redirect(url_for("add_car"))
            filename = secure_filename(file.filename)
            image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        if not brand or not model:
            flash("Marka ve model zorunlu.", "error")
            return redirect(url_for("add_car"))

        with db() as conn:
            conn.execute(
                """
                INSERT INTO cars (brand, model, year, plate, daily_price, status, image, notes, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (brand, model, year, plate, daily_price, status, image_name, notes, datetime.now().isoformat(timespec="seconds")),
            )
        flash("Araç başarıyla eklendi.", "success")
        return redirect(url_for("dashboard"))
    return render_template("car_form.html", car=None)


@app.route("/cars/<int:car_id>/edit", methods=["GET", "POST"])
def edit_car(car_id):
    with db() as conn:
        car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    if not car:
        flash("Araç bulunamadı.", "error")
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        image_name = car["image"]
        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Sadece PNG, JPG, JPEG veya WEBP resim yükleyebilirsin.", "error")
                return redirect(url_for("edit_car", car_id=car_id))
            filename = secure_filename(file.filename)
            image_name = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        with db() as conn:
            conn.execute(
                """
                UPDATE cars SET brand=?, model=?, year=?, plate=?, daily_price=?, status=?, image=?, notes=?
                WHERE id=?
                """,
                (
                    request.form.get("brand", "").strip(),
                    request.form.get("model", "").strip(),
                    request.form.get("year") or None,
                    request.form.get("plate", "").strip().upper(),
                    request.form.get("daily_price") or 0,
                    request.form.get("status", "Müsait"),
                    image_name,
                    request.form.get("notes", "").strip(),
                    car_id,
                ),
            )
        flash("Araç güncellendi.", "success")
        return redirect(url_for("dashboard"))
    return render_template("car_form.html", car=car)


@app.route("/cars/<int:car_id>/delete", methods=["POST"])
def delete_car(car_id):
    with db() as conn:
        conn.execute("DELETE FROM reservations WHERE car_id=?", (car_id,))
        conn.execute("DELETE FROM cars WHERE id=?", (car_id,))
    flash("Araç silindi.", "success")
    return redirect(url_for("dashboard"))


@app.route("/reservations/add", methods=["POST"])
def add_reservation():
    car_id = request.form.get("car_id")
    start_date = request.form.get("start_date")
    end_date = request.form.get("end_date")
    customer_name = request.form.get("customer_name", "").strip()
    phone = request.form.get("phone", "").strip()

    with db() as conn:
        car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
        if not car:
            flash("Araç bulunamadı.", "error")
            return redirect(url_for("dashboard"))
        try:
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            days = max((d2 - d1).days + 1, 1)
        except Exception:
            days = 1
        total_price = days * float(car["daily_price"])
        conn.execute(
            """
            INSERT INTO reservations (car_id, customer_name, phone, start_date, end_date, total_price, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (car_id, customer_name, phone, start_date, end_date, total_price, datetime.now().isoformat(timespec="seconds")),
        )
        conn.execute("UPDATE cars SET status='Kirada' WHERE id=?", (car_id,))
    flash("Rezervasyon oluşturuldu ve araç Kirada olarak işaretlendi.", "success")
    return redirect(url_for("dashboard"))


@app.route("/reservations/<int:reservation_id>/finish", methods=["POST"])
def finish_reservation(reservation_id):
    with db() as conn:
        res = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
        if res:
            conn.execute("UPDATE reservations SET status='Tamamlandı' WHERE id=?", (reservation_id,))
            conn.execute("UPDATE cars SET status='Müsait' WHERE id=?", (res["car_id"],))
    flash("Rezervasyon tamamlandı, araç müsait yapıldı.", "success")
    return redirect(url_for("dashboard"))


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
