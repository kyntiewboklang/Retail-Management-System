from flask import (
    render_template,
    redirect,
    request,
    session,
    url_for,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from flask_mail import Message

from itsdangerous import URLSafeTimedSerializer

from database import get_db_connection

def register_auth_routes(app, mail):
    serializer = URLSafeTimedSerializer(
        app.config["SECRET_KEY"]
    )

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
                INSERT INTO users(username, email, password, role)
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_password, "admin"))

            conn.commit()

            cursor.close()
            conn.close()

            return redirect("/login")

        return render_template("register.html")



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