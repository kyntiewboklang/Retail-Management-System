from flask import (
    render_template,
    redirect,
    session
)

def register_staff_dashboard_route(app):

    @app.route("/staff/dashboard")
    def staff_dashboard():

        if session.get("role") != "staff":
            return redirect("/login")

        return render_template("staff/dashboard.html")