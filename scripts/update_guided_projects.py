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
import urllib.parse, time
QUERIES = [f"{USER} in:readme", '"Anjum Y. Mansuri" in:readme', '"Anjum Mansuri" in:readme', f"topic:guided-by-{USER}"]
items = {}
def readme(full):
    for b in ("main", "master"):
        try: return urllib.request.urlopen(f"https://raw.githubusercontent.com/{full}/{b}/README.md").read().decode("utf-8", "ignore").lower()
        except Exception: pass
    return ""
def classify(r):
    lang = r["language"] or ""
    text = " ".join([r["name"], r["description"] or "", " ".join(r["topics"])]).lower()
    if "udp" in text: return "UDP", lang or "Web"
    if lang == "Shell" or any(k in text for k in ("linux", "bash", "shell", "ubuntu", "ubantu")): return "Linux Shell Scripting", "Bash"
    if lang in ("Jupyter Notebook", "Python") or any(k in text for k in ("machine-learning", "machine learning", " ml ", "predict", "classifier")): return "Machine Learning", "Python · Jupyter"
    rd = readme(r["full_name"])
    if "udp" in rd: return "UDP", lang or "Web"
    if "linux" in rd or "bash" in rd: return "Linux Shell Scripting", "Bash"
    if "machine learning" in rd or "ml-i" in rd or "jupyter" in rd: return "Machine Learning", "Python · Jupyter"
    if lang in ("TypeScript", "JavaScript", "Dart", "HTML", "PHP", "CSS", "Java"): return "UDP", lang
    return "Machine Learning", lang or "Python"
for q in QUERIES:
    for r in search(urllib.parse.quote(q)):
        items[r["full_name"]] = r
    time.sleep(3)
old = {p["repo"]: p for p in json.load(open("projects.json"))} if os.path.exists("projects.json") else {}
excluded = set(json.load(open("excluded.json"))) if os.path.exists("excluded.json") else set()
out = [p for n, p in old.items() if n not in items and n not in excluded]
for name, r in items.items():
    if r["owner"]["login"] in SKIP_OWNERS or name in excluded or r["fork"]: continue
    if name in old: out.append(old[name]); continue          # keep hand-edited titles
    course, tech = classify(r)
    title = re.sub(r"^[-_ ]*((?:[A-Za-z]\d+)[-_ ]+)+", "", r["name"]).strip("-_ ")   # drop codes like L26-, B07-P25-, F22_L36_
    title = re.sub(r"^(linux|ubantu|ubuntu)[-_ ]+(project[-_ ]+)?", "", title, flags=re.I)
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
    rows = "\n".join(f"| [{x['title']}]({x['url']}) | [@{x['student']}]({x.get('student_url') or 'https://github.com/' + x['student']}) | {x['tech']} |" for x in ps)
    sec.append(f"### {icon} {c} ({len(ps)})\n\n| Project | Student | Tech |\n|---|---|---|\n{rows}")
table = f"**{len(out)} student projects guided** · ML · Linux · UDP · auto-updated daily\n\n" + "\n\n".join(sec)
readme = open("README.md").read()
readme = re.sub(r"<!-- GUIDED:START -->.*<!-- GUIDED:END -->", lambda m: f"<!-- GUIDED:START -->\n{table}\n<!-- GUIDED:END -->", readme, flags=re.S)
open("README.md", "w").write(readme)
print(len(out), "projects")
