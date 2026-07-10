from flask import Flask, render_template, redirect, request, session, url_for, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
import requests

from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer

app = Flask(__name__)

app.secret_key = "your_secret_key_here"

app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 587
app.config["MAIL_USE_TLS"] = True
app.config["MAIL_USERNAME"] = "phangkykurkalang12@gmail.com"
app.config["MAIL_PASSWORD"] = "qlww wrfi mssl iiyn"
app.config["MAIL_DEFAULT_SENDER"] = "phangkykurkalang12@gmail.com"

mail = Mail(app)

serializer = URLSafeTimedSerializer(app.secret_key)

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="rmsDB",
        user="postgres",
        password="0000"
    )
    return conn

def create_users_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Books table created successfully.")

def create_products_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id SERIAL PRIMARY KEY,
            product_name VARCHAR(255) NOT NULL,
            category VARCHAR(100),
            brand VARCHAR(100),
            price NUMERIC(10,2),
            quantity INTEGER,
            sku VARCHAR(100) UNIQUE,
            supplier VARCHAR(255),
            description TEXT
                   )
    """)
    conn.commit()
    cursor.close()
    conn.close()

    print("Products table created successfully.")

@app.route("/")
def home():
    return redirect("/login")

@app.route("/admin/dashboard")
def dashboard():
    return render_template("admin/dashboard.html")


@app.route("/admin/add_product", methods=["GET", "POST"])
def add_product():
    if request.method =="POST":
        product_name = request.form["product_name"]
        category = request.form["category"]
        brand = request.form["brand"]
        price = request.form["price"]
        quantity = request.form["quantity"]
        sku = request.form["sku"]
        supplier = request.form["supplier"]
        description = request.form["description"]
        
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (
                product_name,
                category,
                brand,
                price,
                quantity,
                sku,
                supplier,
                description
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            product_name,
            category,
            brand,
            price,
            quantity,
            sku,
            supplier,
            description
        ))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Product added successfully!", "success")

        return redirect(url_for("add_product"))

    return render_template("admin/add_product.html")

@app.route("/admin/available_stock")
def available_stock():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY product_name
    """)

    stocks = cursor.fetchall()

    total_products = len(stocks)

    total_stock = sum(row[5] for row in stocks)

    low_stock = sum(
        1 for row in stocks
        if row[5] > 0 and row[5] <= 10
    )

    out_stock = sum(
        1 for row in stocks
        if row[5] == 0
    )

    cursor.close()
    conn.close()

    return render_template(
        "admin/available_stocks.html",
        stocks=stocks,
        total_products=total_products,
        total_stock=total_stock,
        low_stock=low_stock,
        out_stock=out_stock
    )

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match!"

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users(username, email, password)
            VALUES (%s, %s, %s)
        """, (username, email, hashed_password))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        print("Email:", email)
        print("Password:", password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM users
            WHERE email=%s
        """, (email,))
        user = cursor.fetchone()

        print("User found:", user)

        cursor.close()
        conn.close()

        if user and check_password_hash(user[3], password):
            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]

            return redirect("/admin/dashboard")

        print("Login Failed")
        return "Invalid email or password"

    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form["email"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT * FROM users WHERE email = %s",
            (email,))

        user = cursor.fetchone()

        conn.commit()
        conn.close()

        if user:
            token = serializer.dumps(email)

            reset_link = f"http://127.0.0.1:5000/reset-password/{token}"

            msg = Message(
                subject = "BookNest Password Reset",
                recipients=[email]
            )

            msg.body = f"""
        Hello,

        Someone requested to reset your password.

        Click the link below:

        {reset_link}

        This link expires in 15 minutes.

        If you did not request this, simply ignore this email.

        BookNest Team
            """

            mail.send(msg)

            return "Password reset email has been sent successfully."

    return render_template("forgot_password.html")

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = serializer.loads(token, max_age=900)
    except:
        return "Invalid or Expired Link"
    
    if request.method == 'POST':
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            return "Password do not match"
        
        hashed_password = generate_password_hash(new_password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """UPDATE users SET password = %s WHERE email = %s""",
            (hashed_password, email))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect("/login")

    return render_template("reset_password.html", token=token)

@app.route("/change-password", methods=["GET", "POST"])
def change_password():

    if "user_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        current_password = request.form["current_password"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if new_password != confirm_password:
            flash("New passwords do not match.", "danger")
            return redirect(url_for("change_password"))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get the current hashed password
        cursor.execute(
            "SELECT password FROM users WHERE id = %s",
            (session["user_id"],)
        )

        user = cursor.fetchone()

        if not user:
            cursor.close()
            conn.close()
            flash("User not found.", "danger")
            return redirect(url_for("login"))

        # Verify current password
        if not check_password_hash(user[0], current_password):
            cursor.close()
            conn.close()
            flash("Current password is incorrect.", "danger")
            return redirect(url_for("change_password"))

        # Hash the new password
        hashed_password = generate_password_hash(new_password)

        # Update password
        cursor.execute(
            "UPDATE users SET password = %s WHERE id = %s",
            (hashed_password, session["user_id"])
        )

        conn.commit()

        cursor.close()
        conn.close()

        flash("Password updated successfully!", "success")

        return redirect(url_for("dashboard"))

    return render_template("change_password.html")

@app.route("/change-email", methods=["GET", "POST"])
def change_email():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT email FROM users WHERE id = %s",
        (session["user_id"],)
    )

    current_email = cursor.fetchone()[0]

    if request.method == "POST":

        new_email = request.form["new_email"]
        confirm_email = request.form["confirm_email"]

        if new_email != confirm_email:
            flash("Email addresses do not match.", "danger")
            cursor.close()
            conn.close()
            return render_template(
                "change_email.html",
                current_email=current_email
            )

        cursor.execute(
            "SELECT id FROM users WHERE email = %s",
            (new_email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:
            flash("This email is already registered.", "danger")
            cursor.close()
            conn.close()
            return render_template(
                "change_email.html",
                current_email=current_email
            )

        cursor.execute(
            "UPDATE users SET email = %s WHERE id = %s",
            (new_email, session["user_id"])
        )

        conn.commit()

        session["email"] = new_email

        flash("Email updated successfully!", "success")

        cursor.close()
        conn.close()

        return redirect(url_for("dashboard"))

    cursor.close()
    conn.close()

    return render_template(
        "change_email.html",
        current_email=current_email
    )

@app.route("/delete-account", methods=["GET", "POST"])
def delete_account():

    if "user_id" not in session:
        return redirect("/login")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM users WHERE id = %s",
        (session["user_id"],)
    )

    conn.commit()

    cursor.close()
    conn.close()

    session.clear()

    flash("Your account has been deleted successfully.", "success")

    return redirect("/login")

@app.route("/admin/new-orders")
def new_orders():
    return render_template("admin/new_orders.html")


@app.route("/api/search_product/<barcode>")
def search_product(barcode):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            product_name,
            category,
            brand,
            price,
            quantity,
            supplier,
            description
        FROM products
        WHERE sku = %s
    """, (barcode,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if product:

        return jsonify({
            "found": True,
            "source": "local",
            "product_name": product[0],
            "category": product[1],
            "brand": product[2],
            "price": product[3],
            "quantity": product[4],
            "supplier": product[5],
            "description": product[6]
        })

    return jsonify({
        "found": False
    })


if __name__ == "__main__":
    create_users_table()
    create_products_table()
    app.run(host="0.0.0.0", port=5000, debug=True)
