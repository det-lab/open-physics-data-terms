#!/usr/bin/env python3
"""Find the Zenodo record that the GitHub integration created for a release of a
repository, using Zenodo's public search API (no token needed).

Usage: zenodo_lookup.py OWNER/REPO [TAG] [--wait SECONDS] [--sandbox]
Prints JSON {"doi": version DOI, "conceptdoi": concept DOI, "version": ..., "url": ...}
or exits 1 if not found within the wait.
"""
import argparse, json, sys, time
import requests


def find_record(repo, tag=None, sandbox=False):
    base = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
    url = f"https://github.com/{repo}"
    r = requests.get(f"{base}/records", params={"q": f'"{url}"', "sort": "mostrecent", "size": 50, "all_versions": "true"}, timeout=60)
    r.raise_for_status()
    hits = r.json().get("hits", {}).get("hits", [])
    for h in hits:
        rel = h.get("metadata", {}).get("related_identifiers", []) or []
        ids = [x.get("identifier", "") for x in rel]
        if not any(i.startswith(url) for i in ids):
            continue
        if tag and not any(i.rstrip("/").endswith(f"/tree/{tag}") for i in ids):
            continue
        return {"doi": h.get("doi"), "conceptdoi": h.get("conceptdoi"),
                "version": (h.get("metadata", {}).get("version")), "url": h.get("links", {}).get("self_html") or h.get("links", {}).get("html")}
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("tag", nargs="?")
    ap.add_argument("--wait", type=int, default=0, help="keep polling for up to this many seconds")
    ap.add_argument("--sandbox", action="store_true")
    a = ap.parse_args()
    deadline = time.time() + a.wait
    while True:
        rec = find_record(a.repo, a.tag, a.sandbox)
        if rec:
            print(json.dumps(rec)); return
        if time.time() >= deadline:
            print(f"no Zenodo record found for {a.repo} {a.tag or ''}", file=sys.stderr); sys.exit(1)
        time.sleep(30)


if __name__ == "__main__":
    main()
