# The Edge of Evidence

Quarto source for **The Edge of Evidence — Scientific commentary by iLo**.

## Local preview

```powershell
quarto preview
```

## Create a post

Copy either `templates/analysis/` or `templates/brief/` into `posts/YYYY-MM-DD-short-title/`. Replace the front matter, add a cover image, keep `draft: true` while editing, and remove that line only after completing the checklist in `PUBLISHING.md`.

## Render the complete site

```powershell
quarto render
```

## Publication safeguard

The GitHub workflow publishes only while the reviewed `.publish-approved` marker is present. To pause future deployments, remove that marker in a commit.

Before launch, replace `https://ichunglo.github.io` if GitHub assigns a different final account or domain.
