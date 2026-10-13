# Open physics data: what license and attribution terms should it carry?

Contributions, catalog, and codebook for the moderated discussion at
SESAPS 2026 (Kennesaw State University, Nov 12–14), organized by
Amy Roberts (CU Denver, SuperCDMS) and Michela Taufer (UT Knoxville).

Everything here is licensed CC BY 4.0 (see LICENSE). Each release of this
repository is archived at Zenodo and gets a DOI.

## Layout

- `contributions/` — one-page perspectives from contributors, as PDFs,
  one file per contributor. Each PDF carries its own CC BY 4.0 notice.
- `contributions.yml` — the index: who wrote each page, a one-sentence
  descriptor, dates received and approved. The website is built from this.
- `sections/` — Markdown sections shown on the website after the
  contributions (license options, who took part, papers and methods).
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
