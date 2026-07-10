from flask import (
    render_template,
    request,
    redirect,
    url_for,
    flash,
    jsonify
)

from database import get_db_connection

def register_product_routes(app):
    @app.route("/admin/add_product", methods=["GET", "POST"])
    def add_product():
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
                    product_name,
                    category,
                    brand,
                    price,
                    quantity,
                    sku,
                    supplier,
                    description
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
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

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT *
            FROM products
            ORDER BY product_name
        """)

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

        cursor.close()
        conn.close()

        return render_template(
            "admin/available_stocks.html",
            stocks=stocks,
            total_products=total_products,
            total_stock=total_stock,
            low_stock=low_stock,
            out_stock=out_stock
        )
    
    @app.route("/api/search_product/<barcode>")
    def search_product(barcode):

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
            WHERE sku = %s
        """, (barcode,))

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

        return jsonify({
            "found": False
        })
