from flask import render_template

def register_settings_routes(app):
    @app.route("/admin/settings")
    def settings():
        return render_template("admin/settings.html")