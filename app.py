# app.py
from xhtml2pdf import pisa
import streamlit as st
from meal_planner import generate_meal_plan, suggest_alternative_dish
from recipe_finder import fetch_recipes, search_recipe_links
from pdf_exporter import convert_html_to_pdf, build_html_for_pdf
from supabase_rate_limiter import check_and_increment_usage, get_remaining_calls
from streamlit_google_auth import Authenticate
import json

st.set_page_config(page_title="Personalized Meal Planner", layout="wide")
st.title("🍽️ Personalized Meal Planner")

with open("google_credentials.json", "w") as f:
    json.dump({
        "installed": {   # some libraries expect an "installed" key around these fields
            "client_id": st.secrets["client_id"],
            "client_secret": st.secrets["client_secret"],
            "redirect_uris": [st.secrets["redirect_uri"]],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }, f)

# 3b) Initialize the authenticator
authenticator = Authenticate(
    secret_credentials_path="google_credentials.json",
    cookie_name="meal_planner_cookie",
    cookie_key=st.secrets["cookie_secret"],    # define a random 32-byte in secrets.toml too
    redirect_uri=st.secrets["redirect_uri"],
)

# 3c) Run the check → login flow
authenticator.check_authentification()
authenticator.login()

# 3d) Gate the rest of your app
if not st.session_state.get("connected"):
    st.stop()
else:
    if st.button('Log out'):
        authenticator.logout()

    user_email = st.session_state['user_info'].get('email')

    remaining = get_remaining_calls(user_email)
    LIMIT = 20

    st.sidebar.markdown(f"**Remaining calls:** `{remaining} / {LIMIT}`")

    # --- User Inputs ---
    st.sidebar.header("User Preferences")
    diet = st.sidebar.selectbox("Dietary Preference", ["Non-Vegetarian", "Pescatarian", "Eggetarian", "Vegetarian", "Vegan", "Keto", "Gluten-Free"])
    meals = st.sidebar.multiselect("Meals", ["Breakfast", "Lunch", "Snack", "Dinner"])
    location = st.sidebar.text_input("Your Location", "India")
    cuisine = st.sidebar.text_input("Preferred Cuisine", "Indian")
    variance = st.sidebar.slider("Cuisine Variance (%)", 0, 100, 30)
    ingredients = st.sidebar.text_area("Must-include Ingredients (comma-separated)", "tofu, spinach")
    allergies = st.sidebar.text_area("Allergies (comma-separated)", "peanuts, pineapple")
    days = st.sidebar.radio("Number of Days", [1, 3, 5, 7, 10])

    if "plan" not in st.session_state:
        st.session_state.plan = {}
        st.session_state.enriched = {}
        st.session_state.replacements = {}
        st.session_state.alternatives = {}

    if st.sidebar.button("Generate Plan"):
        with st.spinner("Generating meal plan and fetching recipes..."):
            check_and_increment_usage(user_email)
            plan = generate_meal_plan(diet, location, cuisine, variance, ingredients, days, meals, allergies)
            enriched = fetch_recipes(plan, location)
            st.session_state.plan = plan
            st.session_state.enriched = enriched
            st.session_state.replacements = {}
            st.session_state.alternatives = {}

    # --- Display Table and Manage Replacements ---
    plan = st.session_state.plan
    enriched = st.session_state.enriched

    for day, meals in enriched.items():
        st.markdown(f"## 🗓️ {day}")
        html_output = """
        <style>
            table {
                width: 100%;
                border-collapse: collapse;
                font-family: Arial, sans-serif;
                font-size: 15px;
                margin-bottom: 20px;
            }
            th {
                background-color: #6c757d;
                color: white;
                padding: 10px;
            }
            td {
                background-color: #f8f9fa;
                padding: 10px;
                border: 1px solid #dee2e6;
                vertical-align: top;
            }
            tr:hover td {
                background-color: #e9ffe9;
            }
        </style>
        <table>
            <tr>
                <th>🍽️ Meal</th>
                <th>🍛 Dish</th>
                <th>📊 Macros</th>
                <th>🔗 Recipes</th>
                <th>Replace?</th>
            </tr>
        """
        for meal_time, info in meals.items():
            if meal_time.lower() == "total macros":
                continue

            dish = info["dish"]
            macros = info.get("macros", "")
            recipes = info.get("recipes", [])
            links = "<br>".join([
                f"<a href='{link}' target='_blank'>🍽️ Recipe {i+1}</a>" for i, link in enumerate(recipes)
            ])

            meal_id = f"{day}_{meal_time}".replace(" ", "_")
            checkbox = st.checkbox(f"Replace {dish} ({meal_time})", key=f"check_{meal_id}")
            if checkbox and meal_id not in st.session_state.replacements:
                st.session_state.replacements[meal_id] = None
                with st.spinner("Suggesting alternatives..."):
                    check_and_increment_usage(user_email)
                    st.session_state.alternatives[meal_id] = suggest_alternative_dish(
                        diet=diet,
                        location=location,
                        cuisine=cuisine,
                        ingredients=ingredients,
                        allergies=allergies,
                        meal_type=meal_time,
                        current_dish=dish
                    )

            html_output += f"""
            <tr>
                <td>{meal_time}</td>
                <td>{dish}</td>
                <td>{macros}</td>
                <td>{links}</td>
                <td>{'Yes' if checkbox else 'No'}</td>
            </tr>
            """

            # Show dropdowns for selected dishes
            if checkbox and meal_id in st.session_state.alternatives:
                options = [a["Dish"] for a in st.session_state.alternatives[meal_id]]
                choice = st.selectbox("Choose replacement", options, key=f"select_{meal_id}")
                st.session_state.replacements[meal_id] = choice

        html_output += "</table>"
        html_output = html_output.replace("\n", "")
        st.markdown(html_output, unsafe_allow_html=True)

        if "Total Macros" in meals:
            st.markdown("### 🧪 Total Macros")
            st.success(meals["Total Macros"])

    # --- Download PDF and Replace Dishes ---
    if enriched:
        if st.button("✅ Replace Selected Dishes"):
            for day, meals in st.session_state.enriched.items():
                for meal_time, info in meals.items():
                    meal_id = f"{day}_{meal_time}".replace(" ", "_")
                    if meal_id in st.session_state.replacements and st.session_state.replacements[meal_id]:
                        new_dish = st.session_state.replacements[meal_id]
                        new_macros = next(
                            (a["Macros"] for a in st.session_state.alternatives[meal_id] if a["Dish"] == new_dish),
                            ""
                        )
                        plan[day][meal_time] = {
                            "Dish": new_dish,
                            "Macros": new_macros
                        }
                        st.session_state.enriched[day][meal_time] = {
                            "dish": new_dish,
                            "macros": new_macros,
                            "recipes": search_recipe_links(new_dish, location)
                        }
            st.rerun()
        html_for_pdf = build_html_for_pdf(enriched)
        pdf_bytes = convert_html_to_pdf(html_for_pdf)
        if pdf_bytes:
            st.download_button(
                label="📄 Download Meal Plan as PDF",
                data=pdf_bytes,
                file_name="meal_plan.pdf",
                mime="application/pdf"
            )
