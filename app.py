from flask import Flask, render_template, redirect, request, session, url_for, flash, jsonify, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer
import psycopg2

#For report making
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

#for bar code generation
import barcode
from barcode.writer import ImageWriter

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

UPLOAD_FOLDER = "static/uploads/resumes"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def get_db_connection():
    conn = psycopg2.connect(
        host="localhost",
        database="rmsDB",
        user="postgres",
        password="1234"
    )
    return conn

def create_table():
    conn = get_db_connection()
    cursor = conn.cursor()

    #Users table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id SERIAL PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL
        )
    """)

    #Product table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS products (
            id SERIAL PRIMARY KEY,
            product_name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            brand VARCHAR(50),
            sku VARCHAR(50) UNIQUE,
            barcode VARCHAR(50) UNIQUE,
            price DECIMAL(10,2),
            quantity INTEGER,
            supplier VARCHAR(100),
            expiry_date DATE,
            manufacture_date DATE,
            image VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    #Sale table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS sales(
            id SERIAL PRIMARY KEY,
            staff_id INTEGER,
            payment_method VARCHAR(20),
            total DECIMAL(10,2),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    """)

    #Sale Items table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS sale_items(
            id SERIAL PRIMARY KEY,
            sale_id INTEGER REFERENCES sales(id),
            product_id INTEGER,
            quantity INTEGER,
            price DECIMAL(10,2)
        )
    """)

    #Job vacancieq table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS job_vacancies (
            id SERIAL PRIMARY KEY,
            position VARCHAR(100) NOT NULL,
            department VARCHAR(100),
            vacancies INTEGER NOT NULL,
            salary DECIMAL(10,2),
            requirements TEXT,
            deadline DATE,
            status VARCHAR(20) DEFAULT 'Open',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    #Job Application table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS job_applications (
            id SERIAL PRIMARY KEY,
            vacancy_id INTEGER REFERENCES job_vacancies(id),
            full_name VARCHAR(100) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            address TEXT,
            qualification VARCHAR(100),
            experience TEXT,
            resume VARCHAR(255),
            status VARCHAR(20) DEFAULT 'Pending',
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    #Interview table
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS interviews (
            id SERIAL PRIMARY KEY,
            application_id INTEGER REFERENCES job_applications(id),
            interview_date DATE,
            interview_time TIME,
            interviewer VARCHAR(100),
            interview_type VARCHAR(50),
            location VARCHAR(255),
            remarks TEXT,
            status VARCHAR(20) DEFAULT 'Scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("Users and Products tables created successfully.")

@app.route("/")
def home():

    return render_template(
        "index.html",
        admin_exists=admin_exists()
    )
def admin_exists():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT COUNT(*)
        FROM users
        WHERE role = 'admin'
    """)

    count = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return count > 0

@app.route("/login")
def login():
    return render_template("login.html", admin_exists=admin_exists())

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():

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

            if user[4] != "admin":
                return "This account is not an admin."

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]

            return redirect("/admin/dashboard")

        print("Login Failed")
        return "Invalid email or password"
    return render_template("index.html")

@app.route("/admin/dashboard")
def admin_dashboard():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Sales
    cursor.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM sales
    """)
    total_sales = cursor.fetchone()[0]

    # Items Sold Today
    cursor.execute("""
        SELECT COALESCE(SUM(quantity),0)
        FROM sale_items
        WHERE sale_id IN (
            SELECT id
            FROM sales
            WHERE DATE(created_at)=CURRENT_DATE
        )
    """)
    items_sold = cursor.fetchone()[0]

    # Total Products
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)
    total_products = cursor.fetchone()[0]

    # Low Stock
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity < 10
    """)
    low_stock = cursor.fetchone()[0]

    # Recent Orders
    cursor.execute("""
        SELECT
            s.id,
            u.username,
            s.total,
            s.payment_method,
            s.created_at
        FROM sales s
        LEFT JOIN users u
            ON s.staff_id=u.id
        ORDER BY s.created_at DESC
        LIMIT 5
    """)

    recent_orders = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/dashboard.html",
        total_sales=total_sales,
        items_sold=items_sold,
        total_products=total_products,
        low_stock=low_stock,
        recent_orders=recent_orders
    )

