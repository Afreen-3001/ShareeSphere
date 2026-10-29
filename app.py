from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "sharesphere_secret_key"

# ---------- IN-MEMORY STORAGE (no database) ----------
users = []
ngos = []
needs = []
donations = []

next_ids = {"user": 1, "ngo": 1, "need": 1, "donation": 1}

def new_id(kind):
    i = next_ids[kind]
    next_ids[kind] += 1
    return i

def find_user_by_email(email):
    return next((u for u in users if u["email"] == email), None)

def find_user(uid):
    return next((u for u in users if u["id"] == uid), None)

def find_ngo(nid):
    return next((n for n in ngos if n["id"] == nid), None)

def ngo_of_user(uid):
    return next((n for n in ngos if n["user_id"] == uid), None)

# Seed admin account
users.append({
    "id": new_id("user"), "name": "Admin",
    "email": "admin@sharesphere.com",
    "password": generate_password_hash("admin123"),
    "role": "admin"
})

# ---------- HOME ----------
@app.route("/")
def index():
    verified = [n for n in ngos if n["verified"] == 1]
    return render_template("index.html", ngos=verified)

# ---------- AUTH ----------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        role = request.form.get("role", "donor")

        if not name or not email or not password:
            flash("All fields are required.", "error")
            return redirect(url_for("register"))
        if find_user_by_email(email):
            flash("Email already registered.", "error")
            return redirect(url_for("register"))

        uid = new_id("user")
        users.append({
            "id": uid, "name": name, "email": email,
            "password": generate_password_hash(password), "role": role
        })

        if role == "ngo":
            ngos.append({
                "id": new_id("ngo"), "user_id": uid,
                "name": request.form.get("ngo_name", name) or name,
                "cause": request.form.get("cause", "General") or "General",
                "description": request.form.get("description", ""),
                "verified": 0
            })

        flash("Account created. Please log in.", "success")
        return redirect(url_for("login"))
    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = find_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.", "error")
        return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

# ---------- NGO LIST ----------
@app.route("/ngos")
def ngo_list():
    verified = [n for n in ngos if n["verified"] == 1]
    return render_template("ngos.html", ngos=verified)

# ---------- DONATE ----------
@app.route("/donate/<int:ngo_id>", methods=["GET", "POST"])
def donate(ngo_id):
    if "user_id" not in session or session.get("role") != "donor":
        flash("Please log in as a donor to donate.", "error")
        return redirect(url_for("login"))
    ngo = find_ngo(ngo_id)
    if not ngo:
        flash("NGO not found.", "error")
        return redirect(url_for("ngo_list"))

    if request.method == "POST":
        detail = request.form.get("detail", "").strip()
        dtype = request.form.get("dtype", "item")
        if not detail:
            return jsonify({"ok": False, "message": "Please provide donation details."})
        donations.append({
            "id": new_id("donation"),
            "donor_id": session["user_id"],
            "ngo_id": ngo_id,
            "dtype": dtype,
            "detail": detail,
            "status": "pledged",
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
        return jsonify({"ok": True, "message": "Thank you! Your donation pledge was recorded."})

    return render_template("donate.html", ngo=ngo)

# ---------- DASHBOARD ----------
@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    role = session["role"]
    data = {}

    if role == "donor":
        data["donations"] = [
            {**d, "ngo_name": (find_ngo(d["ngo_id"]) or {}).get("name", "Unknown")}
            for d in donations if d["donor_id"] == session["user_id"]
        ][::-1]

    elif role == "ngo":
        ngo = ngo_of_user(session["user_id"])
        if ngo:
            data["ngo"] = ngo
            data["received"] = [
                {**d, "donor_name": (find_user(d["donor_id"]) or {}).get("name", "Unknown")}
                for d in donations if d["ngo_id"] == ngo["id"]
            ][::-1]
            data["needs"] = [n for n in needs if n["ngo_id"] == ngo["id"]]

    return render_template("dashboard.html", role=role, data=data)

# ---------- NGO ADD NEED (AJAX) ----------
@app.route("/add_need", methods=["POST"])
def add_need():
    if "user_id" not in session or session.get("role") != "ngo":
        return jsonify({"ok": False, "error": "Unauthorized"}), 401
    item_type = request.form.get("item_type", "").strip()
    description = request.form.get("description", "").strip()
    if not item_type:
        return jsonify({"ok": False, "error": "Item type required"}), 400
    ngo = ngo_of_user(session["user_id"])
    if not ngo:
        return jsonify({"ok": False, "error": "No NGO profile"}), 400
    needs.append({
        "id": new_id("need"),
        "ngo_id": ngo["id"],
        "item_type": item_type,
        "description": description
    })
    return jsonify({"ok": True, "message": "Need added."})

# ---------- ADMIN ----------
@app.route("/admin")
def admin():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    sorted_ngos = sorted(ngos, key=lambda n: n["verified"])
    return render_template("admin.html", ngos=sorted_ngos)

@app.route("/admin/verify/<int:ngo_id>", methods=["POST"])
def verify_ngo(ngo_id):
    if session.get("role") != "admin":
        return jsonify({"ok": False}), 401
    ngo = find_ngo(ngo_id)
    if ngo:
        ngo["verified"] = 1
    return jsonify({"ok": True})

if __name__ == "__main__":
    app.run(debug=True)