from flask import Flask, render_template, request
from database import get_db_connection
import qrcode
import io
import base64
import os
import razorpay



app = Flask(__name__)

# -------------------- HOME --------------------

@app.route("/")
def home():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, movie_name, poster FROM movies")
    rows = cursor.fetchall()

    movies = []
    for row in rows:
        movies.append({
            "id": row[0],
            "movie_name": row[1],
            "poster": row[2]
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

    return render_template("seats.html",
                           booked_seats=booked_seats,
                           show_id=show_id)


# -------------------- PAYMENT --------------------
client = razorpay.Client(auth=("rzp_test_SdcdrsUYh4HLqZ", "8z7n8lHaSJ2oCx3IifP8Sq8l"))
@app.route('/payment')
def payment():
    seats = request.args.get('seats')
    show_id = request.args.get('show_id')

    if not seats:
        return "Seats not selected", 400

    seat_list = [s for s in seats.split(',') if s.strip() != ""]
    ticket_count = len(seat_list)

    # 💰 pricing logic
    price_per_ticket = 150
    subtotal = ticket_count * price_per_ticket
    gst = subtotal * 0.18
    total = subtotal + gst

    order = client.order.create({
        "amount": int(total * 100),  # paise
        "currency": "INR",
        "payment_capture": 1
    })

    return render_template(
        "payment.html",
        seats=seats,
        show_id=show_id,
        order=order,
        amount=total,
        ticket_count=ticket_count,
        price_per_ticket=price_per_ticket,
        subtotal=subtotal,
        gst=gst,
        total=total
    )

@app.route('/success')
def success():
    payment_id = request.args.get('payment_id')
    show_id = request.args.get('show_id')
    seats = request.args.get('seats')

    conn = get_db_connection()
    cur = conn.cursor()

    # ✅ SINGLE INSERT ONLY
    cur.execute("""
        INSERT INTO bookings (show_id, seats, payment_method)
        VALUES (%s, %s, %s)
        RETURNING id
    """, (show_id, seats, "Razorpay"))

    booking_id = cur.fetchone()[0]
    conn.commit()

    import qrcode, io, base64, os

    base_url = os.getenv("RENDER_EXTERNAL_URL", "http://localhost:5000")

    qr_data = f"{base_url}/verify?booking_id={booking_id}"

    qr = qrcode.make(qr_data)
    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")
    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    cur.close()
    conn.close()

    return render_template(
        "confirmation.html",
        booking_id=booking_id,
        show_id=show_id,
        seats=seats,
        method="Razorpay",
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





# -------------------- CANCEL PAGE --------------------

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


@app.route("/cancel_preview", methods=["POST"])
def cancel_preview():

    booking_id = request.form.get("booking_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT bookings.id, bookings.seats, bookings.payment_method,
               shows.screen, shows.show_time,
               movies.movie_name
        FROM bookings
        JOIN shows ON bookings.show_id = shows.id
        JOIN movies ON shows.movie_id = movies.id
        WHERE bookings.id = %s
    """, (booking_id,))

    booking = cursor.fetchone()

    cursor.close()
    conn.close()

    if not booking:
        return "<h3 style='color:red;text-align:center;'>❌ Booking not found</h3>"

    booking_data = {
        "id": booking[0],
        "seats": booking[1],
        "payment_method": booking[2],
        "screen": booking[3],
        "show_time": booking[4],
        "movie_name": booking[5]
    }

    return render_template("cancel_preview.html", booking=booking_data)


@app.route("/confirm_cancel", methods=["POST"])
def confirm_cancel():

    booking_id = request.form.get("booking_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get booking first
    cursor.execute(
        "SELECT seats, payment_method FROM bookings WHERE id = %s",
        (booking_id,)
    )

    booking = cursor.fetchone()

    if not booking:
        return "<h3 style='color:red;text-align:center;'>Booking not found</h3>"

    seats = booking[0].split(",")
    seat_count = len(seats)

    ticket_price = 200
    refund_amount = seat_count * ticket_price

    # Delete booking
    cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
    conn.commit()

    cursor.close()
    conn.close()

    return render_template(
        "refund.html",
        booking_id=booking_id,
        seat_count=seat_count,
        refund_amount=refund_amount,
        payment_method=booking[1]
    )

# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run()