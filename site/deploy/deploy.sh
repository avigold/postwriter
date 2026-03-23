#!/usr/bin/env bash
# Deploy site to Hetzner. Run from the site/ directory.
set -euo pipefail

SERVER="${1:?Usage: ./deploy/deploy.sh <server-ip-or-hostname>}"

echo "=== Building ==="
npx vite build --outDir dist

echo "=== Deploying to $SERVER ==="
rsync -avz --delete dist/ "root@${SERVER}:/var/www/postwriter/"

echo "=== Done ==="
echo "Site live at https://postwriter.app"