@app.route("/admin/staff")
def staff():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               username,
               email,
               role
        FROM users
        WHERE role = 'staff'
        ORDER BY id DESC
    """)

    staffs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/staff.html",
        staffs=staffs
    )

@app.route("/admin/add_staff", methods=["POST"])
def add_staff():

    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("staff"))

    hashed_password = generate_password_hash(password)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO users
        (username, email, password, role)
        VALUES (%s, %s, %s, %s)
    """, (
        username,
        email,
        hashed_password,
        "staff"
    ))

    conn.commit()

    cursor.close()
    conn.close()

    flash("Staff account created successfully!", "success")

    return redirect(url_for("staff"))

@app.route("/admin/job_vacancies")
def job_vacancies():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM job_vacancies
        ORDER BY created_at DESC
    """)

    vacancies = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/job_vacancies.html",
        vacancies=vacancies
    )

@app.route("/admin/add_vacancy", methods=["POST"])
def add_vacancy():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO job_vacancies
        (position, department, vacancies, salary, requirements, deadline, status)
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (

        request.form["position"],
        request.form["department"],
        request.form["vacancies"],
        request.form["salary"],
        request.form["requirements"],
        request.form["deadline"],
        request.form["status"]

    ))

    conn.commit()
    cursor.close()
    conn.close()

    return redirect("/admin/job_vacancies")

@app.route("/admin/products")
def products():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin/products.html",
        products=products
    )

@app.route("/admin/add_product", methods=["GET", "POST"])
def add_product():

    if request.method == "POST":

        product_name = request.form["product_name"]
        category = request.form["category"]
        brand = request.form["brand"]
        sku = request.form["sku"]
        barcode = request.form["barcode"]
        price = request.form["price"]
        quantity = request.form["quantity"]
        supplier = request.form["supplier"]
        expiry_date = request.form["expiry_date"]
        manufacture_date = request.form["manufacture_date"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO products
            (product_name, category, brand, sku, barcode,
            price, quantity,supplier, expiry_date, manufacture_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                product_name,
                category,
                brand,
                sku,
                barcode,
                price,
                quantity,
                supplier,
                expiry_date,
                manufacture_date
            ))

        conn.commit()
        flash("✅ Product added successfully!", "success")
        cursor.close()
        conn.close()

        return redirect(url_for("products"))

    return render_template("/admin/partials/view_products.html")

@app.route("/generate_barcode/<code>")
def generate_barcode(code):

    ean = barcode.get("code128", code, writer=ImageWriter())
    filename = "static/barcodes/" + code
    barcode_image = "static/barcodes/" + barcode + ".png"
    ean.save(filename)
    return filename + ".png"

@app.route("/admin/partials/view_products")
def view_products():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               product_name,
               category,
               brand,
               sku,
               barcode,
               price,
               quantity
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "/admin/partials/view_products.html",
        products=products
    )

@app.route("/admin/new-orders")
def new_orders():
    barcode = request.args.get("barcode")
    return render_template("/admin/new_orders.html",barcode=barcode)

@app.route("/admin/reports")
def reports():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Total Revenue
    cursor.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM sales
    """)
    total_sales = cursor.fetchone()[0]

    # Orders
    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
    """)
    total_orders = cursor.fetchone()[0]

    # Products Sold
    cursor.execute("""
        SELECT COALESCE(SUM(quantity),0)
        FROM sale_items
    """)
    products_sold = cursor.fetchone()[0]

    # Low Stock
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
        WHERE quantity < 10
    """)
    low_stock = cursor.fetchone()[0]

    # Recent Orders
    cursor.execute("""
        SELECT
            s.id,
            u.username,
            s.total,
            s.payment_method,
            s.created_at
        FROM sales s
        JOIN users u
        ON s.staff_id = u.id
        ORDER BY s.created_at DESC
        LIMIT 10
    """)

    recent_orders = cursor.fetchall()

    #Top Products
    cursor.execute("""
        SELECT
        p.product_name,
        SUM(si.quantity) AS sold
        FROM sale_items si
        JOIN products p
        ON p.id=si.product_id
        GROUP BY p.product_name
        ORDER BY sold DESC
        LIMIT 10
    """)

    top_products = cursor.fetchall()

    #Staff Report
    cursor.execute("""
        SELECT
        u.username,
        COUNT(s.id),
        COALESCE(SUM(s.total),0)
        FROM users u
        LEFT JOIN sales s
        ON u.id=s.staff_id
        WHERE u.role='staff'
        GROUP BY u.username
        ORDER BY SUM(s.total) DESC NULLS LAST
    """)

    staff_report=cursor.fetchall()

    #Product with Low Stock
    cursor.execute("""
        SELECT
        product_name,
        quantity
        FROM products
        WHERE quantity<10
        ORDER BY quantity ASC
    """)

    low_stock_products=cursor.fetchall()

    #Bar Chart of the sale
    cursor.execute("""
        SELECT
        DATE(created_at),
        SUM(total)
        FROM sales
        WHERE created_at >= CURRENT_DATE - INTERVAL '6 days'
        GROUP BY DATE(created_at)
        ORDER BY DATE(created_at)
    """)

    chart_data = cursor.fetchall()

    #Pie Chart of the payment methods
    cursor.execute("""
        SELECT
        payment_method,
        COUNT(*)
        FROM sales
        GROUP BY payment_method
    """)

    payment_data=cursor.fetchall()

    cursor.close()
    conn.close()

    labels=[]
    sales=[]
    for row in chart_data:
        labels.append(row[0].strftime("%d %b"))
        sales.append(float(row[1]))

    payment_labels=[]
    payment_values=[]
    for row in payment_data:
        payment_labels.append(row[0])
        payment_values.append(row[1])

    return render_template(
        "admin/reports.html",

        total_sales=total_sales,
        total_orders=total_orders,
        products_sold=products_sold,
        low_stock=low_stock,

        recent_orders=recent_orders,
        top_products=top_products,
        staff_report=staff_report,
        low_stock_products=low_stock_products,
        labels=labels,
        sales=sales,
        payment_labels=payment_labels,
        payment_values=payment_values
    )

