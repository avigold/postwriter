#!/usr/bin/env bash
# Deploy site: runs git pull + build on the server.
# Usage: ./deploy/deploy.sh [server-ip]
set -euo pipefail

SERVER="${1:-204.168.181.165}"

echo "=== Deploying to $SERVER ==="
ssh "root@${SERVER}" "bash /opt/postwriter/site/deploy/deploy-server.sh"
echo "=== Site live at https://postwriter.app ==="
