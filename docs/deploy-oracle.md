# Oracle Cloud Ampere — step-by-step deploy

## Do you need a startup script?

**No custom startup script is required** if you use `docker-compose.prod.yml`:

- Every service has `restart: unless-stopped` → containers come back after reboot when Docker starts.
- Docker is enabled on boot via `systemctl enable docker` (done by `scripts/vm-setup.sh`).
- Backend already runs migrations + demo seed on first container start.

Optional helpers in `scripts/`:

| Script | When |
|--------|------|
| `vm-setup.sh` | Once per VM (Docker, firewall, swap) |
| `gen-env.sh` | Once — auto-write `.env` from public IP |
| `deploy.sh` | Deploy / redeploy the stack |

---

## Part A — Oracle Console (browser)

### 1. Create the VM

1. OCI → **Compute** → **Instances** → **Create instance**
2. **Name:** `commerce-engine`
3. **Image:** Ubuntu 22.04 or 24.04 (**aarch64**)
4. **Shape:** `VM.Standard.A1.Flex`
   - **2 OCPUs**, **8 GB RAM** (minimum for full stack)
   - Boot volume: **50–100 GB**
5. **Networking:** assign a **public IPv4**
6. **SSH keys:** paste your laptop’s public key (`cat ~/.ssh/id_ed25519.pub`)
7. **Create**

Note the **public IP** (e.g. `129.146.x.x`).

### 2. Open security list (OCI firewall)

VCN → **Security Lists** → default → **Add ingress rules**:

| Source | Protocol | Port |
|--------|----------|------|
| `0.0.0.0/0` | TCP | 22 |
| `0.0.0.0/0` | TCP | 8000 |
| `0.0.0.0/0` | TCP | 3000 |
| `0.0.0.0/0` | TCP | 3001 |
| `0.0.0.0/0` | TCP | 3002 |
| `0.0.0.0/0` | TCP | 3003 |

(Tighten `0.0.0.0/0` later to your IP if you want.)

---

## Part B — On the VM (SSH)

### 3. SSH into the VM

From your laptop:

```bash
ssh ubuntu@YOUR_PUBLIC_IP
```

### 4. One-time VM setup

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl

git clone https://github.com/amanisrajpoot/ecomengine.git
cd ecomengine
git checkout cursor/docker-full-stack-dfc8   # or main after merge

chmod +x scripts/*.sh
./scripts/vm-setup.sh
```

If Docker was just installed, **log out and SSH back in** (or `newgrp docker`).

### 5. Create `.env` (auto)

```bash
cd ~/ecomengine
./scripts/gen-env.sh YOUR_PUBLIC_IP
nano .env   # optional: review passwords
```

Or manual:

```bash
cp .env.production.example .env
nano .env
```

Set at minimum:

```env
PUBLIC_HOST=YOUR_PUBLIC_IP
NEXT_PUBLIC_API_URL=http://YOUR_PUBLIC_IP:8000
CORS_ORIGINS=http://YOUR_PUBLIC_IP:3000,http://YOUR_PUBLIC_IP:3001,http://YOUR_PUBLIC_IP:3002,http://YOUR_PUBLIC_IP:3003
JWT_SECRET=<long-random-string>
POSTGRES_PASSWORD=<strong-password>
OTP_ECHO_IN_RESPONSE=false
```

`DATABASE_URL` password must match `POSTGRES_PASSWORD`.

### 6. Deploy

```bash
cd ~/ecomengine
./scripts/deploy.sh
```

Or without script:

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

First build: **10–15 minutes** on Ampere.

### 7. Verify

```bash
curl http://localhost:8000/health
docker compose -f docker-compose.prod.yml ps
```

From your laptop browser:

- http://YOUR_PUBLIC_IP:3000 — Customer
- http://YOUR_PUBLIC_IP:3001 — Merchant
- http://YOUR_PUBLIC_IP:3002 — Rider
- http://YOUR_PUBLIC_IP:3003 — Admin
- http://YOUR_PUBLIC_IP:8000/docs — API

### 8. Demo login

```bash
docker compose -f docker-compose.prod.yml exec backend cat /app/demo.env
```

Use emails/passwords from output; paste `NEXT_PUBLIC_TENANT_ID` on each app login.

---

## After reboot

Nothing extra — Docker starts, containers restart automatically.

Check:

```bash
docker compose -f docker-compose.prod.yml ps
```

---

## Useful commands

```bash
# Logs
docker compose -f docker-compose.prod.yml logs -f

# Logs for one service
docker compose -f docker-compose.prod.yml logs -f backend

# Stop everything
docker compose -f docker-compose.prod.yml down

# Update code and redeploy
cd ~/ecomengine && git pull
./scripts/deploy.sh

# Re-seed demo data
docker compose -f docker-compose.prod.yml exec backend python -m app.scripts.seed_demo
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Can't reach ports from browser | OCI security list + run `./scripts/vm-setup.sh` again for iptables |
| Build runs out of memory | Use 8GB VM; `vm-setup.sh` adds 2GB swap |
| Frontends call wrong API | Fix `NEXT_PUBLIC_API_URL` in `.env`, then `docker compose -f docker-compose.prod.yml build customer merchant rider admin && docker compose -f docker-compose.prod.yml up -d` |
| CORS errors | `CORS_ORIGINS` must match exact browser URLs (with IP + port) |
