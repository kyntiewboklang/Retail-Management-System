from flask import (
    render_template,
    redirect,
    session,
    url_for,
    request,
    jsonify,
    flash
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import get_db_connection

from utils.auth import staff_required

def register_staff_dashboard_route(app, mail):

    @app.route("/staff/staff_dashboard")
    @staff_required
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

    @app.route("/staff/staff_view_products")
    @staff_required
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
            "/staff/staff_view_products.html",
            products=products
        )

    @app.route("/staff/staff_new_orders")
    @staff_required
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
    @staff_required
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
    @staff_required
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

                "message": "Order completed successfully.",

                "sale_id": sale_id

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

    @app.route("/staff/receipt/<int:sale_id>")
    @staff_required
    def receipt(sale_id):

        if "staff_id" not in session:
            return redirect(url_for("staff_login"))

        conn = get_db_connection()
        cursor = conn.cursor()

        # Sale details
        cursor.execute("""
            SELECT
                id,
                staff_id,
                payment_method,
                total,
                created_at
            FROM sales
            WHERE id = %s
        """, (sale_id,))

        sale = cursor.fetchone()

        if not sale:

            cursor.close()
            conn.close()

            return "Receipt not found", 404

        # Staff details
        cursor.execute("""
            SELECT
                username,
                email
            FROM staff
            WHERE id = %s
        """, (sale[1],))

        staff = cursor.fetchone()

        # Products in this sale
        cursor.execute("""
            SELECT
                p.product_name,
                si.quantity,
                si.price
            FROM sale_items si
            INNER JOIN products p
                ON si.product_id = p.id
            WHERE si.sale_id = %s
        """, (sale_id,))

        rows = cursor.fetchall()

        cursor.close()
        conn.close()

        sale_data = {
            "id": sale[0],
            "staff_id": sale[1],
            "payment_method": sale[2],
            "total": sale[3],
            "created_at": sale[4]
        }

        staff_data = {
            "username": staff[0],
            "email": staff[1]
        }

        items = []

        for row in rows:

            items.append({

                "product_name": row[0],
                "quantity": row[1],
                "price": row[2]

            })

        return render_template(

            "staff/receipt.html",

            sale=sale_data,

            staff=staff_data,

            items=items

        )

    @app.route("/staff/staff_change_password", methods=["GET", "POST"])
    @staff_required
    def staff_change_password():

        if "staff_id" not in session:
            return redirect(url_for("staff_login"))

        if request.method == "POST":

            current_password = request.form["current_password"]
            new_password = request.form["new_password"]
            confirm_password = request.form["confirm_password"]

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("staff_change_password"))

            conn = get_db_connection()
            cursor = conn.cursor()

            # Get current password
            cursor.execute("""
                SELECT password
                FROM staff
                WHERE id = %s
            """, (session["staff_id"],))

            staff = cursor.fetchone()

            if not staff:
                cursor.close()
                conn.close()

                flash("Staff account not found.", "danger")
                return redirect(url_for("staff_login"))

            # Verify current password
            if not check_password_hash(staff[0], current_password):

                cursor.close()
                conn.close()

                flash("Current password is incorrect.", "danger")
                return redirect(url_for("staff_change_password"))

            # Hash new password
            hashed_password = generate_password_hash(new_password)

            # Update password
            cursor.execute("""
                UPDATE staff
                SET password = %s
                WHERE id = %s
            """, (

                hashed_password,
                session["staff_id"]

            ))

            conn.commit()

            cursor.close()
            conn.close()

            flash("Password changed successfully!", "success")

            return redirect(url_for("staff_dashboard"))

        return render_template("staff/staff_change_password.html")