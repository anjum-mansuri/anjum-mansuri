"""Finds every public repo whose README mentions anjum-mansuri, rebuilds
projects.json and the 'Projects I've Guided' table in README.md."""
import json, os, re, urllib.request
USER = "anjum-mansuri"
SKIP_OWNERS = {USER}
headers = {"Accept": "application/vnd.github+json"}
if os.getenv("GITHUB_TOKEN"): headers["Authorization"] = "Bearer " + os.environ["GITHUB_TOKEN"]
def search(q):
    req = urllib.request.Request(f"https://api.github.com/search/repositories?q={q}&per_page=100", headers=headers)
    return json.load(urllib.request.urlopen(req))["items"]
items = {r["full_name"]: r for r in search(f"{USER}+in:readme") + search(f"topic:guided-by-{USER}")}
old = {p["repo"]: p for p in json.load(open("projects.json"))} if os.path.exists("projects.json") else {}
excluded = set(json.load(open("excluded.json"))) if os.path.exists("excluded.json") else set()
out = []
for name, r in items.items():
    if r["owner"]["login"] in SKIP_OWNERS or name in excluded or r["fork"]: continue
    if name in old: out.append(old[name]); continue          # keep hand-edited titles
    t = r["topics"]; desc = (r["description"] or "").lower()
    if r["language"] == "Shell" or "linux-shell" in t or "linux" in desc: course, tech = "Linux Shell Scripting", "Bash"
    elif "udp" in t or "udp" in desc or r["language"] in ("TypeScript", "JavaScript", "Dart", "HTML", "PHP"): course, tech = "UDP", r["language"] or ""
    else: course, tech = "Machine Learning", "Python · Jupyter"
    title = re.sub(r"^((?:[A-Za-z]\d+)[-_ ]+)+", "", r["name"])   # drop codes like L26-, B07-P25-, H36-L106-
    title = re.sub(r"[-_]+", " ", title).strip()
    title = " ".join(w if w.isupper() else w[:1].upper() + w[1:] for w in title.split())
    out.append({"title": title, "repo": name, "url": r["html_url"], "student": r["owner"]["login"],
                "course": course, "tech": tech,
                "description": (r["description"] or "").strip(), "date": r["created_at"][:10]})
out.sort(key=lambda x: (x["course"], x["title"].lower()))
json.dump(out, open("projects.json", "w"), indent=2, ensure_ascii=False)
sec = []
for c, icon in [("Machine Learning", "🤖"), ("Linux Shell Scripting", "🐧"), ("UDP", "🌐")]:
    ps = [x for x in out if x["course"] == c]
    if not ps: continue
    rows = "\n".join(f"| [{x['title']}]({x['url']}) | [@{x['student']}](https://github.com/{x['student']}) | {x['tech']} |" for x in ps)
    sec.append(f"### {icon} {c} ({len(ps)})\n\n| Project | Student | Tech |\n|---|---|---|\n{rows}")
table = f"**{len(out)} student projects guided** · ML · Linux · UDP · auto-updated weekly\n\n" + "\n\n".join(sec)
readme = open("README.md").read()
readme = re.sub(r"<!-- GUIDED:START -->.*<!-- GUIDED:END -->", lambda m: f"<!-- GUIDED:START -->\n{table}\n<!-- GUIDED:END -->", readme, flags=re.S)
open("README.md", "w").write(readme)
print(len(out), "projects")