@app.route("/admin/report/pdf")
def report_pdf():

    filename = "sales_report.pdf"
    doc = SimpleDocTemplate(filename)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(
        Paragraph("<b>Retail Management Report</b>", styles["Title"])
    )

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
        id,
        total,
        payment_method,
        created_at
        FROM sales
        ORDER BY created_at DESC
    """)

    rows = cursor.fetchall()
    data = [["Invoice","Amount","Payment","Date"]]

    for r in rows:
        data.append([
            r[0],
            f"₹{r[1]}",
            r[2],
            str(r[3])
        ])

    table = Table(data)

    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.grey),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("GRID",(0,0),(-1,-1),1,colors.black),
        ("BACKGROUND",(0,1),(-1,-1),colors.beige)
    ]))

    elements.append(table)
    doc.build(elements)

    cursor.close()
    conn.close()

    return send_file(
        filename,
        as_attachment=True
    )

@app.route("/admin/register", methods=["GET", "POST"])
def register():

    if admin_exists():
        return redirect(url_for("home"))

    if request.method == "POST":

        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return "Passwords do not match."

        hashed_password = generate_password_hash(password)

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO users
            (username, email, password, role)
            VALUES (%s, %s, %s, %s)
        """,
        (
            username,
            email,
            hashed_password,
            "admin"
        ))

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("home"))

    return render_template("admin/register.html")

@app.route("/staff/login", methods=["GET", "POST"])
def staff_login():

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

            if user[4] != "staff":
                return "This account is not a staff account."

            session["user_id"] = user[0]
            session["username"] = user[1]
            session["email"] = user[2]
            session["role"] = user[4]

            return redirect("/staff/staff_dashboard")

        print("Login Failed")
        return "Invalid email or password"
    return render_template("staff/partials/staff_login.html")

@app.route("/staff/staff_dashboard")
def staff_dashboard():

    if "user_id" not in session:
        return redirect(url_for("home"))

    if session.get("role") != "staff":
        return redirect(url_for("home"))

    conn = get_db_connection()
    cursor = conn.cursor()

    staff_id = session["user_id"]

    # Today's Orders
    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
        WHERE staff_id=%s
        AND DATE(created_at)=CURRENT_DATE
    """, (staff_id,))

    todays_orders = cursor.fetchone()[0]

    # Products
    cursor.execute("""
        SELECT COUNT(*)
        FROM products
    """)

    total_products = cursor.fetchone()[0]

    # Sales Today
    cursor.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM sales
        WHERE staff_id=%s
        AND DATE(created_at)=CURRENT_DATE
    """, (staff_id,))

    sales_today = cursor.fetchone()[0]

    # Customers
    cursor.execute("""
        SELECT COUNT(*)
        FROM sales
        WHERE staff_id=%s
    """, (staff_id,))

    customers = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    return render_template(

        "staff/staff_dashboard.html",

        todays_orders=todays_orders,

        total_products=total_products,

        customers=customers,

        sales_today=sales_today

    )

