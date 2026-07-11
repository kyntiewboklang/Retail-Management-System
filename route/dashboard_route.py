from flask import render_template
from database import get_db_connection

def register_dashboard_routes(app):

    @app.route("/admin/dashboard")
    def dashboard():

        conn = get_db_connection()
        cursor = conn.cursor()

        # Total Sales
        cursor.execute("""
            SELECT COALESCE(SUM(total_amount), 0)
            FROM orders
        """)
        total_sales = cursor.fetchone()[0]

        # Total Products
        cursor.execute("""
            SELECT COUNT(*)
            FROM products
        """)
        total_products = cursor.fetchone()[0]

        # Low Stock
        cursor.execute("""
            SELECT COUNT(*)
            FROM products
            WHERE quantity <= 10
            AND quantity > 0
        """)
        low_stock = cursor.fetchone()[0]

        # Items Sold
        cursor.execute("""
            SELECT COALESCE(SUM(quantity), 0)
            FROM order_items
        """)
        items_sold = cursor.fetchone()[0]
        
                # Recent Orders
        cursor.execute("""
            SELECT
                id,
                order_date,
                payment_method,
                total_amount
            FROM orders
            ORDER BY order_date DESC
            LIMIT 10
        """)

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