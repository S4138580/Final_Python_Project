import sys
import Python.pyhtml as pyhtml
import io
import csv
from urllib.parse import urlencode
from html import escape

DATABASE = "immunisation.db"
TEMPLATE = "Webpage3.html"
TARGET = 90
COUNTRY_ROWS_PER_PAGE = 15


def get_first_value(form_data, key, default_value):
    values = form_data.get(key)
    if values is None or len(values) == 0 or values[0] == "":
        return default_value
    return values[0].strip()


def get_raw_value(form_data, key):
    values = form_data.get(key)
    if values is None or len(values) == 0:
        return ""
    return values[0].strip()


def to_int(value, default_value):
    try:
        return int(value)
    except:
        return default_value


def format_rate(value):
    if value is None:
        return "0.0"
    return f"{float(value):.1f}"


def sql_escape(value):
    return value.replace("'", "''")


def render_error_box(errors):
    if len(errors) == 0:
        return ""

    html = ""
    for error in errors:
        html += f"<div>{escape(error)}</div>"

    return f'<div class="error-box">{html}</div>'


def make_options(rows, selected_value, placeholder):
    html = f'<option value="">{placeholder}</option>'

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


def get_region_for_country(country):
    rows = pyhtml.get_results_from_query(
        DATABASE,
        f"""
        SELECT region
        FROM Country
        WHERE CountryID = '{sql_escape(country)}';
        """
    )

    if len(rows) == 0:
        return "ALL"
    return rows[0][0]


def get_default_values(form_data):
    antigen_options = get_antigen_options()
    year_options = get_year_options()

    default_antigen = antigen_options[0][0]
    default_year = year_options[0][0]

    antigen = get_first_value(form_data, "antigen", default_antigen)
    year = to_int(get_first_value(form_data, "year", default_year), default_year)
    region = get_first_value(form_data, "region", "ALL")
    country = get_first_value(form_data, "country", "ALL")
    target = to_int(get_first_value(form_data, "target", TARGET), TARGET)
    country_search = get_first_value(form_data, "country_search", "")
    country_page = to_int(get_first_value(form_data, "country_page", "1"), 1)

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
    if country != "ALL":
        region = get_region_for_country(country)
    if target < 0:
        target = TARGET
    if target > 100:
        target = 100
    if country_page < 1:
        country_page = 1

    return antigen, year, region, country, target, country_search, country_page


def build_filter_condition(antigen, year, region, country):
    condition = f"""
        v.antigen = '{sql_escape(antigen)}'
        AND v.year = {year}
        AND v.coverage IS NOT NULL
        AND typeof(v.coverage) IN ('integer', 'real')
    """

    if region != "ALL":
        condition += f" AND c.region = '{sql_escape(region)}'"
    if country != "ALL":
        condition += f" AND c.CountryID = '{sql_escape(country)}'"

    return condition


def add_country_search_condition(condition, country_search):
    if country_search != "":
        condition += f" AND c.name LIKE '%{sql_escape(country_search)}%'"
    return condition


def build_action_query(antigen, year, region, country, target, country_search):
    return urlencode({
        "antigen": antigen,
        "year": year,
        "region": region,
        "country": country,
        "target": target,
        "country_search": country_search,
    })


def make_csv_response(filename, headers, rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)

    return {
        "content": output.getvalue(),
        "content_type": "text/csv; charset=utf-8",
        "filename": filename,
    }


def get_summary(antigen, year, region, country, target):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      COUNT(DISTINCT CASE WHEN v.coverage >= {target} THEN v.country END),
      COUNT(DISTINCT CASE WHEN v.coverage < {target} THEN v.country END),
      AVG(v.coverage)
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    WHERE {condition};
    """

    row = pyhtml.get_results_from_query(DATABASE, query)[0]
    return row[0] or 0, row[1] or 0, row[2] or 0


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
          <div class="bar"><i style="width:{width:.0f}%"></i></div>
          <strong>{avg_coverage:.0f}%</strong>
        </div>
        """

    return html


def get_country_count(antigen, year, region, country, target, country_search):
    condition = build_filter_condition(antigen, year, region, country)
    condition = add_country_search_condition(condition, country_search)

    query = f"""
    SELECT COUNT(DISTINCT v.country)
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    WHERE {condition}
      AND v.coverage >= {target};
    """

    return pyhtml.get_results_from_query(DATABASE, query)[0][0] or 0


