from flask import Flask, render_template, request

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/add_product")
def add_product():
    return render_template("add_product.html")

@app.route("/new-orders")
def new_orders():
    barcode = request.args.get("barcode")
    return render_template("new_orders.html",barcode=barcode)

@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


if __name__ == "__main__":
    app.run(debug=True)