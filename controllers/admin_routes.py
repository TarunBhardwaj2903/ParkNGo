



from flask import Blueprint, render_template, request, redirect, url_for, flash, session
import parking_models   # top-level module
import database         # top-level module for add_user, find_user_by_email if needed

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/admin")


def _require_admin():
    """Return True if an admin is currently logged in."""
    return session.get("role") == "admin"



@admin_bp.route("/dashboard")
def dashboard():
    if not _require_admin():
        flash("Admin access required.", "danger")
        return redirect(url_for("login"))

    lots  = parking_models.get_all_lots()
    users = parking_models.get_all_users()
    return render_template("admin_dashboard.html", lots=lots, users=users)


@admin_bp.route("/add_lot", methods=["POST"])
def add_lot():
    if not _require_admin():
        flash("Admin access required.", "danger")
        return redirect(url_for("login"))

    name      = request.form.get("name")
    address   = request.form.get("address")
    pin_code  = request.form.get("pin_code")
    price     = float(request.form.get("price", 0))
    max_spots = int(request.form.get("max_spots", 0))

    parking_models.add_parking_lot(name, address, pin_code, price, max_spots)
    flash("Parking lot added successfully!", "success")
    return redirect(url_for("admin_bp.dashboard"))


@admin_bp.route("/delete_lot/<int:lot_id>")
def delete_lot_view(lot_id):
    if not _require_admin():
        flash("Admin access required.", "danger")
        return redirect(url_for("login"))

    success = parking_models.delete_parking_lot(lot_id)
    if success:
        flash("Parking lot deleted.", "success")
    else:
        flash("Cannot delete: one or more spots occupied.", "danger")
    return redirect(url_for("admin_bp.dashboard"))


@admin_bp.route("/lot/<int:lot_id>")
def view_lot(lot_id):
    if not _require_admin():
        flash("Admin access required.", "danger")
        return redirect(url_for("login"))

    spots = parking_models.get_spots_by_lot(lot_id)
    return render_template("manage_spots.html", spots=spots, lot_id=lot_id)