def render_country_table_rows(
    antigen,
    year,
    region,
    country,
    target,
    country_search,
    country_page
):
    condition = build_filter_condition(antigen, year, region, country)
    condition = add_country_search_condition(condition, country_search)
    offset = (country_page - 1) * COUNTRY_ROWS_PER_PAGE

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
      AND v.coverage >= {target}
    ORDER BY v.coverage DESC, c.name ASC
    LIMIT {COUNTRY_ROWS_PER_PAGE}
    OFFSET {offset};
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
        coverage = row[5] or 0
        html += f"""
        <tr>
          <td>{row[0]}</td>
          <td>{row[1]}</td>
          <td>{row[2] or "Not available"}</td>
          <td>{row[3]}</td>
          <td>{row[4]}</td>
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

    return pyhtml.get_results_from_query(DATABASE, query)[0][0] or 0


def get_csv_country_rows(antigen, year, region, country, target, country_search):
    condition = build_filter_condition(antigen, year, region, country)
    condition = add_country_search_condition(condition, country_search)

    query = f"""
    SELECT
      c.name,
      r.RegionID,
      COALESCE(e.phase, 'Not available'),
      v.antigen,
      v.year,
      v.coverage,
      'MET'
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    LEFT JOIN Economy e ON c.economy = e.economyID
    WHERE {condition}
      AND v.coverage >= {target}
    ORDER BY v.coverage DESC, c.name ASC;
    """

    return pyhtml.get_results_from_query(DATABASE, query)


def get_csv_region_rows(antigen, year, region, country, target):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      v.antigen,
      v.year,
      r.RegionID,
      COUNT(DISTINCT CASE WHEN v.coverage >= {target} THEN v.country END) AS countries_met,
      COUNT(DISTINCT v.country) AS total_countries,
      ROUND(AVG(v.coverage), 1) AS avg_coverage
    FROM Vaccination v
    JOIN Country c ON v.country = c.CountryID
    JOIN Region r ON c.region = r.RegionID
    WHERE {condition}
    GROUP BY v.antigen, v.year, r.RegionID
    ORDER BY countries_met DESC, r.RegionID ASC;
    """

    return pyhtml.get_results_from_query(DATABASE, query)


def render_region_table_rows(antigen, year, region, country, target):
    condition = build_filter_condition(antigen, year, region, country)

    query = f"""
    SELECT
      v.antigen,
      v.year,
      r.RegionID,
      COUNT(DISTINCT CASE WHEN v.coverage >= {target} THEN v.country END) AS countries_met,
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
          <td colspan="7">No regional data available for this filter.</td>
        </tr>
        """

    html = ""
    for row in rows:
        countries_met = row[3] or 0
        total_countries = row[4] or 0
        avg_coverage = row[5] or 0
        herd_immunity_rate = 0
        if total_countries > 0:
            herd_immunity_rate = (countries_met / total_countries) * 100

        html += f"""
        <tr>
          <td>{row[0]}</td>
          <td>{row[1]}</td>
          <td>{row[2]}</td>
          <td>{countries_met}</td>
          <td>{total_countries}</td>
          <td>{format_rate(avg_coverage)}%</td>
          <td><span class="mini-bar {mini_bar_class(herd_immunity_rate)}"></span>{format_rate(herd_immunity_rate)}%</td>
        </tr>
        """

    return html

