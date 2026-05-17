import sys

import pyhtml

DATABASE = "immunisation.db"
TEMPLATE = "Webpage3.html"
TARGET = 90


def get_first_value(form_data, key, default_value):
    values = form_data.get(key)
    if values is None or len(values) == 0 or values[0] == "":
        return default_value
    return values[0]


def to_int(value, default_value):
    try:
        return int(value)
    except:
        return default_value


def format_rate(value):
    if value is None:
        return "0"
    return f"{float(value):.1f}"


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
        """
    )


def get_year_options():
    return pyhtml.get_results_from_query(
        DATABASE,
        """
        SELECT DISTINCT year, year
        FROM Vaccination
        ORDER BY year DESC;
        """
    )


def get_region_options():
    rows = pyhtml.get_results_from_query(
        DATABASE,
        """
        SELECT RegionID, region
        FROM Region
        ORDER BY region;
        """
    )

    return [("ALL", "All Regions")] + rows


def get_country_options():
    rows = pyhtml.get_results_from_query(
        DATABASE,
        """
        SELECT CountryID, name
        FROM Country
        ORDER BY name;
        """
    )

    return [("ALL", "All Countries")] + rows


def get_default_values(form_data):
    antigen_options = get_antigen_options()
    year_options = get_year_options()

    default_antigen = antigen_options[0][0]
    default_year = year_options[0][0]

    antigen = get_first_value(form_data, "antigen", default_antigen)
    year = to_int(get_first_value(form_data, "year", default_year), default_year)
    region = get_first_value(form_data, "region", "ALL")
    country = get_first_value(form_data, "country", "ALL")

    valid_antigens = [row[0] for row in antigen_options]
    valid_years = [row[0] for row in year_options]
    valid_regions = [row[0] for row in get_region_options()]
    valid_countries = [row[0] for row in get_country_options()]

    if antigen not in valid_antigens:
        antigen = default_antigen

    if year not in valid_years:
        year = default_year

    if region not in valid_regions:
        region = "ALL"

    if country not in valid_countries:
        country = "ALL"

    return antigen, year, region, country


def build_filter_condition(antigen, year, region, country):
    condition = f"""
        v.antigen = '{antigen}'
        AND v.year = {year}
        AND v.coverage IS NOT NULL
    """

    if region != "ALL":
        condition += f" AND c.region = '{region}'"

    if country != "ALL":
        condition += f" AND c.CountryID = '{country}'"

    return condition


def get_summary(antigen, year, region, country):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      COUNT(DISTINCT CASE WHEN v.coverage >= {TARGET} THEN v.country END),
      COUNT(DISTINCT CASE WHEN v.coverage < {TARGET} THEN v.country END),
      AVG(v.coverage)
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    WHERE {condition};
    """

    row = pyhtml.get_results_from_query(DATABASE, query)[0]

    countries_met = row[0] or 0
    countries_below = row[1] or 0
    avg_coverage = row[2] or 0

    return countries_met, countries_below, avg_coverage


def bar_status_class(value):
    if value >= 80:
        return ""
    if value >= 65:
        return "warning"
    return "danger"


def mini_bar_class(value):
    if value >= 90:
        return "good"
    if value >= 60:
        return "mid"
    return "low"


def render_region_bars(antigen, year, region, country):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      r.RegionID,
      AVG(v.coverage) AS avg_coverage
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    WHERE {condition}
    GROUP BY r.RegionID
    ORDER BY avg_coverage DESC;
    """

    rows = pyhtml.get_results_from_query(DATABASE, query)

    if len(rows) == 0:
        return "<p>No regional data available.</p>"

    html = ""

    for row in rows:
        region_id = row[0]
        avg_coverage = row[1] or 0
        width = min(100, max(0, avg_coverage))

        html += f"""
        <div class="bar-row {bar_status_class(avg_coverage)}">
          <span>{region_id}</span>
          <div class="bar">
            <i style="width:{width:.0f}%"></i>
          </div>
          <strong>{avg_coverage:.0f}%</strong>
        </div>
        """

    return html


def get_country_count(antigen, year, region, country):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT COUNT(DISTINCT v.country)
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    WHERE {condition}
      AND v.coverage >= {TARGET};
    """

    return pyhtml.get_results_from_query(DATABASE, query)[0][0]


