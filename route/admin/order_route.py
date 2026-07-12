from flask import (
    request,
    jsonify,
    render_template,
    session,
    redirect,
    url_for
)
from database import get_db_connection

def register_order_routes(app):

    @app.route("/admin/new-orders")
    def new_orders():
        if "user_id" not in session:
            return redirect(url_for("admin_login"))
        return render_template("admin/new_orders.html")

    @app.route("/admin/complete-order", methods=["POST"])
    def complete_order():
        if "user_id" not in session:
            return redirect(url_for("admin_login"))

        data = request.get_json()

        items = data["items"]
        payment_method = data["payment_method"]

        total_amount = 0

        for item in items:
            total_amount += item["price"] * item["quantity"]

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO orders
            (
                user_id,
                total_amount,
                payment_method
            )
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                session["user_id"],
                total_amount,
                payment_method
            )
        )   

        order_id = cursor.fetchone()[0]

        for item in items:

            cursor.execute("""
                SELECT id, quantity
                FROM products
                WHERE sku = %s
                AND user_id = %s
            """, (
                item["barcode"],
                session["user_id"]
            ))

            product = cursor.fetchone()

            if product is None:
                conn.rollback()

                return jsonify({
                    "success": False,
                    "message": f"Product not found: {item['product_name']}"
                }), 404

            product_id = product[0]
            current_stock = product[1]

            # Check available stock
            if current_stock < item["quantity"]:

                conn.rollback()

                cursor.close()
                conn.close()

                return jsonify({
                    "success": False,
                    "message": f"Only {current_stock} item(s) left for {item['product_name']}."
                }), 400

            subtotal = item["price"] * item["quantity"]

            cursor.execute("""
                INSERT INTO order_items
                (
                    order_id,
                    user_id,
                    product_id,
                    quantity,
                    price,
                    subtotal
                )
                VALUES
                (%s, %s, %s, %s, %s, %s)
            """,
            (
                order_id,
                session["user_id"],
                product_id,
                item["quantity"],
                item["price"],
                subtotal
            ))

            cursor.execute("""
                UPDATE products
                SET quantity = quantity - %s
                WHERE id = %s
                AND user_id = %s
            """,
            (
                item["quantity"],
                product_id,
                session["user_id"]
            ))

        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({
            "success": True,
            "message": f"Order #{order_id} saved successfully."
        })