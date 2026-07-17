from flask import (
    render_template,
    redirect,
    session,
    url_for,
    request,
    jsonify
)
from database import get_db_connection

def register_staff_dashboard_route(app):

    @app.route("/staff/staff_dashboard")
    def staff_dashboard():

        if "staff_id" not in session:
            return redirect(url_for("staff_login"))

        if session.get("role") != "staff":
            return redirect(url_for("staff_login"))

        conn = get_db_connection()
        cursor = conn.cursor()

        staff_id = session["staff_id"]

        # Today's Orders
        cursor.execute("""
            SELECT COUNT(*)
            FROM sales
            WHERE staff_id=%s
            AND DATE(created_at)=CURRENT_DATE
        """, (staff_id,))

        todays_orders = cursor.fetchone()[0]

        # Products
        cursor.execute("""
            SELECT COUNT(*)
            FROM products
        """)

        total_products = cursor.fetchone()[0]

        # Sales Today
        cursor.execute("""
            SELECT COALESCE(SUM(total),0)
            FROM sales
            WHERE staff_id=%s
            AND DATE(created_at)=CURRENT_DATE
        """, (staff_id,))

        sales_today = cursor.fetchone()[0]

        # Customers
        cursor.execute("""
            SELECT COUNT(*)
            FROM sales
            WHERE staff_id=%s
        """, (staff_id,))

        customers = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return render_template(

            "staff/staff_dashboard.html",

            todays_orders=todays_orders,

            total_products=total_products,

            customers=customers,

            sales_today=sales_today

        )

    @app.route("/staff/staff_products")
    def staff_products():
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY id DESC
        """)

        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "staff/staff_products.html",
            products=products
        )

    @app.route("/staff/partials/staff_view_products")
    def staff_view_products():

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id,
                product_name,
                category,
                brand,
                sku,
                barcode,
                price,
                quantity
            FROM products
            ORDER BY id DESC
        """)

        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            "/staff/partials/staff_view_products.html",
            products=products
        )

    @app.route("/staff/staff_new_orders")
    def staff_new_orders():

        barcode = request.args.get("barcode")

        conn = get_db_connection()
        cursor = conn.cursor()

        product = None

        if barcode:

            cursor.execute("""
                SELECT id,
                    product_name,
                    price,
                    quantity,
                    barcode
                FROM products
                WHERE barcode = %s
            """, (barcode,))

            product = cursor.fetchone()

        cursor.close()
        conn.close()

        return render_template(
            "staff/staff_new_orders.html",
            product=product,
            barcode=barcode
        )

    @app.route("/staff/get_product", methods=["POST"])
    def get_product():

        data = request.get_json()
        barcode = data["barcode"]

        conn = get_db_connection()      # however you connect
        cursor = conn.cursor()

        cursor.execute("""
            SELECT product_name, price, barcode
            FROM products
            WHERE barcode = %s
        """, (barcode,))

        product = cursor.fetchone()

        cursor.close()
        conn.close()

        if not product:
            return jsonify({"success": False})

        return jsonify({
            "success": True,
            "name": product[0],
            "price": float(product[1]),
            "barcode": product[2]
        })

    @app.route("/staff/complete_order", methods=["POST"])
    def staff_complete_order():

        data = request.get_json()

        cart = data["cart"]
        payment_method = data["payment_method"]

        staff_id = session["staff_id"]

        conn = get_db_connection()
        cursor = conn.cursor()

        try:

            total = 0

            for item in cart:
                total += item["price"] * item["qty"]

            # Create sale
            cursor.execute("""
                INSERT INTO sales(staff_id, payment_method, total)
                VALUES (%s, %s, %s)
                RETURNING id
            """, (staff_id, payment_method, total))

            sale_id = cursor.fetchone()[0]

            # Save every product
            for item in cart:

                cursor.execute("""
                    SELECT id
                    FROM products
                    WHERE barcode=%s
                """, (item["barcode"],))

                product = cursor.fetchone()

                if not product:
                    continue

                product_id = product[0]

                cursor.execute("""
                    INSERT INTO sale_items
                    (sale_id, product_id, quantity, price)

                    VALUES(%s,%s,%s,%s)
                """, (

                    sale_id,
                    product_id,
                    item["qty"],
                    item["price"]

                ))

                # Reduce stock
                cursor.execute("""
                    UPDATE products
                    SET quantity = quantity - %s
                    WHERE id=%s
                """, (

                    item["qty"],
                    product_id

                ))

            conn.commit()

            return jsonify({

                "success": True,

                "message": "Order completed successfully."

            })

        except Exception as e:

            conn.rollback()

            return jsonify({

                "success": False,

                "message": str(e)

            })

        finally:

            cursor.close()
            conn.close()
