# parkingapp_sample/controllers/user_routes.py

from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import parking_models   # top-level module

user_bp = Blueprint("user_bp", __name__, url_prefix="/user")


def _require_user():
    """Return True if a normal user is logged in."""
    return session.get("role") == "user"


@user_bp.route("/dashboard")
def dashboard():
    if not _require_user():
        flash("User login required.", "danger")
        return redirect(url_for("login"))

    lots     = parking_models.get_all_lots()
    bookings = parking_models.get_user_bookings(session["user_id"])
    return render_template("user_dashboard.html", lots=lots, bookings=bookings)


@user_bp.route("/book", methods=["POST"])
def book():
    if not _require_user():
        flash("User login required.", "danger")
        return redirect(url_for("login"))

    lot_id         = int(request.form.get("lot_id"))
    vehicle_number = request.form.get("vehicle_number")

    spot_id = parking_models.book_spot(session["user_id"], lot_id, vehicle_number)
    if spot_id:
        flash("Spot booked successfully!", "success")
    else:
        flash("No available spots in the selected lot.", "danger")
    return redirect(url_for("user_bp.dashboard"))


@user_bp.route("/release/<int:booking_id>")
def release(booking_id):
    if not _require_user():
        flash("User login required.", "danger")
        return redirect(url_for("login"))

    cost = parking_models.release_spot(booking_id)
    if cost is not None:
        flash(f"Spot released. Total cost: ₹{cost}", "info")
    else:
        flash("Invalid booking or already released.", "danger")
    return redirect(url_for("user_bp.dashboard"))

