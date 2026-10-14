# Open physics data: what license and attribution terms should it carry?

Contributions, catalog, and codebook for the moderated discussion at
SESAPS 2026 (Kennesaw State University, Nov 12–14), organized by
Amy Roberts (CU Denver, SuperCDMS), Michela Taufer (UT Knoxville), and
Jessica Walker (UT Knoxville).

Everything here is licensed CC BY 4.0 (see LICENSE). Each release of this
repository is archived at Zenodo and gets a DOI.

## Layout

- `contributions/` — one-page perspectives from contributors, as PDFs,
  one file per contributor. Each PDF carries its own CC BY 4.0 notice.
- `contributions.yml` — the index: who wrote each page, a one-sentence
  descriptor, dates received and approved. The website is built from this.
- `sections/` — one Markdown file per website page (who took part, papers
  and methods, agenda, ...), shown in the site navigation in filename order.
- `catalog/` — the coded survey data (not shown on the website).
- `codebook/` — the codebook (current version) used to code the catalog.
- `open-questions.md` — questions the discussion left open.

## Adding a contribution

1. Put the PDF in `contributions/` named `lastname-affiliation.pdf`
   (lowercase, hyphens).
2. Add an entry to `contributions.yml` (copy an existing one).
3. Commit. The website rebuilds from the next tagged release.

## Releases

Tag a release (`v0.1`, `v0.2`, …) on GitHub. The Zenodo integration
archives the whole repository at that tag and mints a DOI. The DOI for the
concept record (all versions) goes in `CITATION.cff` once it exists.

## Zenodo: one record per contribution

Besides the whole-repository snapshot that the Zenodo GitHub integration
archives at each tag, every contribution gets its own Zenodo record, so each
author has a DOI under their own name. `scripts/zenodo_deposit.py` creates
those records from `contributions.yml` (creator = the contributor, with
ORCID; the organizers as Editors; CC BY 4.0; `isPartOf` the collection DOI;
in the session's Zenodo community) and writes each DOI back into the yml.

    pip install requests pyyaml
    export ZENODO_TOKEN=...   # scopes: deposit:write, deposit:actions
    python scripts/zenodo_deposit.py --community open-physics-data-terms \
        --collection-doi 10.5281/zenodo.NNNNNNN            # drafts, for review
    python scripts/zenodo_deposit.py ... --publish          # when the drafts look right

Run it once per release, after tagging; entries that already have a `doi:`
are skipped. A corrected PDF goes up as a new version with `--new-version
--only <id>`. Test against the sandbox with `--sandbox` and a sandbox token.
