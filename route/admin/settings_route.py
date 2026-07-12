from flask import render_template,session

def register_settings_routes(app):
    @app.route("/admin/settings")
    def settings():
        if "user_id" not in session:
             return redirect(url_for("admin_login"))
        return render_template("admin/settings.html")