@app.route("/staff/staff_products")
def staff_products():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "staff/staff_products.html",
        products=products
    )

@app.route("/staff/partials/staff_view_products")
def staff_view_products():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id,
               product_name,
               category,
               brand,
               sku,
               barcode,
               price,
               quantity
        FROM products
        ORDER BY id DESC
    """)

    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "/staff/partials/staff_view_products.html",
        products=products
    )

@app.route("/staff/staff_new_orders")
def staff_new_orders():

    barcode = request.args.get("barcode")

    conn = get_db_connection()
    cursor = conn.cursor()

    product = None

    if barcode:

        cursor.execute("""
            SELECT id,
                   product_name,
                   price,
                   quantity,
                   barcode
            FROM products
            WHERE barcode = %s
        """, (barcode,))

        product = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "staff/staff_new_orders.html",
        product=product,
        barcode=barcode
    )

@app.route("/staff/get_product", methods=["POST"])
def get_product():

    data = request.get_json()
    barcode = data["barcode"]

    conn = get_db_connection()      # however you connect
    cursor = conn.cursor()

    cursor.execute("""
        SELECT product_name, price, barcode
        FROM products
        WHERE barcode = %s
    """, (barcode,))

    product = cursor.fetchone()

    cursor.close()
    conn.close()

    if not product:
        return jsonify({"success": False})

    return jsonify({
        "success": True,
        "name": product[0],
        "price": float(product[1]),
        "barcode": product[2]
    })

@app.route("/staff/complete_order", methods=["POST"])
def complete_order():

    data = request.get_json()

    cart = data["cart"]
    payment_method = data["payment_method"]

    staff_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor()

    try:

        total = 0

        for item in cart:
            total += item["price"] * item["qty"]

        # Create sale
        cursor.execute("""
            INSERT INTO sales(staff_id, payment_method, total)
            VALUES (%s, %s, %s)
            RETURNING id
        """, (staff_id, payment_method, total))

        sale_id = cursor.fetchone()[0]

        # Save every product
        for item in cart:

            cursor.execute("""
                SELECT id
                FROM products
                WHERE barcode=%s
            """, (item["barcode"],))

            product = cursor.fetchone()

            if not product:
                continue

            product_id = product[0]

            cursor.execute("""
                INSERT INTO sale_items
                (sale_id, product_id, quantity, price)

                VALUES(%s,%s,%s,%s)
            """, (

                sale_id,
                product_id,
                item["qty"],
                item["price"]

            ))

            # Reduce stock
            cursor.execute("""
                UPDATE products
                SET quantity = quantity - %s
                WHERE id=%s
            """, (

                item["qty"],
                product_id

            ))

        conn.commit()

        return jsonify({

            "success": True,

            "message": "Order completed successfully."

        })

    except Exception as e:

        conn.rollback()

        return jsonify({

            "success": False,

            "message": str(e)

        })

    finally:

        cursor.close()
        conn.close()

@app.route("/logout")
def logout():

    session.clear()

    return redirect(url_for("home"))

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
                subject = "RMS Password Reset",
                recipients=[email]
            )

            msg.body = f"""
        Hello,

        Someone requested to reset your password.

        Click the link below:

        {reset_link}

        This link expires in 15 minutes.

        If you did not request this, simply ignore this email.

        RMS Team
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

        return redirect(url_for("home"))

    return render_template("reset_password.html", token=token)

@app.route("/careers")
def careers():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM job_vacancies
        WHERE status='Open'
        ORDER BY created_at DESC
    """)

    jobs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "careers.html",
        jobs=jobs
    )

@app.route("/apply/<int:job_id>")
def apply(job_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM job_vacancies
        WHERE id=%s
    """, (job_id,))

    job = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "apply_job.html",
        job=job
    )

