#!/usr/bin/env bash
# Hetzner Cloud server setup for postwriter.app
# Run on a fresh Ubuntu 22.04+ instance
set -euo pipefail

echo "=== Installing Caddy ==="
apt-get update -y
apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | tee /etc/apt/sources.list.d/caddy-stable.list
apt-get update -y
apt-get install -y caddy

echo "=== Creating web directory ==="
mkdir -p /var/www/postwriter

echo "=== Installing Caddyfile ==="
cp /root/Caddyfile /etc/caddy/Caddyfile

echo "=== Enabling Caddy ==="
systemctl enable caddy
systemctl restart caddy

echo "=== Done ==="
echo "Now:"
echo "  1. Point postwriter.app DNS to this server's IP"
echo "  2. Copy site files: scp -r dist/* root@<IP>:/var/www/postwriter/"
echo "  3. Caddy will auto-provision HTTPS via Let's Encrypt"
