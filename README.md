# Open physics data: what license and attribution terms should it carry?

Contributions to the moderated discussion at
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
     approved: null                        # the date the author signed off; see below
     file: contributions/usai-alabama.pdf
     license: CC-BY-4.0
   ```

3. Commit and push to `main`.

What happens next depends on `approved`:

- `approved: null` — the entry appears on the website (rebuilt
  automatically) but nothing is sent to Zenodo. Use this while the author
  is still reviewing.
- `approved: <date>` — the "Release and deposit" workflow runs on the push:
  it deposits the page at Zenodo under the author's name (its own DOI, the
  organizers as editors, CC BY 4.0, part of the collection), writes the
  DOIs into `contributions.yml`, bumps the collection version in
  `CITATION.cff`, publishes a GitHub release (Zenodo archives the new
  collection version), and rebuilds the website with the new citations.

**A Zenodo record cannot be deleted once published, only versioned.** So
`approved` is the real gate: set it only when the author has signed off on
the exact PDF in the repository. To correct a PDF later, replace the file
and run the "Deposit contributions to Zenodo" workflow with `only` set to
the id and `new_version` ticked.

The website is built from `main`, so it always shows the current list.

## Releases

Releases are made by the workflow above whenever approved contributions
are deposited; versions go v0.1, v0.2, … The first run also creates the
first release and reads the collection's concept DOI from Zenodo into
`CITATION.cff`. Concept DOIs (the "Cite all versions" DOI) are used
everywhere on the website because they always resolve to the latest
version; each upload's own DOI is kept in `contributions.yml` as
`doi_version`.

To release by hand (for a change that is not a new contribution), run
"Release and deposit new contributions" from the Actions tab; it does
nothing if there are no approved contributions without a DOI, so for a
plain snapshot use GitHub's "Draft a new release" instead.

## Workflows and secrets

- `release.yml` — on every push to `main` that touches `contributions/` or
  `contributions.yml`: deposits approved contributions, releases, and
  rebuilds the website (also when there is nothing to deposit).
- `site.yml` — on pushes that touch `sections/`, `open-questions.md` or
  `CITATION.cff`: rebuilds the website.
- `zenodo.yml` — manual fallback for depositing (see below).

Secrets (Settings → Secrets and variables → Actions):
- `ZENODO_TOKEN` — a Zenodo personal access token with scopes
  `deposit:write` and `deposit:actions`.
- `SITE_DISPATCH_TOKEN` — a fine-grained GitHub token with access to
  `det-lab/open-physics-data-terms-site` and Contents: read and write, so
  this repository can start the site build. Without it, rebuild the site by
  hand ("Run workflow" on the site repo's Actions tab).

## Zenodo: one record per contribution (manual fallback)

The release workflow does this automatically. Besides the whole-repository snapshot that the Zenodo GitHub integration
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

Entries that already have a `doi:` are skipped. A corrected PDF goes up as a new version with `--new-version
--only <id>`. Test against the sandbox with `--sandbox` and a sandbox token.
