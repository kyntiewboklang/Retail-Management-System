from flask import (render_template,request,redirect,url_for,flash,jsonify)
from database import get_db_connection

def register_staff_routes(app):
    @app.route("/admin/staff")
    def staff():
        return render_template("admin/staff.html")
    @app.route("/admin/add_staff")
    def addstaff():
        return render_template("admin/add_staff.html")
    


        
