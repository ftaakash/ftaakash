"""Build assets/streak.svg from GitHub's contribution calendar (same data as the profile graph)."""
import datetime as dt, json, os, urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
OUT = "assets/streak.svg"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def gql(query, **variables):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        raise SystemExit(data["errors"])
    return data["data"]


created = dt.datetime.fromisoformat(
    gql("query($u:String!){user(login:$u){createdAt}}", u=USER)["user"]["createdAt"].replace("Z", "+00:00")
)
now = dt.datetime.now(dt.timezone.utc)

days = {}
start = created
while start < now:
    end = min(start + dt.timedelta(days=365), now)
    cal = gql(
        """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){
             contributionsCollection(from:$f,to:$t){contributionCalendar{weeks{contributionDays{date contributionCount}}}}}}""",
        u=USER, f=start.isoformat(), t=end.isoformat(),
    )["user"]["contributionsCollection"]["contributionCalendar"]
    for w in cal["weeks"]:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]
    start = end

dates = sorted(days)
total = sum(days.values())
first = next((d for d in dates if days[d]), dates[0])

# longest streak
longest, run, run_start, best = 0, 0, None, (None, None)
for d in dates:
    if days[d]:
        run_start = d if run == 0 else run_start
        run += 1
        if run > longest:
            longest, best = run, (run_start, d)
    else:
        run = 0

# current streak: today may still be 0 without breaking it
today = now.astimezone(IST).date().isoformat()
idx = len(dates) - 1
while idx >= 0 and dates[idx] > today:
    idx -= 1
if idx >= 0 and days[dates[idx]] == 0:
    idx -= 1
cur, cur_end = 0, dates[idx] if idx >= 0 else None
while idx >= 0 and days[dates[idx]]:
    cur += 1
    idx -= 1
cur_start = dates[idx + 1] if cur else None

fmt = lambda s: dt.date.fromisoformat(s).strftime("%b %-d") if s else ""
fmt_full = lambda s: dt.date.fromisoformat(s).strftime("%b %-d, %Y")
rng = lambda a, b: f"{fmt(a)} - {fmt(b)}" if a else "—"

G, FG, MUTED, BG, LINE = "#39d353", "#c9d1d9", "#8b949e", "#0d1117", "#30363d"
F = "font-family=\"'Segoe UI',Ubuntu,'DejaVu Sans',sans-serif\""
svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195">
<style>@keyframes fade{{from{{opacity:0}}to{{opacity:1}}}} .f{{animation:fade .6s ease-in-out forwards;opacity:0}}</style>
<rect width="495" height="195" rx="5" fill="{BG}"/>
<line x1="165" y1="28" x2="165" y2="170" stroke="{LINE}"/>
<line x1="330" y1="28" x2="330" y2="170" stroke="{LINE}"/>
<g {F} text-anchor="middle">
  <text class="f" x="82.5" y="79" font-size="28" font-weight="700" fill="{FG}">{total:,}</text>
  <text class="f" x="82.5" y="115" font-size="14" fill="{FG}">Total Contributions</text>
  <text class="f" x="82.5" y="145" font-size="12" fill="{MUTED}">{fmt_full(first)} - Present</text>

  <circle cx="247.5" cy="71" r="40" fill="none" stroke="{G}" stroke-width="5"/>
  <rect x="235" y="15" width="25" height="26" fill="{BG}"/>
  <path transform="translate(237 18) scale(.85)" fill="{G}" d="M12 0c1 4-1 6-3 9-2 3-3 6-1 10-3-1-5-4-5-7 0-3 2-5 3-7 0 2 1 3 2 4 0-4 2-7 4-9zm1 9c2 2 4 5 4 8 0 4-3 7-6 7 2-1 3-3 3-5 0-1-1-3-2-4 0 2-1 3-2 3 1-3 3-6 3-9z"/>
  <text class="f" x="247.5" y="81" font-size="28" font-weight="700" fill="{FG}">{cur}</text>
  <text class="f" x="247.5" y="138" font-size="14" font-weight="700" fill="{G}">Current Streak</text>
  <text class="f" x="247.5" y="160" font-size="12" fill="{MUTED}">{rng(cur_start, cur_end)}</text>

  <text class="f" x="412.5" y="79" font-size="28" font-weight="700" fill="{FG}">{longest}</text>
  <text class="f" x="412.5" y="115" font-size="14" fill="{FG}">Longest Streak</text>
  <text class="f" x="412.5" y="145" font-size="12" fill="{MUTED}">{rng(*best)}</text>
</g>
</svg>'''
os.makedirs("assets", exist_ok=True)
open(OUT, "w").write(svg)
print(f"total={total} current={cur} longest={longest}")
