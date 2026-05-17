import sys

import pyhtml


DATABASE = "immunisation.db"
TEMPLATE = "Webpage5.html"


def get_first_value(form_data, key, default_value):
    values = form_data.get(key)
    if values == None or len(values) == 0 or values[0] == "":
        return default_value
    return values[0]


def to_int(value, default_value):
    try:
        return int(value)
    except:
        return default_value


def format_rate(value):
    if value == None or value == "":
        return "0"
    text = f"{float(value):,.2f}"
    return text.rstrip("0").rstrip(".")


def format_signed_rate(value):
    if value == None or value == "":
        value = 0

    value = float(value)
    sign = "+"
    if value < 0:
        sign = "-"

    return f"{sign}{format_rate(abs(value))}%"


def make_options(rows, selected_value):
    html = ""
    for row in rows:
        value = str(row[0])
        label = str(row[1])
        selected = ""
        if value == str(selected_value):
            selected = ' selected="selected"'
        html += f'<option value="{value}"{selected}>{label}</option>'
    return html


def get_antigen_options():
    return pyhtml.get_results_from_query(
        DATABASE,
        """
        SELECT AntigenID, AntigenID || ' - ' || name
        FROM Antigen
        ORDER BY AntigenID;
        """,
    )


def get_year_options():
    return pyhtml.get_results_from_query(
        DATABASE,
        """
        SELECT DISTINCT year, year
        FROM Vaccination
        ORDER BY year DESC;
        """,
    )


def get_limit_options():
    return [
        (5, "Top 5"),
        (10, "Top 10"),
        (15, "Top 15"),
        (20, "Top 20"),
    ]


def get_selected_label(rows, selected_value, default_label):
    for row in rows:
        if str(row[0]) == str(selected_value):
            return str(row[1])
    return default_label


def get_default_values(form_data):
    antigen_options = get_antigen_options()
    year_options = get_year_options()
    limit_options = get_limit_options()

    default_antigen = antigen_options[0][0]
    default_end_year = year_options[0][0]
    default_start_year = year_options[min(4, len(year_options) - 1)][0]
    default_limit = 10

    antigen = get_first_value(form_data, "antigen", default_antigen)
    start_year = to_int(
        get_first_value(form_data, "start_year", default_start_year),
        default_start_year,
    )
    end_year = to_int(
        get_first_value(form_data, "end_year", default_end_year),
        default_end_year,
    )
    limit = to_int(get_first_value(form_data, "limit", default_limit), default_limit)
    mode = get_first_value(form_data, "mode", "gains")

    valid_antigens = [row[0] for row in antigen_options]
    valid_years = [row[0] for row in year_options]
    valid_limits = [row[0] for row in limit_options]

    if antigen not in valid_antigens:
        antigen = default_antigen

    if start_year not in valid_years:
        start_year = default_start_year

    if end_year not in valid_years:
        end_year = default_end_year

    if start_year > end_year:
        old_start_year = start_year
        start_year = end_year
        end_year = old_start_year

    if start_year == end_year:
        sorted_years = sorted(valid_years)
        year_index = sorted_years.index(end_year)
        if year_index > 0:
            start_year = sorted_years[year_index - 1]

    if limit not in valid_limits:
        limit = default_limit

    if mode not in ["gains", "declines"]:
        mode = "gains"

    return antigen, start_year, end_year, limit, mode


def build_improver_query(antigen, start_year, end_year, limit, mode):
    order_direction = "DESC"
    if mode == "declines":
        order_direction = "ASC"

    return f"""
    SELECT
      c.name AS country_name,
      r.region AS region_name,
      e.phase AS income_group,
      CAST(start_v.coverage AS REAL) AS start_rate,
      CAST(end_v.coverage AS REAL) AS end_rate,
      ROUND(CAST(end_v.coverage AS REAL) - CAST(start_v.coverage AS REAL), 2) AS rate_change
    FROM Vaccination start_v
    JOIN Vaccination end_v
      ON start_v.country = end_v.country
     AND start_v.antigen = end_v.antigen
    JOIN Country c ON start_v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    LEFT JOIN Economy e ON c.economy = e.economyID
    WHERE start_v.antigen = '{antigen}'
      AND start_v.year = {start_year}
      AND end_v.year = {end_year}
      AND start_v.coverage IS NOT NULL
      AND end_v.coverage IS NOT NULL
      AND start_v.coverage != ''
      AND end_v.coverage != ''
    ORDER BY rate_change {order_direction}, country_name ASC
    LIMIT {limit};
    """


