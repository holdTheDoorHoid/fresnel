#!/usr/bin/env python3
"""After a story batch: tidy, check, test and (with --publish) commit and push.

  research/post_batch.py ID-FILE [ID-FILE ...] [--publish "message"]

Each ID-FILE lists one station id per line (the batch's ids). With batches running in parallel, publish only
when all of them have finished, passing every finished batch's ID-FILE (their stories share data/stories, and
the build and tests read all of it). Steps, stopping at the first failure:
  1. research/reconcile.py (cite lists, footnotes missing from sources)
  2. research/check_quotes.py on the batch's ids (missing quotes are reported, not fatal: the checker
     verdicts decide; stations with missing quotes are listed for a look)
  3. every story names its own station in its opening (a scratch-file collision once swapped two stories),
     no story or research file outside the batch was touched, and no stray files in the repo root
  4. pipeline/validate.py, the pipeline tests, build_site_data, the web type check, tests and build
  5. with --publish: git add data/stories data/research, commit, push
Exit status 0 only when every step passed."""
import argparse, glob, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, cwd=ROOT, quiet=True):
    p = subprocess.run(cmd, cwd=cwd, shell=isinstance(cmd, str), capture_output=True, text=True)
    if not quiet or p.returncode:
        sys.stdout.write(p.stdout[-3000:])
        sys.stderr.write(p.stderr[-3000:])
    return p


def station_name(sid):
    p = glob.glob(os.path.join(ROOT, "data", "stations", "*", f"{sid}.json"))
    return json.load(open(p[0], encoding="utf-8"))["name"] if p else None


STOP = {"light", "lighthouse", "station", "range", "lights", "front", "rear", "the", "of", "de", "la", "le", "du",
        "island", "point", "head", "harbor", "harbour", "cape", "life", "saving", "lightship", "pier", "breakwater",
        "north", "south", "east", "west", "phare", "faro", "isla", "punta", "mount", "rock", "reef", "shoal"}


def name_keys(name):
    words = [w for w in re.findall(r"[\w'’-]+", name.lower()) if w not in STOP and len(w) > 2]
    return words or [w for w in re.findall(r"[\w'’-]+", name.lower()) if len(w) > 2]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("idfiles", nargs="+")
    ap.add_argument("--publish", metavar="MESSAGE")
    a = ap.parse_args()
    ids = []
    for f in a.idfiles:
        ids += [l.strip() for l in open(f, encoding="utf-8") if l.strip() and not l.startswith("#")]
    ok = True

    print("1. reconcile"); run(["python3", "research/reconcile.py"], quiet=False)

    print("2. quotes")
    p = run(["python3", "research/check_quotes.py", *ids])
    bad = [l for l in p.stdout.splitlines() if l.startswith(("MISSING", "ABSENT"))]
    print("\n".join(bad) or "   all quotes found"); print("   " + (p.stdout.strip().splitlines() or ["?"])[-1])

    print("3. identity and stray files")
    for sid in ids:
        sp = os.path.join(ROOT, "data", "stories", f"{sid}.md")
        if not os.path.exists(sp):
            print(f"   NO STORY {sid}")
            continue
        head = open(sp, encoding="utf-8").read()[:3000].lower()
        name = station_name(sid) or sid
        if not any(k in head for k in name_keys(name)):
            print(f"   CHECK IDENTITY {sid}: the opening never names {name!r}"); ok = False
    st = run(["git", "status", "--porcelain", "--untracked-files=all"]).stdout.splitlines()
    touched = {re.sub(r"^.. ", "", l) for l in st}
    batch = {f"data/stories/{i}.md" for i in ids} | {f"data/research/{i}.json" for i in ids}
    other = sorted(t for t in touched if t.startswith(("data/stories/", "data/research/")) and t not in batch)
    untracked = {l[3:] for l in st if l.startswith("??")}
    stray = sorted(t for t in untracked if "/" not in t)  # new files dropped in the repo root by an agent
    if other:
        print("   OUTSIDE THE BATCH:", ", ".join(other[:20])); ok = False
    if stray:
        print("   STRAY FILES IN THE REPO ROOT:", ", ".join(stray)); ok = False

    print("4. validate, tests, build")
    for label, cmd, cwd in [("validate", ["python3", "pipeline/validate.py"], ROOT),
                            ("pipeline tests", ["python3", "-m", "unittest", "discover", "-s", "pipeline"], ROOT),
                            ("site data", ["python3", "pipeline/build_site_data.py", "--quiet"], ROOT),
                            ("type check", ["npm", "run", "check"], os.path.join(ROOT, "web")),
                            ("web tests", ["npx", "vitest", "run"], os.path.join(ROOT, "web")),
                            ("web build", ["npm", "run", "build"], os.path.join(ROOT, "web"))]:
        r = run(cmd, cwd=cwd)
        print(f"   {label}: {'ok' if r.returncode == 0 else 'FAILED'}")
        if r.returncode:
            ok = False
            break

    if a.publish and ok:
        print("5. publish")
        # Only this batch's files: another batch may be writing its own next to them.
        files = [f for f in sorted(batch) if os.path.exists(os.path.join(ROOT, f))]
        run(["git", "add", "--", *files])
        r = run(["git", "commit", "-q", "-m", a.publish + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"])
        if r.returncode == 0:
            r = run(["git", "push", "-q"])
        print("   pushed" if r.returncode == 0 else "   PUSH FAILED"); ok = ok and r.returncode == 0
    elif a.publish:
        print("5. NOT published: fix the failures above first")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
