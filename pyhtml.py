import sqlite3
import http.server
import socketserver
from urllib.parse import parse_qs, urlparse


need_debugging_help = True


class MyRequestHandler(http.server.SimpleHTTPRequestHandler):
    pages = {}

    def do_GET(self):
        parsed_url = urlparse(self.path)
        path = parsed_url.path

        debugging_helper(f"A web browser wants to GET: {path}")

        if path in MyRequestHandler.pages:
            form_data = parse_qs(parsed_url.query)
            debugging_helper(f"Received GET data: {form_data}")

            page_module = MyRequestHandler.pages[path]
            response = page_module.get_page_html(form_data)

            self.send_response(200)

            if isinstance(response, dict):
                content = response.get("content", "")
                content_type = response.get(
                    "content_type",
                    "text/plain; charset=utf-8"
                )
                filename = response.get("filename")

                self.send_header("Content-type", content_type)

                if filename is not None:
                    self.send_header(
                        "Content-Disposition",
                        f'attachment; filename="{filename}"'
                    )

                self.end_headers()
                self.wfile.write(content.encode("utf-8"))

            else:
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(response.encode("utf-8"))

        else:
            super().do_GET()


def host_site():
    port = 8000

    with socketserver.TCPServer(("", port), MyRequestHandler) as httpd:
        print("Server running.")
        print("Open this link in your browser:")
        print(f"http://localhost:{port}/")
        httpd.serve_forever()


def get_results_from_query(database, query):
    debugging_helper("\n------------------------")
    debugging_helper(f'Opening database "{database}"...')

    connection = sqlite3.connect(database)
    cursor = connection.cursor()

    debugging_helper("Executing query:")
    debugging_helper(query)

    cursor.execute(query)
    results = cursor.fetchall()

    debugging_helper("Query results:")
    debugging_helper(results)
    debugging_helper("------------------------\n")

    connection.close()
    return results


def debugging_helper(message):
    if need_debugging_help:
        print(message)