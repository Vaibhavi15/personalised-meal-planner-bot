# recipe_finder.py
import requests
import os
from dotenv import load_dotenv

load_dotenv()
SERPER_API_KEY = os.getenv("SERPER_API_KEY")

def search_recipe_links(query, location="India"):
    url = "https://google.serper.dev/search"
    headers = {"X-API-KEY": SERPER_API_KEY}
    payload = {"q": f"{query} recipe {location}", "num": 3}

    res = requests.post(url, json=payload, headers=headers)
    results = res.json().get("organic", [])
    return [r["link"] for r in results[:2]]  # Top 2 links

def fetch_recipes(meal_plan, location):
    enriched = {}
    for day, meals in meal_plan.items():
        enriched[day] = {}
        for meal_time, meal_data in meals.items():
            if meal_time.lower() == "total macros":
                enriched[day][meal_time] = meal_data
                continue
            dish_name = meal_data["Dish"] if isinstance(meal_data, dict) else meal_data
            links = search_recipe_links(dish_name, location)

            enriched[day][meal_time] = {
                "dish": dish_name,
                "macros": meal_data.get("Macros", ""),
                "recipes": links
            }
    return enriched

def fetch_single_recipe(dish_name, location):
    return search_recipe_links(dish_name, location)