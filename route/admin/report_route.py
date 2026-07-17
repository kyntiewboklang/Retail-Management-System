#For report making
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

from flask import (
    render_template,
    redirect,
    session,
    url_for,
    request,
    jsonify
)
from database import get_db_connection

def report_route(app):
    @app.route("/admin/reports")
    def reports():

        conn = get_db_connection()
        cursor = conn.cursor()

        # Total Revenue
        cursor.execute("""
            SELECT COALESCE(SUM(total),0)
            FROM sales
        """)
        total_sales = cursor.fetchone()[0]

        # Orders
        cursor.execute("""
            SELECT COUNT(*)
            FROM sales
        """)
        total_orders = cursor.fetchone()[0]

        # Products Sold
        cursor.execute("""
            SELECT COALESCE(SUM(quantity),0)
            FROM sale_items
        """)
        products_sold = cursor.fetchone()[0]

        # Low Stock
        cursor.execute("""
            SELECT COUNT(*)
            FROM products
            WHERE quantity < 10
        """)
        low_stock = cursor.fetchone()[0]

        # Recent Orders
        cursor.execute("""
            SELECT
                s.id,
                u.username,
                s.total,
                s.payment_method,
                s.created_at
            FROM sales s
            JOIN users u
            ON s.staff_id = u.id
            ORDER BY s.created_at DESC
            LIMIT 10
        """)

        recent_orders = cursor.fetchall()

        #Top Products
        cursor.execute("""
            SELECT
            p.product_name,
            SUM(si.quantity) AS sold
            FROM sale_items si
            JOIN products p
            ON p.id=si.product_id
            GROUP BY p.product_name
            ORDER BY sold DESC
            LIMIT 10
        """)

        top_products = cursor.fetchall()

        #Staff Report
        cursor.execute("""
            SELECT
            u.username,
            COUNT(s.id),
            COALESCE(SUM(s.total),0)
            FROM users u
            LEFT JOIN sales s
            ON u.id=s.staff_id
            WHERE u.role='staff'
            GROUP BY u.username
            ORDER BY SUM(s.total) DESC NULLS LAST
        """)

        staff_report=cursor.fetchall()

        #Product with Low Stock
        cursor.execute("""
            SELECT
            product_name,
            quantity
            FROM products
            WHERE quantity<10
            ORDER BY quantity ASC
        """)

        low_stock_products=cursor.fetchall()

        #Bar Chart of the sale
        cursor.execute("""
            SELECT
            DATE(created_at),
            SUM(total)
            FROM sales
            WHERE created_at >= CURRENT_DATE - INTERVAL '6 days'
            GROUP BY DATE(created_at)
            ORDER BY DATE(created_at)
        """)

        chart_data = cursor.fetchall()

        #Pie Chart of the payment methods
        cursor.execute("""
            SELECT
            payment_method,
            COUNT(*)
            FROM sales
            GROUP BY payment_method
        """)

        payment_data=cursor.fetchall()

        cursor.close()
        conn.close()

        labels=[]
        sales=[]
        for row in chart_data:
            labels.append(row[0].strftime("%d %b"))
            sales.append(float(row[1]))

        payment_labels=[]
        payment_values=[]
        for row in payment_data:
            payment_labels.append(row[0])
            payment_values.append(row[1])

        return render_template(
            "admin/reports.html",

            total_sales=total_sales,
            total_orders=total_orders,
            products_sold=products_sold,
            low_stock=low_stock,

            recent_orders=recent_orders,
            top_products=top_products,
            staff_report=staff_report,
            low_stock_products=low_stock_products,
            labels=labels,
            sales=sales,
            payment_labels=payment_labels,
            payment_values=payment_values
        )

    @app.route("/admin/report/pdf")
    def report_pdf():

        filename = "sales_report.pdf"
        doc = SimpleDocTemplate(filename)
        styles = getSampleStyleSheet()
        elements = []

        elements.append(
            Paragraph("<b>Retail Management Report</b>", styles["Title"])
        )

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
            id,
            total,
            payment_method,
            created_at
            FROM sales
            ORDER BY created_at DESC
        """)

        rows = cursor.fetchall()
        data = [["Invoice","Amount","Payment","Date"]]

        for r in rows:
            data.append([
                r[0],
                f"₹{r[1]}",
                r[2],
                str(r[3])
            ])

        table = Table(data)

        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.grey),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("GRID",(0,0),(-1,-1),1,colors.black),
            ("BACKGROUND",(0,1),(-1,-1),colors.beige)
        ]))

        elements.append(table)
        doc.build(elements)

        cursor.close()
        conn.close()

        return send_file(
            filename,
            as_attachment=True
        )