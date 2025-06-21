import streamlit as st

st.title("🔍 HTML Table Render Debug")

html = """
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
        <th>Meal</th>
        <th>Dish</th>
        <th>Macros</th>
        <th>Recipes</th>
    </tr>
    <tr>
        <td>Lunch</td>
        <td>Paneer Butter Masala</td>
        <td>Carbs: 70g, Protein: 20g, Fiber: 5g</td>
        <td><a href='https://hebbarskitchen.com' target='_blank'>🍽️ Recipe 1</a></td>
    </tr>
</table>
"""

# See what will be rendered
#st.code(html, language='html')

# Actually render the table
st.markdown(html, unsafe_allow_html=True)
