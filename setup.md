# GBPJPY AI Trade Analyst Bot — Setup Guide

## Architecture

```
MT5 (EA) --screenshots+data--> FastAPI Server --analysis--> Claude API
                                     |
                                     +--> Telegram Bot --> You
```

Three components:
1. **MT5 Expert Advisor** — captures charts and sends data to the server
2. **Python FastAPI Server** — receives data, calls Claude API, sends results to Telegram
3. **Telegram Bot** — delivers trade setups with Execute/Skip buttons

---

## Prerequisites

- A VPS (Hetzner recommended) running Ubuntu 22.04+
- Docker and Docker Compose installed on the VPS
- MetaTrader 5 running on a Windows machine or VPS
- A Telegram account

---

## Step 1: Create a Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send `/newbot`
3. Choose a name (e.g., "GBPJPY Analyst") and username (e.g., `gbpjpy_analyst_bot`)
4. Copy the **bot token** — you'll need it later
5. Send a message to your new bot (just say "hello")
6. Get your **chat ID**: search for **@userinfobot** on Telegram, start it, and it will show your chat ID

---

## Step 2: Get an Anthropic API Key

1. Go to [console.anthropic.com](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to **API Keys**
4. Create a new key and copy it

---

## Step 3: Deploy the Server on Hetzner VPS

### 3.1 — Initial server setup

```bash
# SSH into your VPS
ssh root@YOUR_VPS_IP

# Install Docker (if not already installed)
curl -fsSL https://get.docker.com | sh
```

### 3.2 — Clone the repository

```bash
git clone https://github.com/manuham/GBPJPY-AI-Trade-Analyst-Bot.git
cd GBPJPY-AI-Trade-Analyst-Bot
```

### 3.3 — Configure environment variables

```bash
cp server/.env.example server/.env
nano server/.env
```

Fill in your values:
```
ANTHROPIC_API_KEY=sk-ant-your-key-here
TELEGRAM_BOT_TOKEN=123456789:your-token-here
TELEGRAM_CHAT_ID=your-chat-id-here
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO
```

### 3.4 — Build and start

```bash
docker compose up -d --build
```

### 3.5 — Verify it's running

```bash
# Check container status
docker compose ps

# Check logs
docker compose logs -f

# Test health endpoint
curl http://localhost:8000/health
```

You should see `{"status":"ok","last_analysis":false,"setups_count":0}`.

### 3.6 — Open the firewall port

```bash
ufw allow 8000/tcp
```

> **Security note**: For production, consider using a reverse proxy (nginx) with HTTPS and restrict port 8000 to your MT5 machine's IP only.

---

## Step 4: Configure the MT5 Expert Advisor

### 4.1 — Allow WebRequest URLs in MT5

This is required for the EA to send HTTP requests.

1. Open MetaTrader 5
2. Go to **Tools → Options → Expert Advisors**
3. Check **"Allow WebRequest for listed URL"**
4. Click **Add** and enter: `http://YOUR_VPS_IP:8000`
5. Click **OK**

### 4.2 — Install the EA

1. Copy `mt5/GBPJPY_Analyst.mq5` to your MT5 data folder:
   ```
   MQL5/Experts/GBPJPY_Analyst.mq5
   ```
   (In MT5: File → Open Data Folder → MQL5 → Experts)
2. In MT5 Navigator, right-click **Expert Advisors** and select **Refresh**
3. Compile the EA: double-click to open in MetaEditor, press F7

### 4.3 — Attach to a GBPJPY chart

1. Open a **GBPJPY** chart (any timeframe — the EA opens its own temporary charts)
2. Drag the EA from the Navigator onto the chart
3. In the **Inputs** tab, configure:

| Parameter | Default | Description |
|-----------|---------|-------------|
| ServerURL | `http://127.0.0.1:8000/analyze` | Change to `http://YOUR_VPS_IP:8000/analyze` |
| LondonOpenHour | 8 | London open hour in CET |
| LondonOpenMin | 0 | London open minute |
| NYOpenHour | 14 | NY open hour in CET |
| NYOpenMin | 30 | NY open minute |
| TimezoneOffset | 0 | Server time minus CET (e.g., if broker is UTC+2 and CET is UTC+1, set to 1) |
| CooldownMinutes | 30 | Minimum time between scans |
| ScreenshotWidth | 1920 | Screenshot width in pixels |
| ScreenshotHeight | 1080 | Screenshot height in pixels |
| ManualTrigger | false | Set to true to force an immediate scan |

4. Check **"Allow Algo Trading"** and click **OK**
5. Make sure the **AutoTrading** button in the MT5 toolbar is enabled (green icon)

---

## Step 5: Test the Connection

### Quick test from VPS

```bash
curl http://YOUR_VPS_IP:8000/health
```

### Test from MT5

1. Click the **"Scan GBPJPY"** button on the chart (added by the EA)
2. Check the **Experts** tab in MT5 for log messages
3. Check your Telegram for the analysis result

### Test Telegram bot

Send these commands to your bot on Telegram:
- `/start` — verify the bot responds
- `/status` — check connection status
- `/help` — see available commands

---

## Troubleshooting

### EA says "URL not allowed"
- Go to Tools → Options → Expert Advisors → Allowed URLs and add `http://YOUR_VPS_IP:8000`

### EA says "WebRequest failed"
- Check that the VPS firewall allows port 8000
- Verify the server is running: `docker compose ps`
- Test from the MT5 machine: open `http://YOUR_VPS_IP:8000/health` in a browser

### No Telegram messages
- Verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in `.env`
- Make sure you've sent at least one message to the bot first
- Check server logs: `docker compose logs -f`

### Claude API errors
- Verify `ANTHROPIC_API_KEY` in `.env`
- Check your API credit balance at console.anthropic.com
- Check server logs for specific error messages

---

## Operations

### View logs
```bash
docker compose logs -f
```

### Restart the server
```bash
docker compose restart
```

### Update to latest version
```bash
git pull
docker compose up -d --build
```

### Stop the server
```bash
docker compose down
```
