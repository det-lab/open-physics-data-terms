#!/usr/bin/env python3
"""Hands-off release of the collection. Run by .github/workflows/release.yml on
every push to main that changes contributions; safe to run by hand.

Steps
 1. Find contributions with an `approved` date and no DOI. None -> exit 0.
 2. Make sure the collection has a concept DOI in CITATION.cff. If not (first
    release), create the GitHub release for the current version, wait for the
    Zenodo GitHub integration to archive it, and read the concept DOI from
    Zenodo's public API.
 3. Deposit and publish each pending contribution (scripts/zenodo_deposit.py),
    which writes doi / doi_version into contributions.yml.
 4. Bump the minor version, write version and concept DOI into CITATION.cff,
    commit and push, and create the GitHub release for the new version so
    Zenodo archives the collection with the DOIs in it.

Env: GITHUB_TOKEN (contents: write), GITHUB_REPOSITORY (owner/repo), ZENODO_TOKEN.
"""
import datetime, json, os, re, subprocess, sys, time
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from zenodo_lookup import find_record  # noqa: E402

REPO = os.environ.get("GITHUB_REPOSITORY", "det-lab/open-physics-data-terms")
GH = os.environ.get("GITHUB_TOKEN")
COMMUNITY = "open-physics-data-terms"
CFF = ROOT / "CITATION.cff"
YML = ROOT / "contributions.yml"


def sh(*cmd, check=True):
    print("+", " ".join(cmd), flush=True)
    return subprocess.run(cmd, check=check, text=True, capture_output=True).stdout


def cff_get(key):
    m = re.search(rf"^{key}:\s*(.+?)\s*$", CFF.read_text(), re.M)
    return m.group(1).strip('"') if m else None


def cff_set(key, value):
    s = CFF.read_text()
    if re.search(rf"^#? ?{key}:", s, re.M):
        s = re.sub(rf"^#? ?{key}:.*$", f"{key}: {value}", s, count=1, flags=re.M)
    else:
        s = s.rstrip("\n") + f"\n{key}: {value}\n"
    CFF.write_text(s)


def gh_release(tag, name, body):
    r = requests.post(f"https://api.github.com/repos/{REPO}/releases",
                      headers={"Authorization": f"Bearer {GH}", "Accept": "application/vnd.github+json"},
                      json={"tag_name": tag, "target_commitish": "main", "name": name, "body": body}, timeout=60)
    if r.status_code == 422 and "already_exists" in r.text:
        print(f"release {tag} already exists"); return
    r.raise_for_status()
    print("created release", r.json().get("html_url"))


def bump(version):
    major, minor = (version or "0.0").split(".")[:2]
    return f"{major}.{int(minor) + 1}"


def main():
    contribs = yaml.safe_load(YML.read_text()) or []
    pending = [c for c in contribs if c.get("approved") and not c.get("doi") and (ROOT / c["file"]).exists()]
    if not pending:
        print("nothing to release: no approved contributions without a DOI"); return
    print("pending:", [c["id"] for c in pending])

    sh("git", "config", "user.name", "github-actions[bot]")
    sh("git", "config", "user.email", "github-actions[bot]@users.noreply.github.com")

    concept = cff_get("doi")
    version = cff_get("version") or "0.1"
    if not concept or "XXXX" in concept:
        # First release: Zenodo has to archive something before a concept DOI exists.
        tag = f"v{version}"
        gh_release(tag, f"{tag}", "First archived version of the collection.")
        print("waiting for Zenodo to archive the release ...")
        rec = None
        deadline = time.time() + 900
        while time.time() < deadline and not rec:
            rec = find_record(REPO, tag)
            if not rec:
                time.sleep(30)
        if not rec or not rec.get("conceptdoi"):
            sys.exit("Zenodo record for the first release not found after 15 minutes; is the GitHub integration switched on for this repository?")
        concept = rec["conceptdoi"]
        cff_set("doi", concept)
        print("collection concept DOI:", concept)

    # Deposit the pending contributions and publish them.
    sh(sys.executable, str(ROOT / "scripts" / "zenodo_deposit.py"), "--community", COMMUNITY,
       "--collection-doi", concept, "--publish")

    # New collection version with the DOIs recorded.
    new_version = bump(version)
    cff_set("version", new_version)
    cff_set("date-released", datetime.date.today().isoformat())
    sh("git", "add", "contributions.yml", "CITATION.cff")
    if sh("git", "status", "--porcelain", check=False).strip():
        ids = ", ".join(c["id"] for c in pending)
        sh("git", "commit", "-m", f"Release v{new_version}: Zenodo DOIs for {ids}")
        sh("git", "push")
    gh_release(f"v{new_version}", f"v{new_version}", f"Adds: {', '.join(c['id'] for c in pending)}. Each contribution has its own Zenodo record; see contributions.yml.")
    print(json.dumps({"version": new_version, "concept_doi": concept, "deposited": [c["id"] for c in pending]}))


if __name__ == "__main__":
    main()
