from flask import Flask, render_template, request
import mysql.connector
import qrcode
import io
import base64

app = Flask(__name__)

# -------------------- DATABASE --------------------

def get_db_connection():
    return mysql.connector.connect(
        host="metro.proxy.rlwy.net",
        user="root",
        password="ZCrXqGuTnPlHvFKQRXUIEqyQyagoAblB",   # 🔴 replace this
        database="railway",
        port=26996
    )

# -------------------- HOME --------------------

@app.route("/")
def home():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, movie_name, poster FROM movies")
        movies = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("index.html", movies=movies)

    except Exception as e:
        return f"ERROR in home(): {str(e)}"


# -------------------- SHOWS --------------------

@app.route("/shows/<int:movie_id>")
def shows(movie_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT shows.id, shows.screen, shows.show_time, movies.movie_name
            FROM shows
            JOIN movies ON shows.movie_id = movies.id
            WHERE movies.id = %s
        """, (movie_id,))

        shows = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("shows.html", shows=shows)

    except Exception as e:
        return f"ERROR in shows(): {str(e)}"


# -------------------- SEATS --------------------

@app.route("/seats")
def seats():
    try:
        show_id = request.args.get("show_id")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT seats FROM bookings WHERE show_id = %s",
            (show_id,)
        )

        data = cursor.fetchall()

        booked_seats = []
        for row in data:
            if row[0]:
                booked_seats += row[0].split(",")

        cursor.close()
        conn.close()

        return render_template(
            "seats.html",
            booked_seats=booked_seats,
            show_id=show_id
        )

    except Exception as e:
        return f"ERROR in seats(): {str(e)}"


# -------------------- PAYMENT --------------------

@app.route("/payment")
def payment():
    seats = request.args.get("seats")
    show_id = request.args.get("show_id")

    return render_template(
        "payment.html",
        seats=seats,
        show_id=show_id
    )


# -------------------- CONFIRMATION --------------------

@app.route("/confirmation")
def confirmation():
    try:
        seats = request.args.get("seats")
        show_id = request.args.get("show_id")
        method = request.args.get("method")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO bookings (show_id, seats, payment_method) VALUES (%s, %s, %s)",
            (show_id, seats, method)
        )

        conn.commit()
        booking_id = cursor.lastrowid

        cursor.close()
        conn.close()

        # ✅ Railway public URL (CHANGE THIS)
        BASE_URL = "web-production-cd13de.up.railway.app"

        qr_data = f"{BASE_URL}/verify?booking_id={booking_id}"

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

    except Exception as e:
        return f"ERROR in confirmation(): {str(e)}"


# -------------------- VERIFY --------------------

@app.route("/verify")
def verify():
    try:
        booking_id = request.args.get("booking_id")

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
        <body style="font-family:Arial; text-align:center;">
            <h1>✅ Booking Verified</h1>
            <p><b>Booking ID:</b> {booking_id}</p>
            <p><b>Show ID:</b> {booking[0]}</p>
            <p><b>Seats:</b> {booking[1]}</p>
            <p><b>Payment:</b> {booking[2]}</p>
        </body>
        </html>
        """

    except Exception as e:
        return f"ERROR in verify(): {str(e)}"


# -------------------- FEEDBACK --------------------

@app.route("/feedback")
def feedback():
    return render_template("feedback.html")


@app.route("/submit_feedback", methods=["POST"])
def submit_feedback():
    try:
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

    except Exception as e:
        return f"ERROR in feedback(): {str(e)}"


# -------------------- CANCEL --------------------

@app.route("/cancel")
def cancel():
    return render_template("cancel.html")


@app.route("/cancel_preview", methods=["POST"])
def cancel_preview():
    try:
        booking_id = request.form.get("booking_id")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

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
            return "<h3>❌ Booking not found</h3>"

        return render_template("cancel_preview.html", booking=booking)

    except Exception as e:
        return f"ERROR in cancel_preview(): {str(e)}"


@app.route("/confirm_cancel", methods=["POST"])
def confirm_cancel():
    try:
        booking_id = request.form.get("booking_id")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT seats, payment_method FROM bookings WHERE id = %s",
            (booking_id,)
        )

        booking = cursor.fetchone()

        if not booking:
            return "<h3>Booking not found</h3>"

        seat_count = len(booking["seats"].split(","))
        refund_amount = seat_count * 200

        cursor.execute("DELETE FROM bookings WHERE id = %s", (booking_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return render_template(
            "refund.html",
            booking_id=booking_id,
            seat_count=seat_count,
            refund_amount=refund_amount,
            payment_method=booking["payment_method"]
        )

    except Exception as e:
        return f"ERROR in cancel(): {str(e)}"


# -------------------- RUN --------------------

if __name__ == "__main__":
    app.run()