import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
DB_PATH = os.path.join(BASE_DIR, "database.db")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "arac-kiralama-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024


def allowed_file(filename):
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
            plate TEXT,
            year TEXT,
            daily_price REAL NOT NULL,
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
            start_date TEXT,
            end_date TEXT,
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
        JOIN cars ON cars.id = reservations.car_id
        ORDER BY reservations.id DESC
        LIMIT 20
        """
    ).fetchall()
    conn.close()
    return render_template("index.html", cars=cars, reservations=reservations)


@app.route("/add", methods=["POST"])
def add_car():
    brand = request.form.get("brand", "").strip()
    model = request.form.get("model", "").strip()
    plate = request.form.get("plate", "").strip()
    year = request.form.get("year", "").strip()
    daily_price = request.form.get("daily_price", "0").replace(",", ".").strip()
    status = request.form.get("status", "Müsait")
    image_file = request.files.get("image")

    if not brand or not model:
        flash("Marka ve model zorunlu.")
        return redirect(url_for("index"))

    try:
        daily_price_value = float(daily_price)
    except ValueError:
        daily_price_value = 0

    image_name = None
    if image_file and image_file.filename:
        if allowed_file(image_file.filename):
            safe_name = secure_filename(image_file.filename)
            image_name = f"{int(datetime.now().timestamp())}_{safe_name}"
            image_file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))
        else:
            flash("Sadece jpg, png, webp, gif yükleyebilirsin.")
            return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO cars (brand, model, plate, year, daily_price, status, image, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (brand, model, plate, year, daily_price_value, status, image_name, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


@app.route("/status/<int:car_id>/<status>")
def change_status(car_id, status):
    if status not in ["Müsait", "Kirada", "Bakımda"]:
        status = "Müsait"
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
        path = os.path.join(UPLOAD_FOLDER, car["image"])
        if os.path.exists(path):
            try:
                os.remove(path)
            except OSError:
                pass
    return redirect(url_for("index"))


@app.route("/reserve/<int:car_id>", methods=["POST"])
def reserve(car_id):
    customer_name = request.form.get("customer_name", "").strip()
    phone = request.form.get("phone", "").strip()
    start_date = request.form.get("start_date", "").strip()
    end_date = request.form.get("end_date", "").strip()
    note = request.form.get("note", "").strip()

    if not customer_name:
        flash("Müşteri adı zorunlu.")
        return redirect(url_for("index"))

    conn = get_db()
    conn.execute(
        """
        INSERT INTO reservations (car_id, customer_name, phone, start_date, end_date, note, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (car_id, customer_name, phone, start_date, end_date, note, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.execute("UPDATE cars SET status='Kirada' WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("index"))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
