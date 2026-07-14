from flask import (
    render_template,
    redirect,
    session
)

def register_staff_new_orders_route(app):
    @app.route("/staff/staff_new_orders")
    def staff_new_orders():
        return render_template("staff/staff_new_orders.html")