def render_country_pager(
    antigen,
    year,
    region,
    country,
    target,
    country_search,
    current_page,
    country_count
):
    total_pages = max(1, (country_count + COUNTRY_ROWS_PER_PAGE - 1) // COUNTRY_ROWS_PER_PAGE)

    def make_page_link(page_number, label, disabled=False):
        query = urlencode({
            "antigen": antigen,
            "year": year,
            "region": region,
            "country": country,
            "target": target,
            "country_search": country_search,
            "country_page": page_number
        })

        disabled_class = " disabled" if disabled else ""
        return f'<a class="{disabled_class}" href="/Webpage3.html?{query}#country-table">{label}</a>'

    prev_page = max(1, current_page - 1)
    next_page = min(total_pages, current_page + 1)

    return (
        make_page_link(prev_page, "Prev", disabled=(current_page <= 1))
        + f'<span class="page-number">{current_page}</span>'
        + make_page_link(next_page, "Next", disabled=(current_page >= total_pages))
    )

def replace_placeholders(page_html, replacements):
    for placeholder in replacements:
        page_html = page_html.replace(placeholder, str(replacements[placeholder]))
    return page_html


def render_empty_page(page_html):
    replacements = {
        "{{ERROR_BOX}}": "",
        "{{PRINT_CLASS}}": "",
        "{{ANTIGEN_OPTIONS}}": make_options(get_antigen_options(), "", "Select vaccine"),
        "{{YEAR_OPTIONS}}": make_options(get_year_options(), "", "Select year"),
        "{{REGION_OPTIONS}}": make_options(get_region_options(), "", "Select region"),
        "{{COUNTRY_OPTIONS}}": make_options(get_country_options(), "", "Select country"),
        "{{TARGET_VALUE}}": "",
        "{{COUNTRY_SEARCH_VALUE}}": "",
        "{{COUNTRIES_MET}}": "-",
        "{{COUNTRIES_BELOW}}": "-",
        "{{GLOBAL_AVG_COVERAGE}}": "-",
        "{{SELECTED_YEAR}}": "-",
        "{{REGION_BARS}}": "<p>Please complete the required filters.</p>",
        "{{COUNTRY_TABLE_ROWS}}": '<tr><td colspan="7">Please complete the required filters.</td></tr>',
        "{{REGION_TABLE_ROWS}}": '<tr><td colspan="7">Please complete the required filters.</td></tr>',
        "{{COUNTRY_TABLE_SUBTITLE}}": "No filters applied",
        "{{COUNTRY_COUNT_LABEL}}": "0 countries",
        "{{COUNTRY_TABLE_NOTE}}": "",
        "{{COUNTRY_TABLE_PAGE_LABEL}}": "Showing 0 of 0",
        "{{COUNTRY_PAGER}}": "<span>0</span>",
        "{{ACTION_QUERY}}": "",
        "{{REGIONAL_TABLE_SUBTITLE}}": "No filters applied",
        "{{REGION_COUNT_LABEL}}": "0 Regions",
        "{{REGION_TABLE_PAGE_LABEL}}": "Showing 0 regions",
    }

    return replace_placeholders(page_html, replacements)


def render_incomplete_page(page_html, antigen, year, region, country, target_value, country_search, errors):
    replacements = {
        "{{ERROR_BOX}}": render_error_box(errors),
        "{{PRINT_CLASS}}": "",
        "{{ANTIGEN_OPTIONS}}": make_options(get_antigen_options(), antigen, "Select vaccine"),
        "{{YEAR_OPTIONS}}": make_options(get_year_options(), year, "Select year"),
        "{{REGION_OPTIONS}}": make_options(get_region_options(), region, "Select region"),
        "{{COUNTRY_OPTIONS}}": make_options(get_country_options(), country, "Select country"),
        "{{TARGET_VALUE}}": escape(target_value),
        "{{COUNTRY_SEARCH_VALUE}}": escape(country_search),
        "{{COUNTRIES_MET}}": "-",
        "{{COUNTRIES_BELOW}}": "-",
        "{{GLOBAL_AVG_COVERAGE}}": "-",
        "{{SELECTED_YEAR}}": "-",
        "{{REGION_BARS}}": "<p>Please complete the required filters.</p>",
        "{{COUNTRY_TABLE_ROWS}}": '<tr><td colspan="7">Please complete the required filters.</td></tr>',
        "{{REGION_TABLE_ROWS}}": '<tr><td colspan="7">Please complete the required filters.</td></tr>',
        "{{COUNTRY_TABLE_SUBTITLE}}": "No filters applied",
        "{{COUNTRY_COUNT_LABEL}}": "0 countries",
        "{{COUNTRY_TABLE_NOTE}}": "",
        "{{COUNTRY_TABLE_PAGE_LABEL}}": "Showing 0 of 0",
        "{{COUNTRY_PAGER}}": "<span>0</span>",
        "{{ACTION_QUERY}}": "",
        "{{REGIONAL_TABLE_SUBTITLE}}": "No filters applied",
        "{{REGION_COUNT_LABEL}}": "0 Regions",
        "{{REGION_TABLE_PAGE_LABEL}}": "Showing 0 regions",
    }

    return replace_placeholders(page_html, replacements)


def get_page_html(form_data):
    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    if len(form_data) == 0:
        return render_empty_page(page_html)

    antigen = get_raw_value(form_data, "antigen")
    year_value = get_raw_value(form_data, "year")
    region = get_raw_value(form_data, "region")
    country = get_raw_value(form_data, "country")
    target_value = get_raw_value(form_data, "target")
    country_search = get_raw_value(form_data, "country_search")
    country_page = to_int(get_raw_value(form_data, "country_page"), 1)
    export = get_raw_value(form_data, "export")
    print_class = "print-mode" if get_raw_value(form_data, "print") == "1" else ""

    errors = []
    antigen_options = get_antigen_options()
    year_options = get_year_options()
    valid_antigens = [row[0] for row in antigen_options]
    valid_years = [str(row[0]) for row in year_options]
    valid_regions = [row[0] for row in get_region_options()]
    valid_countries = [row[0] for row in get_country_options()]

    if antigen == "":
        errors.append("Please select a vaccine.")
    elif antigen not in valid_antigens:
        errors.append("Please select a valid vaccine.")

    if year_value == "":
        errors.append("Please select a year.")
    elif year_value not in valid_years:
        errors.append("Please select a valid year.")

    if region == "":
        errors.append("Please select a region.")
    elif region not in valid_regions:
        errors.append("Please select a valid region.")

    if country == "":
        errors.append("Please select a country.")
    elif country not in valid_countries:
        errors.append("Please select a valid country.")

    if target_value == "":
        errors.append("Please enter a target percentage.")

    target = to_int(target_value, -1)
    if target_value != "" and target < 0:
        errors.append("Target must be 0 or higher.")
    if target > 100:
        errors.append("Target cannot be greater than 100.")

    if len(errors) > 0:
        return render_incomplete_page(
            page_html,
            antigen,
            year_value,
            region,
            country,
            target_value,
            country_search,
            errors
        )

    year = to_int(year_value, 0)
    if country != "ALL":
        region = get_region_for_country(country)

    if country_page < 1:
        country_page = 1

    if export == "country_csv":
        return make_csv_response(
            "vaccination_country_coverage.csv",
            ["Country", "Region", "Income Group", "Antigen", "Year", "Coverage", "Target"],
            get_csv_country_rows(antigen, year, region, country, target, country_search)
        )
    
    if export == "region_csv":
        return make_csv_response(
            "vaccination_region_summary.csv",
            ["Antigen", "Year", "Region", "Countries Met", "Total Countries", "Avg Coverage"],
            get_csv_region_rows(antigen, year, region, country, target)
        )    
    countries_met, countries_below, avg_coverage = get_summary(antigen, year, region, country, target)
    country_count = get_country_count(antigen, year, region, country, target, country_search)
    region_count = get_region_count(antigen, year, region, country)

    total_country_pages = max(1, (country_count + COUNTRY_ROWS_PER_PAGE - 1) // COUNTRY_ROWS_PER_PAGE)
    if country_page > total_country_pages:
        country_page = total_country_pages

    first_country = 0
    last_country = 0
    if country_count > 0:
        first_country = ((country_page - 1) * COUNTRY_ROWS_PER_PAGE) + 1
        last_country = min(country_page * COUNTRY_ROWS_PER_PAGE, country_count)

    replacements = {
        "{{ERROR_BOX}}": "",
        "{{PRINT_CLASS}}": print_class,
        "{{ANTIGEN_OPTIONS}}": make_options(antigen_options, antigen, "Select vaccine"),
        "{{YEAR_OPTIONS}}": make_options(year_options, year, "Select year"),
        "{{REGION_OPTIONS}}": make_options(get_region_options(), region, "Select region"),
        "{{COUNTRY_OPTIONS}}": make_options(get_country_options(), country, "Select country"),
        "{{TARGET_VALUE}}": str(target),
        "{{COUNTRY_SEARCH_VALUE}}": country_search,
        "{{COUNTRIES_MET}}": str(countries_met),
        "{{COUNTRIES_BELOW}}": str(countries_below),
        "{{GLOBAL_AVG_COVERAGE}}": f"{format_rate(avg_coverage)}%",
        "{{SELECTED_YEAR}}": str(year),
        "{{REGION_BARS}}": render_region_bars(antigen, year, region, country),
        "{{COUNTRY_TABLE_ROWS}}": render_country_table_rows(
            antigen,
            year,
            region,
            country,
            target,
            country_search,
            country_page
        ),
        "{{REGION_TABLE_ROWS}}": render_region_table_rows(antigen, year, region, country, target),
        "{{COUNTRY_TABLE_SUBTITLE}}": f"Showing countries meeting {target}% target - {antigen} antigen - {year}",
        "{{COUNTRY_COUNT_LABEL}}": f"{country_count} countries",
        "{{COUNTRY_TABLE_NOTE}}": "",
        "{{COUNTRY_TABLE_PAGE_LABEL}}": f"Showing {first_country}-{last_country} of {country_count}",
        "{{COUNTRY_PAGER}}": render_country_pager(
            antigen,
            year,
            region,
            country,
            target,
            country_search,
            country_page,
            country_count
        ),
        "{{ACTION_QUERY}}": build_action_query(
            antigen,
            year,
            region,
            country,
            target,
            country_search
        ),

        "{{REGIONAL_TABLE_SUBTITLE}}": f"{antigen} antigen - {year}",
        "{{REGION_COUNT_LABEL}}": f"{region_count} Regions",
        "{{REGION_TABLE_PAGE_LABEL}}": f"Showing {region_count} regions",
    }

    return replace_placeholders(page_html, replacements)


if __name__ == "__main__":
    pyhtml.MyRequestHandler.pages["/"] = sys.modules[__name__]
    pyhtml.MyRequestHandler.pages["/Webpage3"] = sys.modules[__name__]
    pyhtml.MyRequestHandler.pages["/Webpage3.html"] = sys.modules[__name__]
    pyhtml.host_site()
