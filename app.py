import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rentacar.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "rentacar-secret-key")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS cars (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT NOT NULL,
            year TEXT,
            plate TEXT,
            daily_price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Müsait',
            image TEXT,
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
            note TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(car_id) REFERENCES cars(id)
        )
        """
    )
    conn.commit()
    conn.close()


@app.before_request
def before_request():
    init_db()


@app.route("/")
def index():
    conn = get_db()
    cars = conn.execute("SELECT * FROM cars ORDER BY id DESC").fetchall()
    reservations = conn.execute(
        """
        SELECT reservations.*, cars.brand, cars.model, cars.plate
        FROM reservations
        LEFT JOIN cars ON cars.id = reservations.car_id
        ORDER BY reservations.id DESC
        """
    ).fetchall()
    total_cars = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    available_cars = conn.execute("SELECT COUNT(*) FROM cars WHERE status='Müsait'").fetchone()[0]
    rented_cars = conn.execute("SELECT COUNT(*) FROM cars WHERE status='Kirada'").fetchone()[0]
    conn.close()
    return render_template(
        "index.html",
        cars=cars,
        reservations=reservations,
        total_cars=total_cars,
        available_cars=available_cars,
        rented_cars=rented_cars,
    )


@app.route("/add", methods=["POST"])
def add_car():
    brand = request.form.get("brand", "").strip()
    model = request.form.get("model", "").strip()
    year = request.form.get("year", "").strip()
    plate = request.form.get("plate", "").strip()
    daily_price = request.form.get("daily_price", "0").strip() or "0"
    status = request.form.get("status", "Müsait")

    if not brand or not model:
        flash("Marka ve model zorunlu.", "error")
        return redirect(url_for("index"))

    image_name = None
    file = request.files.get("image")
    if file and file.filename:
        if allowed_file(file.filename):
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1].lower()
            image_name = f"car_{int(datetime.now().timestamp())}.{ext}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))
        else:
            flash("Resim formatı desteklenmiyor. jpg, png, webp kullan.", "error")
            return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO cars (brand, model, year, plate, daily_price, status, image, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (brand, model, year, plate, float(daily_price), status, image_name, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    flash("Araç eklendi.", "success")
    return redirect(url_for("index"))


@app.route("/status/<int:car_id>/<status>")
def change_status(car_id, status):
    status = "Kirada" if status == "kirada" else "Müsait"
    conn = get_db()
    conn.execute("UPDATE cars SET status=? WHERE id=?", (status, car_id))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/delete/<int:car_id>")
def delete_car(car_id):
    conn = get_db()
    car = conn.execute("SELECT image FROM cars WHERE id=?", (car_id,)).fetchone()
    conn.execute("DELETE FROM reservations WHERE car_id=?", (car_id,))
    conn.execute("DELETE FROM cars WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    if car and car["image"]:
        img_path = os.path.join(app.config["UPLOAD_FOLDER"], car["image"])
        if os.path.exists(img_path):
            try:
                os.remove(img_path)
            except OSError:
                pass
    flash("Araç silindi.", "success")
    return redirect(url_for("index"))


@app.route("/reserve", methods=["POST"])
def reserve():
    car_id = request.form.get("car_id")
    customer_name = request.form.get("customer_name", "").strip()
    phone = request.form.get("phone", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    note = request.form.get("note", "").strip()

    if not car_id or not customer_name or not start_date or not end_date:
        flash("Rezervasyon için müşteri, araç ve tarihler zorunlu.", "error")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        "INSERT INTO reservations (car_id, customer_name, phone, start_date, end_date, note, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (car_id, customer_name, phone, start_date, end_date, note, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.execute("UPDATE cars SET status='Kirada' WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    flash("Rezervasyon oluşturuldu.", "success")
    return redirect(url_for("index"))


@app.route("/reservation/delete/<int:reservation_id>")
def delete_reservation(reservation_id):
    conn = get_db()
    conn.execute("DELETE FROM reservations WHERE id=?", (reservation_id,))
    conn.commit()
    conn.close()
    flash("Rezervasyon silindi.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
