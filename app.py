from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("dashboard.html")

@app.route("/new-orders")
def new_orders():
    return render_template("new_orders.html")

@app.route("/scanner")
def scanner():
    return render_template("scanner.html")


if __name__ == "__main__":
    app.run(debug=True)