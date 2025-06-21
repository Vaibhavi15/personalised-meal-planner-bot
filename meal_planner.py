from openai import OpenAI
import os
from dotenv import load_dotenv
import json
import re

load_dotenv()

def extract_json(text):
    # Try extracting JSON from ```json blocks first
    match = re.search(r"```(?:json)?\\s*(\\{.*\\})\\s*```", text, re.DOTALL)
    if match:
        return match.group(1)
    
    # Fall back to raw if not wrapped
    return text.strip()

def generate_meal_plan(diet, location, cuisine, variance, ingredients, days, meals, allergies):
    prompt = f"""
Generate a structured meal plan in valid JSON format for {days} days. Generate a structured meal plan in valid JSON format for {days} days. Include only the following meals each day: {meals}.
Avoid repetition, ensure each meal is balanced, and uses ingredients available in {location}.
Preferred cuisine: {cuisine} with {variance}% variation.
Dietary preference: {diet}.
Try to include these ingredients in a few dishes: {ingredients}.
Must avoid: {allergies}.

Depending on the variation %, include dishes from other cuisines like South/North Indian, Asian, Indo-Chinese, Continental, etc, but ensure to adhere to the days, meals, dietary preference and allergens.

Eggetarian should include eggs, vegetarians should avoid meat, pescatarians can have fish, vegans should avoid all animal products, and keto should be low-carb.

Ensure each meal has adequate protein, carbs, and fiber.

Return ONLY the JSON output with no explanation or markdown wrapping.
{{
  "Day 1": {{
    "Breakfast": {{
      "Dish": "Dish name",
      "Macros": "Carbs: xg, Protein: yg, Fiber: zg"
    }},
    "Lunch": {{
      "Dish": "Dish name",
      "Macros": "..."
    }},
    ...
    "Total Macros": "..."
  }}
}}
"""
    client = OpenAI()
    
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    temperature=0.7
    )

    try:
        content = response.choices[0].message.content
        json_text = extract_json(content)
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Full content:\n", content)
        return {}

def suggest_alternative_dish(diet, location, cuisine, ingredients, allergies, meal_type, current_dish):
    prompt = f"""
Suggest 2 alternative dishes to replace: "{current_dish}" for {meal_type} in a {diet} diet.
Preferred cuisine: {cuisine}. Location: {location}.
Must avoid: {allergies}.
For each alternative, return dish name and estimated macros (Carbs, Protein, Fiber) in JSON format:
[
  {{
    "Dish": "Dish name",
    "Macros": "Carbs: xg, Protein: yg, Fiber: zg"
  }},
  ...
]
Only return the JSON array.
"""

    client = OpenAI()
    
    response = client.chat.completions.create(
        model="gpt-4",  # or your model
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )

    content = response.choices[0].message.content
    json_text = extract_json(content)
    try:
        data = json.loads(json_text)
        return data
    except json.JSONDecodeError as e:
        print("Failed to parse JSON:", e)
        print("Full content:\n", content)
        return {}