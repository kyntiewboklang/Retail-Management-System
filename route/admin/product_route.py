from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify,
    session
)

#Generate the barcode image using python-barcode pillow library
import os
import barcode
from barcode.writer import ImageWriter
from flask import send_from_directory

import requests

from database import get_db_connection

from utils.auth import admin_required

def register_product_routes(app):
    @app.route("/admin/add_product", methods=["GET", "POST"])
    @admin_required
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
            barcode = request.form["barcode"]
            supplier = request.form["supplier"]
            
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
                    barcode,
                    supplier
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
                barcode,
                supplier
            ))

            conn.commit()

            cursor.close()
            conn.close()

            flash("Product added successfully!", "success")

            return redirect(url_for("add_product"))

        return render_template("admin/add_product.html")

    @app.route("/generate_barcode/<barcode_number>")
    @admin_required
    def generate_barcode(barcode_number):

        folder = os.path.join("static", "barcodes")

        os.makedirs(folder, exist_ok=True)

        filename = os.path.join(folder, barcode_number)

        ean = barcode.get(
            "ean13",
            barcode_number,
            writer=ImageWriter()
        )

        ean.save(filename)

        return f"static/barcodes/{barcode_number}.png"
    
    @app.route("/admin/available_stock")
    @admin_required
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
    @admin_required
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
                supplier
            FROM products
            WHERE user_id = %s
            AND barcode = %s
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
                        "supplier": ""
                    })

        except Exception as e:
            print(e)

        return jsonify({
            "found": False
        })
