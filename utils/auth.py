from functools import wraps
from flask import session, redirect, url_for, flash


def admin_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "admin":
            flash("Access denied.", "danger")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated


def staff_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):

        if "user_id" not in session:
            return redirect(url_for("login"))

        if session.get("role") != "staff":
            flash("Access denied.", "danger")
            return redirect(url_for("login"))

        return f(*args, **kwargs)

    return decorated