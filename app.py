from flask import Flask, render_template, request
from database import get_db_connection
import qrcode
import io
import base64
import os

app = Flask(__name__)

# -------------------- HOME --------------------

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, movie_name FROM movies")
    rows = cursor.fetchall()

    movies = []
    for row in rows:
        movies.append({
            "id": row[0],
            "movie_name": row[1]
        })

    cursor.close()
    conn.close()

    return render_template("index.html", movies=movies)


# -------------------- SHOWS --------------------

@app.route("/shows/<int:movie_id>")
def shows(movie_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT shows.id, shows.screen, shows.show_time, movies.movie_name
        FROM shows
        JOIN movies ON shows.movie_id = movies.id
        WHERE movies.id = %s
        ORDER BY shows.screen ASC, shows.show_time ASC
    """, (movie_id,))

    rows = cursor.fetchall()

    shows = []
    for row in rows:
        shows.append({
            "id": row[0],
            "screen": row[1],
            "show_time": row[2],
            "movie_name": row[3]
        })

    cursor.close()
    conn.close()

    return render_template("shows.html", shows=shows)


# -------------------- SEATS --------------------

@app.route('/seats')
def seats():
    show_id = request.args.get('show_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT seats FROM bookings WHERE show_id = %s", (show_id,))
    data = cursor.fetchall()

    booked_seats = []
    for row in data:
        booked_seats += row[0].split(",")

    cursor.close()
    conn.close()

    return render_template(
        "seats.html",
        booked_seats=booked_seats,
        show_id=show_id
    )


# -------------------- PAYMENT --------------------

@app.route('/payment')
def payment():
    seats = request.args.get('seats')
    show_id = request.args.get('show_id')

    return render_template(
        "payment.html",
        seats=seats,
        show_id=show_id
    )


# -------------------- CONFIRMATION --------------------

@app.route('/confirmation')
def confirmation():
    seats = request.args.get('seats')
    show_id = request.args.get('show_id')
    method = request.args.get('method')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO bookings (show_id, seats, payment_method) VALUES (%s, %s, %s) RETURNING id",
        (show_id, seats, method)
    )

    booking_id = cursor.fetchone()[0]
    conn.commit()

    cursor.close()
    conn.close()

    # Use deployed URL instead of localhost
    base_url = os.getenv("RENDER_EXTERNAL_URL", "")
    qr_data = f"{base_url}/verify?booking_id={booking_id}"

    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    return render_template(
        "confirmation.html",
        booking_id=booking_id,
        show_id=show_id,
        seats=seats,
        method=method,
        qr_code=qr_base64
    )


# -------------------- VERIFY --------------------

@app.route('/verify')
def verify():
    booking_id = request.args.get('booking_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT show_id, seats, payment_method FROM bookings WHERE id = %s",
        (booking_id,)
    )

    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    if not booking:
        return "<h2>❌ Invalid Booking</h2>"

    return f"""
    <html>
    <body style="font-family:Arial; text-align:center; background:#0f172a; color:white;">
    <h1>✅ Booking Verified</h1>
    <div style="background:white; color:black; width:400px; margin:auto; padding:20px; border-radius:10px;">
    <p><b>Booking ID:</b> {booking_id}</p>
    <p><b>Show ID:</b> {booking[0]}</p>
    <p><b>Seats:</b> {booking[1]}</p>
    <p><b>Payment Method:</b> {booking[2]}</p>
    </div>
    </body>
    </html>
    """


# -------------------- FEEDBACK --------------------

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")


@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    name = request.form["name"]
    rating = request.form["rating"]
    comments = request.form["comments"]

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO feedback (name, rating, comments) VALUES (%s, %s, %s)",
        (name, rating, comments)
    )

    conn.commit()
    cursor.close()
    conn.close()

    return "<h2>Thank you for your feedback! 😊</h2>"


# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run()