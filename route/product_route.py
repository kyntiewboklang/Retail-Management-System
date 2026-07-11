from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session
)

import requests

from database import get_db_connection

def register_product_routes(app):
    @app.route("/admin/add_product", methods=["GET", "POST"])
    def add_product():
        if "user_id" not in session:
            return redirect(url_for("admin_login"))
        
        if request.method =="POST":
            product_name = request.form["product_name"]
            category = request.form["category"]
            brand = request.form["brand"]
            price = request.form["price"]
            quantity = request.form["quantity"]
            sku = request.form["sku"]
            supplier = request.form["supplier"]
            description = request.form["description"]
            
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO products
                (
                    user_id,
                    product_name,
                    category,
                    brand,
                    price,
                    quantity,
                    sku,
                    supplier,
                    description
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s,%s)
            """,
            (
                session["user_id"],
                product_name,
                category,
                brand,
                price,
                quantity,
                sku,
                supplier,
                description
            ))

            conn.commit()

            cursor.close()
            conn.close()

            flash("Product added successfully!", "success")

            return redirect(url_for("add_product"))

        return render_template("admin/add_product.html")
    
    @app.route("/admin/available_stock")
    def available_stock():
        if "user_id" not in session:
            return redirect(url_for("admin_login"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM products WHERE user_id = %s
            ORDER BY product_name
        """, (session["user_id"],))

        stocks = cursor.fetchall()

        total_products = len(stocks)

        total_stock = sum(row[5] for row in stocks)

        low_stock = sum(
            1 for row in stocks
            if row[5] > 0 and row[5] <= 10
        )

        out_stock = sum(
            1 for row in stocks
            if row[5] == 0
        )

        cursor.execute("""
            SELECT DISTINCT category
            FROM products
            WHERE user_id = %s AND category IS NOT NULL
            ORDER BY category
        """, (session["user_id"],))

        categories = [row[0] for row in cursor.fetchall()]

        cursor.close()
        conn.close()

        return render_template(
            "admin/available_stocks.html",
            stocks=stocks,
            total_products=total_products,
            total_stock=total_stock,
            low_stock=low_stock,
            out_stock=out_stock,
            categories=categories
        )
    
    @app.route("/api/search_product/<barcode>")
    def search_product(barcode):
        if "user_id" not in session:
            return redirect(url_for("admin_login"))

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                product_name,
                category,
                brand,
                price,
                quantity,
                supplier,
                description
            FROM products
            WHERE user_id = %s
            AND sku = %s
        """, (
            session["user_id"],
            barcode
        ))
        product = cursor.fetchone()

        cursor.close()
        conn.close()

        if product:

            return jsonify({
                "found": True,
                "source": "local",
                "product_name": product[0],
                "category": product[1],
                "brand": product[2],
                "price": product[3],
                "quantity": product[4],
                "supplier": product[5],
                "description": product[6]
            })

        # Search Open Food Facts
        # ----------------------------

        url = f"https://world.openfoodfacts.org/api/v2/product/{barcode}.json"

        try:
            response = requests.get(url, timeout=5)

            if response.status_code == 200:

                data = response.json()

                if data.get("status") == 1:

                    p = data["product"]

                    return jsonify({
                        "found": True,
                        "source": "openfoodfacts",
                        "product_name": p.get("product_name", ""),
                        "category": p.get("categories", ""),
                        "brand": p.get("brands", ""),
                        "price": "",
                        "quantity": 0,
                        "supplier": "",
                        "description": p.get("generic_name", "")
                    })

        except Exception as e:
            print(e)

        return jsonify({
            "found": False
        })