def render_country_table_rows(antigen, year, region, country):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      c.name,
      r.RegionID,
      e.phase,
      v.antigen,
      v.year,
      v.coverage
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    LEFT JOIN Economy e ON c.economy = e.economyID
    WHERE {condition}
      AND v.coverage >= {TARGET}
    ORDER BY v.coverage DESC, c.name ASC
    LIMIT 15;
    """

    rows = pyhtml.get_results_from_query(DATABASE, query)

    if len(rows) == 0:
        return """
        <tr>
          <td colspan="7">No countries met the selected vaccination target.</td>
        </tr>
        """

    html = ""

    for row in rows:
        country_name = row[0]
        region_id = row[1]
        economy = row[2] or "Not available"
        antigen_id = row[3]
        selected_year = row[4]
        coverage = row[5] or 0

        html += f"""
        <tr>
          <td>{country_name}</td>
          <td>{region_id}</td>
          <td>{economy}</td>
          <td>{antigen_id}</td>
          <td>{selected_year}</td>
          <td><span class="mini-bar {mini_bar_class(coverage)}"></span>{format_rate(coverage)}%</td>
          <td>MET</td>
        </tr>
        """

    return html


def get_region_count(antigen, year, region, country):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT COUNT(DISTINCT c.region)
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    WHERE {condition};
    """

    return pyhtml.get_results_from_query(DATABASE, query)[0][0]


def render_region_table_rows(antigen, year, region, country):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      v.antigen,
      v.year,
      r.RegionID,
      COUNT(DISTINCT CASE WHEN v.coverage >= {TARGET} THEN v.country END) AS countries_met,
      COUNT(DISTINCT v.country) AS total_countries,
      AVG(v.coverage) AS avg_coverage
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    WHERE {condition}
    GROUP BY v.antigen, v.year, r.RegionID
    ORDER BY countries_met DESC, r.RegionID ASC;
    """

    rows = pyhtml.get_results_from_query(DATABASE, query)

    if len(rows) == 0:
        return """
        <tr>
          <td colspan="8">No regional data available for this filter.</td>
        </tr>
        """

    html = ""

    for row in rows:
        antigen_id = row[0]
        selected_year = row[1]
        region_id = row[2]
        countries_met = row[3] or 0
        total_countries = row[4] or 0
        avg_coverage = row[5] or 0

        if total_countries > 0:
            percent_region = (countries_met / total_countries) * 100
        else:
            percent_region = 0

        html += f"""
        <tr>
          <td>{antigen_id}</td>
          <td>{selected_year}</td>
          <td>{region_id}</td>
          <td>{countries_met}</td>
          <td>{total_countries}</td>
          <td><span class="mini-bar {mini_bar_class(percent_region)}"></span>{format_rate(percent_region)}%</td>
          <td>{format_rate(avg_coverage)}%</td>
          <td><span class="mini-bar {mini_bar_class(percent_region)}"></span>{format_rate(percent_region)}%</td>
        </tr>
        """

    return html


def replace_placeholders(page_html, replacements):
    for placeholder in replacements:
        page_html = page_html.replace(placeholder, replacements[placeholder])

    return page_html


def get_page_html(form_data):
    antigen, year, region, country = get_default_values(form_data)

    countries_met, countries_below, avg_coverage = get_summary(
        antigen,
        year,
        region,
        country
    )

    country_count = get_country_count(antigen, year, region, country)
    region_count = get_region_count(antigen, year, region, country)

    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    replacements = {
        "{{ANTIGEN_OPTIONS}}": make_options(get_antigen_options(), antigen),
        "{{YEAR_OPTIONS}}": make_options(get_year_options(), year),
        "{{REGION_OPTIONS}}": make_options(get_region_options(), region),
        "{{COUNTRY_OPTIONS}}": make_options(get_country_options(), country),

        "{{COUNTRIES_MET}}": str(countries_met),
        "{{COUNTRIES_BELOW}}": str(countries_below),
        "{{GLOBAL_AVG_COVERAGE}}": f"{format_rate(avg_coverage)}%",
        "{{SELECTED_YEAR}}": str(year),

        "{{REGION_BARS}}": render_region_bars(antigen, year, region, country),

        "{{COUNTRY_TABLE_ROWS}}": render_country_table_rows(antigen, year, region, country),
        "{{REGION_TABLE_ROWS}}": render_region_table_rows(antigen, year, region, country),

        "{{COUNTRY_TABLE_SUBTITLE}}": f"Showing countries meeting {TARGET}% target - {antigen} antigen - {year}",
        "{{COUNTRY_COUNT_LABEL}}": f"{country_count} countries",

        "{{REGION_TABLE_SUBTITLE}}": f"{antigen} antigen - {year}",
        "{{REGIONAL_TABLE_SUBTITLE}}": f"{antigen} antigen - {year}",
        "{{REGION_COUNT_LABEL}}": f"{region_count} Regions",
    }

    return replace_placeholders(page_html, replacements)


if __name__ == "__main__":
    pyhtml.MyRequestHandler.pages["/"] = sys.modules[__name__]
    pyhtml.MyRequestHandler.pages["/Webpage3"] = sys.modules[__name__]
    pyhtml.MyRequestHandler.pages["/Webpage3.html"] = sys.modules[__name__]
    pyhtml.host_site()
