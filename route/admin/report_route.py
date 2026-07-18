#For report making
from flask import send_file, request,render_template
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch
from datetime import datetime
from database import get_db_connection

def report_route(app):
    @app.route("/admin/reports")
    def reports():

        start = request.args.get("start")
        end = request.args.get("end")

        conn = get_db_connection()
        cursor = conn.cursor()

        # Total Revenue
        if start and end:
            cursor.execute("""
                SELECT COALESCE(SUM(total),0)
                FROM sales
                WHERE DATE(created_at) BETWEEN %s AND %s
            """, (start, end))
        else:
            cursor.execute("""
                SELECT COALESCE(SUM(total),0)
                FROM sales
            """)
        total_sales = cursor.fetchone()[0]

        # Orders
        if start and end:
            cursor.execute("""
                SELECT COUNT(*)
                FROM sales
                WHERE DATE(created_at) BETWEEN %s AND %s
            """, (start, end))
        else:
            cursor.execute("""
                SELECT COUNT(*)
                FROM sales
            """)
        total_orders = cursor.fetchone()[0]

        # Products Sold
        if start and end:
            cursor.execute("""
                SELECT COALESCE(SUM(si.quantity),0)
                FROM sale_items si
                JOIN sales s ON si.sale_id = s.id
                WHERE DATE(s.created_at) BETWEEN %s AND %s
            """, (start, end))
        else:
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
        if start and end:
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
                WHERE DATE(s.created_at) BETWEEN %s AND %s
                ORDER BY s.created_at DESC
                LIMIT 10
            """, (start, end))
        else:
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
        if start and end:
            cursor.execute("""
                SELECT
                    DATE(created_at),
                    SUM(total)
                FROM sales
                WHERE DATE(created_at) BETWEEN %s AND %s
                GROUP BY DATE(created_at)
                ORDER BY DATE(created_at)
            """, (start, end))
        else:
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

        conn = get_db_connection()
        cursor = conn.cursor()

        # Summary
        cursor.execute("SELECT COALESCE(SUM(total),0) FROM sales")
        total_sales = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM sales")
        total_orders = cursor.fetchone()[0]

        cursor.execute("SELECT COALESCE(SUM(quantity),0) FROM sale_items")
        total_products = cursor.fetchone()[0]

        cursor.execute("""
            SELECT
                id,
                total,
                payment_method,
                created_at
            FROM sales
            ORDER BY created_at DESC
        """)

        sales = cursor.fetchall()

        cursor.close()
        conn.close()

        filename = "Sales_Report.pdf"

        doc = SimpleDocTemplate(
            filename,
            rightMargin=30,
            leftMargin=30,
            topMargin=30,
            bottomMargin=30
        )

        styles = getSampleStyleSheet()

        title = styles["Title"]
        title.alignment = TA_CENTER

        heading = styles["Heading2"]

        normal = styles["BodyText"]

        elements = []

        elements.append(
            Paragraph("Retail Management System", title)
        )

        elements.append(
            Paragraph("Sales Report", heading)
        )

        elements.append(
            Paragraph(
                f"Generated on: {datetime.now().strftime('%d %B %Y %I:%M %p')}",
                normal
            )
        )

        elements.append(Spacer(1, 0.3 * inch))

        summary = [
            ["Total Revenue", f"₹ {total_sales:,.2f}"],
            ["Total Orders", total_orders],
            ["Products Sold", total_products]
        ]

        summary_table = Table(summary, colWidths=[220,150])

        summary_table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,-1),colors.whitesmoke),
            ("GRID",(0,0),(-1,-1),1,colors.grey),
            ("FONTNAME",(0,0),(-1,-1),"Helvetica-Bold"),
            ("BOTTOMPADDING",(0,0),(-1,-1),8)
        ]))

        elements.append(summary_table)

        elements.append(Spacer(1,0.4*inch))

        elements.append(
            Paragraph("Sales Details", heading)
        )

        table_data = [[
            "Invoice",
            "Amount",
            "Payment",
            "Date"
        ]]

        for sale in sales:
            table_data.append([
                sale[0],
                f"₹ {sale[1]}",
                sale[2],
                sale[3].strftime("%d-%m-%Y")
            ])

        table = Table(table_data)

        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.darkblue),
            ("TEXTCOLOR",(0,0),(-1,0),colors.white),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
            ("ALIGN",(0,0),(-1,-1),"CENTER"),
            ("GRID",(0,0),(-1,-1),0.5,colors.black),
            ("BACKGROUND",(0,1),(-1,-1),colors.beige),
            ("BOTTOMPADDING",(0,0),(-1,0),10)
        ]))

        elements.append(table)

        doc.build(elements)

        return send_file(
            filename,
            as_attachment=True
        )