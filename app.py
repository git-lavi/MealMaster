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


# API call exception
class NixAPICallError(Exception):
    pass


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

    try:
        conn, cursor = connect_to_db()
        cursor.execute("SELECT * from meals WHERE username  = ?", (session['username'],))
        records = cursor.fetchall()
        
        # Convert records to a list of dictionaries
        meal_columns = [column[0] for column in cursor.description]
        meals = [dict(zip(meal_columns, record)) for record in records]
        

        # Fetch foods for each meal
        for meal in meals:
            cursor.execute("SELECT * FROM foods WHERE meal_id = ?", (meal['meal_id'],))
            food_records = cursor.fetchall()
            food_columns = [column[0] for column in cursor.description]
            meal['foods'] = [dict(zip(food_columns, record)) for record in food_records]

        # testprint
        print(meal_columns, meals)

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


@app.route("/add_food", methods=['POST'])
@login_required
def add_food():
    meal_id = request.form.get('meal-id')
    food_name = request.form.get("food-name")
    food_servings = request.form.get("food-servings")

    if not meal_id or not food_name or not food_servings or not food_servings.isdigit():
        flash("invalid input", "error")
        return redirect("/diary")
    
    food_servings = int(food_servings)

    try:
        nix_food_name = get_nix_food_name(food_name)
    except Exception as e:
        flash(str(e), "error")
        return redirect("/diary")
    
    nutrients = get_nutrients(nix_food_name, food_servings)

    if not nutrients:
        flash("Error fetching nutrients", "error")
        return redirect("/diary")
    
    # Nutrient details from nutrients
    calories, protein, carbohydrates, fat = nutrients['calories'], nutrients['protein'], nutrients['carbohydrates'], nutrients['fat']
    
    print(f"meal_id: {meal_id}, food_name: {food_name}, food_servings: {food_servings}, nix_food_name: {nix_food_name}, calories: {calories}, protein: {protein}, carbohydrates: {carbohydrates}, fat: {fat}")

    # Insert food into DB
    try:
        conn, cursor = connect_to_db()
        cursor.execute("""
                       INSERT INTO foods (food_name, servings, calories, protein, carbohydrates, fat, meal_id)
                       VALUES (?, ?, ?, ?, ?, ?, ?)
                       """, (food_name, food_servings, calories, protein, carbohydrates, fat, meal_id)
                       )
    except sqlite3.Error as e:
        print("Error entering food into DB", e)
        flash("An error occurred while adding food", "error")
        conn.rollback()
    finally:
        if conn:
            conn.commit()
            conn.close()
        
    flash("Food added successfully", "success")
    return redirect("/diary")


def get_nix_food_name(food_name):
    # Call API
    url = 'https://trackapi.nutritionix.com/v2/search/instant'
    headers = {'Content-Type': 'application/x-www-form-urlencoded', 'x-app-id': APP_ID, 'x-app-key': API_KEY}
    params = {'query': food_name}
    
    # testprint
    print(params)
    
    response = requests.get(url, headers=headers, params=params)
    print("get_food_nix_id API call response:",  response)
    if response.status_code != 200:
        print("Error fetching food list Nutritionix API")
        raise NixAPICallError("Error fetching food list from Nutritionix API")
    
    data = response.json()
    
    # Get food only from common item list
    common_list = data.get('common', [])
    
    if not common_list:
        print("Error obtaining food from Nutritionix API")
        raise NixAPICallError("Sorry, we couldn't find this food.")
    
    nix_food_name = common_list[0]['food_name']
    return nix_food_name      


def get_nutrients(nix_food_name: str, servings: int):
    url = 'https://trackapi.nutritionix.com/v2/natural/nutrients'
    headers = {'Content-Type': 'application/json', 'x-app-id': APP_ID, 'x-app-key': API_KEY}
    json = {'query': nix_food_name}

    response = requests.post(url, headers=headers, json=json)
    print("get_nutrition API call response:", response)
    data = response.json()

    foods = data['foods']
    nf_calories = foods[0]['nf_calories']
    nf_protein = foods[0]['nf_protein']
    nf_total_carbohydrate = foods[0]['nf_total_carbohydrate']
    nf_total_fat = foods[0]['nf_total_fat']

    # Multiply with servings
    calories = int(round((nf_calories * servings), 0))
    protein = int(round((nf_protein * servings), 0))
    carbohydrates = int(round((nf_total_carbohydrate * servings), 0))
    fat = int(round((nf_total_fat * servings), 0))

    print(f"calories = {calories}, protein = {protein}, carbohydrates = {carbohydrates}, fat = {fat}")
    return {'calories': calories, 'protein': protein, 'carbohydrates': carbohydrates, 'fat': fat, 'servings': servings}


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))



if __name__ == "__main__":
    app.run(debug=True)

