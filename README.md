# 🐰 Bramblewick

A small rabbit companion for Claude Code. She sits quietly, watches what you're working on, and occasionally shares a witty observation in your status bar.

```
📋 brainstorming | 🧠 ctx 45% | ↑12k ↓8k  🐰｢你已经问了三遍同一个问题了，要不要先睡一觉？｣
```

## How it works

Every 30 minutes, Bramblewick reads your current session transcript, passes the recent conversation to Claude Haiku, and generates one contextual comment — max 50 characters, no empty encouragement, just honest observations.

Between triggers, she costs zero tokens. She only speaks when she has something to say.

## Requirements

- Claude Code with `statusLine` configured
- Python 3
- `curl`
- `ANTHROPIC_API_KEY` set in your environment or `~/.claude/settings.json`

## Install

```bash
git clone https://github.com/seangreenidge949-lang/bramblewick
cd bramblewick
bash install.sh
```

That's it. Bramblewick will appear the next time your status bar refreshes.

## Adjust trigger interval

Default is 30 minutes. To change it, add to `~/.claude/settings.json`:

```json
{
  "env": {
    "BRAMBLEWICK_INTERVAL": "1800"
  }
}
```

Unit is seconds. `900` = 15 min, `3600` = 1 hour.

## Manual reset

To force an immediate new comment:

```bash
rm ~/.claude/bramblewick-state.json
```
