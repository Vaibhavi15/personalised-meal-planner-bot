from xhtml2pdf import pisa
from io import BytesIO
import html

def build_html_for_pdf(enriched_plan: dict) -> str:
    
    html_output = """
    <html>
    <head>
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
            h2 {
                color: #333333;
            }
        </style>
    </head>
    <body>
    """

    for day, meals in enriched_plan.items():
        html_output += f"<h2>🗓️ {html.escape(day)}</h2>"
        html_output += """
        <table>
            <tr>
                <th>🍽️ Meal</th>
                <th>🍛 Dish</th>
                <th>📊 Macros</th>
                <th>🔗 Recipes</th>
            </tr>
        """

        for meal_time, info in meals.items():
            if meal_time.lower() == "total macros":
                continue
            meal = html.escape(meal_time)
            dish = html.escape(info.get("dish", ""))
            macros = html.escape(info.get("macros", ""))
            recipes = info.get("recipes", [])
            recipe_links = "<br>".join(
                f"<a href='{html.escape(link)}'>🔗 Recipe {i+1}</a>" for i, link in enumerate(recipes)
            )
            html_output += f"""
            <tr>
                <td>{meal}</td>
                <td>{dish}</td>
                <td>{macros}</td>
                <td>{recipe_links}</td>
            </tr>
            """

        html_output += "</table>"

        if "Total Macros" in meals:
            total_macros = html.escape(meals["Total Macros"])
            html_output += f"<p><strong>🧮 Total Macros:</strong> {total_macros}</p>"

    html_output += "</body></html>"
    return html_output


def convert_html_to_pdf(source_html: str) -> bytes:
    output = BytesIO()
    pisa_status = pisa.CreatePDF(src=source_html, dest=output)
    if pisa_status.err:
        return None
    return output.getvalue()