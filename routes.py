from flask import render_template, redirect, url_for, flash, session, request, jsonify
from app import app
from database import connect_to_db, commit_close_db
from utils import get_nutrients, NixAPICallError, totals
import sqlite3
import werkzeug.security
from functools import wraps
import json


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
    
    try:
        conn, cursor = connect_to_db()
        cursor.execute("""
                    SELECT m.meal_name, f.food_name, f.calories, f.protein, f.carbohydrates, f.fat
                    FROM meals as m
                    JOIN foods as f
                    ON m.meal_id = f.meal_id
                    """)
        records = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
        foods = [dict(zip(columns, record)) for record in records]
        total_nutrients = totals(foods)
    
    except Exception as e:
        print("An error occurred:", str(e))
        flash("Error loading nutrients", "error")
        return redirect("/diary")
    
    finally:
        if conn:
            conn.close()
    
    total_nutrients_json = json.dumps(total_nutrients)

    if not records:
        total_nutrients_json = None

    print(f"total_nutrients_json = {total_nutrients_json}, type = {type(total_nutrients_json)}")
    return render_template("dashboard.html",
                           current_user=current_user, total_nutrients=total_nutrients_json, calories=total_nutrients['Calories'])


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
        nutrients = get_nutrients(food_name, food_servings)
    except Exception as e:
        flash(str(e), "error")
        return redirect("/diary")

    if not nutrients:
        flash("Error fetching nutrients", "error")
        return redirect("/diary")
    
    # Nutrient details from nutrients
    calories, protein, carbohydrates, fat = nutrients['calories'], nutrients['protein'], nutrients['carbohydrates'], nutrients['fat']

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


@app.route("/remove_meal", methods=['POST'])
@login_required
def remove_meal():
    meal_id = request.form.get('meal-id')

    try:
        conn, cursor = connect_to_db()
        cursor.execute("""
                       DELETE FROM foods WHERE meal_id = ?
                       """, (meal_id,)
                       )
        cursor.execute("""
                       DELETE FROM meals WHERE meal_id = ?
                       """, (meal_id,)
                       )

    except sqlite3.Error as e:
        conn.rollback()
        print("Error deleting meal", str(e))
        flash("Error deleting meal", "error")
        return redirect("/diary")

    finally:
        if conn:
            commit_close_db(conn)

    flash("Meal deleted successfully", "success")
    return redirect("/diary")


@app.route("/remove_food", methods=['POST'])
@login_required
def remove_food():
    food_id = request.form.get("food-id")
    print(food_id)

    try:
        conn, cursor = connect_to_db()
        cursor.execute("DELETE FROM foods WHERE food_id = ?", (food_id,))
    except sqlite3.Error as e:
        flash("Error deleting food", "error")
        print("Error deleting food", str(e))
        conn.rollback()
        return redirect("/diary")
    finally:
        if conn:
            conn.commit()
            conn.close()
    
    flash("Food deleted successfully.", "success")
    return redirect("/diary")


@app.route("/change_pw", methods=['GET', 'POST'])
@login_required
def change_pw():
    current_user = session['username']
    
    if request.method == 'POST':
        current_pw = request.form.get("current-pw")
        new_pw = request.form.get("new-pw")
        confirm_pw = request.form.get("confirm-pw")

        if not current_pw or not new_pw or not confirm_pw:
            flash("Please fill out all fields", "error")
            return redirect("/change_pw")
        elif new_pw != current_pw:
            flash("Passwords do not match.", "error")
            return redirect("/change_pw")
        
        # Update pw in DB
        try:
            conn, cursor = connect_to_db()
            cursor.execute("SELECT hash FROM users WHERE username = ?", (current_user,))
            db_pw = cursor.fetchone()[0]
            print(db_pw)

            if not werkzeug.security.check_password_hash(db_pw, current_pw):
                flash("'Current password' is incorrect.", "error")
                if conn:
                    conn.close()
                return redirect("/change_pw")
            
            else:
                hashed_pw = werkzeug.security.generate_password_hash(new_pw)
                cursor.execute("""
                               UPDATE users
                               SET hash = ?
                               WHERE username = ?
                               """,
                               (hashed_pw, current_user)
                               )
                flash("Password changed successfully", "success")
                conn.commit()

        except sqlite3.Error as e:
            flash("An error occurred. Please try again later.", "error")
            print("Error occurred when changing password", str(e))
            if conn:
                conn.rollback()
            return redirect("/change_pw")
        
        finally:
            if conn:
                conn.close()
        
        return redirect("/dashboard")

    else:
        return render_template("change_pw.html", current_user=current_user)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

