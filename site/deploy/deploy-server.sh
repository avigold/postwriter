#!/usr/bin/env bash
# Run ON the server: pulls latest, builds, deploys.
# Usage: ssh root@204.168.181.165 "bash /opt/postwriter/site/deploy/deploy-server.sh"
set -euo pipefail

REPO_DIR="/opt/postwriter"
WEB_DIR="/var/www/postwriter"

# Clone or pull
if [ -d "$REPO_DIR" ]; then
    cd "$REPO_DIR"
    git pull
else
    git clone https://github.com/avigold/postwriter.git "$REPO_DIR"
    cd "$REPO_DIR"
fi

# Install node if needed
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y nodejs
fi

# Build site
cd "$REPO_DIR/site"
npm install --production=false
npx vite build --outDir dist

# Deploy
rsync -a --delete dist/ "$WEB_DIR/"

echo "=== Deployed ==="
