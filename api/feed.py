import json
import os
import re
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler
from urllib.request import Request, urlopen


GITHUB_API = "https://api.github.com/repos/ethereum/pm/issues"
DURATIONS = {"acde": 90, "acdc": 90, "acdt": 60}


def gh_request(url):
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    with urlopen(Request(url, headers=headers)) as r:
        return json.loads(r.read())


def fetch_issues():
    return gh_request(
        f"{GITHUB_API}?labels=ACD&state=all&per_page=100&sort=created&direction=desc"
    )


def fetch_bot_comment(issue_number):
    comments = gh_request(
        f"{GITHUB_API}/{issue_number}/comments?per_page=5"
    )
    for c in comments:
        if "Protocol Call Resources" in (c.get("body") or ""):
            return c["body"]
    return ""


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


def date_from_title(title):
    m = re.search(r"(\w+ \d{1,2},?\s*\d{4})", title)
    if not m:
        return None
    for fmt in ("%B %d, %Y", "%B %d %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(m.group(1), fmt).replace(hour=14)
        except ValueError:
            pass
    return None


def series(title):
    t = title.lower()
    if "acde" in t or "execution" in t:
        return "acde"
    if "acdc" in t or "consensus" in t:
        return "acdc"
    if "acdt" in t or "testing" in t:
        return "acdt"
    return "acd"


def grab_links(text):
    zoom = re.search(r"https://[a-z]*\.?zoom\.us/[^\s)>\]]+", text)
    yt = re.search(r"https://(?:www\.)?(?:youtube\.com|youtu\.be)/[^\s)>\]]+", text)
    return zoom.group() if zoom else None, yt.group() if yt else None


def clean_title(title):
    return re.sub(r",?\s+(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s*\d{4}$", "", title)


def esc(text):
    return text.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")


def fold(line):
    if len(line.encode("utf-8")) <= 75:
        return line
    parts, cur = [], ""
    for ch in line:
        if len((cur + ch).encode("utf-8")) > (75 if not parts else 74):
            parts.append(cur)
            cur = ch
        else:
            cur += ch
    parts.append(cur)
    return "\r\n ".join(parts)


def build_ics(issues):
    out = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//acd-ics//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        "X-WR-CALNAME:Ethereum All Core Devs",
    ]

    for issue in issues:
        body = issue.get("body") or ""
        title = issue["title"]

        dt = parse_date(section(body, "UTC Date & Time")) or date_from_title(title)
        if not dt:
            continue

        s = series(title)
        dur = DURATIONS.get(s, 90)
        agenda = section(body, "Agenda")
        url = issue.get("html_url", "")

        zoom, yt = grab_links(body)
        if issue.get("state") == "open" or not zoom:
            bot = fetch_bot_comment(issue["number"])
            if bot:
                bz, by = grab_links(bot)
                zoom = bz or zoom
                yt = by or yt

        desc_parts = []
        if agenda:
            desc_parts.append(f"Agenda:\n{agenda}")
        if zoom:
            desc_parts.append(f"Zoom: {zoom}")
        if yt:
            desc_parts.append(f"YouTube: {yt}")
        if url:
            desc_parts.append(url)

        out.append("BEGIN:VEVENT")
        out.append(f"UID:acd-{issue['number']}@ethereum-pm")
        out.append(fold(f"SUMMARY:{esc(clean_title(title))}"))
        out.append(f"DTSTART:{dt.strftime('%Y%m%dT%H%M%SZ')}")
        out.append(f"DTEND:{(dt + timedelta(minutes=dur)).strftime('%Y%m%dT%H%M%SZ')}")
        out.append(fold(f"DESCRIPTION:{esc(chr(10).join(desc_parts))}"))
        if zoom:
            out.append(fold(f"LOCATION:{esc(zoom)}"))
        if url:
            out.append(fold(f"URL:{url}"))
        out.append("BEGIN:VALARM")
        out.append("TRIGGER:-PT2H")
        out.append("ACTION:DISPLAY")
        out.append("DESCRIPTION:ACD call in 2 hours")
        out.append("END:VALARM")
        out.append("END:VEVENT")

    out.append("END:VCALENDAR")
    return "\r\n".join(out)


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            ics = build_ics(fetch_issues())
            self.send_response(200)
            self.send_header("Content-Type", "text/calendar; charset=utf-8")
            self.send_header("Cache-Control", "public, s-maxage=3600, stale-while-revalidate=600")
            self.end_headers()
            self.wfile.write(ics.encode("utf-8"))
        except Exception as e:
            self.send_response(502)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"upstream error: {e}".encode("utf-8"))

    def log_message(self, *args):
        pass