@app.route("/submit_application", methods=["POST"])
def submit_application():

    vacancy_id = request.form["vacancy_id"]
    full_name = request.form["full_name"]
    email = request.form["email"]
    phone = request.form["phone"]
    address = request.form["address"]
    qualification = request.form["qualification"]
    experience = request.form["experience"]

    resume = request.files["resume"]

    filename = secure_filename(resume.filename)

    filepath = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    resume.save(filepath)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""

        INSERT INTO job_applications

        (

            vacancy_id,
            full_name,
            email,
            phone,
            address,
            qualification,
            experience,
            resume

        )

        VALUES

        (%s,%s,%s,%s,%s,%s,%s,%s)

    """,

    (

        vacancy_id,
        full_name,
        email,
        phone,
        address,
        qualification,
        experience,
        filename

    ))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/application_success")

@app.route("/application_success")
def application_success():

    return render_template(
        "application_success.html"
    )

@app.route("/admin/applications")
def applications():

    conn = get_db_connection()
    cursor = conn.cursor()

    # Summary Cards

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_applications
        WHERE status='Pending'
    """)
    pending = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_applications
        WHERE status='Interview'
    """)
    interviews = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_applications
        WHERE status='Hired'
    """)
    hired = cursor.fetchone()[0]

    cursor.execute("""
        SELECT COUNT(*)
        FROM job_applications
        WHERE status='Rejected'
    """)
    rejected = cursor.fetchone()[0]

    # Applicants Table

    cursor.execute("""

        SELECT

            a.id,
            a.full_name,
            j.position,
            a.email,
            a.phone,
            a.resume,
            a.status,
            a.applied_at

        FROM job_applications a

        JOIN job_vacancies j
        ON a.vacancy_id=j.id

        ORDER BY a.applied_at DESC

    """)

    applications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(

        "admin/applications.html",

        pending=pending,
        interviews=interviews,
        hired=hired,
        rejected=rejected,

        applications=applications

    )

@app.route("/admin/application/<int:application_id>")
def review_application(application_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            a.id,
            a.full_name,
            a.email,
            a.phone,
            a.address,
            a.qualification,
            a.experience,
            a.resume,
            a.status,
            a.applied_at,

            j.position,
            j.department,
            j.salary

        FROM job_applications a

        JOIN job_vacancies j
        ON a.vacancy_id = j.id

        WHERE a.id = %s

    """, (application_id,))

    application = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "admin/review_application.html",
        application=application
    )

@app.route("/admin/interviews")
def interviews():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            i.id,
            a.full_name,
            j.position,
            i.interview_date,
            i.interview_time,
            i.interviewer,
            i.status

        FROM interviews i

        JOIN job_applications a
        ON i.application_id=a.id

        JOIN job_vacancies j
        ON a.vacancy_id=j.id

        ORDER BY interview_date ASC,
                 interview_time ASC

    """)

    interviews = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(

        "admin/interviews.html",

        interviews=interviews

    )

@app.route("/admin/schedule_interview/<int:application_id>")
def schedule_interview(application_id):

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""

        SELECT

            a.id,
            a.full_name,
            a.email,
            a.phone,
            a.address,
            a.qualification,
            a.experience,
            a.resume,
            a.status,
            a.applied_at,

            j.position,
            j.department

        FROM job_applications a

        JOIN job_vacancies j
        ON a.vacancy_id=j.id

        WHERE a.id=%s

    """,(application_id,))

    application=cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "admin/schedule_interview.html",
        application=application

    )

@app.route("/admin/save_interview", methods=["POST"])
def save_interview():

    application_id = request.form["application_id"]
    interview_date = request.form["interview_date"]
    interview_time = request.form["interview_time"]
    interviewer = request.form["interviewer"]
    interview_type = request.form["interview_type"]
    location = request.form["location"]
    remarks = request.form["remarks"]

    conn = get_db_connection()
    cursor = conn.cursor()

    # Save interview
    cursor.execute("""
        INSERT INTO interviews
        (
            application_id,
            interview_date,
            interview_time,
            interviewer,
            interview_type,
            location,
            remarks
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s)
    """, (
        application_id,
        interview_date,
        interview_time,
        interviewer,
        interview_type,
        location,
        remarks
    ))

    # Update applicant status
    cursor.execute("""
        UPDATE job_applications
        SET status='Interview'
        WHERE id=%s
    """, (application_id,))

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin/interviews")

if __name__ == "__main__":
    create_table()
    app.run(debug=True)
