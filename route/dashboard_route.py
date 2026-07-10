from flask import render_template


def register_dashboard_routes(app):

    @app.route("/admin/dashboard")
    def dashboard():
        return render_template("admin/dashboard.html")