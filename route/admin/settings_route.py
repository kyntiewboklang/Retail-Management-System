from flask import render_template,session
from utils.auth import admin_required

def register_settings_routes(app):
    @app.route("/admin/settings")
    @admin_required
    def settings():
        if "user_id" not in session:
             return redirect(url_for("admin_login"))
        return render_template("admin/settings.html")