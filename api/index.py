import json
import os
import re
from datetime import datetime
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen


GITHUB_API = "https://api.github.com/repos/ethereum/pm/issues"


def gh_request(url):
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    with urlopen(Request(url, headers=headers)) as r:
        return json.loads(r.read())


def section(body, heading):
    m = re.search(rf"###\s+{re.escape(heading)}\s*\n(.*?)(?=\n###|\Z)", body, re.DOTALL)
    return m.group(1).strip() if m else ""


def parse_date(raw):
    raw = re.sub(r"\s+", " ", raw.strip().split("\n")[0].strip())
    for fmt in ("%b %d, %Y, %H:%M UTC", "%B %d, %Y, %H:%M UTC"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            pass
    return None


def clean_title(title):
    return re.sub(r",?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}$", "", title)


def upcoming_calls():
    issues = gh_request(f"{GITHUB_API}?labels=ACD&state=open&per_page=10&sort=created&direction=desc")
    calls = []
    for issue in issues:
        body = issue.get("body") or ""
        dt = parse_date(section(body, "UTC Date & Time"))
        if not dt:
            continue
        calls.append({
            "title": clean_title(issue["title"]),
            "date": dt.strftime("%b %d, %Y at %H:%M UTC"),
            "url": issue.get("html_url", ""),
        })
    calls.sort(key=lambda c: c["date"])
    return calls


def render(calls):
    rows = ""
    for c in calls:
        rows += f'<tr><td>{c["title"]}</td><td>{c["date"]}</td><td><a href="{c["url"]}">agenda</a></td></tr>'

    if not rows:
        rows = '<tr><td colspan="3">No upcoming calls</td></tr>'

    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethereum ACD Calendar</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }}
h1 {{ font-size: 1.4em; }}
p {{ color: #555; line-height: 1.5; }}
table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
th, td {{ text-align: left; padding: 8px; border-bottom: 1px solid #eee; }}
th {{ color: #888; font-weight: normal; font-size: 0.85em; text-transform: uppercase; }}
code {{ background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }}
a {{ color: #2563eb; }}
.feeds {{ margin: 20px 0; }}
.feeds code {{ display: block; margin: 6px 0; }}
</style>
</head>
<body>
<h1>Ethereum All Core Devs Calendar</h1>
<p>Live ICS feed for Ethereum's All Core Dev calls. Subscribe in any calendar app.</p>

<div class="feeds">
<strong>Subscribe:</strong>
<code>https://acd-ics.vercel.app/feed.ics</code>
<code>https://acd-ics.vercel.app/feed.ics?series=acde</code>
<code>https://acd-ics.vercel.app/feed.ics?series=acdc</code>
<code>https://acd-ics.vercel.app/feed.ics?series=acdt</code>
</div>

<h2 style="font-size:1.1em;">Upcoming calls</h2>
<table>
<tr><th>Call</th><th>Date</th><th></th></tr>
{rows}
</table>

<p style="font-size:0.85em;color:#999;">Data from <a href="https://github.com/ethereum/pm">ethereum/pm</a>. Refreshes hourly.</p>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            calls = upcoming_calls()
            html = render(calls)
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=600")
            self.end_headers()
            self.wfile.write(html.encode("utf-8"))
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"upstream error: {e}".encode("utf-8"))

    def log_message(self, *args):
        pass
