import requests
from flask import flash
from app import APP_ID, API_KEY


# API call exception
class NixAPICallError(Exception):
    pass


def get_nutrients(food_name: str, servings: int):
    """Gets nutrient info from Nutritionix Natural API"""
    
    url = 'https://trackapi.nutritionix.com/v2/natural/nutrients'
    headers = {'Content-Type': 'application/json', 'x-app-id': APP_ID, 'x-app-key': API_KEY}
    json = {'query': food_name}

    try:
        response = requests.post(url, headers=headers, json=json)
        print("get_nutrition API call response:", response)
        data = response.json()
    except requests.RequestException as e:
        print("Error calling API", str(e))
        flash("An error occurred while fetching nutrients", "error")

    if 'foods' not in data:
        print("Food not found in Nutritionix Natural API")
        raise NixAPICallError("Food not found")

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