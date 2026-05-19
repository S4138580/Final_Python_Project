import Python.pyhtml as pyhtml

DATABASE = "Database/immunisation.db"
TEMPLATE = "Html/Webpage1.html"


def format_number(value):
    if value is None:
        return "0"

    if value >= 1_000_000_000:
        return f"{value / 1_000_000_000:.2f} B"

    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f} M"

    if value >= 1_000:
        return f"{value / 1_000:.1f} K"

    return str(int(value))


def get_homepage_summary():

    year_data = pyhtml.get_results_from_query(DATABASE, """
        SELECT MIN(year), MAX(year), COUNT(DISTINCT year)
        FROM Vaccination;
    """)[0]

    country_data = pyhtml.get_results_from_query(DATABASE, """
        SELECT COUNT(DISTINCT country)
        FROM Vaccination;
    """)[0]

    dose_data = pyhtml.get_results_from_query(DATABASE, """
        SELECT SUM(doses)
        FROM Vaccination
        WHERE doses IS NOT NULL;
    """)[0]

    case_data = pyhtml.get_results_from_query(DATABASE, """
        SELECT SUM(cases)
        FROM InfectionData
        WHERE cases IS NOT NULL;
    """)[0]

    min_year, max_year, total_years = year_data

    return {
        "YEAR_RANGE": f"{min_year}–{max_year}",
        "YEAR_SUBTITLE": f"{total_years} years of comprehensive records",
        "TOTAL_COUNTRIES": str(country_data[0]),
        "TOTAL_DOSES": format_number(dose_data[0]),
        "TOTAL_CASES": format_number(case_data[0]),
    }


def disease_color(index):
    colors = ["measles", "rubella", "pertussis"]
    return colors[index % len(colors)]


def render_disease_item(disease, index):

    code = disease[0]
    name = disease[1]
    color = disease_color(index)

    return f"""
    <li class="disease-item">
      <span class="disease-item__dot disease-item__dot--{color}"></span>

      <div class="disease-item__info">
        <span class="disease-item__name">{name}</span>
        <span class="disease-item__code">{code}</span>
      </div>

      <span class="disease-item__badge">
        Tracked
      </span>
    </li>
    """


def render_disease_list():

    diseases = pyhtml.get_results_from_query(DATABASE, """
        SELECT id, description
        FROM Infection_Type
        ORDER BY id;
    """)

    disease_html = ""

    for index, disease in enumerate(diseases):
        disease_html += render_disease_item(disease, index)

    return f"""
    <ul class="disease-list">
        {disease_html}
    </ul>
    """


def get_page_html(form_data):

    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    summary = get_homepage_summary()

    for key, value in summary.items():
        page_html = page_html.replace(
            "{{" + key + "}}",
            value
        )

    page_html = page_html.replace(
        "{{DISEASE_LIST}}",
        render_disease_list()
    )

    return page_html
