# 🦞 ClawLens

[![PyPI](https://img.shields.io/pypi/v/clawlens)](https://pypi.org/project/clawlens/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![GitHub stars](https://img.shields.io/github/stars/0xChitlin/clawlens)](https://github.com/0xChitlin/clawlens/stargazers)

**Full observability for your .claw agent.** Watch your agent think, track costs, debug crons, and browse memory — all in one dashboard.

One command. Zero config. Auto-detects everything.

```bash
pip install clawlens && clawlens
```

Opens at **http://localhost:8900** and you're done.

![Flow Visualization](https://clawlens.com/screenshots/flow.png)

## What You Get

- **Flow** — Live animated diagram showing messages flowing through channels, brain, tools, and back
- **Overview** — Health checks, activity heatmap, session counts, model info
- **Usage** — Token and cost tracking with daily/weekly/monthly breakdowns
- **Sessions** — Active agent sessions with model, tokens, last activity
- **Crons** — Scheduled jobs with status, next run, duration
- **Logs** — Color-coded real-time log streaming
- **Memory** — Browse SOUL.md, MEMORY.md, AGENTS.md, daily notes
- **Transcripts** — Chat-bubble UI for reading session histories

## Screenshots

| Flow | Overview | Sub-Agent |
|------|----------|-----------|
| ![Flow](https://clawlens.com/screenshots/flow.png) | ![Overview](https://clawlens.com/screenshots/overview.png) | ![Sub-Agent](https://clawlens.com/screenshots/subagent.png) |

| Summary | Crons | Memory |
|---------|-------|--------|
| ![Summary](https://clawlens.com/screenshots/summary.png) | ![Crons](https://clawlens.com/screenshots/crons.png) | ![Memory](https://clawlens.com/screenshots/memory.png) |

## Install

**pip (recommended):**
```bash
pip install clawlens
clawlens
```

**One-liner:**
```bash
curl -sSL https://raw.githubusercontent.com/0xChitlin/clawlens/main/install.sh | bash
```

**From source:**
```bash
git clone https://github.com/0xChitlin/clawlens.git
cd clawlens && pip install flask && python3 dashboard.py
```

## Configuration

Most people don't need any config. ClawLens auto-detects your workspace, logs, sessions, and crons.

If you do need to customize:

```bash
clawlens --port 9000              # Custom port (default: 8900)
clawlens --host 127.0.0.1         # Bind to localhost only
clawlens --workspace ~/mybot      # Custom workspace path
clawlens --name "Alice"           # Your name in Flow visualization
```

All options: `clawlens --help`

## Requirements

- Python 3.8+
- Flask (installed automatically via pip)
- OpenClaw running on the same machine
- Linux or macOS

## Cloud Deployment

See the **[Cloud Testing Guide](docs/CLOUD_TESTING.md)** for SSH tunnels, reverse proxy, and Docker.

## License

MIT

---

<p align="center">
  <strong>🦞 Full observability for your .claw agent</strong><br>
  <sub>Built by <a href="https://github.com/vivekchand">@vivekchand</a> · <a href="https://clawlens.com">clawlens.com</a> · Part of the <a href="https://github.com/openclaw/openclaw">OpenClaw</a> ecosystem</sub>
</p>
