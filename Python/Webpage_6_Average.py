import Python.pyhtml as pyhtml


DATABASE = "Database/immunisation.db"
TEMPLATE = "Webpage_6_Average.html"
ROWS_PER_PAGE = 5
ORDER_OPTIONS = [
    ("country_az", "A-z"),
    ("country_za", "Z-a"),
    ("rate_desc", "Rate high-low"),
    ("rate_asc", "Rate low-high"),
]
ORDER_BY_SQL = {
    "country_az": "country_name ASC, country_rate DESC",
    "country_za": "country_name DESC, country_rate DESC",
    "rate_desc": "country_rate DESC, country_name ASC",
    "rate_asc": "country_rate ASC, country_name ASC",
}


def get_first_value(form_data, key, default_value):
    values = form_data.get(key)
    if values == None or len(values) == 0:
        return default_value
    return values[0]


def to_int(value, default_value):
    try:
        return int(value)
    except:
        return default_value


def format_rate(value):
    if value == None:
        return "0"
    text = f"{float(value):,.2f}"
    return text.rstrip("0").rstrip(".")


def make_options(rows, selected_value, with_placeholder=False):
    html = ""
    if with_placeholder:
        html += '<option value="" selected disabled>Select</option>'
        for row in rows:
            html += f'<option value="{row[0]}">{row[1]}</option>'
    else:
        for row in rows:
            value = str(row[0])
            label = str(row[1])
            selected = ' selected="selected"' if value == str(selected_value) else ""
            html += f'<option value="{value}"{selected}>{label}</option>'
    return html


def build_where_clause(infection, year):
    return f"WHERE i.inf_type = '{infection}' AND i.year = {year}"


def build_query_string(infection, year, order_by, country_page):
    return f"infection={infection}&year={year}&order_by={order_by}&country_page={country_page}&submitted=1"


def get_global_rate(infection, year):
    where_clause = build_where_clause(infection, year)
    query = f"""
    SELECT ROUND((SUM(i.cases) / SUM(cp.population)) * 100000, 2)
    FROM InfectionData i
    JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
    {where_clause};
    """
    rows = pyhtml.get_results_from_query(DATABASE, query)
    if rows[0][0] == None:
        return 0
    return rows[0][0]


def get_above_average_count(infection, year, global_rate):
    where_clause = build_where_clause(infection, year)
    having_clause = f"WHERE country_rate > {global_rate}"
    query = f"""
    SELECT COUNT(*)
    FROM (
      SELECT ROUND((i.cases / cp.population) * 100000, 2) AS country_rate
      FROM InfectionData i
      JOIN Country c ON i.country = c.CountryID
      JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
      {where_clause}
    )
    {having_clause};
    """
    rows = pyhtml.get_results_from_query(DATABASE, query)
    return rows[0][0]


def get_above_average_rows(infection, year, global_rate, order_by, country_page):
    offset = (country_page - 1) * ROWS_PER_PAGE
    where_clause = build_where_clause(infection, year)
    order_clause = ORDER_BY_SQL[order_by]
    query = f"""
    SELECT country_name, disease, country_rate, year_value,
           ROUND(country_rate - {global_rate}, 2) AS above_global_by
    FROM (
      SELECT c.name AS country_name,
             it.description AS disease,
             ROUND((i.cases / cp.population) * 100000, 2) AS country_rate,
             i.year AS year_value
      FROM InfectionData i
      JOIN Infection_Type it ON i.inf_type = it.id
      JOIN Country c ON i.country = c.CountryID
      JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
      {where_clause}
    )
    WHERE country_rate > {global_rate}
    ORDER BY {order_clause}
    LIMIT {ROWS_PER_PAGE}
    OFFSET {offset};
    """
    return pyhtml.get_results_from_query(DATABASE, query)


def get_all_above_average_rows(infection, year, global_rate, order_by):
    where_clause = build_where_clause(infection, year)
    order_clause = ORDER_BY_SQL[order_by]
    query = f"""
    SELECT country_name, disease, country_rate, year_value,
           ROUND(country_rate - {global_rate}, 2) AS above_global_by
    FROM (
      SELECT c.name AS country_name,
             it.description AS disease,
             ROUND((i.cases / cp.population) * 100000, 2) AS country_rate,
             i.year AS year_value
      FROM InfectionData i
      JOIN Infection_Type it ON i.inf_type = it.id
      JOIN Country c ON i.country = c.CountryID
      JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
      {where_clause}
    )
    WHERE country_rate > {global_rate}
    ORDER BY {order_clause};
    """
    return pyhtml.get_results_from_query(DATABASE, query)


def csv_value(value):
    text = str(value)
    text = text.replace('"', '""')
    if "," in text or '"' in text or "\n" in text:
        text = '"' + text + '"'
    return text


def make_csv_response(filename, headers, rows):
    csv_text = ",".join(headers) + "\n"
    for row in rows:
        csv_text += ",".join(csv_value(value) for value in row) + "\n"

    return {
        "content": csv_text,
        "content_type": "text/csv; charset=utf-8",
        "filename": filename,
    }


def render_country_table(rows, global_rate, country_page):
    if len(rows) == 0:
        return '<tr class="empty-row"><td colspan="5">No countries exceed the global rate.</td></tr>'

    html = ""
    if country_page == 1:
        global_disease = rows[0][1]
        html += f"""
                <tr>
                  <td>Global</td>
                  <td>{global_disease}</td>
                  <td>{format_rate(global_rate)}</td>
                  <td>-</td>
                  <td>-</td>
                </tr>
        """

    for row in rows:
        html += f"""
                <tr>
                  <td>{row[0]}</td>
                  <td>{row[1]}</td>
                  <td>{format_rate(row[2])}</td>
                  <td>{row[3]}</td>
                  <td>+{format_rate(row[4])}</td>
                </tr>
        """
    return html


