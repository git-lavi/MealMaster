from flask import Flask, flash, request, redirect, session, render_template, abort, url_for, jsonify
import werkzeug
import sqlite3
import werkzeug.security
import requests


app = Flask(__name__)
app.secret_key = 'my super secret key'

APP_ID = 'b1fa76db'
API_KEY = '53125e7fe9fd59ceb0f1c2dc4b04ab8f'


def connect_to_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    return conn, cursor


def commit_close_db(conn: sqlite3.Connection):
    conn.commit()
    conn.close()


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
def dashboard():
    if 'username' not in session:
        abort(401)  # Unauthorized: User is not logged in
    current_user = session['username']
    return render_template("dashboard.html", current_user=current_user)


@app.errorhandler(401)
def unauthorized(error):
    return render_template('unauthorized.html'), 401


@app.route("/food/<food_name>")
def get_food_nutrition(food_name):
    url = 'https://trackapi.nutritionix.com/v2/search/instant/'
    headers = {'Content-Type': 'application/json', 'x-app-id': APP_ID, 'x-app-key': API_KEY}
    params = {'query': food_name, 'fields': 'item_name,nf_calories,nf_protein,nf_total_carbohydrate,nf_total_fat'}

    response = requests.get(url, headers=headers, params=params)
    print("API response: ", response)
    data = response.json()

    # Extract info from response
    if 'foods' in data and data['foods']:
        food_item = data['foods'][0]  # Assuming the first item in the list is the desired one
        nutrition_info = {
            'name': food_item['food_name'],
            'calories': food_item['nf_calories'],
            'protein': food_item['nf_protein'],
            'carbohydrates': food_item['nf_total_carbohydrate'],
            'fat': food_item['nf_total_fat']
        }
        return jsonify(nutrition_info)
    else:
        return jsonify({'error': 'Food not found'}), 404



@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)

