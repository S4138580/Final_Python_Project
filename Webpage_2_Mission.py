import pyhtml


DATABASE = "Database/persona_team.db"
TEMPLATE = "Webpage_2_Mission.html"


def persona_icon(label):
    icons = {
        "PERSONA 1": "P1",
        "PERSONA 2": "P2",
        "PERSONA 3": "H1",
        "PERSONA 4": "H2",
    }
    return icons.get(label, "U")


def render_persona_card(persona):
    name = persona[0]
    role = persona[1]
    age = persona[2]
    location = persona[3]
    description = persona[4]
    persona_label = persona[5]
    border_color = persona[6]

    return f"""
    <article class="persona-card border-{border_color}">
      <div class="persona-avatar" aria-hidden="true">{persona_icon(persona_label)}</div>
      <div class="persona-info">
        <h3>{name}</h3>
        <p class="persona-meta">
          {role} · Age {age} · {location}
        </p>
        <p class="persona-copy">{description}</p>
        <span class="persona-tag tag-{border_color}">{persona_label}</span>
      </div>
    </article>
    """


def render_team_rows(team_members):
    page_html = ""

    for member in team_members:
        name = member[0]
        student_id = member[1]
        sub_task = member[2]
        pages = member[3]

        page_html += f"""
            <tr>
              <td>{name}</td>
              <td>{student_id}</td>
              <td><span>{sub_task}</span></td>
              <td>{pages}</td>
            </tr>
            """

    return page_html


def get_page_html(form_data):
    print("About to return mission page...")

    with open(TEMPLATE, "r", encoding="utf-8") as file:
        page_html = file.read()

    persona_query = """
    SELECT name, role, age, location, description, persona_label, border_color
    FROM personas
    ORDER BY id;
    """
    team_query = """
    SELECT name, student_id, sub_task, pages
    FROM team_members
    ORDER BY id;
    """

    personas = pyhtml.get_results_from_query(DATABASE, persona_query)
    team_members = pyhtml.get_results_from_query(DATABASE, team_query)

    group1 = ""
    group2 = ""

    for persona in personas[:2]:
        group1 += render_persona_card(persona)

    for persona in personas[2:]:
        group2 += render_persona_card(persona)

    page_html = page_html.replace("{{GROUP1}}", group1)
    page_html = page_html.replace("{{GROUP2}}", group2)
    page_html = page_html.replace("{{TEAM_MEMBERS}}", render_team_rows(team_members))

    return page_html
