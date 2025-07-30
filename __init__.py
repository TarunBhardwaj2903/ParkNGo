# parkingapp_sample/__init__.py

from flask import Flask, render_template, request, redirect, url_for, flash, session
import database        # local module
import parking_models  # local module

def create_app():
    app = Flask(__name__)
    app.secret_key = "supersecretkey"  # use env var in production

    # Initialize DB + default admin
    database.create_tables()

    # --- AUTH ROUTES ---
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            username = request.form["username"]
            email    = request.form["email"]
            pwd      = request.form["password"]
            if database.find_user_by_email(email):
                flash("Email already registered", "danger")
            else:
                database.add_user(username, email, pwd)
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for("login"))
        return render_template("register.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            pwd   = request.form["password"]
            user  = database.find_user_by_email(email)
            if user and user[3] == pwd:
                session["user_id"] = user[0]
                session["role"]    = user[4]
                flash("Login successful", "success")
                if user[4] == "admin":
                    return redirect(url_for("admin_bp.dashboard"))
                else:
                    return redirect(url_for("user_bp.dashboard"))
            flash("Invalid credentials", "danger")
        return render_template("login.html")

    @app.route("/logout")
    def logout():
        session.clear()
        flash("Logged out", "info")
        return redirect(url_for("login"))

    # --- BLUEPRINTS ---
    from controllers.admin_routes  import admin_bp
    from controllers.user_routes   import user_bp
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)

    # redirect root → login
    @app.route("/")
    def home():
        return redirect(url_for("login"))

    return app




# from flask import Flask
# from .models.database import create_tables

# def create_app():
#     app = Flask(__name__)
#     app.secret_key = "supersecretkey"  # TODO: move to env var

#     # Ensure DB + default admin
#     create_tables()

#     # Import blueprints here (inside function avoids circular import)
#     from .controllers import admin_bp, user_bp
#     app.register_blueprint(admin_bp)
#     app.register_blueprint(user_bp)

#     return app

    

