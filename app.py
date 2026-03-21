from flask import Flask, render_template, request
from database import get_db_connection
import qrcode
import io
import base64
from datetime import datetime

app = Flask(__name__)

# -------------------- HOME --------------------
@app.route("/")
def home():
    return render_template("index.html")


# -------------------- SEATS PAGE --------------------
@app.route('/seats')
def seats():

    show_id = request.args.get('show_id')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch booked seats ONLY for this show
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


# -------------------- PAYMENT PAGE --------------------
@app.route('/payment')
def payment():

    seats = request.args.get('seats')
    show_id = request.args.get('show_id')

    print("Seats:", seats)
    print("Show ID:", show_id)

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
        "INSERT INTO bookings (show_id, seats, payment_method) VALUES (%s, %s, %s)",
        (show_id, seats, method)
    )

    conn.commit()

    # ✅ STEP 1: get booking_id
    booking_id = cursor.lastrowid

    cursor.close()
    conn.close()

    # ✅ STEP 2: create QR code
    import qrcode
    import io
    import base64

    qr_data = f"http://127.0.0.1:5000/verify?booking_id={booking_id}"

    qr = qrcode.make(qr_data)

    buffer = io.BytesIO()
    qr.save(buffer, format="PNG")

    qr_base64 = base64.b64encode(buffer.getvalue()).decode()

    # ✅ STEP 3: render template AFTER variables exist
    return render_template(
        "confirmation.html",
        booking_id=booking_id,
        show_id=show_id,
        seats=seats,
        method=method,
        qr_code=qr_base64
    )
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
    <head>
    <title>Verify Ticket</title>
    </head>
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

    cursor.close()
    conn.close()

    return "<h2>✅ Booking Confirmed!</h2>"


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

    query = "INSERT INTO feedback (name, rating, comments) VALUES (%s, %s, %s)"
    cursor.execute(query, (name, rating, comments))

    conn.commit()

    cursor.close()
    conn.close()

    return "<h2>Thank you for your feedback! 😊</h2>"


# -------------------- RUN APP --------------------
if __name__ == "__main__":
    app.run(debug=True)