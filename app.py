import os
import sqlite3
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "rentacar.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "rentacar-secret-key")
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
            plate TEXT,
            year INTEGER,
            daily_price REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Müsait',
            image TEXT,
            note TEXT,
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
            total_price REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Aktif',
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
    total_cars = conn.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    available = conn.execute("SELECT COUNT(*) FROM cars WHERE status='Müsait'").fetchone()[0]
    rented = conn.execute("SELECT COUNT(*) FROM cars WHERE status='Kirada'").fetchone()[0]
    reservations = conn.execute(
        """
        SELECT r.*, c.brand, c.model, c.plate
        FROM reservations r
        JOIN cars c ON c.id = r.car_id
        ORDER BY r.id DESC LIMIT 8
        """
    ).fetchall()
    conn.close()
    return render_template("index.html", cars=cars, total_cars=total_cars, available=available, rented=rented, reservations=reservations)


@app.route("/cars/new", methods=["GET", "POST"])
def new_car():
    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        plate = request.form.get("plate", "").strip()
        year = request.form.get("year") or None
        daily_price = request.form.get("daily_price") or 0
        status = request.form.get("status", "Müsait")
        note = request.form.get("note", "").strip()
        image_name = None

        if not brand or not model:
            flash("Marka ve model zorunludur.", "error")
            return redirect(url_for("new_car"))

        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Sadece png, jpg, jpeg, webp veya gif yükleyebilirsin.", "error")
                return redirect(url_for("new_car"))
            filename = secure_filename(file.filename)
            image_name = f"{int(datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        conn = get_db()
        conn.execute(
            """
            INSERT INTO cars (brand, model, plate, year, daily_price, status, image, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (brand, model, plate, year, daily_price, status, image_name, note, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.commit()
        conn.close()
        flash("Araç başarıyla eklendi.", "success")
        return redirect(url_for("index"))

    return render_template("car_form.html", car=None)


@app.route("/cars/<int:car_id>/edit", methods=["GET", "POST"])
def edit_car(car_id):
    conn = get_db()
    car = conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
    if not car:
        conn.close()
        flash("Araç bulunamadı.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        brand = request.form.get("brand", "").strip()
        model = request.form.get("model", "").strip()
        plate = request.form.get("plate", "").strip()
        year = request.form.get("year") or None
        daily_price = request.form.get("daily_price") or 0
        status = request.form.get("status", "Müsait")
        note = request.form.get("note", "").strip()
        image_name = car["image"]

        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                conn.close()
                flash("Resim formatı uygun değil.", "error")
                return redirect(url_for("edit_car", car_id=car_id))
            filename = secure_filename(file.filename)
            image_name = f"{int(datetime.now().timestamp())}_{filename}"
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], image_name))

        conn.execute(
            """
            UPDATE cars SET brand=?, model=?, plate=?, year=?, daily_price=?, status=?, image=?, note=? WHERE id=?
            """,
            (brand, model, plate, year, daily_price, status, image_name, note, car_id),
        )
        conn.commit()
        conn.close()
        flash("Araç güncellendi.", "success")
        return redirect(url_for("index"))

    conn.close()
    return render_template("car_form.html", car=car)


@app.route("/cars/<int:car_id>/delete", methods=["POST"])
def delete_car(car_id):
    conn = get_db()
    conn.execute("DELETE FROM reservations WHERE car_id=?", (car_id,))
    conn.execute("DELETE FROM cars WHERE id=?", (car_id,))
    conn.commit()
    conn.close()
    flash("Araç silindi.", "success")
    return redirect(url_for("index"))


@app.route("/reservations", methods=["GET", "POST"])
def reservations():
    conn = get_db()
    if request.method == "POST":
        car_id = request.form.get("car_id")
        customer_name = request.form.get("customer_name", "").strip()
        phone = request.form.get("phone", "").strip()
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        total_price = request.form.get("total_price") or 0

        if not car_id or not customer_name or not start_date or not end_date:
            conn.close()
            flash("Araç, müşteri adı, başlangıç ve bitiş tarihi zorunludur.", "error")
            return redirect(url_for("reservations"))

        conn.execute(
            """
            INSERT INTO reservations (car_id, customer_name, phone, start_date, end_date, total_price, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'Aktif', ?)
            """,
            (car_id, customer_name, phone, start_date, end_date, total_price, datetime.now().strftime("%Y-%m-%d %H:%M")),
        )
        conn.execute("UPDATE cars SET status='Kirada' WHERE id=?", (car_id,))
        conn.commit()
        flash("Rezervasyon oluşturuldu.", "success")
        conn.close()
        return redirect(url_for("reservations"))

    cars = conn.execute("SELECT * FROM cars ORDER BY brand, model").fetchall()
    reservations_list = conn.execute(
        """
        SELECT r.*, c.brand, c.model, c.plate
        FROM reservations r
        JOIN cars c ON c.id = r.car_id
        ORDER BY r.id DESC
        """
    ).fetchall()
    conn.close()
    return render_template("reservations.html", cars=cars, reservations=reservations_list)


@app.route("/reservations/<int:reservation_id>/finish", methods=["POST"])
def finish_reservation(reservation_id):
    conn = get_db()
    reservation = conn.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone()
    if reservation:
        conn.execute("UPDATE reservations SET status='Tamamlandı' WHERE id=?", (reservation_id,))
        conn.execute("UPDATE cars SET status='Müsait' WHERE id=?", (reservation["car_id"],))
        conn.commit()
    conn.close()
    flash("Rezervasyon tamamlandı, araç müsait yapıldı.", "success")
    return redirect(url_for("reservations"))


@app.route("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
