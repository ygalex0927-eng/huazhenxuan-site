#!/usr/bin/env bash
set -euo pipefail
SITE="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$(cd "$SITE/../huazhen-catalog/web" && pwd)"
python3 "$SITE/scripts/export-catalog-api.py"
mkdir -p "$WEB/public/data"
cp "$SITE/data/catalog.json" "$WEB/public/data/catalog.json"
( cd "$WEB" && VITE_STATIC=1 VITE_BASE=./ npm run build )
rsync -a --delete \
  --exclude data --exclude images --exclude CNAME --exclude scripts \
  --exclude qa --exclude .git --exclude README.md --exclude .gitignore \
  "$WEB/dist"/ "$SITE"/
cp "$SITE/index.html" "$SITE/404.html"
echo "Built. Review, then: git add -A && git commit && git push"
