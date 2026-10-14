#!/usr/bin/env python3
"""Deposit each contribution PDF as its own Zenodo record and write the DOI back
into contributions.yml.

One record per contribution: creator = the contributor (with ORCID when given),
contributors = the organizers with role Editor, license CC BY 4.0, the PDF as
the file, related identifier isPartOf -> the collection DOI, and membership in
the session's Zenodo community.

Usage
  export ZENODO_TOKEN=...            # personal access token, scopes deposit:write deposit:actions
  python scripts/zenodo_deposit.py --community open-physics-data-terms \
      --collection-doi 10.5281/zenodo.NNNNNNN [--sandbox] [--dry-run] [--publish]

Without --publish the records are left as drafts for you to look at on Zenodo
(the DOI is reserved and written to the yml). Re-running is safe: a contribution
that already has a doi: is skipped unless --new-version is given, which uploads
the current PDF as a new version of that record.

Sandbox: https://sandbox.zenodo.org needs its own token; use --sandbox to test.
"""
import argparse, os, sys, json
from pathlib import Path

import requests
import yaml

ROOT = Path(__file__).resolve().parent.parent
YML = ROOT / "contributions.yml"

EDITORS = [
    {"name": "Roberts, Amy", "affiliation": "University of Colorado Denver", "type": "Editor"},
    {"name": "Taufer, Michela", "affiliation": "University of Tennessee, Knoxville", "type": "Editor"},
    {"name": "Walker, Jessica", "affiliation": "University of Tennessee, Knoxville", "type": "Editor"},
]
TITLE = "Open physics data: what license and attribution terms should it carry?"
SITE = "https://det-lab.github.io/open-physics-data-terms-site/"


def cite_name(c):
    cn = c.get("cite_name")
    if cn and "," in cn:
        return cn.strip()
    parts = c["name"].split()
    return f"{parts[-1]}, {' '.join(parts[:-1])}"


def metadata(c, args):
    creator = {"name": cite_name(c), "affiliation": c["affiliation"].split(",")[0].strip()}
    if c.get("orcid"):
        creator["orcid"] = str(c["orcid"]).strip()
    desc = (f"<p>{c['descriptor']}</p>"
            f"<p>A one-page contribution to <i>{TITLE}</i>, a moderated discussion at SESAPS 2026 "
            f"(Kennesaw State University, Nov 12–14, 2026). "
            f"{'Drafted by the organizers from a 20-minute call and approved by the contributor.' if c.get('kind') == 'call' else 'Written by the contributor.'} "
            f"All contributions: <a href=\"{SITE}\">{SITE}</a></p>")
    lic = c.get("licenses") or {}
    if lic:
        desc += "<p>Terms reported for the contributor's own releases: " + "; ".join(f"{k}: {v}" for k, v in lic.items()) + ".</p>"
    md = {
        "upload_type": "publication",
        "publication_type": "section",
        "title": c.get("title") or f"Contribution by {c['name']}",
        "creators": [creator],
        "contributors": EDITORS,
        "description": desc,
        "license": "cc-by-4.0",
        "access_right": "open",
        "keywords": ["open data", "data licensing", "attribution", "physics", "SESAPS"],
        "related_identifiers": [
            {"identifier": SITE, "relation": "isSupplementedBy", "resource_type": "other"},
        ],
    }
    if args.collection_doi:
        md["related_identifiers"].append(
            {"identifier": args.collection_doi, "relation": "isPartOf", "resource_type": "publication-other"})
    if args.community:
        md["communities"] = [{"identifier": args.community}]
    return md


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--community", help="Zenodo community identifier")
    ap.add_argument("--collection-doi", help="CONCEPT DOI of the collection record (the one Zenodo labels 'Cite all versions')")
    ap.add_argument("--sandbox", action="store_true")
    ap.add_argument("--dry-run", action="store_true", help="print metadata, touch nothing")
    ap.add_argument("--publish", action="store_true", help="publish instead of leaving drafts")
    ap.add_argument("--new-version", action="store_true", help="for entries that already have a doi, upload the current PDF as a new version")
    ap.add_argument("--only", help="contribution id to process (default: all)")
    args = ap.parse_args()

    base = "https://sandbox.zenodo.org/api" if args.sandbox else "https://zenodo.org/api"
    token = os.environ.get("ZENODO_TOKEN")
    if not token and not args.dry_run:
        sys.exit("set ZENODO_TOKEN")
    s = requests.Session()
    s.params = {"access_token": token}

    contribs = yaml.safe_load(YML.read_text()) or []
    changed = False
    for c in contribs:
        if args.only and c["id"] != args.only:
            continue
        pdf = ROOT / c["file"]
        if not pdf.exists():
            print(f"skip {c['id']}: {c['file']} missing"); continue
        if (c.get("doi") or c.get("doi_version")) and not args.new_version:
            print(f"skip {c['id']}: already deposited ({c.get('doi') or c.get('doi_version')})"); continue
        md = metadata(c, args)
        if args.dry_run:
            print(json.dumps({"id": c["id"], "metadata": md}, indent=2)); continue

        if c.get("doi") and args.new_version:
            rec_id = (c.get("doi_version") or c["doi"]).rsplit(".", 1)[-1]
            r = s.post(f"{base}/deposit/depositions/{rec_id}/actions/newversion"); r.raise_for_status()
            dep_url = r.json()["links"]["latest_draft"]
            dep = s.get(dep_url).json()
            for f in dep.get("files", []):
                s.delete(f["links"]["self"])
        else:
            r = s.post(f"{base}/deposit/depositions", json={}); r.raise_for_status()
            dep = r.json()
        dep_id = dep["id"]
        bucket = dep["links"]["bucket"]
        with open(pdf, "rb") as fh:
            r = s.put(f"{bucket}/{pdf.name}", data=fh); r.raise_for_status()
        r = s.put(f"{base}/deposit/depositions/{dep_id}", json={"metadata": md}); r.raise_for_status()
        dep = r.json()
        vdoi = dep["metadata"].get("prereserve_doi", {}).get("doi") or dep.get("doi")
        cdoi = dep.get("conceptdoi")
        if args.publish:
            r = s.post(f"{base}/deposit/depositions/{dep_id}/actions/publish"); r.raise_for_status()
            pub = r.json()
            vdoi, cdoi = pub["doi"], pub.get("conceptdoi")
        print(f"{c['id']}: {'published' if args.publish else 'draft'} version {vdoi} concept {cdoi}  {dep['links'].get('html')}")
        # doi = concept DOI (permalink to the latest version), used on the website;
        # doi_version = this upload. Before publishing only the version DOI is reserved.
        c["doi_version"] = vdoi
        if cdoi:
            c["doi"] = cdoi
        changed = True

    if changed and not args.dry_run:
        # rewrite the yml preserving the header comment block
        text = YML.read_text()
        head = text[: text.index("- id:")] if "- id:" in text else ""
        YML.write_text(head + yaml.safe_dump(contribs, sort_keys=False, allow_unicode=True, width=1000))
        print("wrote DOIs to contributions.yml")


if __name__ == "__main__":
    main()
