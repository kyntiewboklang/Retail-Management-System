from flask import (
    render_template,
    request,
    redirect,
    session,
    flash
)

import re

from werkzeug.security import generate_password_hash

from database import get_db_connection


def register_staff_routes(app, mail):

    @app.route("/admin/staff")
    def staff():

        if "user_id" not in session:
            return redirect("/login")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                id,
                username,
                email,
                phone,
                created_at
            FROM staff
            WHERE admin_id = %s
            ORDER BY created_at DESC
        """, (session["user_id"],))

        staff_list = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "admin/staff.html",
            staff_list=staff_list
        )


    @app.route("/admin/add_staff", methods=["GET", "POST"])
    def addstaff():

        if "user_id" not in session:
            return redirect("/login")

        if request.method == "POST":

            username = request.form["username"]
            email = request.form["email"]
            phone = request.form["phone"]
            password = request.form["password"]

            conn = get_db_connection()
            cursor = conn.cursor()

            
            cursor.execute(
                "SELECT id FROM users WHERE email = %s",
                (email,)
            )
            user_exists = cursor.fetchone()

            # Check if email already exists in staff table
            cursor.execute(
                "SELECT id FROM staff WHERE email = %s",
                (email,)
            )
            staff_exists = cursor.fetchone()

            if user_exists or staff_exists:
                cursor.close()
                conn.close()

                return render_template(
                    "admin/add_staff.html",
                    error="Email already exists. Please use another email."
                )

            #  Check if username already exists
            cursor.execute(
                "SELECT id FROM users WHERE username = %s",
                (username,)
            )
            username_exists = cursor.fetchone()

            cursor.execute(
                "SELECT id FROM staff WHERE username = %s",
                (username,)
            )
            staff_username_exists = cursor.fetchone()

            if username_exists or staff_username_exists:
                cursor.close()
                conn.close()

                return render_template(
                    "admin/add_staff.html",
                    error="Username already taken, try another one."
                )

            hashed_password = generate_password_hash(password)

            cursor.execute("""
                INSERT INTO staff
                (
                    admin_id,
                    username,
                    email,
                    phone,
                    password
                )
                VALUES (%s, %s, %s, %s, %s)
            """, (
                session["user_id"],
                username,
                email,
                phone,
                hashed_password
            ))

            conn.commit()

            cursor.close()
            conn.close()

            flash("Staff added successfully.", "success")

            return redirect("/admin/staff")

        return render_template("admin/add_staff.html")
    
    @app.route("/admin/delete_staff/<int:staff_id>")
    def delete_staff(staff_id):

        if "user_id" not in session:
            return redirect("/login")

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM staff
            WHERE id = %s
            AND admin_id = %s
        """, (staff_id, session["user_id"]))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Staff deleted successfully.", "success")

        return redirect("/admin/staff")

    @app.route("/admin/edit_staff/<int:staff_id>", methods=["GET", "POST"])
    def edit_staff(staff_id):

        if "user_id" not in session:
            return redirect("/login")

        conn = get_db_connection()
        cursor = conn.cursor()

        # ===========================
        # UPDATE STAFF
        # ===========================
        if request.method == "POST":

            username = request.form["username"]
            email = request.form["email"]
            phone = request.form["phone"]
            password = request.form["password"]

            if password.strip():

                hashed_password = generate_password_hash(password)

                cursor.execute("""
                    UPDATE staff
                    SET
                        username = %s,
                        email = %s,
                        phone = %s,
                        password = %s
                    WHERE id = %s
                    AND admin_id = %s
                """, (
                    username,
                    email,
                    phone,
                    hashed_password,
                    staff_id,
                    session["user_id"]
                ))

            else:

                cursor.execute("""
                    UPDATE staff
                    SET
                        username = %s,
                        email = %s,
                        phone = %s
                    WHERE id = %s
                    AND admin_id = %s
                """, (
                    username,
                    email,
                    phone,
                    staff_id,
                    session["user_id"]
                ))

            conn.commit()

            cursor.close()
            conn.close()

            flash("Staff updated successfully.", "success")

            return redirect("/admin/staff")

        # ===========================
        # LOAD STAFF FOR EDITING
        # ===========================

        cursor.execute("""
            SELECT
                id,
                username,
                email,
                phone
            FROM staff
            WHERE id = %s
            AND admin_id = %s
        """, (
            staff_id,
            session["user_id"]
        ))

        staff = cursor.fetchone()

        cursor.close()
        conn.close()

        if not staff:
            flash("Staff member not found.", "danger")
            return redirect("/admin/staff")

        return render_template(
            "admin/add_staff.html",
            staff=staff
        )