def get_improver_rows(antigen, start_year, end_year, limit, mode):
    query = build_improver_query(antigen, start_year, end_year, limit, mode)
    return pyhtml.get_results_from_query(DATABASE, query)


def get_region_rows(antigen, start_year, end_year, mode):
    order_direction = "DESC"
    if mode == "declines":
        order_direction = "ASC"

    query = f"""
    SELECT
      r.region AS region_name,
      AVG(CAST(start_v.coverage AS REAL)) AS start_rate,
      AVG(CAST(end_v.coverage AS REAL)) AS end_rate,
      ROUND(AVG(CAST(end_v.coverage AS REAL) - CAST(start_v.coverage AS REAL)), 2) AS avg_change
    FROM Vaccination start_v
    JOIN Vaccination end_v
      ON start_v.country = end_v.country
     AND start_v.antigen = end_v.antigen
    JOIN Country c ON start_v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    WHERE start_v.antigen = '{antigen}'
      AND start_v.year = {start_year}
      AND end_v.year = {end_year}
      AND start_v.coverage IS NOT NULL
      AND end_v.coverage IS NOT NULL
      AND start_v.coverage != ''
      AND end_v.coverage != ''
    GROUP BY r.region
    ORDER BY avg_change {order_direction}, region_name ASC;
    """

    return pyhtml.get_results_from_query(DATABASE, query)


def get_most_common(rows, column_index):
    counts = {}
    for row in rows:
        value = row[column_index]
        if value == None or value == "":
            value = "Not available"
        if value not in counts:
            counts[value] = 0
        counts[value] += 1

    if len(counts) == 0:
        return "No data", "0 of 0 countries"

    best_value = None
    best_count = -1
    for value in counts:
        if counts[value] > best_count:
            best_value = value
            best_count = counts[value]

    return best_value, f"{best_count} of top {len(rows)} countries"


def get_average_change(rows):
    if len(rows) == 0:
        return 0

    total = 0
    for row in rows:
        total += float(row[5] or 0)
    return total / len(rows)


def bar_class(index):
    if index < 3:
        return ""
    if index < 5:
        return "mid"
    return "low"


def render_improver_bars(rows):
    if len(rows) == 0:
        return "<p>No vaccination change data available for this filter.</p>"

    max_change = 0
    for row in rows:
        change = abs(float(row[5] or 0))
        if change > max_change:
            max_change = change

    if max_change == 0:
        max_change = 1

    html = ""
    for index, row in enumerate(rows):
        country = row[0]
        change = float(row[5] or 0)
        width = max(2, int((abs(change) / max_change) * 100))

        html += f"""
          <div class="improver-row">
            <span>{country}</span>
            <div class="improver-track">
              <div class="improver-fill {bar_class(index)}" style="width: {width}%"></div>
            </div>
            <strong>{format_signed_rate(change)}</strong>
          </div>
        """

    return html


def render_region_bars(rows):
    if len(rows) == 0:
        return "<p>No regional coverage data available for this filter.</p>"

    max_change = 0
    for row in rows:
        change = abs(float(row[3] or 0))
        if change > max_change:
            max_change = change

    if max_change == 0:
        max_change = 1

    html = ""
    for index, row in enumerate(rows):
        region = row[0]
        start_rate = row[1] or 0
        end_rate = row[2] or 0
        change = float(row[3] or 0)
        width = max(2, int((abs(change) / max_change) * 100))

        html += f"""
          <div class="region-row">
            <span>{region}</span>
            <div class="region-track" title="{format_rate(start_rate)}% to {format_rate(end_rate)}%">
              <div class="region-fill {bar_class(index)}" style="width: {width}%"></div>
            </div>
            <strong>{format_signed_rate(change)}</strong>
          </div>
        """

    return html


