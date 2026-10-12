#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
# A fixed metadata epoch makes this version reproducible. No scientific code runs.
export SOURCE_DATE_EPOCH=1791792000
export FORCE_SOURCE_DATE=1
for target in main supplement; do
  pdflatex -recorder -interaction=nonstopmode -halt-on-error "$target.tex"
  bibtex "$target"
  pdflatex -recorder -interaction=nonstopmode -halt-on-error "$target.tex"
  pdflatex -recorder -interaction=nonstopmode -halt-on-error "$target.tex"
done
for target in title_page cover_letter_draft highlights_draft; do
  pdflatex -recorder -interaction=nonstopmode -halt-on-error "$target.tex"
  pdflatex -recorder -interaction=nonstopmode -halt-on-error "$target.tex"
done
if grep -E 'Overfull \\[hv]box|undefined references|undefined citations|Citation .* undefined|Reference .* undefined' main.log supplement.log title_page.log cover_letter_draft.log highlights_draft.log; then
  exit 2
fi
