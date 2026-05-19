import Python.pyhtml as pyhtml


DATABASE = "Database/immunisation.db"
TEMPLATE = "Html/Webpage_4_Economy.html"
ROWS_PER_PAGE = 5
ORDER_OPTIONS = [
    ("country_az", "A-z"),
    ("country_za", "Z-a"),
    ("cases_desc", "Total cases high-low"),
    ("cases_asc", "Total cases low-high"),
]
ORDER_BY_SQL = {
    "country_az": "c.name ASC, i.cases DESC",
    "country_za": "c.name DESC, i.cases DESC",
    "cases_desc": "i.cases DESC, c.name ASC",
    "cases_asc": "i.cases ASC, c.name ASC",
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


def format_number(value):
    if value == None:
        return "0"
    return f"{int(round(float(value))):,}"


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


def build_query_string(economy, infection, year, order_by, country_page):
    return (
        f"economy={economy}"
        f"&infection={infection}"
        f"&year={year}"
        f"&order_by={order_by}"
        f"&country_page={country_page}"
        f"&submitted=1"
    )


def get_country_rows(economy, infection, year, order_by, country_page):
    offset = (country_page - 1) * ROWS_PER_PAGE
    order_clause = ORDER_BY_SQL[order_by]
    query = f"""
    SELECT it.description, c.name, e.phase, i.cases,
           ROUND((i.cases / cp.population) * 100000, 2) AS case_per_100k
    FROM InfectionData i
    JOIN Infection_Type it ON i.inf_type = it.id
    JOIN Country c ON i.country = c.CountryID
    JOIN Economy e ON c.economy = e.economyID
    JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
    WHERE e.economyID = {economy}
      AND i.inf_type = '{infection}'
      AND i.year = {year}
    ORDER BY {order_clause}
    LIMIT {ROWS_PER_PAGE}
    OFFSET {offset};
    """
    return pyhtml.get_results_from_query(DATABASE, query)


def get_all_country_rows(economy, infection, year, order_by):
    order_clause = ORDER_BY_SQL[order_by]
    query = f"""
    SELECT it.description, c.name, e.phase, i.cases,
           ROUND((i.cases / cp.population) * 100000, 2) AS case_per_100k
    FROM InfectionData i
    JOIN Infection_Type it ON i.inf_type = it.id
    JOIN Country c ON i.country = c.CountryID
    JOIN Economy e ON c.economy = e.economyID
    JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
    WHERE e.economyID = {economy}
      AND i.inf_type = '{infection}'
      AND i.year = {year}
    ORDER BY {order_clause};
    """
    return pyhtml.get_results_from_query(DATABASE, query)


def get_country_count(economy, infection, year):
    query = f"""
    SELECT COUNT(*)
    FROM InfectionData i
    JOIN Country c ON i.country = c.CountryID
    JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
    WHERE c.economy = {economy}
      AND i.inf_type = '{infection}'
      AND i.year = {year};
    """
    rows = pyhtml.get_results_from_query(DATABASE, query)
    return rows[0][0]


def get_summary_rows(economy, infection, year):
    query = f"""
    SELECT e.phase,
           COUNT(DISTINCT c.CountryID) AS country_count,
           it.description,
           SUM(i.cases) AS total_cases,
           ROUND((SUM(i.cases) / SUM(cp.population)) * 100000, 2) AS case_per_100k
    FROM InfectionData i
    JOIN Infection_Type it ON i.inf_type = it.id
    JOIN Country c ON i.country = c.CountryID
    JOIN Economy e ON c.economy = e.economyID
    JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
    WHERE e.economyID = {economy}
      AND i.inf_type = '{infection}'
      AND i.year = {year}
    GROUP BY e.phase, it.description;
    """
    return pyhtml.get_results_from_query(DATABASE, query)


def get_chart_rows(infection, year):
    query = f"""
    SELECT e.phase,
           ROUND(AVG((i.cases / cp.population) * 100000), 2) AS avg_case_per_100k
    FROM InfectionData i
    JOIN Country c ON i.country = c.CountryID
    JOIN Economy e ON c.economy = e.economyID
    JOIN CountryPopulation cp ON cp.country = i.country AND cp.year = i.year
    WHERE i.inf_type = '{infection}'
      AND i.year = {year}
    GROUP BY e.economyID, e.phase
    ORDER BY e.economyID;
    """
    return pyhtml.get_results_from_query(DATABASE, query)


def csv_value(value):
    text = str(value)
    text = text.replace('"', '""')
    if "," in text or '"' in text or "\n" in text:
        text = '"' + text + '"'
    return text


def make_csv(headers, rows):
    csv_text = ",".join(headers) + "\n"
    for row in rows:
        values = []
        for value in row:
            values.append(csv_value(value))
        csv_text += ",".join(values) + "\n"
    return csv_text


def make_csv_response(filename, headers, rows):
    return {
        "content": make_csv(headers, rows),
        "content_type": "text/csv; charset=utf-8",
        "filename": filename,
    }


def render_country_table(rows):
    if len(rows) == 0:
        return '<tr class="empty-row"><td colspan="5">No matching data found.</td></tr>'

    html = ""
    for row in rows:
        html += f"""
                <tr>
                  <td>{row[0]}</td>
                  <td>{row[1]}</td>
                  <td>{row[2]}</td>
                  <td>{format_number(row[3])}</td>
                  <td>{format_rate(row[4])}</td>
                </tr>
        """
    return html


def render_summary_table(rows):
    if len(rows) == 0:
        return '<tr class="empty-row"><td colspan="5">No matching summary found.</td></tr>'

    html = ""
    for row in rows:
        html += f"""
                <tr>
                  <td>{row[0]}</td>
                  <td>{format_number(row[1])}</td>
                  <td>{row[2]}</td>
                  <td>{format_number(row[3])}</td>
                  <td>{format_rate(row[4])}</td>
                </tr>
        """
    return html


def render_chart(rows):
    if len(rows) == 0:
        return '<p>No chart data available.</p>'

    max_value = 0
    for row in rows:
        if row[1] != None and row[1] > max_value:
            max_value = row[1]

    if max_value == 0:
        max_value = 1

    html = ""
    bar_number = 1
    for row in rows:
        phase = row[0]
        value = row[1] or 0
        width = max(2, int((value / max_value) * 100))
        html += f"""
              <div class="bar-row">
                <div class="bar-top">
                  <span>{phase}</span>
                  <span>{format_rate(value)}</span>
                </div>
                <div class="bar-track">
                  <div class="bar-fill bar-{bar_number}" style="width: {width}%"></div>
                </div>
              </div>
        """
        bar_number += 1
    return html


def render_pager(economy, infection, year, order_by, country_page, total_rows):
    total_pages = max(1, ((total_rows - 1) // ROWS_PER_PAGE) + 1)

    prev_page = max(1, country_page - 1)
    next_page = min(total_pages, country_page + 1)

    prev_class = ""
    next_class = ""
    if country_page <= 1:
        prev_class = " disabled"
    if country_page >= total_pages:
        next_class = " disabled"

    prev_query = build_query_string(economy, infection, year, order_by, prev_page)
    next_query = build_query_string(economy, infection, year, order_by, next_page)

    return (
        f'<a class="{prev_class}" href="/Webpage_4_Economy.html?{prev_query}#country-table">Prev</a>',
        f'<a class="{next_class}" href="/Webpage_4_Economy.html?{next_query}#country-table">Next</a>',
        str(country_page),
    )


def get_page_html(form_data):
    print("About to return Webpage 4 - Infection by Economy...")

    economy_options = pyhtml.get_results_from_query(
        DATABASE,
        "SELECT economyID, phase FROM Economy ORDER BY economyID;",
    )
    infection_options = pyhtml.get_results_from_query(
        DATABASE,
        "SELECT id, description FROM Infection_Type ORDER BY description;",
    )
    year_options = pyhtml.get_results_from_query(
        DATABASE,
        "SELECT DISTINCT year, year FROM InfectionData ORDER BY year DESC;",
    )

    default_economy = 3
    default_infection = "MEA"
    default_year = 2020
    default_order_by = "country_az"

    economy = to_int(get_first_value(form_data, "economy", default_economy), default_economy)
    infection = get_first_value(form_data, "infection", default_infection)
    year = to_int(get_first_value(form_data, "year", default_year), default_year)
    order_by = get_first_value(form_data, "order_by", default_order_by)
    country_page = to_int(get_first_value(form_data, "country_page", 1), 1)

    valid_economies = [row[0] for row in economy_options]
    valid_infections = [row[0] for row in infection_options]
    valid_years = [row[0] for row in year_options]

    if economy not in valid_economies:
        economy = default_economy
    if infection not in valid_infections:
        infection = default_infection
    if year not in valid_years:
        year = default_year
    if order_by not in ORDER_BY_SQL:
        order_by = default_order_by
    if country_page < 1:
        country_page = 1

    country_count = get_country_count(economy, infection, year)
    total_pages = max(1, ((country_count - 1) // ROWS_PER_PAGE) + 1)
    if country_page > total_pages:
        country_page = total_pages

    export_type = get_first_value(form_data, "export", "")
    if export_type == "country":
        rows = get_all_country_rows(economy, infection, year, order_by)
        return make_csv_response(
            "country_infection_cases.csv",
            ["Disease", "Country", "Economic Phase", "Total Cases", "Case per 100k"],
            rows,
        )

    if export_type == "summary":
        rows = get_summary_rows(economy, infection, year)
        return make_csv_response(
            "summary_by_economic_phase.csv",
            ["Economic Phase", "No of Country", "Disease", "Total Cases", "Case per 100k"],
            rows,
        )

    country_rows = get_country_rows(economy, infection, year, order_by, country_page)
    summary_rows = get_summary_rows(economy, infection, year)
    chart_rows = get_chart_rows(infection, year)

    start_row = 0
    end_row = 0
    if country_count > 0:
        start_row = ((country_page - 1) * ROWS_PER_PAGE) + 1
        end_row = min(country_page * ROWS_PER_PAGE, country_count)

    selected_disease = ""
    for row in infection_options:
        if row[0] == infection:
            selected_disease = row[1]

    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    country_prev, country_next, country_page_text = render_pager(
        economy,
        infection,
        year,
        order_by,
        country_page,
        country_count,
    )
    csv_query = build_query_string(economy, infection, year, order_by, country_page)
    country_csv_query = csv_query + "&export=country"
    summary_csv_query = csv_query + "&export=summary"

    show_data = "submitted" in form_data
    data_style = "" if show_data else 'style="display:none"'
    placeholder = not show_data

    replacements = {
        "{{ECONOMY_OPTIONS}}": make_options(economy_options, economy, with_placeholder=placeholder),
        "{{INFECTION_OPTIONS}}": make_options(infection_options, infection, with_placeholder=placeholder),
        "{{YEAR_OPTIONS}}": make_options(year_options, year, with_placeholder=placeholder),
        "{{ORDER_OPTIONS}}": make_options(ORDER_OPTIONS, order_by, with_placeholder=placeholder),
        "{{COUNTRY_ROWS}}": render_country_table(country_rows),
        "{{SUMMARY_ROWS}}": render_summary_table(summary_rows),
        "{{CHART_ROWS}}": render_chart(chart_rows),
        "{{CHART_DISEASE}}": selected_disease,
        "{{CHART_YEAR}}": str(year),
        "{{COUNTRY_SHOWING}}": f"Showing {start_row}-{end_row} of {country_count}",
        "{{COUNTRY_PREV}}": country_prev,
        "{{COUNTRY_NEXT}}": country_next,
        "{{COUNTRY_PAGE}}": country_page_text,
        "{{COUNTRY_CSV_QUERY}}": country_csv_query,
        "{{SUMMARY_CSV_QUERY}}": summary_csv_query,
        "{{DATA_SECTION_STYLE}}": data_style,
    }

    for placeholder in replacements:
        page_html = page_html.replace(placeholder, replacements[placeholder])

    return page_html