def render_detail_table_rows(rows):
    if len(rows) == 0:
        return """
          <tr>
            <td colspan="8">No country-level vaccination changes found.</td>
          </tr>
        """

    html = ""
    for index, row in enumerate(rows, start=1):
        country = row[0]
        region = row[1]
        income = row[2] or "Not available"
        start_rate = row[3] or 0
        end_rate = row[4] or 0
        change = row[5] or 0
        trend_width = max(4, min(100, int(abs(float(change)) * 12)))

        html += f"""
          <tr>
            <td>{index}</td>
            <td>{country}</td>
            <td>{region}</td>
            <td>{income}</td>
            <td>{format_rate(start_rate)}%</td>
            <td>{format_rate(end_rate)}%</td>
            <td>{format_signed_rate(change)}</td>
            <td><span class="trend-bar" style="width: {trend_width}px"></span> {format_rate(abs(float(change)))}</td>
          </tr>
        """

    return html


def replace_placeholders(page_html, replacements):
    for placeholder in replacements:
        page_html = page_html.replace(placeholder, replacements[placeholder])
    return page_html


def get_page_html(form_data):
    print("About to return Webpage 5 - Top Improvers...")

    antigen, start_year, end_year, limit, mode = get_default_values(form_data)
    rows = get_improver_rows(antigen, start_year, end_year, limit, mode)
    region_rows = get_region_rows(antigen, start_year, end_year, mode)

    antigen_options = get_antigen_options()
    year_options = get_year_options()
    limit_options = get_limit_options()

    antigen_label = get_selected_label(antigen_options, antigen, antigen)
    result_subtitle = f"{antigen} antigen - {start_year} to {end_year}"

    if len(rows) == 0:
        best_improvement = "0%"
        best_country = "No data"
    else:
        best_improvement = format_signed_rate(rows[0][5])
        best_country = rows[0][0]

    avg_change = get_average_change(rows)
    most_region, most_region_sub = get_most_common(rows, 1)
    most_income, most_income_sub = get_most_common(rows, 2)

    sort_label = "Sorted by rate increase"
    result_word = "improvers"
    if mode == "declines":
        sort_label = "Sorted by rate decrease"
        result_word = "declines"

    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    replacements = {
        "{{ANTIGEN_OPTIONS}}": make_options(antigen_options, antigen),
        "{{START_YEAR_OPTIONS}}": make_options(year_options, start_year),
        "{{END_YEAR_OPTIONS}}": make_options(year_options, end_year),
        "{{TOP_COUNTRY_OPTIONS}}": make_options(limit_options, limit),
        "{{GAINS_CHECKED}}": 'checked="checked"' if mode == "gains" else "",
        "{{DECLINES_CHECKED}}": 'checked="checked"' if mode == "declines" else "",
        "{{BEST_IMPROVEMENT}}": best_improvement,
        "{{BEST_COUNTRY}}": best_country,
        "{{AVG_IMPROVEMENT}}": format_signed_rate(avg_change),
        "{{AVG_LABEL}}": f"Avg change in top {len(rows)}",
        "{{MOST_REGION}}": most_region,
        "{{MOST_REGION_SUB}}": most_region_sub,
        "{{MOST_INCOME}}": most_income,
        "{{MOST_INCOME_SUB}}": most_income_sub,
        "{{RESULT_TITLE}}": f"Top {limit} {result_word} - vaccination rate change",
        "{{RESULT_SUBTITLE}}": result_subtitle,
        "{{SORT_LABEL}}": sort_label,
        "{{REGION_BARS}}": render_region_bars(region_rows),
        "{{IMPROVER_BARS}}": render_improver_bars(rows),
        "{{DETAIL_TABLE_ROWS}}": render_detail_table_rows(rows),
    }

    return replace_placeholders(page_html, replacements)


if __name__ == "__main__":
    pyhtml.MyRequestHandler.pages["/"] = sys.modules[__name__]
    pyhtml.MyRequestHandler.pages["/Webpage5"] = sys.modules[__name__]
    pyhtml.MyRequestHandler.pages["/Webpage5.html"] = sys.modules[__name__]
    pyhtml.host_site()
