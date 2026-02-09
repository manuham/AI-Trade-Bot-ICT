# GBPJPY AI Trade Analyst Bot

Automated GBPJPY analysis system that captures MetaTrader 5 chart screenshots at London open (08:00 CET) and NY open (14:30 CET), sends them to Claude's API for institutional-grade ICT analysis, and delivers trade setups via Telegram.

## Components

| Component | Path | Description |
|-----------|------|-------------|
| MT5 Expert Advisor | `mt5/GBPJPY_Analyst.mq5` | Captures H1/M15/M5 screenshots + market data, sends to server |
| FastAPI Server | `server/` | Receives data, calls Claude API with web search, sends results |
| Telegram Bot | integrated in server | Delivers formatted trade setups with Execute/Skip buttons |

## How It Works

```
MT5 EA ──screenshots + JSON──> FastAPI Server ──images + data──> Claude API
                                     │                              │
                                     │          analysis result <───┘
                                     │
                                     └──formatted alerts──> Telegram Bot ──> You
```

1. The EA runs on a GBPJPY chart and triggers at session open times
2. It captures screenshots of H1, M15, and M5 timeframes and gathers market data (bid/ask, ATR, OHLC)
3. Everything is POSTed to the FastAPI server as multipart form data
4. The server sends the images + data to Claude (with web search enabled for live fundamentals)
5. Claude analyzes using ICT methodology (BOS, ChoCH, order blocks, FVGs, liquidity sweeps)
6. Structured trade setups are delivered to Telegram with inline Execute/Skip buttons

## Quick Start

```bash
# 1. Clone and configure
git clone https://github.com/manuham/GBPJPY-AI-Trade-Analyst-Bot.git
cd GBPJPY-AI-Trade-Analyst-Bot
cp server/.env.example server/.env
# Edit server/.env with your API keys

# 2. Run with Docker
docker compose up -d --build

# 3. Install the EA in MT5 (see setup.md)
```

## Telegram Commands

- `/scan` — trigger manual analysis or re-send last result
- `/status` — show bot status and last scan time
- `/help` — show available commands

## Setup

See [setup.md](setup.md) for full deployment instructions including:
- Creating a Telegram bot
- Getting an Anthropic API key
- Deploying to a VPS
- Configuring the MT5 EA
- Testing the connection

## Project Structure

```
├── mt5/
│   └── GBPJPY_Analyst.mq5      # MetaTrader 5 Expert Advisor
├── server/
│   ├── main.py                  # FastAPI app and endpoints
│   ├── analyzer.py              # Claude API integration
│   ├── telegram_bot.py          # Telegram bot logic
│   ├── config.py                # Environment variable config
│   ├── models.py                # Pydantic data models
│   ├── requirements.txt         # Python dependencies
│   └── .env.example             # Environment variable template
├── Dockerfile
├── docker-compose.yml
└── setup.md                     # Deployment guide
```
