#!/usr/bin/env python3
"""Find the Zenodo record that the GitHub integration created for a release of a
repository, using Zenodo's public search API (no token needed).

Usage: zenodo_lookup.py OWNER/REPO [TAG] [--wait SECONDS] [--sandbox]
Prints JSON {"doi": version DOI, "conceptdoi": concept DOI, "version": ..., "url": ...}
or exits 1 if not found within the wait.
"""
import argparse, json, os, sys, time
from pathlib import Path
import requests


def find_record(repo, tag=None, sandbox=False):
    base = "https://sandbox.zenodo.org/api" if sandbox else "https://zenodo.org/api"
    url = f"https://github.com/{repo}"
    name = repo.split("/")[-1]
    hits = []
    # Title from .zenodo.json: with that file present, Zenodo uses our title and our
    # related identifiers, not its usual "owner/repo: tag" title and GitHub tree link.
    ztitle = None
    zj = Path(__file__).resolve().parent.parent / ".zenodo.json"
    if zj.exists():
        try: ztitle = json.loads(zj.read_text()).get("title")
        except Exception: pass
    token = os.environ.get("ZENODO_TOKEN")
    if token:
        # The account's own depositions: sees records that are still pending community review.
        try:
            r = requests.get(f"{base}/deposit/depositions", params={"q": name, "size": 25, "sort": "mostrecent", "all_versions": "true", "access_token": token}, timeout=60)
            if r.status_code == 200:
                for d in r.json():
                    hits.append({"id": d.get("id"), "doi": d.get("doi") or d.get("metadata", {}).get("prereserve_doi", {}).get("doi"),
                                 "conceptdoi": d.get("conceptdoi"), "metadata": d.get("metadata", {}), "links": d.get("links", {})})
                print(f"::notice::zenodo depositions: {len(hits)} for {name}")
            else:
                print(f"::warning::zenodo depositions HTTP {r.status_code}: {r.text[:200]}")
        except Exception as ex:
            print(f"::warning::zenodo depositions error: {ex}")
    queries = [f'"{url}"', f'title:"{repo}"', f'"{name}"']
    if ztitle:
        queries = [ztitle, f'title:"{ztitle}"'] + queries
    for q in queries:
        try:
            r = requests.get(f"{base}/records", params={"q": q, "sort": "mostrecent", "size": 25, "all_versions": "true"},
                             headers={"Accept": "application/json"}, timeout=60)
            if r.status_code != 200:
                print(f"::warning::zenodo search HTTP {r.status_code} for {q}: {r.text[:200]}"); continue
            hits += r.json().get("hits", {}).get("hits", [])
        except Exception as ex:  # network hiccup: keep polling
            print(f"::warning::zenodo search error: {ex}")
    # DataCite indexes every Zenodo DOI with its GitHub tree URL as a related identifier.
    try:
        q = f'relatedIdentifiers.relatedIdentifier:"{url}/tree/{tag}"' if tag else f'relatedIdentifiers.relatedIdentifier:"{url}*"'
        r = requests.get("https://api.datacite.org/dois", params={"query": q, "page[size]": 25, "sort": "-created"},
                         headers={"Accept": "application/vnd.api+json"}, timeout=60)
        if r.status_code == 200:
            for d in r.json().get("data", []):
                a = d.get("attributes", {})
                rel = a.get("relatedIdentifiers") or []
                concept = next((x.get("relatedIdentifier") for x in rel if x.get("relationType") == "IsVersionOf"), None)
                hits.append({"id": "datacite:" + a.get("doi", ""), "doi": a.get("doi"), "conceptdoi": concept,
                             "metadata": {"title": (a.get("titles") or [{}])[0].get("title", ""), "version": a.get("version"),
                                          "related_identifiers": [{"identifier": x.get("relatedIdentifier")} for x in rel]},
                             "links": {"html": a.get("url")}})
            print(f"::notice::datacite: {len(r.json().get('data', []))} for {q}")
        else:
            print(f"::warning::datacite HTTP {r.status_code}: {r.text[:200]}")
    except Exception as ex:
        print(f"::warning::datacite error: {ex}")
    seen = set(); hits = [h for h in hits if not (h.get("id") in seen or seen.add(h.get("id")))]
    print(f"::notice::zenodo search: {len(hits)} hits for {url}")
    for h in hits:
        t = h.get('metadata', {}).get('title', '')
        if (ztitle and t.strip() == ztitle.strip()) or t.startswith(repo + ":") or name in t:
            print(f"::notice::candidate {h.get('doi')} concept={h.get('conceptdoi')} version={h.get('metadata', {}).get('version')!r} title={t!r}")
    for h in hits:
        rel = h.get("metadata", {}).get("related_identifiers", []) or []
        ids = [x.get("identifier", "") for x in rel]
        title = h.get("metadata", {}).get("title", "")
        ours = any(i.startswith(url) for i in ids) or title.startswith(repo + ":") or (ztitle and title.strip() == ztitle.strip())
        if not ours:
            continue
        ver = str(h.get("metadata", {}).get("version") or "")
        if tag and not (any(i.rstrip("/").endswith(f"/tree/{tag}") for i in ids) or ver == tag or ver == tag.lstrip("v")):
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
            print(f"::notice::FOUND {json.dumps(rec)}"); print(json.dumps(rec)); return
        if time.time() >= deadline:
            print(f"no Zenodo record found for {a.repo} {a.tag or ''}", file=sys.stderr); sys.exit(1)
        time.sleep(30)


if __name__ == "__main__":
    main()
