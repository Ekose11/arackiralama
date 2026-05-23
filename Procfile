<!doctype html>
<html lang="tr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Araç Kiralama Paneli</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
</head>
<body>
  <div class="wrap">
    <header>
      <div>
        <h1>Araç Kiralama Paneli</h1>
        <p>Araç ekle, fotoğraf yükle, günlük fiyat ve rezervasyon yönet.</p>
      </div>
      <div class="badge">Render Uyumlu</div>
    </header>

    {% with messages = get_flashed_messages(with_categories=true) %}
      {% if messages %}
        <div class="messages">
          {% for category, message in messages %}
            <div class="msg {{ category }}">{{ message }}</div>
          {% endfor %}
        </div>
      {% endif %}
    {% endwith %}

    <section class="stats">
      <div class="stat"><span>Toplam Araç</span><strong>{{ total_cars }}</strong></div>
      <div class="stat"><span>Müsait</span><strong>{{ available_cars }}</strong></div>
      <div class="stat"><span>Kirada</span><strong>{{ rented_cars }}</strong></div>
    </section>

    <section class="grid two">
      <div class="card">
        <h2>Araç Ekle</h2>
        <form action="/add" method="post" enctype="multipart/form-data">
          <div class="row"><input name="brand" placeholder="Marka: Renault" required><input name="model" placeholder="Model: Clio" required></div>
          <div class="row"><input name="year" placeholder="Yıl: 2020"><input name="plate" placeholder="Plaka: 11 ABC 111"></div>
          <div class="row"><input name="daily_price" type="number" step="0.01" placeholder="Günlük fiyat" required><select name="status"><option>Müsait</option><option>Kirada</option></select></div>
          <input type="file" name="image" accept="image/*">
          <button type="submit">Aracı Kaydet</button>
        </form>
      </div>

      <div class="card">
        <h2>Rezervasyon Oluştur</h2>
        <form action="/reserve" method="post">
          <select name="car_id" required>
            <option value="">Araç seç</option>
            {% for car in cars %}
              <option value="{{ car.id }}">{{ car.brand }} {{ car.model }} - {{ car.plate or 'Plaka yok' }}</option>
            {% endfor %}
          </select>
          <div class="row"><input name="customer_name" placeholder="Müşteri adı" required><input name="phone" placeholder="Telefon"></div>
          <div class="row"><input name="start_date" type="date" required><input name="end_date" type="date" required></div>
          <input name="note" placeholder="Not">
          <button type="submit">Rezervasyon Kaydet</button>
        </form>
      </div>
    </section>

    <section class="card">
      <h2>Araç Listesi</h2>
      <div class="cars">
        {% for car in cars %}
          <div class="car">
            <div class="img">
              {% if car.image %}<img src="{{ url_for('static', filename='uploads/' ~ car.image) }}" alt="Araç">{% else %}<span>Resim Yok</span>{% endif %}
            </div>
            <div class="car-body">
              <h3>{{ car.brand }} {{ car.model }}</h3>
              <p>{{ car.year or '-' }} · {{ car.plate or 'Plaka yok' }}</p>
              <strong>{{ '%.2f'|format(car.daily_price) }} TL / Gün</strong>
              <div class="status {{ 'ok' if car.status == 'Müsait' else 'busy' }}">{{ car.status }}</div>
              <div class="actions">
                <a href="/status/{{ car.id }}/musait">Müsait Yap</a>
                <a href="/status/{{ car.id }}/kirada">Kirada Yap</a>
                <a class="danger" href="/delete/{{ car.id }}" onclick="return confirm('Araç silinsin mi?')">Sil</a>
              </div>
            </div>
          </div>
        {% else %}
          <p class="empty">Henüz araç eklenmedi.</p>
        {% endfor %}
      </div>
    </section>

    <section class="card">
      <h2>Rezervasyonlar</h2>
      <div class="table-wrap">
        <table>
          <thead><tr><th>Müşteri</th><th>Telefon</th><th>Araç</th><th>Tarih</th><th>Not</th><th></th></tr></thead>
          <tbody>
          {% for r in reservations %}
            <tr>
              <td>{{ r.customer_name }}</td><td>{{ r.phone }}</td><td>{{ r.brand }} {{ r.model }} {{ r.plate or '' }}</td><td>{{ r.start_date }} / {{ r.end_date }}</td><td>{{ r.note }}</td><td><a class="danger" href="/reservation/delete/{{ r.id }}">Sil</a></td>
            </tr>
          {% else %}
            <tr><td colspan="6">Henüz rezervasyon yok.</td></tr>
          {% endfor %}
          </tbody>
        </table>
      </div>
    </section>
  </div>
</body>
</html>
