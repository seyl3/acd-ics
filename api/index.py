from http.server import BaseHTTPRequestHandler

HTML = """<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ethereum ACD Calendar</title>
<style>
body { font-family: system-ui, sans-serif; max-width: 640px; margin: 40px auto; padding: 0 20px; color: #1a1a1a; }
h1 { font-size: 1.4em; }
p { color: #555; line-height: 1.5; }
code { background: #f4f4f4; padding: 2px 6px; border-radius: 3px; font-size: 0.9em; }
a { color: #2563eb; text-decoration: none; }
.feeds { margin: 20px 0; }
.btn { display: block; margin: 6px 0; padding: 8px 12px; background: #f4f4f4; border-radius: 4px; color: #1a1a1a; }
.btn:hover { background: #e8e8e8; }
</style>
</head>
<body>
<h1>Ethereum All Core Devs Calendar</h1>
<p>Live ICS feed for Ethereum's All Core Dev calls. Subscribe in any calendar app.</p>

<div class="feeds">
<strong>Subscribe:</strong>
<a class="btn" href="webcal://acd-ics.vercel.app/feed.ics">All calls</a>
<a class="btn" href="webcal://acd-ics.vercel.app/feed.ics?series=acde">Execution (ACDE)</a>
<a class="btn" href="webcal://acd-ics.vercel.app/feed.ics?series=acdc">Consensus (ACDC)</a>
<a class="btn" href="webcal://acd-ics.vercel.app/feed.ics?series=acdt">Testing (ACDT)</a>
</div>

<p style="font-size:0.85em;color:#999;">Data from <a href="https://github.com/ethereum/pm">ethereum/pm</a>. Refreshes hourly.</p>
</body>
</html>"""


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "public, s-maxage=86400")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

    def log_message(self, *args):
        pass
