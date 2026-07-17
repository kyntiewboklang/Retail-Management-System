from flask import (
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)
from database import get_db_connection
from werkzeug.utils import secure_filename
import os

def apply_job(app):
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