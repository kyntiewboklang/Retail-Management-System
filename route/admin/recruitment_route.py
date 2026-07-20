from flask import render_template, request, redirect, flash, session, url_for
from werkzeug.security import generate_password_hash
from flask_mail import Message
import secrets
from database import get_db_connection
from utils.auth import admin_required

def recruitment_route(app, mail):
    @app.route("/admin/job_vacancies")
    @admin_required
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
    @admin_required
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

    @app.route("/admin/delete_vacancy/<int:id>", methods=["POST"])
    @admin_required
    def delete_vacancy(id):

        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if there are applications
        cursor.execute("""
            SELECT COUNT(*)
            FROM job_applications
            WHERE vacancy_id = %s
        """, (id,))

        count = cursor.fetchone()[0]

        if count > 0:

            flash(
                "This vacancy has applicants. It has been closed instead of deleted.",
                "warning"
            )

            cursor.execute("""
                UPDATE job_vacancies
                SET status='Closed'
                WHERE id=%s
            """, (id,))

        else:

            cursor.execute("""
                DELETE FROM job_vacancies
                WHERE id=%s
            """, (id,))

            flash("Vacancy deleted successfully.", "success")

        conn.commit()

        cursor.close()
        conn.close()

        return redirect(url_for("job_vacancies"))

    @app.route("/admin/applications")
    @admin_required
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
    @admin_required
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
    @admin_required
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
    @admin_required
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
    @admin_required
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

    @app.route("/admin/hire/<int:application_id>", methods=["POST"])
    @admin_required
    def hire_applicant(application_id):

        conn = get_db_connection()
        cursor = conn.cursor()

        # Get applicant details
        cursor.execute("""
            SELECT
                full_name,
                email,
                phone,
                vacancy_id
            FROM job_applications
            WHERE id = %s
        """, (application_id,))

        applicant = cursor.fetchone()

        if not applicant:
            flash("Applicant not found.", "danger")
            cursor.close()
            conn.close()
            return redirect("/admin/applications")

        full_name = applicant[0]
        email = applicant[1]
        phone = applicant[2]
        vacancy_id = applicant[3]

        # Check if staff account already exists
        cursor.execute("""
            SELECT id
            FROM staff
            WHERE email = %s
        """, (email,))

        if cursor.fetchone():
            flash("Staff account already exists.", "warning")
            cursor.close()
            conn.close()
            return redirect(f"/admin/application/{application_id}")

        # Generate username
        username = full_name.lower().replace(" ", "")

        # Generate temporary password
        temporary_password = secrets.token_urlsafe(8)

        # Hash password
        hashed_password = generate_password_hash(temporary_password)

        # Get current admin id
        admin_id = session["user_id"]

        # Create staff account
        cursor.execute("""
            INSERT INTO staff
            (
                admin_id,
                username,
                email,
                phone,
                password
            )
            VALUES (%s,%s,%s,%s,%s)
        """,
        (
            admin_id,
            username,
            email,
            phone,
            hashed_password
        ))

        # Update application status
        cursor.execute("""
            UPDATE job_applications
            SET status='Hired'
            WHERE id=%s
        """, (application_id,))

        #Update Job Vacancies
        cursor.execute("""
            UPDATE job_vacancies
            SET vacancies = vacancies - 1
            WHERE id = %s
            AND vacancies > 0
        """, (vacancy_id,))

        #Notify it that it is close
        cursor.execute("""
            UPDATE job_vacancies
            SET status = 'Closed'
            WHERE id = %s
            AND vacancies = 0
        """, (vacancy_id,))

        conn.commit()

        # Send Email
        msg = Message(
            subject="Department Store Staff Account",
            recipients=[email]
        )

        msg.body = f"""
    Congratulations {full_name}!

    You have been hired.

    Your staff account has been created.

    Login Email:
    {email}

    Temporary Password:
    {temporary_password}

    Please change your password after your first login.

    Regards,
    Department Store
    """

        mail.send(msg)

        cursor.close()
        conn.close()

        flash("Applicant hired successfully and credentials emailed.", "success")

        return redirect(f"/admin/application/{application_id}")

    @app.route("/admin/reject/<int:application_id>", methods=["POST"])
    @admin_required
    def reject_applicant(application_id):

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE job_applications
            SET status='Rejected'
            WHERE id=%s
        """, (application_id,))

        conn.commit()

        cursor.close()
        conn.close()

        flash("Applicant rejected.", "danger")

        return redirect(f"/admin/application/{application_id}")