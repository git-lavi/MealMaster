from flask import Flask, flash, request, redirect, session, render_template, abort, url_for, jsonify
from functools import wraps
import werkzeug
import sqlite3
import werkzeug.security
import requests # type: ignore

# App
app = Flask(__name__)
app.secret_key = 'my super secret key'


# API
APP_ID = 'b1fa76db'
API_KEY = '53125e7fe9fd59ceb0f1c2dc4b04ab8f'


# DB
def connect_to_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return conn, cursor


def commit_close_db(conn: sqlite3.Connection):
    conn.commit()
    conn.close()


# Login required
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('unauthorized'))
        return f(*args, **kwargs)
    return decorated_function


@app.route("/unauthorized")
def unauthorized():
    return render_template('unauthorized.html'), 401


# Main app routes
@app.route("/")
def home():
    return redirect("/login")


@app.route("/register", methods=['POST'])
def register():
    # Get variables
    username = request.form.get("register-username")
    password = request.form.get("register-password")
    confirm_password = request.form.get("register-password-confirm")
    
    # Check for empty fields
    if not username or not password or not confirm_password:
        flash("Please fill out all fields!", "error")
        print("All fields not filled")
        return redirect("/login")
    
    # Check if confirmed password matches
    if password != confirm_password:
        flash("Passwords do not match", "error")
        return redirect("/login") 

    # Hash password, enter to db
    pw_hash = werkzeug.security.generate_password_hash(confirm_password)
    try:
        conn, cursor = connect_to_db()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Username already exists. Please choose a different username.", "error")
            return redirect("/login")
        else:
            cursor.execute("INSERT INTO users (username, hash) VALUES (?, ?)", (username, pw_hash))
            flash("Registration successful! You can now log in.", "success")
    except sqlite3.Error as e:
        print("error entering to database:", e)
        conn.rollback()
        flash("An error occurred during registration. Please try again later.", "error")
        return redirect("/login")
    finally:
        if conn:
            commit_close_db(conn)

    print("user registered successfully!")
    return redirect("/login")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get("login-username")
        password = request.form.get("login-password")

        if not username or not password:
            flash("Please enter username and password", "error")
            return redirect("/login")

        try:
            conn, cursor = connect_to_db()
            cursor.execute("SELECT hash FROM users WHERE username = ?", (username,))
            result = cursor.fetchone()
        except sqlite3.Error as e:
            print("Error querying database", e)
            return redirect("/login")
        finally:
            if conn:
                conn.close()
        
        # If username found
        if result:
            stored_hash = result[0]
            
            if werkzeug.security.check_password_hash(stored_hash, password):
                session['username'] = username
                flash("Logged in successfully!", "success")
                return redirect("/dashboard")
            else:
                flash("Incorrect username or password", "error")
                return redirect("/login")
        
        else:
            flash("Incorrect username or password", "error")
            return redirect("/login")

    # If method is GET
    else:
        return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    current_user = session['username']
    return render_template("dashboard.html", current_user=current_user)


@app.route("/diary")
@login_required
def diary():
    current_user = session['username']
    meals = []

    try:
        conn, cursor = connect_to_db()
        cursor.execute("SELECT meal_name from meals WHERE username  = ?", (session['username'],))
        records = cursor.fetchall()
        for record in records:
            meals.append(record[0])
    except sqlite3.Error as e:
        flash("Error fetching meals")
        print("Error in db while fetching meals -", e)

    finally:
        conn.close()

    return render_template("diary.html", current_user=current_user, meals=meals)


@app.route("/add_meal", methods=['POST'])
@login_required
def add_meal():
    meal_name = request.form.get('meal_name')
    if not meal_name:
        flash("Please enter a meal name.", "error")
        return redirect("/diary")
    if not meal_name.isalpha():
        flash("Meal name can only be alphabetical", "error")
        return redirect("/diary")
    
    try:
        conn, cursor = connect_to_db()
        cursor.execute("SELECT * FROM meals WHERE username = ? AND meal_name = ?", (session['username'], meal_name))
        meal_exists = cursor.fetchall()
        
        if meal_exists:
            flash("This meal already exists!",  "error")
            return redirect("/diary")
        else:
            cursor.execute("INSERT INTO meals (meal_name, username) VALUES (?,?)", (meal_name, session['username']))
            conn.commit()
            flash("Meal entered successfully", "success")
        
    except sqlite3.Error as e:
        print("Error fetching Meals", e)
        flash("An error occurred while entering meal.", "error")
        return redirect("/diary")
    
    finally:
        if conn:
            conn.close()

    return redirect("/diary")


@app.route("/food/<food_name>")
def get_food(food_name):
    url = 'https://trackapi.nutritionix.com/v2/search/instant'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-app-id': APP_ID, 'x-app-key': API_KEY}
    params = {'query': food_name}

    response = requests.get(url, headers=headers, params=params)
    print("Instant API response: ", response)
    
    if response.status_code != 200:
        return jsonify({"error": "Failed to fetch data from Nutritionix API"}), 500
    
    data = response.json()
    
    branded_list = data.get('branded', [])
    common_list = data.get('common', [])
    
    if not branded_list:
        return jsonify({"message": "Food not found."}), 404
    
    nix_item_id = branded_list[0]['nix_item_id']
    print(nix_item_id)
    return get_nutrients(nix_item_id)

def get_nutrients(nix_item_id):
    url = 'https://trackapi.nutritionix.com//v2/search/item'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-app-id': APP_ID, 'x-app-key': API_KEY}
    params = {'nix_item_id': nix_item_id}

    response = requests.get(url, headers=headers, params=params)
    print("get_nutrients API response:", response)

    if response.status_code != 200:
        print("Error in getting nutrients")
        return jsonify({"error": "Failed to fetch data from Nutritionix API"}), 500

    data = response.json()

    serving_qty = data['foods'][0]['serving_qty']
    serving_weight_grams = data['foods'][0]['serving_weight_grams']

    print(serving_qty, serving_weight_grams)

    nf_calories = data['foods'][0]['nf_calories']
    nf_protein = data['foods'][0]['nf_protein']
    nf_total_carbohydrate = data['foods'][0]['nf_total_carbohydrate']
    nf_total_fat = data['foods'][0]['nf_total_fat']

    print(nf_calories, nf_protein, nf_total_carbohydrate, nf_total_fat)

    return jsonify(
        {'calories': nf_calories, 'protein': nf_protein, 'carbohydates': nf_total_carbohydrate, 'fat': nf_total_fat}
        )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)

