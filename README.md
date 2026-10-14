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
- The survey codebook and coded catalog live in their own repository,
  [det-lab/open-physics-data-codebook](https://github.com/det-lab/open-physics-data-codebook),
  with their own DOI, so they can be versioned and cited independently of
  this collection.
- `open-questions.md` — questions the discussion left open.

## Adding a contribution

1. Save the PDF as `contributions/lastname-affiliation.pdf` (lowercase,
   hyphens; e.g. `usai-alabama.pdf`). Check that the author's CC BY 4.0
   line is on the page.
2. Add an entry to `contributions.yml`, at the end of the list:

   ```yaml
   - id: usai-alabama                      # same as the PDF name, without .pdf
     name: Emanuele Usai
     affiliation: University of Alabama, CMS Collaboration
     orcid: 0000-0001-9323-2107            # if known
     kind: written                         # or: call
     title: "Don't just ship the container: lessons from 42 TiB of low-level CMS open data"
     descriptor: One plain sentence on what the page says.
     licenses: {data: CC0, code: GPL v3}   # only what the page itself states; omit if none
     received: 2026-10-14
     approved: 2026-10-14                  # the date the author signed off; null until then
     file: contributions/usai-alabama.pdf
     license: CC-BY-4.0
   ```

3. Commit and push to `main`. The website rebuilds itself within a couple of
   minutes (see below) with the new entry and its citations. The entry's
   Zenodo DOI is added later by the deposit workflow at the next release.

The website is built from `main`, so it always shows the current list.
Release tags are only for Zenodo.

## Releases

Tag a release (`v0.1`, `v0.2`, …) on GitHub. The Zenodo integration
archives the whole repository at that tag, mints a DOI, and submits the
record to the `open-physics-data-terms` community. Then run the Zenodo deposit workflow (below) with the collection's
**concept DOI** (the one Zenodo offers under "Cite all versions"); it
records that DOI in `CITATION.cff` and gives each contribution its own
record. Concept DOIs are used everywhere on the website because they always
resolve to the latest version; the version DOI of each upload is kept in
`contributions.yml` as `doi_version`.

## Website rebuilds

`.github/workflows/site.yml` pings the site repository on every push to
`main` that touches contributions, sections or open questions. It needs a
repository secret `SITE_DISPATCH_TOKEN`: a fine-grained personal access
token with access to `det-lab/open-physics-data-terms-site` and the
permission Contents: read and write. Without it, rebuild the site by hand
("Run workflow" on the site repo's Actions tab).

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
