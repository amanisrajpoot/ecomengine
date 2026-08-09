#!/usr/bin/env bash
# One-time VM setup: Docker, firewall, swap (Oracle Ampere Ubuntu).
set -euo pipefail

echo "==> Installing Docker..."
if ! command -v docker >/dev/null 2>&1; then
  curl -fsSL https://get.docker.com | sudo sh
  sudo usermod -aG docker "$USER"
  echo "Docker installed. Log out and back in (or run: newgrp docker) before deploy."
fi

sudo systemctl enable docker
sudo systemctl start docker

echo "==> Opening host firewall (iptables)..."
for port in 22 8000 3000 3001 3002 3003; do
  sudo iptables -C INPUT -p tcp --dport "$port" -j ACCEPT 2>/dev/null \
    || sudo iptables -I INPUT -p tcp --dport "$port" -j ACCEPT
done

if command -v netfilter-persistent >/dev/null 2>&1; then
  sudo netfilter-persistent save
elif command -v iptables-save >/dev/null 2>&1; then
  sudo sh -c 'iptables-save > /etc/iptables.rules' 2>/dev/null || true
fi

echo "==> Optional: 2GB swap (helps 8GB VMs during docker build)..."
if [ ! -f /swapfile ]; then
  sudo fallocate -l 2G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=2048
  sudo chmod 600 /swapfile
  sudo mkswap /swapfile
  sudo swapon /swapfile
  grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
fi

echo "==> Done. Next: clone repo, edit .env, run scripts/deploy.sh"
