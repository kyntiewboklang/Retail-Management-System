from flask import (render_template,request,redirect,url_for,flash,jsonify)
from database import get_db_connection

def register_staff_routes(app):
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

        return render_template("admin/staff.html", staffs=staffs)
    
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
