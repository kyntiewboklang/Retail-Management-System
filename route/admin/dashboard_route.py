from flask import render_template, session, redirect, url_for
from database import get_db_connection
from utils.auth import admin_required

def register_dashboard_routes(app):

    @app.route("/admin/dashboard")
    @admin_required
    def dashboard():

        if "user_id" not in session:
            return redirect(url_for("admin_login"))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Total Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM orders WHERE user_id=%s
        """,(session["user_id"],))
        total_sales = cursor.fetchone()[0]

        # Total Products
        cursor.execute("""
            SELECT COUNT(*)
            FROM products WHERE user_id=%s
        """, (session["user_id"],))
        total_products = cursor.fetchone()[0]

        # Low Stock
        cursor.execute("""
            SELECT COUNT(*)
            FROM products
            WHERE user_id = %s
            AND quantity <= 10
            AND quantity > 0
        """, (session["user_id"],))
        low_stock = cursor.fetchone()[0]

        # Items Sold
        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM order_items
            WHERE user_id = %s
        """, (session["user_id"],))
        items_sold = cursor.fetchone()[0]
        
                # Recent Orders
        cursor.execute("""
            SELECT
                p.product_name,
                o.order_date,
                o.payment_method,
                o.total_amount
            FROM orders o
            JOIN order_items oi
                ON o.id = oi.order_id
            JOIN products p
                ON oi.product_id = p.id
            WHERE o.user_id = %s
            ORDER BY o.order_date DESC
            LIMIT 10
        """, (session["user_id"],))

        recent_orders = cursor.fetchall()

        cursor.close()

        conn.close()

        return render_template(
            "admin/dashboard.html",
            total_sales=total_sales,
            total_products=total_products,
            low_stock=low_stock,
            items_sold=items_sold,
            recent_orders=recent_orders
        )