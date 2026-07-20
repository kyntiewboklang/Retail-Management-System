from flask import Flask, render_template, redirect, request, session, url_for, flash
from database import get_db_connection
from config import Config
from models import create_products_table, create_users_table, create_orders_table, create_order_items_table, create_staff_table, create_table
from route.admin.dashboard_route import register_dashboard_routes
from route.admin.product_route import register_product_routes
from route.auth_route import register_auth_routes
from route.admin.order_route import register_order_routes
from route.admin.staff_route import register_staff_routes
from route.admin.settings_route import register_settings_routes
from route.staff.staff_dashboard_route import register_staff_dashboard_route
from route.admin.recruitment_route import recruitment_route
from route.apply_job import apply_job
from route.admin.report_route import report_route


from flask_mail import Mail


app = Flask(__name__)
app.config.from_object(Config)

mail = Mail(app)

UPLOAD_FOLDER = "static/uploads/resumes"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

register_dashboard_routes(app)
register_product_routes(app)
register_auth_routes(app, mail)
register_order_routes(app)
register_staff_routes(app, mail)
register_settings_routes(app)
register_staff_dashboard_route(app, mail)
recruitment_route(app, mail)
apply_job(app)
report_route(app)

@app.route("/")
def home():
    return render_template("index.html", admin_exists=admin_exists())
def admin_exists():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM users WHERE role = %s", ("admin",))
    count = cur.fetchone()[0]

    cur.close()
    conn.close()

    return count > 0

@app.route("/careers")
def careers():

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM job_vacancies
        WHERE
            status = 'Open'
            AND vacancies > 0
            AND deadline >= CURRENT_DATE
        ORDER BY created_at DESC
    """)

    jobs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "careers.html",
        jobs=jobs
    )

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

if __name__ == "__main__":
    create_users_table()
    create_products_table()
    create_orders_table()
    create_order_items_table()
    create_staff_table()
    create_table()
    app.run(host="0.0.0.0", port=5000, debug=True)