def render_chart(rows, global_rate):
    if len(rows) == 0:
        return "<p>No chart data available.</p>"

    max_value = global_rate
    for row in rows:
        if row[2] > max_value:
            max_value = row[2]

    if max_value == 0:
        max_value = 1

    chart_rows = [("Global", global_rate)] + [(row[0], row[2]) for row in rows[:4]]
    html = ""
    bar_number = 1

    for row in chart_rows:
        label = row[0]
        value = row[1]
        width = max(2, int((value / max_value) * 100))
        html += f"""
              <div class="bar-row">
                <div class="bar-top">
                  <span>{label}</span>
                  <span>{format_rate(value)}</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill bar-{bar_number}" style="width: {width}%"></div>
                </div>
              </div>
        """
        bar_number += 1
    return html


def render_pager(infection, year, order_by, country_page, total_rows):
    total_pages = max(1, ((total_rows - 1) // ROWS_PER_PAGE) + 1)
    prev_page = max(1, country_page - 1)
    next_page = min(total_pages, country_page + 1)

    prev_class = ""
    next_class = ""
    if country_page <= 1:
        prev_class = " disabled"
    if country_page >= total_pages:
        next_class = " disabled"

    prev_query = build_query_string(infection, year, order_by, prev_page)
    next_query = build_query_string(infection, year, order_by, next_page)

    return (
        f'<a class="{prev_class}" href="/Webpage_6_Average.html?{prev_query}#above-average-table">Prev</a>',
        f'<a class="{next_class}" href="/Webpage_6_Average.html?{next_query}#above-average-table">Next</a>',
        str(country_page),
    )


def get_selected_label(rows, selected_value, all_label):
    for row in rows:
        if row[0] == selected_value:
            return row[1]
    return all_label


def get_page_html(form_data):
    print("About to return Webpage 6 - Above Average...")

    infection_options = pyhtml.get_results_from_query(
        DATABASE,
        "SELECT id, description FROM Infection_Type ORDER BY description;",
    )
    year_options = pyhtml.get_results_from_query(
        DATABASE,
        "SELECT DISTINCT year, year FROM InfectionData ORDER BY year DESC;",
    )

    default_infection = "MEA"
    default_year = 2020
    default_order_by = "country_az"

    infection = get_first_value(form_data, "infection", default_infection)
    year_value = get_first_value(form_data, "year", default_year)
    order_by = get_first_value(form_data, "order_by", default_order_by)
    country_page = to_int(get_first_value(form_data, "country_page", 1), 1)

    valid_infections = [row[0] for row in infection_options]
    valid_years = [str(row[0]) for row in year_options]

    if infection not in valid_infections:
        infection = default_infection
    if year_value not in valid_years:
        year_value = str(default_year)
    if order_by not in ORDER_BY_SQL:
        order_by = default_order_by

    year = to_int(year_value, default_year)

    if country_page < 1:
        country_page = 1

    global_rate = get_global_rate(infection, year)
    country_count = get_above_average_count(infection, year, global_rate)
    total_pages = max(1, ((country_count - 1) // ROWS_PER_PAGE) + 1)
    if country_page > total_pages:
        country_page = total_pages

    export_type = get_first_value(form_data, "export", "")
    if export_type == "csv":
        rows = get_all_above_average_rows(infection, year, global_rate, order_by)
        return make_csv_response(
            "countries_above_global_rate.csv",
            ["Country", "Infection Type", "Case per 100k", "Year", "Above Global By"],
            rows,
        )

    rows = get_above_average_rows(infection, year, global_rate, order_by, country_page)

    start_row = 0
    end_row = 0
    if country_count > 0:
        start_row = ((country_page - 1) * ROWS_PER_PAGE) + 1
        end_row = min(country_page * ROWS_PER_PAGE, country_count)

    selected_disease = get_selected_label(infection_options, infection, "Measles")
    selected_year = str(year)
    global_title = f"Global {selected_disease} Rate ({selected_year}): {format_rate(global_rate)} per 100,000 people"

    chart_label = f"{selected_disease} · {selected_year}"
    country_prev, country_next, country_page_text = render_pager(
        infection,
        year,
        order_by,
        country_page,
        country_count,
    )
    csv_query = build_query_string(infection, year, order_by, country_page) + "&export=csv"

    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    show_data = "submitted" in form_data
    data_style = "" if show_data else 'style="display:none"'
    placeholder = not show_data

    replacements = {
        "{{INFECTION_OPTIONS}}": make_options(infection_options, infection, with_placeholder=placeholder),
        "{{YEAR_OPTIONS}}": make_options(year_options, str(year), with_placeholder=placeholder),
        "{{ORDER_OPTIONS}}": make_options(ORDER_OPTIONS, order_by, with_placeholder=placeholder),
        "{{GLOBAL_TITLE}}": global_title,
        "{{COUNTRY_ROWS}}": render_country_table(rows, global_rate, country_page),
        "{{COUNTRY_SHOWING}}": f"Showing {start_row}-{end_row} of {country_count}",
        "{{COUNTRY_PREV}}": country_prev,
        "{{COUNTRY_NEXT}}": country_next,
        "{{COUNTRY_PAGE}}": country_page_text,
        "{{CHART_ROWS}}": render_chart(rows, global_rate),
        "{{CHART_LABEL}}": chart_label,
        "{{CSV_QUERY}}": csv_query,
        "{{DATA_SECTION_STYLE}}": data_style,
    }

    for placeholder in replacements:
        page_html = page_html.replace(placeholder, replacements[placeholder])

    return page_html
